import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
    baseURL: API,
    withCredentials: true,
});

// unified error formatter
export function formatApiError(err) {
    const d = err?.response?.data?.detail;
    if (d == null) return err?.message || "Something went wrong.";
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
        return d
            .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
            .join(" ");
    }
    if (typeof d === "object" && typeof d.message === "string") return d.message;
    return typeof d === "object" ? JSON.stringify(d) : String(d);
}

export function extractDetail(err) {
    return err?.response?.data?.detail;
}
