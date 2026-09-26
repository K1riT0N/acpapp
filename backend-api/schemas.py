import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from database import SubscriptionTier, UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    role: UserRole
    business_name: Optional[str] = None

    @model_validator(mode="after")
    def check_role_specific_fields(self):
        if self.role == UserRole.admin:
            raise ValueError("Cannot self-register as admin")
        if self.role == UserRole.business and not self.business_name:
            raise ValueError("business_name is required when role is 'business'")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    subscription_tier: Optional[SubscriptionTier] = None