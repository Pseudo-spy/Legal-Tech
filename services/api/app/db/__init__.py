"""Database configuration and utilities."""

# NOTE: Keep this file minimal to avoid circular import issues.
# Workers import SessionLocal directly from db.session instead.
# Models are registered via db.base which is imported only when needed.
