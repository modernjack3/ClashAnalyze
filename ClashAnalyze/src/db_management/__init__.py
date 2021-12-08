__all__ = ['get_db']

from .db import DbConnector
def get_db():
    return DbConnector()
