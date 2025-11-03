"""
Async database session management.

DEPRECATED: This module is kept for backward compatibility only.
Use app.backend.db.session_manager.session_manager instead.

The duplicate engine creation in this module was causing connection pool exhaustion.
"""

from sqlmodel import SQLModel

Base = SQLModel

# IMPORTANT: Do not create engines or sessions here!
# Use session_manager from app.backend.db.session_manager instead.
# Creating multiple engines causes duplicate connection pools and connection leaks.
