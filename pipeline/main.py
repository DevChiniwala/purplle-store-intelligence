import asyncio
import logging
import os
import yaml
from pathlib import Path
from pipeline.video_processor import VideoProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_camera_processor(camera_id: str, video_path: str, config_path: str, camera_config_path: str):
    logger.info(f"Initializing processor for {camera_id}")
    processor = VideoProcessor(camera_id, video_path, config_path, camera_config_path)
    # The actual cv2 processing block is synchronous, so we run it in a thread
    await asyncio.to_thread(processor.process)

async def run_pipeline():
    logger.info("Starting Store Intelligence Pipeline...")
    config_path = Path("config/settings.yaml")
    camera_config_path = Path("config/cameras.yaml")
    
    if not config_path.exists() or not camera_config_path.exists():
        logger.error("Config files not found")
        return

    video_dir = Path("data/videos/CCTV Footage")
    if not video_dir.exists():
        logger.warning(f"Video directory {video_dir} not found. Running in idle mode.")
        while True:
            await asyncio.sleep(60)
            
    tasks = []
    # Map video files to camera IDs
    video_map = {
        "CAM 1.mp4": "CAM_1",
        "CAM 2.mp4": "CAM_2",
        "CAM 3.mp4": "CAM_3",
        "CAM 4.mp4": "CAM_4",
        "CAM 5.mp4": "CAM_5"
    }
    
    for video_file, camera_id in video_map.items():
        vpath = video_dir / video_file
        if vpath.exists():
            tasks.append(run_camera_processor(camera_id, str(vpath), str(config_path), str(camera_config_path)))
        else:
            logger.warning(f"Video file {video_file} not found.")

    logger.info(f"Pipeline initialized. Starting {len(tasks)} camera processors.")
    
    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.info("No tasks to run. Idling.")
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
