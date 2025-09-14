import { create } from 'zustand';

import type { TaxiArea } from "../types/index";
import { axiosInstance } from '@/lib/axios';

interface TaxiHotspotStoreState {
    areas: TaxiArea[];
    totalTaxis: number;
    isLoading: boolean;
    error: string | null;
    fetchTaxiAreas: () => Promise<void>;
    reset: () => void;
}
/**
 * Zustand store for managing taxi hotspot data
 *
 * @param {*} set
 */
export const useTaxiStore = create<TaxiHotspotStoreState>((set) => ({
    
    areas: [],
    totalTaxis: 0,
    isLoading: false,
    error: null,
    fetchTaxiAreas: async () => {
        set({ isLoading: true, error: null });
        try {
            const res = await axiosInstance.get("/taxi-availability/top");
            if (res.data.success !== true) {
                throw new Error(`Failed: ${res.data.message}`);
            }
            set({
                areas: res.data.data.areas,
                totalTaxis: res.data.data.total_taxis,
                isLoading: false,
                error: null
            });
            console.log("Fetched taxi areas", res.data.data.areas);
        } catch (err: any) {
            set({
                isLoading: false,
                error: err?.message || 'Fetch error'
            });
        }
    },
    reset: () => set({ areas: [], totalTaxis: 0, isLoading: false, error: null })
}));
