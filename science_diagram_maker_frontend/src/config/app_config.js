class AppConfig {
    static apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
}

export default AppConfig;
