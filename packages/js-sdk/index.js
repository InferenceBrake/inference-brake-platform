/**
 * InferenceBrake Node.js SDK
 * Semantic loop detection for AI agents.
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

const DEFAULT_SUPABASE_URL = 'https://ocnjiyiqeifllbyqohks.supabase.co';

const STEERING_MESSAGE =
  'You are repeating yourself without making progress. Stop retrying the same ' +
  'action. Reassess what is blocking you, try a different approach, or ask for ' +
  'help. Do not repeat the previous action verbatim.';

function steeringMessage(status) {
  return `${STEERING_MESSAGE}\n\nDetected: ${status.message}`;
}

class CheckStatus {
  constructor(data) {
    this.action = data.action; // "KILL" or "PROCEED"
    this.loopDetected = data.loop_detected;
    this.similarity = data.similarity ?? 0;
    this.status = data.status; // "safe", "warning", "danger"
    this.message = data.message;
    this.confidence = data.confidence ?? 0.0;
    this.actionRepeatCount = data.action_repeat_count ?? 0;
    this.ngramOverlap = data.ngram_overlap ?? 0.0;
    this.detectors = data.detectors ?? {};
    this.estimatedCostSaved = data.estimated_cost_saved ?? 0.0;
    this.degraded = data.degraded ?? false;
  }

  get shouldStop() {
    return this.action === 'KILL';
  }

  get score() {
    return this.confidence;
  }

  get detectorTriggered() {
    return Object.entries(this.detectors)
      .filter(([, fired]) => fired)
      .map(([name]) => name)
      .join(', ');
  }

  get estimatedSavings() {
    return this.estimatedCostSaved;
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
      estimatedCostSaved: this.estimatedCostSaved,
      degraded: this.degraded,
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

class LoopDetectedError extends InferenceBrakeError {
  constructor(message = 'Loop detected') {
    super(message);
    this.name = 'LoopDetectedError';
  }
}

// Alias used by the framework adapters.
const DoomLoopException = LoopDetectedError;

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
      this.queue.push({ ...request, timestamp: Date.now() });
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
          this.queue = saved.filter((item) => Date.now() - item.timestamp < 3600000);
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

/**
 * Decides what happens when a loop is detected.
 *
 * Precedence on detection:
 *   1. escalate (while under maxEscalations)
 *   2. onLoop callback
 *   3. throw LoopDetectedError when autoStop
 */
class LoopPolicy {
  constructor({ autoStop = true, maxEscalations = 2, escalate = null, onLoop = null } = {}) {
    this.autoStop = autoStop;
    this.maxEscalations = maxEscalations;
    this.escalate = escalate;
    this.onLoop = onLoop;
    this._escalations = 0;
  }

  handle(status) {
    if (!status.shouldStop) {
      return 'continue';
    }
    if (this.escalate && this._escalations < this.maxEscalations) {
      this._escalations++;
      console.warn(
        `InferenceBrake: loop detected, escalating (${this._escalations}/${this.maxEscalations})`
      );
      this.escalate(status, this._escalations);
      return 'escalate';
    }
    if (this.onLoop) {
      this.onLoop(status);
    }
    if (this.autoStop) {
      throw new LoopDetectedError(status.message);
    }
    return 'stop';
  }

  get escalationsUsed() {
    return this._escalations;
  }

  reset() {
    this._escalations = 0;
  }
}

