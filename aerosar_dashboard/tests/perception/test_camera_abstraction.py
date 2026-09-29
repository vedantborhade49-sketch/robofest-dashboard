import unittest
from app.perception.camera import OpenCVVideoSource, WebcamSource

class TestCameraAbstraction(unittest.TestCase):
    def test_open_invalid_source(self):
        src = OpenCVVideoSource("nonexistent_file.mp4")
        ok = src.open()
        self.assertFalse(ok)

    def test_webcam_index_object(self):
        webcam = WebcamSource(index=0)
        # do not actually open webcam in CI; just check object
        self.assertEqual(webcam.index, 0)
