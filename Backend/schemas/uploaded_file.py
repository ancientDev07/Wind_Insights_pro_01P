from pydantic import BaseModel

class UploadedFileResponse(BaseModel):

    id: int
    filename: str
    filepath: str
    model_config = {
        "from_attributes": True
    }