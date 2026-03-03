/**
 * InferenceBrake Node.js SDK
 * Semantic loop detection for AI agents using Supabase free embeddings
 * 
 * Installation:
 *   npm install inferencebrake
 * 
 * Usage:
 *   const { InferenceBrake } = require('inferencebrake');
 *   
 *   const guard = new InferenceBrake({ apiKey: 'ib_your_key' });
 *   const status = await guard.check('reasoning text', 'agent-1');
 *   
 *   if (status.shouldStop) {
 *     console.log('Loop detected!');
 *   }
 */

class CheckStatus {
  constructor(data) {
    this.action = data.action;           // "KILL" or "PROCEED"
    this.loopDetected = data.loop_detected;
    this.similarity = data.similarity;
    this.status = data.status;           // "safe", "warning", "danger"
    this.message = data.message;
    this.confidence = data.confidence ?? 0.0;
    this.actionRepeatCount = data.action_repeat_count ?? 0;
    this.ngramOverlap = data.ngram_overlap ?? 0.0;
    this.detectors = data.detectors ?? {};
  }

  get shouldStop() {
    return this.action === 'KILL';
  }

  get estimatedSavings() {
    if (this.shouldStop) {
      return 0.23; // ~GPT-4 cost for remaining steps
    }
    return 0.0;
  }

  toJSON() {
    return {
      action: this.action,
      loopDetected: this.loopDetected,
      similarity: this.similarity,
      status: this.status,
      message: this.message,
      confidence: this.confidence,
      actionRepeatCount: this.actionRepeatCount,
      ngramOverlap: this.ngramOverlap,
      detectors: this.detectors,
      shouldStop: this.shouldStop,
    };
  }
}

class InferenceBrakeError extends Error {
  constructor(message) {
    super(message);
    this.name = 'InferenceBrakeError';
  }
}

class AuthenticationError extends InferenceBrakeError {
  constructor(message = 'Invalid API key') {
    super(message);
    this.name = 'AuthenticationError';
  }
}

class RateLimitError extends InferenceBrakeError {
  constructor(message = 'Rate limit exceeded') {
    super(message);
    this.name = 'RateLimitError';
  }
}

class CircuitBreakerError extends InferenceBrakeError {
  constructor(message = 'Circuit breaker open') {
    super(message);
    this.name = 'CircuitBreakerError';
  }
}

class OfflineQueue {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 100;
    this.queue = [];
    this.persistFn = options.persistFn;
    this.restoreFn = options.restoreFn;
    
    if (this.restoreFn) {
      this.restore();
    }
    
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.flush());
    }
  }

  isOnline() {
    if (typeof navigator !== 'undefined') {
      return navigator.onLine;
    }
    return true;
  }

  enqueue(request) {
    if (!this.isOnline()) {
      if (this.queue.length >= this.maxSize) {
        throw new InferenceBrakeError('Offline queue full');
      }
      this.queue.push({
        ...request,
        timestamp: Date.now(),
      });
      this.persist();
      return true;
    }
    return false;
  }

  dequeue() {
    return this.queue.shift();
  }

  clear() {
    this.queue = [];
    this.persist();
  }

  persist() {
    if (this.persistFn && this.queue.length > 0) {
      try {
        this.persistFn(this.queue);
      } catch (e) {
        console.warn('Failed to persist queue:', e);
      }
    }
  }

  restore() {
    if (this.restoreFn) {
      try {
        const saved = this.restoreFn();
        if (Array.isArray(saved)) {
          this.queue = saved.filter(item => 
            Date.now() - item.timestamp < 3600000 // 1 hour max
          );
        }
      } catch (e) {
        console.warn('Failed to restore queue:', e);
      }
    }
  }

  async flush() {
    if (!this.isOnline() || this.queue.length === 0) {
      return;
    }

    const items = [...this.queue];
    this.queue = [];

    for (const item of items) {
      try {
        await item.execute();
      } catch (e) {
        console.warn('Failed to flush queued request:', e);
      }
    }
  }

  get size() {
    return this.queue.length;
  }
}

