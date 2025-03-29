from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class CameraConfig(BaseModel):
    """Esquema para configuración de cámara"""
    camera_id: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    rtsp_url: str = Field(..., description="URL RTSP de la cámara")
    sensitivity: float = Field(0.5, ge=0.1, le=1.0, description="Sensibilidad de detección (0.1-1.0)")
    min_area: int = Field(500, ge=100, le=5000, description="Área mínima para considerar movimiento")

class MotionEvent(BaseModel):
    """Esquema para evento de movimiento"""
    camera_id: str
    timestamp: str
    frame: Optional[str] = None  # Base64 encoded image
    confidence: float