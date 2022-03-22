from typing import List

from pydantic import BaseModel


class ReturnSchemaBase(BaseModel):
    messages: List = []
