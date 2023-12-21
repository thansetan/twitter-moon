from pydantic import BaseModel


class APIResponse(BaseModel):
    message: str
    errors: list | None
    success: bool

    def __init__(self, message: str, errors: list | None = None, success: bool = False):
        super().__init__(message=message, errors=errors, success=success)
