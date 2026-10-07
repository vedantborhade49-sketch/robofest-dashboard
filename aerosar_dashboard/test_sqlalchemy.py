from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()
e
class Foo(Base):
    __tablename__ = 'foo'
    id = Column(Integer, primary_key=True)
    x = Column(Integer)

Foo.x = 2
