from pydantic import BaseModel

class VerificationCode(BaseModel):
    code:str
    error:str

class Token(BaseModel):
    access_token: str
    token_type: str