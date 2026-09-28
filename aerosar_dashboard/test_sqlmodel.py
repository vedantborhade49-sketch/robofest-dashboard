try:
    from sqlmodel import SQLModel, Field
    class Foo(SQLModel):
        timestamp: int = Field()
    f = Foo(timestamp=1)
    f.timestamp = 2
except Exception as e:
    print(repr(e))
