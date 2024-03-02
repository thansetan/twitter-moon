from pydantic import BaseModel


class User(BaseModel):
    access_token: str
    access_token_secret: str

class Secret(BaseModel):
    key: str