export interface CheckStatusOptions {
  action: 'KILL' | 'PROCEED';
  loopDetected: boolean;
  similarity: number;
  status: 'safe' | 'warning' | 'danger';
  message: string;
  confidence?: number;
  actionRepeatCount?: number;
  ngramOverlap?: number;
  detectors?: DetectorVotes;
  estimatedCostSaved?: number;
  degraded?: boolean;
  testMode?: boolean;
  usage?: UsageInfo;
}

export interface DetectorVotes {
  semantic?: boolean;
  action?: boolean;
  ngram?: boolean;
  editdist?: boolean;
  compression?: boolean;
  token_repeat?: boolean;
  [key: string]: boolean | undefined;
}

export interface UsageInfo {
  today: number;
  month: number;
  limit: number;
  remaining: number;
}

export interface InferenceBrakeOptions {
  apiKey: string;
  supabaseUrl?: string;
  timeout?: number;
  autoStop?: boolean;
  failOpen?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  retryBackoff?: number;
  circuitBreakerThreshold?: number;
  circuitBreakerTimeout?: number;
}

export interface CheckOptions {
  threshold?: number;
  action?: string | null;
  model?: string | null;
  prompt?: string | null;
}

export interface LoopPolicyOptions {
  autoStop?: boolean;
  maxEscalations?: number;
  escalate?: (status: CheckStatus, attempt: number) => void;
  onLoop?: (status: CheckStatus) => void;
}

export interface GuardedOptions {
  apiKey?: string;
  supabaseUrl?: string;
  sessionId?: string | ((...args: unknown[]) => string);
  timeout?: number;
  autoStop?: boolean;
  failOpen?: boolean;
  extract?: (result: unknown) => string;
  action?: (result: unknown) => string | null | undefined;
  loopKey?: (action: string) => string | null;
  onLoop?: (status: CheckStatus) => void;
  escalate?: (status: CheckStatus, attempt: number) => void;
  maxEscalations?: number;
  model?: string | ((result: unknown) => string);
  prompt?: string | ((result: unknown) => string);
}

export interface CallbackHandlerOptions extends GuardedOptions {
  threshold?: number;
  onLoopDetected?: (status: CheckStatus) => void;
}

export class CheckStatus {
  readonly action: 'KILL' | 'PROCEED';
  readonly loopDetected: boolean;
  readonly similarity: number;
  readonly status: 'safe' | 'warning' | 'danger';
  readonly message: string;
  readonly confidence: number;
  readonly actionRepeatCount: number;
  readonly ngramOverlap: number;
  readonly detectors: DetectorVotes;
  readonly estimatedCostSaved: number;
  readonly degraded: boolean;
  readonly shouldStop: boolean;
  readonly score: number;
  readonly detectorTriggered: string;
  readonly estimatedSavings: number;

  constructor(data: CheckStatusOptions);
  toJSON(): CheckStatusOptions & { shouldStop: boolean };
}

export class InferenceBrakeError extends Error {
  constructor(message: string);
}

export class AuthenticationError extends InferenceBrakeError {
  constructor(message?: string);
}

export class RateLimitError extends InferenceBrakeError {
  constructor(message?: string);
}

export class CircuitBreakerError extends InferenceBrakeError {
  constructor(message?: string);
}

export class LoopDetectedError extends InferenceBrakeError {
  constructor(message?: string);
}

export const DoomLoopException: typeof LoopDetectedError;

export class LoopPolicy {
  constructor(options?: LoopPolicyOptions);
  handle(status: CheckStatus): 'escalate' | 'stop' | 'continue';
  readonly escalationsUsed: number;
  reset(): void;
}

export class InferenceBrake {
  constructor(options: InferenceBrakeOptions);
  check(
    reasoning: string,
    sessionId: string,
    options?: CheckOptions | number
  ): Promise<CheckStatus>;
  checkBatch(reasoningList: string[], sessionId: string): Promise<CheckStatus[]>;
  getSessionHistory(sessionId: string, limit?: number): Promise<unknown>;
  isOnline(): boolean;
  getQueueSize(): number;
  flushQueue(): Promise<void>;
  clearQueue(): void;
}

export class InferenceBrakeCallbackHandler {
  constructor(options?: CallbackHandlerOptions);
  name: string;
  stepCount: number;
  lastStatus: CheckStatus | null;
  handleLLMStart(...args: unknown[]): Promise<void>;
  handleLLMEnd(output: unknown): Promise<void>;
  handleLLMError(...args: unknown[]): Promise<void>;
  reset(newSessionId?: string): void;
}

export function guarded<F extends (...args: never[]) => Promise<unknown>>(
  fn: F,
  options?: GuardedOptions
): F;

export function steeringMessage(status: CheckStatus): string;
export const STEERING_MESSAGE: string;

export function inferencebrakeMonitor(options: InferenceBrakeOptions): {
  check: (reasoning: string) => Promise<CheckStatus>;
  reset: (newSessionId?: string) => void;
  client: InferenceBrake;
};

export default InferenceBrake;
