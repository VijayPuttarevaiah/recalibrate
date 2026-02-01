from fastapi import FastAPI
from routers.login import router as login_router
from routers.register import router as register_router
from routers.email_verification import router as email_verification_router
from utils.db_session import DBSession
from models.base import Base
import os

engine = DBSession().engine

app = FastAPI()

@app.on_event("startup")
def on_startup():
	Base.metadata.create_all(bind=engine)

app.include_router(login_router)
app.include_router(register_router)
app.include_router(email_verification_router)