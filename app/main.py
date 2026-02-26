from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import email_connections, streaming_accounts

app = FastAPI(title="Hulu Verification Code API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(email_connections.router)
app.include_router(streaming_accounts.router)


@app.get("/v1/health")
def health():
    return {"status": "ok", "env": settings.app_env}
