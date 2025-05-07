import cv2
import os


def read_video(video_path):
    cap = cv2.VideoCapture(video_path)  # opens up video
    frames = []
    while True:
        ret, frame = cap.read()  # reads in current frame
        if not ret:  # if nothing is returned == last frame
            break
        frames.append(frame)
    return frames


