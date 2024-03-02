from pydantic import BaseModel


class APIResponse(BaseModel):
    message: str
    errors: list | None
    success: bool
    data: dict | None

    def __init__(self, message: str, data: dict | None = None, errors: list | None = None, success: bool = False):
        super().__init__(message=message, data=data, errors=errors, success=success)
