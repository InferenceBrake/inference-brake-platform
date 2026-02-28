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

class InferenceBrake {
  /**
   * Create an InferenceBrake client
   * @param {Object} options
   * @param {string} options.apiKey - Your InferenceBrake API key
   * @param {string} [options.supabaseUrl] - Your Supabase URL (or set INFERENCEBRAKE_URL env)
   * @param {number} [options.timeout=10000] - Request timeout in ms
   * @param {boolean} [options.autoStop=false] - Throw on loop detected
   */
  constructor({ apiKey, supabaseUrl, timeout = 10000, autoStop = false }) {
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
  }

  /**
   * Check if reasoning indicates a loop
   * @param {string} reasoning - The agent's reasoning text
   * @param {string} sessionId - Unique session identifier
   * @param {number} [threshold] - Optional custom threshold
   * @returns {Promise<CheckStatus>}
   */
  async check(reasoning, sessionId, threshold) {
    const url = `${this.baseUrl}/check`;
    
    const payload = {
      reasoning,
      session_id: sessionId,
    };
    
    if (threshold !== undefined) {
      payload.threshold = threshold;
    }

    try {
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
        throw new RateLimitError(
          'Rate limit exceeded. Upgrade at inferencebrake.dev/pricing'
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

    } catch (error) {
      if (error.name === 'AbortError') {
        throw new InferenceBrakeError('Request timeout');
      }
      throw error;
    }
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
  inferencebrakeMonitor,
};

// Also support ES modules
module.exports.default = InferenceBrake;
