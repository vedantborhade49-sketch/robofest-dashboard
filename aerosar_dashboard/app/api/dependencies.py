from app.database.database import init_db
from app.database.repository import Repository


def get_repository() -> Repository:
    init_db()
    return Repository()
