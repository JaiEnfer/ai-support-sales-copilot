from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Support + Sales Copilot API",
    version="0.1.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/api/demo")
def demo_message():
    return {
        "reply": "Hello from the backend. Your AI Support + Sales Copilot API is connected."
    }