from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router

app = FastAPI(
    title="AI Support + Sales Copilot API",
    version="0.2.0"
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

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/")
def read_root():
    return {
        "message": "Backend is running",
        "product": "AI Support + Sales Copilot"
    }