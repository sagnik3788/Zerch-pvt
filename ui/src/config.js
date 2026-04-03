const getApiBaseUrl = () => {
    // Use environment variable if provided (e.g. via Vite)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // For production (Vercel/VM):
    // When running on Vercel, we can use an empty string for API_BASE_URL.
    // This makes all fetch() calls relative (e.g. /api/search), 
    // which works perfectly with the vercel.json proxy we set up.
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return '';
    }

    // Default to localhost for development
    return 'http://localhost:8080';
};

export const API_BASE_URL = getApiBaseUrl();
