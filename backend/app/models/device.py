from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)  # 'android' | 'windows' | 'macos' | 'linux' | 'web'
    platform_version = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(String(20), default="offline")    # 'online' | 'offline' | 'idle'
    telemetry = Column(JSON, nullable=True)           # {cpu, ram, battery, disk, network}
    auth_token = Column(String(512), unique=True, index=True, nullable=True)
    last_seen = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ────────────────────────────────────────────────────────
    user = relationship("User", back_populates="devices")
