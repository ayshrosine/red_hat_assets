import React, { useState, useRef } from "react";
import { api, formatApiError } from "@/lib/api";
import { API } from "@/lib/api";
import { UploadCloud, X, Loader2, ImageIcon, FileText } from "lucide-react";
import { toast } from "sonner";

/**
 * Reusable multi-file uploader.
 * Value: array of { file_id, url, content_type, filename }
 * Emits onChange with updated array.
 */
export default function FileUploader({ value = [], onChange, accept = "image/*,application/pdf", multiple = true, label = "Upload files", testId = "file-uploader" }) {
    const [busy, setBusy] = useState(false);
    const inputRef = useRef(null);

    const upload = async (files) => {
        setBusy(true);
        const newItems = [];
        for (const file of files) {
            const fd = new FormData();
            fd.append("file", file);
            try {
                const { data } = await api.post("/uploads", fd, { headers: { "Content-Type": "multipart/form-data" } });
                newItems.push(data);
            } catch (e) {
                toast.error(`Upload failed: ${file.name} — ${formatApiError(e)}`);
            }
        }
        setBusy(false);
        if (newItems.length) onChange([...(value || []), ...newItems]);
        if (inputRef.current) inputRef.current.value = "";
    };

    const remove = (idx) => {
        const next = value.filter((_, i) => i !== idx);
        onChange(next);
    };

    return (
        <div className="space-y-2" data-testid={testId}>
            <label
                className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-white/15 bg-white/[0.02] hover:bg-white/[0.04] py-6 cursor-pointer transition-colors"
                htmlFor={`${testId}-input`}
            >
                {busy ? <Loader2 size={18} className="animate-spin text-white/60" /> : <UploadCloud size={18} className="text-white/60" />}
                <span className="text-xs text-white/60">{busy ? "Uploading…" : label}</span>
                <span className="text-[10px] text-white/40">PNG · JPG · WEBP · PDF · max 10 MB</span>
                <input
                    id={`${testId}-input`}
                    ref={inputRef}
                    type="file"
                    accept={accept}
                    multiple={multiple}
                    className="hidden"
                    onChange={(e) => e.target.files && upload(Array.from(e.target.files))}
                    data-testid={`${testId}-input-native`}
                />
            </label>
            {value?.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                    {value.map((f, i) => (
                        <div key={f.file_id} className="relative rounded-lg border border-white/10 bg-black overflow-hidden group aspect-square">
                            {f.content_type?.startsWith("image/") ? (
                                <AuthedImage src={f.url} alt={f.filename} />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center gap-1 text-white/60 p-2">
                                    <FileText size={20} />
                                    <span className="text-[10px] truncate max-w-full">{f.filename}</span>
                                </div>
                            )}
                            <button
                                type="button"
                                onClick={() => remove(i)}
                                className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/70 border border-white/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                data-testid={`${testId}-remove-${i}`}
                            >
                                <X size={12} />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/**
 * <img> that fetches the resource via authenticated fetch (cookies) and displays as a blob URL.
 * The <img> tag can't send Authorization headers, but cookies flow via credentials: include.
 */
export function AuthedImage({ src, alt, className }) {
    const [blob, setBlob] = React.useState(null);
    React.useEffect(() => {
        let revoked = false; let url = null;
        (async () => {
            try {
                const abs = src.startsWith("http") ? src : `${API.replace(/\/api$/, "")}${src}`;
                const res = await fetch(abs, { credentials: "include" });
                if (!res.ok) return;
                const b = await res.blob();
                if (revoked) return;
                url = URL.createObjectURL(b);
                setBlob(url);
            } catch { /* ignore */ }
        })();
        return () => { revoked = true; if (url) URL.revokeObjectURL(url); };
    }, [src]);
    if (!blob) {
        return <div className={"w-full h-full bg-white/5 flex items-center justify-center " + (className || "")}><ImageIcon size={16} className="text-white/30" /></div>;
    }
    return <img src={blob} alt={alt} className={className || "w-full h-full object-cover"} />;
}
