import { useEffect, useState } from "react";
import { useTranslationStore } from "../../stores/useTranslationStore";
import { axiosInstance } from "../../lib/axios";

export default function TranslationProgressPage() {
    /* Polling the backend for translation progress */
    const meta = useTranslationStore(s => s.metaData);
    const progress = useTranslationStore(s => s.progress);
    const setProgress = useTranslationStore(s => s.setProgress);
    const [intervalId, setIntervalId] = useState<number | null>(null);

    useEffect(() => {
        if (!meta) return;
        const poll = async () => {
            const { origin_title, origin_author, email, language } = meta;
            try {
                const { data } = await axiosInstance.get("/translation_progress", {
                    params: { origin_title, origin_author, email, language },
                });
                setProgress(data);
                if (data.result && intervalId) clearInterval(intervalId);
            } catch (e) {
                setProgress({ running: false, chunks_remaining: 0, error: "Error fetching progress." });
            }
        };
        const id = window.setInterval(poll, 2000);
        setIntervalId(id);
        return () => clearInterval(id);
    }, [meta]);

    if (!meta) return <div>No translation in progress.</div>;
    if (!progress) return <div>Loading progress...</div>;
    if (progress.result) {
        return (
            <div>
            <h2 className="text-lg font-bold mb-2">Translation Result</h2>
            <textarea readOnly value={progress.result} className="w-full h-96 border border-gray-200 rounded p-2" />
            <a
                download="translated_book.txt"
                href={`data:text/plain;charset=utf-8,${encodeURIComponent(progress.result)}`}
                className="inline-block mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
                Download as .txt
            </a>
            </div>
        );
    }
    return (
        <div>
            <div>Translation in progress...</div>
            <div>Chunks remaining: <span className="font-mono">{progress.chunks_remaining}</span></div>
        </div>
    );
}
