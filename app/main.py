from fastapi import FastAPI

from app.api.routers.collections import router as collections_router

app = FastAPI(title="RAG Platform")
app.include_router(collections_router)
