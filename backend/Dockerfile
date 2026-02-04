# Use a lightweight Python base image
FROM python:3.11-slim-bookworm

# Install system dependencies if needed (e.g., for mysql or other extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only the dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the system environment (no virtualenv needed inside Docker)
# --frozen ensures we use the exact versions from uv.lock
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# Expose the port the app runs on
EXPOSE 8000

# Set the environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Command to run the application
# We run migrations and tests before starting the server
CMD ["sh", "-c", "uv run pytest && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
