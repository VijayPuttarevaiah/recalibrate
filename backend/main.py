from fastapi import FastAPI
from routers.login import router as login_router
from routers.register import router as register_router

app = FastAPI()

app.include_router(login_router)
app.include_router(register_router)