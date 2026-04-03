# Backend API

FastAPI backend for the Adaptive Goal Planner.

For complete documentation including setup instructions, API endpoints, design principles, and testing details, see the [project README](../README.md).

## Quick Reference

```bash
# Install dependencies
pip install uv
uv sync --frozen

# Run server
uv run uvicorn main:app --reload --port 8000

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-branch --cov-report=term-missing
```

API docs available at http://localhost:8000/docs after starting the server.
