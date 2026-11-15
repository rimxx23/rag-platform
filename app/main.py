from fastapi import FastAPI

from app.api.routers.ask import router as ask_router
from app.api.routers.collections import router as collections_router
from app.api.routers.documents import router as documents_router

app = FastAPI(title="RAG Platform")
app.include_router(collections_router)
app.include_router(documents_router)
app.include_router(ask_router)
