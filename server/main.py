from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.User import User
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.RefreshToken import RefreshToken
from db.database import Base, engine
from api.v1.api import api_router
from core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,  # required for httpOnly cookies to work
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/status")
async def status():
    return {"status": "ok", "version": "1.0.0", "environment": settings.app_env}
