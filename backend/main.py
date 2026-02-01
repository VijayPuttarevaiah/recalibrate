# Import FastAPI and context management for application lifecycle
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import API routers from the routers directory
from routers.login import router as login_router
from routers.register import router as register_router
from routers.email_verification import router as email_verification_router
from routers.logout import router as logout_router

# Import database session management and the base model for SQLAlchemy
from utils.db_session import DBSession
from models.base import Base

# Initialize the database engine used for creating and connecting to the database
engine = DBSession().engine

# Define the lifespan of the application (startup and shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Create database tables if they don't already exist
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (optional)
    # e.g., engine.dispose()

# Initialize the FastAPI application with the defined lifespan
app = FastAPI(lifespan=lifespan)

# Register routers with the FastAPI application to expose API endpoints
app.include_router(login_router)
app.include_router(register_router)
app.include_router(email_verification_router)
# Include the logout router to handle token invalidation
app.include_router(logout_router)
