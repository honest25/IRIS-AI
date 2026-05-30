from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    device_name: str
    device_type: str

class DeviceCreate(DeviceBase):
    pass

class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    status: str
    last_seen: datetime

    class Config:
        from_attributes = True
