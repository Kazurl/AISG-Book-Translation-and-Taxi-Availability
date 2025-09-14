import { create } from 'zustand';
import type { TranslateJobRequest, TranslationProgressResult, JobStatus } from '../types/index';

/**
 * The ID of the current translation job.
 *
 * @type {(string | null)}
 * @memberof TranslationStoreState
 */
interface TranslationStoreState {
    jobId: string | null;
    jobStatus: JobStatus | null;
    progress: TranslationProgressResult | null;
    metaData: {
        origin_title: string;
        origin_author: string;
        language: string;
        email: string;
    } | null;
    setMetaData(metaData: TranslationStoreState['metaData']): void;
    setJobId(jobId: string | null): void;
    setJobStatus(status: JobStatus): void;
    setProgress(progress: TranslationProgressResult): void;
    reset(): void;
}


/**
 * Zustand store for managing translation job state.
 *
 * @param {*} set
 */
export const useTranslationStore = create<TranslationStoreState>((set) => ({
    jobId: null,
    jobStatus: null,
    progress: null,
    metaData: null,
    setMetaData: (metaData) => set({ metaData }),
    setJobId: (jobId) => set({ jobId }),
    setJobStatus: (status) => set({ jobStatus: status }),
    setProgress: (progress) => set({ progress }),
    reset: () => set({ jobId: null, jobStatus: null, progress: null, metaData: null }),
}));
