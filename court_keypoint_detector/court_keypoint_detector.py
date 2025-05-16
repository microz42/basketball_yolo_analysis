from ultralytics import YOLO
import sys
sys.path.append('../')
from utils import read_video, save_video


class CourtKeypointDetector:
    def __init__(self, model_path):
        self.model=YOLO(model_path)
    
    def get_court_keypoints(self, frames, read_from_stub=False, stub_path=None):

        batch_size=20
        court_keypoints=[]
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i+batch_size], conf=0.5)
            court_keypoints.extend(detection_batch[0].keypoints.xy)
        
        return court_keypoints