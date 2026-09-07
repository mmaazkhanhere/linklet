from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email_address: EmailStr = Field(..., description="Valid RFC 5322 email syntax")
    password: str = Field(..., min_length=8, description="Minimum 8 characters password")


class UserLoginRequest(BaseModel):
    email_address: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email_address: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
