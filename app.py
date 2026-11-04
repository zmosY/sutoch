"""
Main Entry Point for Sutochno & Booking AI Web App
Starts the FastAPI server and opens the browser.
"""

import webbrowser
import uvicorn

if __name__ == "__main__":
    PORT = 8000
    URL = f"http://127.0.0.1:{PORT}"
    print("=" * 70)
    print("🚀 СУТОЧНО.AI & BOOKING CLONE — ЗАПУСК СЕРВЕРА")
    print(f"👉 Веб-интерфейс доступен по адресу: {URL}")
    print(f"📚 Swagger API Документация: {URL}/docs")
    print("=" * 70)

    try:
        webbrowser.open(URL)
    except Exception:
        pass

    uvicorn.run("src.api:app", host="127.0.0.1", port=PORT, reload=True)
