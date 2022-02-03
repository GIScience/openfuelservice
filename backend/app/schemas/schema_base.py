from typing import List

from pydantic import BaseModel


class SchemaBase(BaseModel):
    messages: List = []
