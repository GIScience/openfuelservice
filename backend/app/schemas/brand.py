from typing import Optional

from pydantic import BaseModel


# Shared properties
class BrandBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on Brand creation
class BrandCreate(BrandBase):
    title: str


# Properties to receive on Brand update
class BrandUpdate(BrandBase):
    pass


# Properties shared by models stored in DB
class BrandInDBBase(BrandBase):
    id: int
    title: str
    owner_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Brands(BaseModel):
    brands: list


# Properties properties stored in DB
class BrandInDB(BrandInDBBase):
    pass
