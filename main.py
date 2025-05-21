from utils import read_video, save_video
import os
from trackers import PlayerTracker, BallTracker
from drawers import(
    PlayerTracksDrawer,
    BallTracksDrawer,
    TeamBallControlDrawer,
    PassInterceptionDrawer,
    CourtKeypointDrawer,
    TacticalViewDrawer,
    SpeedAndDistanceDrawer,
)
from team_assigner import TeamAssigner
from ball_acquisition import BallAcquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from court_keypoint_detector import CourtKeypointDetector
from tactical_view_converter import TacticalViewConverter
from speed_and_distance_calculator import SpeedAndDistanceCalculator

from configs import (
    STUBS_DEFAULT_PATH,
    PLAYER_DETECTOR_PATH,
    BALL_DETECTOR_PATH,
    COURT_KEYPOINT_DETECTOR_PATH,
    OUTPUT_VIDEO_PATH,
    )
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description= "Basketball video analysis")
    parser.add_argument("input_video", type=str, help="path of input video file")
    parser.add_argument("--stub_path", type=str, default=STUBS_DEFAULT_PATH, help="path to stub directory")
    # parser.add_argument("--player_detector_path", type=str, default=PLAYER_DETECTOR_PATH, help="path to player detector model")
    # parser.add_argument("--ball_detector_path", type=str, default=BALL_DETECTOR_PATH, help="path to ball detector model")
    # parser.add_argument("--court_keypoint_detector_path", type=str, default=COURT_KEYPOINT_DETECTOR_PATH, help="path to court keypoint detector model")
    parser.add_argument("--output_video_path", type=str, default=OUTPUT_VIDEO_PATH, help="path to output video")
    return parser.parse_args()


def main():
    args = parse_args()

    # Read video
    video_frames = read_video(args.input_video)

    # Initialize Tracker
    player_tracker = PlayerTracker(PLAYER_DETECTOR_PATH)
    ball_tracker = BallTracker(BALL_DETECTOR_PATH)

    # initialize Court keypoint detector
    court_keypoint_detector = CourtKeypointDetector(COURT_KEYPOINT_DETECTOR_PATH)

    # run tracker
    player_tracks = player_tracker.get_object_tracks(video_frames,
                                                     read_from_stub=True,
                                                     stub_path = os.path.join(args.stub_path, "player_track_stubs.pkl")
                                                     )

    ball_tracks = ball_tracker.get_object_tracks(video_frames,
                                                     read_from_stub=True,
                                                     stub_path = os.path.join(args.stub_path, "ball_track_stubs.pkl")
                                                     )

   # Get Court Keypoints
    court_keypoints = court_keypoint_detector.get_court_keypoints(video_frames,
                                                                 read_from_stub=True,
                                                                 stub_path = os.path.join(args.stub_path, "court_key_points_stubs.pkl")
                                                                 ) 

    
    # remove wrong ball detections
    ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
    # interpolate ball tracks
    ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)

    # Assign player teams
    team_assigner = TeamAssigner()
    player_assignment = team_assigner.get_player_teams_across_frames(video_frames,
                                                                player_tracks,
                                                                read_from_stub=True,
                                                                stub_path = os.path.join(args.stub_path, "player_assignment_stubs.pkl")
                                                                )
    # print(player_teams)

    # Ball Acquisition
    ball_acquisition_detector = BallAcquisitionDetector()
    ball_acquisition = ball_acquisition_detector.detect_ball_posession(player_tracks, ball_tracks)

    # Detect passes and interceptions
    pass_and_interception_detector = PassAndInterceptionDetector()
    passes = pass_and_interception_detector.detect_passes(ball_acquisition, player_assignment)
    interceptions = pass_and_interception_detector.detect_interceptions(ball_acquisition, player_assignment)

    # Tactical View
    tactical_view_converter = TacticalViewConverter(court_image_path="./images/basketball_court.png")
    court_keypoints = tactical_view_converter.validate_keypoints(court_keypoints)  # if something is not good, overwrite it with 0,0
    tactical_player_positions = tactical_view_converter.transform_players_to_tactical_view(court_keypoints, player_tracks)

    # speed and distance calculator
    speed_distance_calculator = SpeedAndDistanceCalculator(
        tactical_view_converter.width,
        tactical_view_converter.height,
        tactical_view_converter.actual_width_in_meters,
        tactical_view_converter.actual_height_in_meters,
    )
    player_distance_per_frame = speed_distance_calculator.calculate_distance(tactical_player_positions)
    player_speed_per_frame = speed_distance_calculator.calculate_speed(player_distance_per_frame)

    


    # draw output
    # initialize drawer
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    team_ball_control_drawer = TeamBallControlDrawer()
    pass_interception_drawer = PassInterceptionDrawer()
    court_keypoint_drawer = CourtKeypointDrawer()
    tactical_view_drawer = TacticalViewDrawer()
    speed_distance_drawer = SpeedAndDistanceDrawer()

    # draw object tracks
    output_video_frames = player_tracks_drawer.draw(video_frames,
                                                    player_tracks,
                                                    player_assignment,
                                                    ball_acquisition)
    output_video_frames = ball_tracks_drawer.draw(output_video_frames, ball_tracks)

    # Draw Team Ball Control
    output_video_frames = team_ball_control_drawer.draw(output_video_frames,
                                                         player_assignment,
                                                         ball_acquisition)

    # Draw passes and interceptions
    output_video_frames = pass_interception_drawer.draw(output_video_frames,
                                                        passes,
                                                        interceptions)

    # Draw court keypoints
    output_video_frames = court_keypoint_drawer.draw(output_video_frames,
                                                     court_keypoints)

    # Tactical View
    output_video_frames = tactical_view_drawer.draw(output_video_frames,
                                                   tactical_view_converter.court_image_path,
                                                   tactical_view_converter.width,
                                                   tactical_view_converter.height,
                                                   tactical_view_converter.key_points,
                                                   tactical_player_positions,
                                                   player_assignment,
                                                   ball_acquisition,
                                                   )
    
    # Speed and Distance Drawer
    output_video_frames = speed_distance_drawer.draw(
        output_video_frames,
        player_tracks,
        player_distance_per_frame,
        player_speed_per_frame,
    )

    # save video
    save_video(output_video_frames, args.output_video_path)


if __name__ == "__main__":
    main()

