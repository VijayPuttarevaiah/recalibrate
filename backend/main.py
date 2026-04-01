# Import FastAPI and context management for application lifecycle
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
# Import API routers from feature modules
from auth.login.router import router as login_router
from auth.register.router import router as register_router
from auth.email_verification.router import router as email_verification_router
from auth.logout.router import router as logout_router
from auth.password_reset.router import router as password_reset_router
from goals.goal.router import router as goals_router
from goals.category.router import router as goal_category_router
from health.routers.health_router import router as health_router
from replan.routes.router import router as replan_router
from chat.routers.chat_router import router as chat_router
from goals.task.router import router as task_router
from notifications.routers.notifications import router as notification_router
from onboarding.routers.onboarding_router import router as onboarding_router

# Import database session management and the base model for SQLAlchemy
from core.db_session import DBSession
from core.base import Base
import auth.models
import goals.models
import chat.models
import notifications.models
import onboarding.models
from core.logging_config import LogManager

# Initialize logging via Singleton
logger = LogManager.get_logger()

# Initialize the database engine used for creating and connecting to the database
engine = DBSession().engine
allowed_origins = [
    # Development
    "http://localhost:3000",
    "http://localhost:80",
    "http://localhost",
    # Production - EC2 public IP
    "http://3.22.221.134",
    "http://3.22.221.134:8080",
    "http://3.22.221.134:8081",
    # Backend endpoints (Swagger UI)
    "http://3.22.221.134:8074",
    "http://3.22.221.134:8073",
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
app.include_router(goals_router, tags=["goals"])
app.include_router(goal_category_router, tags=["goals"])
app.include_router(health_router, tags=["health"])
app.include_router(replan_router,tags=["replan"])
app.include_router(task_router,tags=["replan"])  
app.include_router(chat_router)
app.include_router(notification_router)
app.include_router(onboarding_router, tags=["Onboarding"])
