from fastapi import FastAPI, Depends, Request, status, HTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.User import User
from db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}