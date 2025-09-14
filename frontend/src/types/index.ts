export interface TranslateJobRequest {
  book: string;
  language: string;
  email: string;
}

export interface TranslateProgressQuery {
  origin_title: string;
  origin_author: string;
  email: string;
  language: string;
}

export interface CancelJobRequest {
  origin_title: string;
  origin_author: string;
  email: string;
}

export interface LastJobQuery {
  email: string;
}

export type JobStatus = "DONE" | "RUNNING" | "STARTED" | "CANCELLED";

export interface TranslationProgressResult {
  running: boolean;
  chunks_remaining: number;
  result?: string | null;
  error?: string;
}