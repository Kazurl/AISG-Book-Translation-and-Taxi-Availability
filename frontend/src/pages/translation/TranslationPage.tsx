import React, { useState } from "react";
import { axiosInstance } from "../../lib/axios";
import { useTranslationStore } from "../../stores/useTranslationStore";
import { Button } from "@/components/ui/button";
import FileUpload from "../../components/FileUpload";
import type { TranslateJobRequest } from "../../types";

export default function TranslationPage() {
  
    const [text, setText] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [email, setEmail] = useState("");
    const [language, setLanguage] = useState("chinese");
    const [loading, setLoading] = useState(false);

    const setMeta = useTranslationStore(s => s.setMetaData);
    const setJobId = useTranslationStore(s => s.setJobId);
    const setJobStatus = useTranslationStore(s => s.setJobStatus);
    const setProgress = useTranslationStore(s => s.setProgress);
    const [result, setResult] = useState<string | null>(null);
    
/**
 * Handle form submission to initiate book translation.
 *
 * @param {React.FormEvent} e
 */
const handleSubmit = async (e: React.FormEvent) => {
        
        e.preventDefault();
        setLoading(true);
        let bookText = text;
        if (file) {
            bookText = await file.text();
        }
        const meta = {
            book: bookText,
            language,
            email,
        };
        try {
        const res = await axiosInstance.post("/translation/translate_book", meta);
        //   if (res.data.job_id) {
        //     setJobId(res.data.job_id);
        //     // store meta for polling
        //     setMeta({
        //       origin_title: res.data.origin_title, // should backend return these in response? If not, extract from book or frontend
        //       origin_author: res.data.origin_author,
        //       language,
        //       email,
        //     });
            setJobStatus(res.data.status);
            if (res.data && res.data.result) setResult(res.data.result);  
            else alert("No translation result returned.");
        } catch (err) {
            alert("Failed to submit translation job.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <form className="space-y-4" onSubmit={handleSubmit}>
                <textarea
                    className="w-full border rounded p-2"
                    rows={10}
                    placeholder="Paste book text here or upload file"
                    value={text}
                    onChange={e => setText(e.target.value)}
                />
                <FileUpload onFile={setFile} />
                <input
                    type="email"
                    className="w-full border rounded p-2"
                    placeholder="Your email"
                    value={email}
                    required
                    onChange={e => setEmail(e.target.value)}
                />
                <input
                    type="text"
                    className="w-full border rounded p-2"
                    placeholder="Language (e.g. chinese)"
                    value={language}
                    required
                    onChange={e => setLanguage(e.target.value)}
                />
                <Button type="submit" disabled={loading}>{loading ? "Submitting..." : "Submit for Translation"}</Button>
            </form>

            {result && (
                <div className="mt-8">
                    <h2 className="text-lg font-bold mb-2">Translation Result</h2>
                    <textarea
                        readOnly
                        value={result}
                        className="w-full h-96 border border-gray-200 rounded p-2"
                    />
                    <a
                        download="translated_book.txt"
                        href={`data:text/plain;charset=utf-8,${encodeURIComponent(result)}`}
                        className="inline-block mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                        Download as .txt
                    </a>
                </div>
            )}
        </div>
    );
}
