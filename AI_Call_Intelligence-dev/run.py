"""Start the AI Call Intelligence server."""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.realtime_server:app", host="0.0.0.0", port=port, reload=False)
