export interface CheckStatusOptions {
  action: 'KILL' | 'PROCEED';
  loopDetected: boolean;
  similarity: number;
  status: 'safe' | 'warning' | 'danger';
  message: string;
  confidence: number;
  actionRepeatCount: number;
  ngramOverlap: number;
  detectors: DetectorVotes;
  testMode?: boolean;
  usage?: UsageInfo;
  shouldStop: boolean;
}

export interface DetectorVotes {
  semantic: boolean;
  action: boolean;
  ngram: boolean;
}

export interface UsageInfo {
  today: number;
  limit: number;
  remaining: number;
}

export interface InferenceBrakeOptions {
  apiKey: string;
  supabaseUrl?: string;
  timeout?: number;
  autoStop?: boolean;
}

export interface SessionHistoryStep {
  step_number: number;
  reasoning: string;
  similarity: number | null;
  loop_detected: boolean;
  created_at: string;
}

export interface BatchResult {
  step: number;
  status: CheckStatusOptions;
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
  readonly shouldStop: boolean;

  constructor(data: CheckStatusOptions);
  toJSON(): CheckStatusOptions;
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

export function inferencebrakeMonitor(options: InferenceBrakeOptions): {
  check: (reasoning: string) => Promise<CheckStatus>;
  reset: (newSessionId?: string) => void;
  client: InferenceBrake;
};

export class InferenceBrake {
  constructor(options: InferenceBrakeOptions);
  check(reasoning: string, sessionId: string, threshold?: number): Promise<CheckStatus>;
  checkBatch(reasoningList: string[], sessionId: string): Promise<CheckStatus[]>;
  getSessionHistory(sessionId: string, limit?: number): Promise<SessionHistoryStep[]>;
}

export default InferenceBrake;