class InferenceBrake {
  /**
   * Create an InferenceBrake client
   * @param {Object} options
   * @param {string} options.apiKey - Your InferenceBrake API key
   * @param {string} [options.supabaseUrl] - Custom API base URL (defaults to InferenceBrake cloud)
   * @param {number} [options.timeout=10000] - Request timeout in ms
   * @param {boolean} [options.autoStop=false] - Throw on loop detected
   * @param {boolean} [options.failOpen=true] - Return a safe status on network/5xx errors
   * @param {number} [options.maxRetries=3] - Max retry attempts
   * @param {number} [options.retryDelay=1000] - Initial retry delay in ms
   * @param {number} [options.retryBackoff=2] - Exponential backoff multiplier
   */
  constructor({
    apiKey,
    supabaseUrl,
    timeout = 10000,
    autoStop = false,
    failOpen = true,
    maxRetries = 3,
    retryDelay = 1000,
    retryBackoff = 2,
    circuitBreakerThreshold = 5,
    circuitBreakerTimeout = 30000,
  }) {
    this.apiKey = apiKey;
    const envUrl =
      typeof process !== 'undefined' && process.env ? process.env.INFERENCEBRAKE_URL : undefined;
    this.supabaseUrl = supabaseUrl || envUrl || DEFAULT_SUPABASE_URL;

    this.baseUrl = `${this.supabaseUrl}/functions/v1`;
    this.timeout = timeout;
    this.autoStop = autoStop;
    this.failOpen = failOpen;
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
        if (typeof localStorage !== 'undefined' && localStorage) {
          try {
            localStorage.setItem('inferencebrake_queue', JSON.stringify(queue));
          } catch (e) {}
        }
      },
      restoreFn: () => {
        if (typeof localStorage !== 'undefined' && localStorage) {
          try {
            const saved = localStorage.getItem('inferencebrake_queue');
            return saved ? JSON.parse(saved) : [];
          } catch (e) {}
        }
        return [];
      },
    });
  }

  isOnline() {
    return this.offlineQueue.isOnline();
  }

  getQueueSize() {
    return this.offlineQueue.size;
  }

  async flushQueue() {
    return this.offlineQueue.flush();
  }

  clearQueue() {
    this.offlineQueue.clear();
  }

  getRetryDelay(attempt) {
    return this.retryDelay * Math.pow(this.retryBackoff, attempt);
  }

  isRetryable(error) {
    if (error instanceof RateLimitError) {
      const match = error.message.match(/retry after (\d+)/i);
      if (match) {
        this.retryDelay = parseInt(match[1], 10) * 1000;
        return true;
      }
    }
    return (
      error.message.includes('timeout') ||
      error.message.includes('network') ||
      error.message.includes('ECONNREFUSED') ||
      error.message.includes('ETIMEDOUT')
    );
  }

  async executeWithRetry(requestFn) {
    if (!this.circuitBreaker.canAttempt()) {
      throw new CircuitBreakerError(
        `Circuit breaker open. Retry after ${Math.ceil(
          (this.circuitBreaker.nextAttempt - Date.now()) / 1000
        )}s`
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

        if (attempt >= this.maxRetries) {
          this.circuitBreaker.recordFailure();
          break;
        }
        if (!this.isRetryable(error) || !(error instanceof InferenceBrakeError)) {
          this.circuitBreaker.recordFailure();
          throw error;
        }

        const delay = this.getRetryDelay(attempt);
        console.log(
          `InferenceBrake: Retry attempt ${attempt + 1}/${this.maxRetries} after ${delay}ms`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }

    this.circuitBreaker.recordFailure();
    throw lastError;
  }

  _failOpen(reason) {
    const message = `InferenceBrake unavailable (${reason}); failing open`;
    console.warn(message);
    return new CheckStatus({
      action: 'PROCEED',
      loop_detected: false,
      similarity: 0,
      status: 'safe',
      message,
      degraded: true,
    });
  }

  /**
   * Check if reasoning indicates a loop
   * @param {string} reasoning - The agent's reasoning text
   * @param {string} sessionId - Unique session identifier
   * @param {Object|number} [options] - { threshold, action } or a numeric threshold
   * @returns {Promise<CheckStatus>}
   */
  async check(reasoning, sessionId, options = {}) {
    if (typeof options === 'number') {
      options = { threshold: options };
    }
    const { threshold, action } = options;

    return this.executeWithRetry(async () => {
      const url = `${this.baseUrl}/check`;

      const payload = { reasoning, session_id: sessionId };
      if (threshold !== undefined) payload.threshold = threshold;
      if (action !== undefined && action !== null) payload.action = action;

      let response;
      try {
        response = await fetch(url, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(this.timeout),
        });
      } catch (e) {
        if (this.failOpen) {
          return this._failOpen(`request failed: ${e.message}`);
        }
        throw new InferenceBrakeError(`Request failed: ${e.message}`);
      }

      if (response.status === 401) {
        throw new AuthenticationError();
      }

      if (response.status === 429) {
        const data = await response.json().catch(() => ({}));
        const retryAfter = response.headers.get('retry-after');
        throw new RateLimitError(
          `Rate limit exceeded. Upgrade at inferencebrake.dev/pricing${
            retryAfter ? `. Retry after ${retryAfter}s` : ''
          }`
        );
      }

      if (response.status >= 500) {
        if (this.failOpen) {
          return this._failOpen(`API error ${response.status}`);
        }
        throw new InferenceBrakeError(`API error: ${response.status}`);
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new InferenceBrakeError(
          `API error: ${response.status} - ${error.error || error.message}`
        );
      }

      const data = await response.json();
      const status = new CheckStatus(data);

      if (this.autoStop && status.shouldStop) {
        throw new LoopDetectedError(
          `Loop detected: ${status.message} (confidence: ${status.confidence.toFixed(2)})`
        );
      }

      return status;
    });
  }

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

  async getSessionHistory(sessionId, limit = 50) {
    const url = `${this.baseUrl}/session-history?session_id=${sessionId}&limit=${limit}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: { Authorization: `Bearer ${this.apiKey}` },
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

function _defaultExtract(result) {
  try {
    const choice = result?.choices?.[0];
    if (choice?.message?.content) return choice.message.content;
    if (choice?.text) return choice.text;
  } catch (e) {}
  return typeof result === 'string' ? result : JSON.stringify(result);
}

/**
 * Wrap an async function so its result is checked for a loop.
 *
 * @param {Function} fn - Async function performing one model call or agent step
 * @param {Object} options
 * @returns {Function}
 */
function guarded(fn, options = {}) {
  const {
    apiKey,
    supabaseUrl,
    sessionId,
    timeout,
    autoStop = true,
    failOpen = true,
    extract,
    action,
    loopKey,
    onLoop,
    escalate,
    maxEscalations = 2,
  } = options;

  const guard = new InferenceBrake({ apiKey, supabaseUrl, timeout, failOpen });
  const policy = new LoopPolicy({ autoStop, maxEscalations, escalate, onLoop });

  return async function (...args) {
    const result = await fn.apply(this, args);
    const text = extract ? extract(result) : _defaultExtract(result);
    if (text) {
      let identity = action ? action(result) : null;
      if (identity !== null && identity !== undefined && loopKey) {
        try {
          identity = loopKey(String(identity));
        } catch (e) {
          console.warn('loopKey failed; falling back to raw action', e);
        }
      }
      const sid =
        typeof sessionId === 'function'
          ? String(sessionId(...args))
          : sessionId || fn.name || 'guarded';
      const status = await guard.check(String(text), sid, { action: identity });
      policy.handle(status);
    }
    return result;
  };
}

function _langchainText(output) {
  try {
    const generation = output?.generations?.[0]?.[0];
    if (generation?.text) return generation.text;
    if (generation?.message?.content) return generation.message.content;
    if (output?.llmOutput?.text) return output.llmOutput.text;
  } catch (e) {}
  return null;
}

/**
 * LangChain.js callback handler. Duck-typed, so langchain is not a dependency.
 *
 *   const handler = new InferenceBrakeCallbackHandler({ apiKey: 'ib_...' });
 *   await chain.invoke(input, { callbacks: [handler] });
 */
class InferenceBrakeCallbackHandler {
  constructor({
    apiKey,
    supabaseUrl,
    sessionId,
    threshold,
    autoStop = true,
    failOpen = true,
    action,
    loopKey,
    onLoopDetected,
    escalate,
    maxEscalations = 2,
  } = {}) {
    this.name = 'InferenceBrakeCallbackHandler';
    this._client = new InferenceBrake({ apiKey, supabaseUrl, failOpen });
    this.sessionId = sessionId || `langchain-${Math.random().toString(36).slice(2)}`;
    this.threshold = threshold;
    this.action = action;
    this.loopKey = loopKey;
    this.stepCount = 0;
    this.lastStatus = null;
    this._policy = new LoopPolicy({
      autoStop,
      maxEscalations,
      escalate,
      onLoop: onLoopDetected,
    });
  }

  async handleLLMStart() {
    return undefined;
  }

  async handleLLMEnd(output) {
    const text = _langchainText(output);
    if (!text) return undefined;

    this.stepCount++;
    let identity = this.action ? this.action(text) : null;
    if (identity !== null && identity !== undefined && this.loopKey) {
      try {
        identity = this.loopKey(String(identity));
      } catch (e) {
        console.warn('loopKey failed; falling back to raw action', e);
      }
    }

    const status = await this._client.check(text, this.sessionId, {
      threshold: this.threshold,
      action: identity,
    });
    this.lastStatus = status;

    if (status.shouldStop) {
      console.warn(
        `InferenceBrake: loop detected at step ${this.stepCount} ` +
          `(confidence ${status.confidence.toFixed(2)}, detectors: ${status.detectorTriggered || 'none'})`
      );
      this._policy.handle(status);
    }
    return undefined;
  }

  async handleLLMError() {
    return undefined;
  }

  reset(newSessionId) {
    this.stepCount = 0;
    this.lastStatus = null;
    this._policy.reset();
    if (newSessionId) this.sessionId = newSessionId;
  }
}

function inferencebrakeMonitor({ apiKey, supabaseUrl, sessionId }) {
  const guard = new InferenceBrake({ apiKey, supabaseUrl });
  let stepCount = 0;
  let sid = sessionId || `auto-${Date.now()}`;

  return {
    async check(reasoning) {
      stepCount++;
      const status = await guard.check(reasoning, sid);
      if (status.shouldStop) {
        console.log(`Warning: Loop detected at step ${stepCount}: ${status.message}`);
      }
      return status;
    },
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
  LoopDetectedError,
  DoomLoopException,
  LoopPolicy,
  OfflineQueue,
  InferenceBrakeCallbackHandler,
  guarded,
  inferencebrakeMonitor,
  steeringMessage,
  STEERING_MESSAGE,
};

module.exports.default = InferenceBrake;
