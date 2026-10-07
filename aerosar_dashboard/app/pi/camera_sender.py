import os
import sys
import time
import logging
import argparse
import cv2

# Ensure we can import from app.communication
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.communication.frame_sender import FrameSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PiCameraSender")

def get_pi_camera(width: int, height: int, fps: int):
    """
    Tries to open the optimal camera backend for Raspberry Pi 5.
    Defaults to libcamera/V4L2 if available, fallback to index 0.
    """
    # Prefer V4L2 for Pi
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        logger.warning("V4L2 backend failed, falling back to default OpenCV backend")
        cap = cv2.VideoCapture(0)
        
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
    return cap

def main():
    parser = argparse.ArgumentParser(description="AEROSAR Pi Camera Sender")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--width", type=int, default=1280, help="Camera frame width")
    parser.add_argument("--height", type=int, default=720, help="Camera frame height")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--quality", type=int, default=80, help="JPEG encoding quality")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Pi Camera Sender on {args.host}:{args.port}")
    
    sender = FrameSender(
        host=args.host,
        port=args.port,
        camera_id="pi_camera_front",
        jpeg_quality=args.quality
    )
    sender.start()
    
    cap = get_pi_camera(args.width, args.height, args.fps)
    if not cap.isOpened():
        logger.error("Could not open camera. Exiting.")
        sender.stop()
        sys.exit(1)
        
    # Read actual set properties (they might differ from requested)
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    logger.info(f"Camera opened. Resolution: {actual_width}x{actual_height}")
    
    target_frame_time = 1.0 / args.fps
    
    try:
        while True:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                time.sleep(0.1)
                continue
                
            sender.send_frame(frame)
            
            # Simple rate limiting if camera ignores FPS setting
            elapsed = time.time() - start_time
            if elapsed < target_frame_time:
                time.sleep(target_frame_time - elapsed)
                
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        cap.release()
        sender.stop()

if __name__ == "__main__":
    main()
