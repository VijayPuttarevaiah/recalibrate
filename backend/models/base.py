# Import declarative_base from SQLAlchemy ORM
from sqlalchemy.orm import declarative_base

# The declarative_base() function creates a base class from which all mapped classes should inherit.
# Inheriting from Base allows SQLAlchemy's ObjectMapper to discover and manage these models.
Base = declarative_base()