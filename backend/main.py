# Import FastAPI and context management for application lifecycle
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
# Import API routers from the routers directory
from routers.login import router as login_router
from routers.register import router as register_router
from routers.email_verification import router as email_verification_router
from routers.logout import router as logout_router
from routers.password_reset import router as password_reset_router

# Import database session management and the base model for SQLAlchemy
from utils.db_session import DBSession
from models.base import Base
from utils.logging_config import LogManager

# Initialize logging via Singleton
logger = LogManager.get_logger()

# Initialize the database engine used for creating and connecting to the database
engine = DBSession().engine
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:80",
    "http://localhost"
]
# Define the lifespan of the application (startup and shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Create database tables if they don't already exist
    logger.info("Application starting up...")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (optional)
    logger.info("Application shutting down...")
    # e.g., engine.dispose()

# Initialize the FastAPI application with the defined lifespan
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with the FastAPI application to expose API endpoints
app.include_router(login_router, tags=["auth"])
app.include_router(register_router, tags=["auth"])
app.include_router(email_verification_router, tags=["verification"])
app.include_router(logout_router, tags=["auth"])
app.include_router(password_reset_router, tags=["auth"])
