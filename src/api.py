from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
from .lib.VideoProcessor import VideoProcessor
from .lib.Config import Config
import time
from datetime import datetime

app = FastAPI(
    title="AI Reel Generator API",
    description="API for processing videos and generating reels",
    version="1.0.0"
)

class VideoProcessRequest(BaseModel):
    video_url: HttpUrl
    video_name: Optional[str] = None

class VideoProcessResponse(BaseModel):
    video_id: str
    data: dict
    start_time: datetime
    end_time: datetime
    duration_minutes: float

@app.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest):
    try:
        start_time = datetime.utcnow()
        video_processor = VideoProcessor(Config.from_env())
        
        results = video_processor.process_video(
            str(request.video_url)
        )
        
        end_time = datetime.utcnow()
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        return VideoProcessResponse(
            video_id=results["videoId"],
            data=results["data"],
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