class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.successThreshold = options.successThreshold || 2;
    this.timeout = options.timeout || 30000;
    this.resetTimeout = options.resetTimeout || 30000;
    
    this.state = 'CLOSED';
    this.failures = 0;
    this.successes = 0;
    this.nextAttempt = Date.now();
  }

  get isOpen() {
    return this.state === 'OPEN';
  }

  recordSuccess() {
    this.failures = 0;
    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.successThreshold) {
        this.state = 'CLOSED';
        this.successes = 0;
      }
    }
  }

  recordFailure() {
    this.failures++;
    this.successes = 0;
    
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.resetTimeout;
    }
  }

  canAttempt() {
    if (this.state === 'OPEN') {
      if (Date.now() >= this.nextAttempt) {
        this.state = 'HALF_OPEN';
        this.failures = 0;
        return true;
      }
      return false;
    }
    return true;
  }
}

class InferenceBrake {
  /**
   * Create an InferenceBrake client
   * @param {Object} options
   * @param {string} options.apiKey - Your InferenceBrake API key
   * @param {string} [options.supabaseUrl] - Your Supabase URL (or set INFERENCEBRAKE_URL env)
   * @param {number} [options.timeout=10000] - Request timeout in ms
   * @param {boolean} [options.autoStop=false] - Throw on loop detected
   * @param {number} [options.maxRetries=3] - Max retry attempts
   * @param {number} [options.retryDelay=1000] - Initial retry delay in ms
   * @param {number} [options.retryBackoff=2] - Exponential backoff multiplier
   */
  constructor({ 
    apiKey, 
    supabaseUrl, 
    timeout = 10000, 
    autoStop = false,
    maxRetries = 3,
    retryDelay = 1000,
    retryBackoff = 2,
    circuitBreakerThreshold = 5,
    circuitBreakerTimeout = 30000,
  }) {
    this.apiKey = apiKey;
    this.supabaseUrl = supabaseUrl || process.env.INFERENCEBRAKE_URL;
    
    if (!this.supabaseUrl) {
      throw new InferenceBrakeError(
        'Supabase URL required. Pass supabaseUrl or set INFERENCEBRAKE_URL env variable.'
      );
    }

    this.baseUrl = `${this.supabaseUrl}/functions/v1`;
    this.timeout = timeout;
    this.autoStop = autoStop;
    this.maxRetries = maxRetries;
    this.retryDelay = retryDelay;
    this.retryBackoff = retryBackoff;
    
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: circuitBreakerThreshold,
      resetTimeout: circuitBreakerTimeout,
    });
    
    this.offlineQueue = new OfflineQueue({
      maxSize: 100,
      persistFn: (queue) => {
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('inferencebrake_queue', JSON.stringify(queue));
        }
      },
      restoreFn: () => {
        if (typeof localStorage !== 'undefined') {
          const saved = localStorage.getItem('inferencebrake_queue');
          return saved ? JSON.parse(saved) : [];
        }
        return [];
      },
    });
  }

  /**
   * Check if currently online
   * @returns {boolean}
   */
  isOnline() {
    return this.offlineQueue.isOnline();
  }

  /**
   * Get queued requests count
   * @returns {number}
   */
  getQueueSize() {
    return this.offlineQueue.size;
  }

  /**
   * Flush offline queue
   * @returns {Promise<void>}
   */
  async flushQueue() {
    return this.offlineQueue.flush();
  }

  /**
   * Clear offline queue
   */
  clearQueue() {
    this.offlineQueue.clear();
  }

  /**
   * Calculate delay with exponential backoff
   * @param {number} attempt - Current attempt number (0-indexed)
   * @returns {number} - Delay in ms
   */
  getRetryDelay(attempt) {
    return this.retryDelay * Math.pow(this.retryBackoff, attempt);
  }

  /**
   * Check if error is retryable
   * @param {Error} error - The error to check
   * @returns {boolean}
   */
  isRetryable(error) {
    if (error instanceof RateLimitError) {
      const match = error.message.match(/retry after (\d+)/i);
      if (match) {
        this.retryDelay = parseInt(match[1], 10) * 1000;
        return true;
      }
    }
    // Retry on network errors, timeouts, 5xx errors
    return error.message.includes('timeout') || 
           error.message.includes('network') ||
           error.message.includes('ECONNREFUSED') ||
           error.message.includes('ETIMEDOUT');
  }

  /**
   * Execute request with retry logic and circuit breaker
   * @param {Function} requestFn - Function that returns a promise
   * @returns {Promise<any>}
   */
  async executeWithRetry(requestFn) {
    if (!this.circuitBreaker.canAttempt()) {
      throw new CircuitBreakerError(
        `Circuit breaker open. Retry after ${Math.ceil((this.circuitBreaker.nextAttempt - Date.now()) / 1000)}s`
      );
    }
    
    let lastError;
    
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const result = await requestFn();
        this.circuitBreaker.recordSuccess();
        return result;
      } catch (error) {
        lastError = error;
        
        // Don't retry if max retries reached
        if (attempt >= this.maxRetries) {
          this.circuitBreaker.recordFailure();
          break;
        }
        
        // Don't retry on non-retryable errors
        if (!this.isRetryable(error) || !(error instanceof InferenceBrakeError)) {
          this.circuitBreaker.recordFailure();
          throw error;
        }
        
        const delay = this.getRetryDelay(attempt);
        console.log(`InferenceBrake: Retry attempt ${attempt + 1}/${this.maxRetries} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    this.circuitBreaker.recordFailure();
    throw lastError;
  }

  /**
   * Check if reasoning indicates a loop
   * @param {string} reasoning - The agent's reasoning text
   * @param {string} sessionId - Unique session identifier
   * @param {number} [threshold] - Optional custom threshold
   * @returns {Promise<CheckStatus>}
   */
  async check(reasoning, sessionId, threshold) {
    return this.executeWithRetry(async () => {
      const url = `${this.baseUrl}/check`;
      
      const payload = {
        reasoning,
        session_id: sessionId,
      };
      
      if (threshold !== undefined) {
        payload.threshold = threshold;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (response.status === 401) {
        throw new AuthenticationError();
      }

      if (response.status === 429) {
        const data = await response.json().catch(() => ({}));
        const retryAfter = response.headers.get('retry-after');
        throw new RateLimitError(
          `Rate limit exceeded. Upgrade at inferencebrake.dev/pricing${retryAfter ? `. Retry after ${retryAfter}s` : ''}`
        );
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new InferenceBrakeError(`API error: ${response.status} - ${error.error || error.message}`);
      }

      const data = await response.json();
      const status = new CheckStatus(data);

      if (this.autoStop && status.shouldStop) {
        throw new InferenceBrakeError(
          `Loop detected: ${status.message} (similarity: ${status.similarity.toFixed(2)})`
        );
      }

      return status;
    });
  }

  /**
   * Check multiple reasoning steps in batch
   * @param {string[]} reasoningList - List of reasoning texts
   * @param {string} sessionId - Session identifier
   * @returns {Promise<CheckStatus[]>}
   */
  async checkBatch(reasoningList, sessionId) {
    const results = [];
    for (const reasoning of reasoningList) {
      const status = await this.check(reasoning, sessionId);
      results.push(status);
      if (status.shouldStop) {
        break;
      }
    }
    return results;
  }

  /**
   * Get session history (requires endpoint)
   * @param {string} sessionId - Session identifier
   * @param {number} [limit=50] - Max steps to return
   */
  async getSessionHistory(sessionId, limit = 50) {
    const url = `${this.baseUrl}/session/${sessionId}?limit=${limit}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
      },
      signal: AbortSignal.timeout(this.timeout),
    });

    if (response.status === 401) {
      throw new AuthenticationError();
    }

    if (!response.ok) {
      throw new InferenceBrakeError(`API error: ${response.status}`);
    }

    return response.json();
  }
}

