from app.schemas.schema_base import ReturnSchemaBase


# Properties to return to client
class Brands(ReturnSchemaBase):
    data: list
