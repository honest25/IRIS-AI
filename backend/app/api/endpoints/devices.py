"""
IRIS AI — Device Management Endpoints
Register, list, command, and unregister devices.
"""
import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse
from app.services.automation_service import automation_service
from app.api.deps import get_current_user
from app.websockets.manager import manager

router = APIRouter()


class DeviceCommandRequest:
    pass


from pydantic import BaseModel
from typing import Optional, Any


class DeviceCommandBody(BaseModel):
    action: str
    params: Optional[dict] = {}


class DeviceRegisterResponse(DeviceResponse):
    auth_token: str  # Only returned at registration


@router.post("/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    body: DeviceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a new device. Returns a device-specific auth token.
    The device should store this token and use it to authenticate WebSocket connections.
    """
    # Generate a secure device token
    device_token = secrets.token_urlsafe(64)

    device = Device(
        user_id=current_user.id,
        device_name=body.device_name,
        device_type=body.device_type,
        ip_address=request.client.host if request.client else None,
        auth_token=device_token,
        status="offline",
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return DeviceRegisterResponse(
        id=device.id,
        user_id=device.user_id,
        device_name=device.device_name,
        device_type=device.device_type,
        status=device.status,
        last_seen=device.last_seen,
        auth_token=device_token,
    )


@router.get("/", response_model=List[DeviceResponse])
def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all registered devices with their current status and telemetry."""
    devices = db.query(Device).filter(Device.user_id == current_user.id).all()

    # Enrich with live connection status from WebSocket manager
    active_devices = manager.active_connections.get(current_user.id, {})
    for device in devices:
        if str(device.id) in active_devices or device.device_name in active_devices:
            device.status = "online"

    return devices


@router.post("/{device_id}/command")
async def send_command(
    device_id: int,
    body: DeviceCommandBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a command directly to a specific device."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")

    if body.action not in automation_service.get_supported_actions():
        raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")

    result = await automation_service.dispatch_command(
        user_id=current_user.id,
        intent=body.action,
        command={"action": body.action, "params": body.params or {}},
        target_device_id=device.device_name,
    )
    return result


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unregister a device."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    db.delete(device)
    db.commit()
