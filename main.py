from utils import read_video, save_video
from trackers import PlayerTracker, BallTracker
from drawers import(
    PlayerTracksDrawer,
    BallTracksDrawer,
    TeamBallControlDrawer,
    PassInterceptionDrawer,
    CourtKeypointDrawer,
    TacticalViewDrawer,
)
from team_assigner import TeamAssigner
from ball_acquisition import BallAcquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from court_keypoint_detector import CourtKeypointDetector
from tactical_view_converter import TacticalViewConverter



def main():

    # Read video
    video_frames = read_video("input_videos/video_3.mp4")

    # Initialize Tracker
    player_tracker = PlayerTracker("models/player_detector.pt")
    ball_tracker = BallTracker("models/ball_detector_model.pt")

    # initialize Court keypoint detector
    court_keypoint_detector = CourtKeypointDetector("models/court_keypoint_detector.pt")

    # run tracker
    player_tracks = player_tracker.get_object_tracks(video_frames,
                                                     read_from_stub=True,
                                                     stub_path = "stubs/player_track_stubs.pkl"
                                                     )

    ball_tracks = ball_tracker.get_object_tracks(video_frames,
                                                     read_from_stub=True,
                                                     stub_path = "stubs/ball_track_stubs.pkl"
                                                     )

   # Get Court Keypoints
    court_keypoints = court_keypoint_detector.get_court_keypoints(video_frames,
                                                                 read_from_stub=True,
                                                                 stub_path = "stubs/court_key_points_stubs.pkl",
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
                                                                stub_path="stubs/player_assignment_stub.pkl"
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


    # draw output
    # initialize drawer
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    team_ball_control_drawer = TeamBallControlDrawer()
    pass_interception_drawer = PassInterceptionDrawer()
    court_keypoint_drawer = CourtKeypointDrawer()
    tactical_view_drawer = TacticalViewDrawer()

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
                                                   )

    # save video
    save_video(output_video_frames, "output_videos/output_video.avi")


if __name__ == "__main__":
    main()

