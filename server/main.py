from fastapi import FastAPI
from models.User import User
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.RefreshToken import RefreshToken
from db.database import Base, engine
from api.v1.api import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
