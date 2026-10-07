import cv2
import time
import threading
import logging
import numpy as np

from app.communication.frame_sender import FrameSender
from app.communication.frame_receiver import FrameReceiver, ConnectionState

logging.basicConfig(level=logging.INFO)

def test_transport():
    # Start sender
    sender = FrameSender(host="127.0.0.1", port=5000, camera_id="test_cam")
    sender.start()
    
    # Start receiver
    receiver = FrameReceiver(host="127.0.0.1", port=5000)
    receiver.start()
    
    time.sleep(1.0)
    assert receiver.state == ConnectionState.CONNECTED, f"Expected CONNECTED, got {receiver.state}"
    
    # Send a dummy frame
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.putText(dummy_frame, "TEST FRAME", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    success = sender.send_frame(dummy_frame)
    assert success, "Failed to send frame"
    
    # Wait for receiver
    time.sleep(0.5)
    
    network_frame = receiver.get_latest_frame()
    assert network_frame is not None, "Receiver did not get frame"
    assert network_frame.image is not None, "Receiver did not get image data"
    
    assert network_frame.image.shape == (720, 1280, 3), f"Expected (720, 1280, 3), got {network_frame.image.shape}"
    
    # Disconnect test
    sender.stop()
    time.sleep(0.5)
    
    # Send should fail or not crash
    success2 = sender.send_frame(dummy_frame)
    assert not success2, "Sender should fail when stopped"
    
    # Receiver should reconnect
    receiver.stop()
    print("Transport test passed!")

if __name__ == "__main__":
    test_transport()
