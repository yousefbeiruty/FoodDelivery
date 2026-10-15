"""Compatibility entry point for `uvicorn main:app` and IDE run configurations."""

from app.main import app

__all__ = ["app"]
