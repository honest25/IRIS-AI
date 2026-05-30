from fastapi import APIRouter
from app.api.endpoints import auth, ws, chat, devices, tasks, memory

api_router = APIRouter()

api_router.include_router(auth.router,    prefix="/auth",    tags=["Authentication"])
api_router.include_router(ws.router,      prefix="",         tags=["WebSocket"])
api_router.include_router(chat.router,    prefix="/chat",    tags=["Chat & AI"])
api_router.include_router(devices.router, prefix="/devices", tags=["Device Management"])
api_router.include_router(tasks.router,   prefix="/productivity", tags=["Tasks & Notes"])
api_router.include_router(memory.router,  prefix="/memory",  tags=["Memory"])
