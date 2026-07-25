from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    file_size: int
    saved_path: str
    status: str
    message: str
