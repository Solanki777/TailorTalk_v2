from pydantic import BaseModel
from typing import Optional


class SearchIntent(BaseModel):
    name: Optional[str] = None
    file_type: Optional[str] = None