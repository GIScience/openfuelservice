from pydantic import BaseModel


class PhenomenonBase(BaseModel):
    name: str
    unit: str

    class Config:
        orm_mode = True


class PhenomenonCreate(BaseModel):
    name: str
    unit: str


class PhenomenonUpdate(BaseModel):
    name: str
    unit: str
