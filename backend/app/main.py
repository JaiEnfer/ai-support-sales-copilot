from fastapi import FastAPI

app = FastAPI(
    title="AI Support + Sales Copilot API",
    version="0.1.0"
)


@app.get("/")
def read_root():
    return {
        "message": "Backend is running",
        "product": "AI Support + Sales Copilot"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}