/**
 * Create a middleware/decorator for agent functions
 * @param {Object} options
 * @param {string} options.apiKey
 * @param {string} options.supabaseUrl
 * @param {string} [options.sessionId]
 */
function inferencebrakeMonitor({ apiKey, supabaseUrl, sessionId }) {
  const guard = new InferenceBrake({ apiKey, supabaseUrl });
  let stepCount = 0;
  let sid = sessionId || `auto-${Date.now()}`;

  return {
    /**
     * Check a reasoning step
     * @param {string} reasoning
     * @returns {Promise<CheckStatus>}
     */
    async check(reasoning) {
      stepCount++;
      const status = await guard.check(reasoning, sid);
      
      if (status.shouldStop) {
        console.log(`Warning: Loop detected at step ${stepCount}: ${status.message}`);
      }
      
      return status;
    },

    /**
     * Reset the session
     * @param {string} [newSessionId]
     */
    reset(newSessionId) {
      stepCount = 0;
      sid = newSessionId || `auto-${Date.now()}`;
    },

    get client() {
      return guard;
    },
  };
}

module.exports = {
  InferenceBrake,
  CheckStatus,
  InferenceBrakeError,
  AuthenticationError,
  RateLimitError,
  CircuitBreakerError,
  OfflineQueue,
  inferencebrakeMonitor,
};

// Also support ES modules
module.exports.default = InferenceBrake;
