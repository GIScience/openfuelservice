from pydantic import BaseModel


# Properties to return to client
class Brands(BaseModel):
    brands: list
