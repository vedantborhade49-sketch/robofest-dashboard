from pydantic import BaseModel
class Foo(BaseModel):
    x: int
f = Foo(x=1)
f.x = 2
