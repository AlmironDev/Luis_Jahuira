from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import asyncio
import cv2
import numpy as np
from datetime import datetime
import base64
import logging
from schemas import CameraConfig, MotionEvent
from cameras import CameraManager

app = FastAPI(title="Motion Detection API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Manager para las cámaras
camera_manager = CameraManager()

@app.get("/")
async def root():
    return {"message": "Motion Detection API"}

@app.get("/cameras/")
async def list_cameras():
    """Lista todas las cámaras activas"""
    return camera_manager.get_active_cameras()

@app.post("/cameras/add/")
async def add_camera(config: CameraConfig):
    """Agrega una nueva cámara para monitoreo"""
    try:
        camera_id = camera_manager.add_camera(
            camera_id=config.camera_id,
            rtsp_url=config.rtsp_url,
            sensitivity=config.sensitivity,
            min_area=config.min_area
        )
        return {"status": "success", "camera_id": camera_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/cameras/{camera_id}/")
async def remove_camera(camera_id: str):
    """Remueve una cámara del monitoreo"""
    try:
        camera_manager.remove_camera(camera_id)
        return {"status": "success", "message": f"Camera {camera_id} removed"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Camera not found")

@app.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    """WebSocket para recibir frames con detección de movimiento"""
    await websocket.accept()
    
    if camera_id not in camera_manager.active_cameras:
        await websocket.close(code=1008, reason="Camera not found")
        return
    
    try:
        while True:
            # Obtener el último frame procesado
            frame_data = camera_manager.get_camera_frame(camera_id)
            if frame_data:
                await websocket.send_bytes(frame_data)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)