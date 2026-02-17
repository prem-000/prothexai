// PROD:
// const API_BASE_URL = "https://your-backend-name.onrender.com";
// DEV:
export const API_BASE_URL = "http://localhost:8000";

export async function apiRequest(endpoint, method = "GET", data = null) {
    const token = localStorage.getItem("token")

    const config = {
        method,
        headers: {
            "Content-Type": "application/json"
        }
    }

    if (token) {
        config.headers["Authorization"] = `Bearer ${token}`
    }

    if (data) {
        config.body = JSON.stringify(data)
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config)

        if (response.status === 401) {
            localStorage.clear()
            window.location.href = "auth.html"
            return null
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.status}`);
        }

        return response.json()
    } catch (error) {
        console.error("API Request Failed:", error)
        throw error
    }
}
