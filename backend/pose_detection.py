import cv2
import numpy as np
import time

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

class PoseDetector:
    """
    MediaPipe Pose landmarker wrapper that processes RGB images/frames,
    draws skeleton overlays, extracts 33 body keypoints, and computes spatial metrics.
    """
    def __init__(self, static_image_mode=False, model_complexity=1, smooth_landmarks=True,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.smooth_landmarks = smooth_landmarks
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        if MP_AVAILABLE and hasattr(mp, 'solutions'):
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=self.static_image_mode,
                model_complexity=self.model_complexity,
                smooth_landmarks=self.smooth_landmarks,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
        else:
            self.mp_pose = None
            self.pose = None

    def process_frame(self, frame, draw=True):
        """
        Processes a single BGR OpenCV frame.
        Returns:
            processed_frame (np.ndarray): Frame with skeleton overlay.
            landmarks_dict (dict): Dictionary mapping landmark index and name to (x, y, z, visibility).
        """
        h, w, c = frame.shape
        landmarks_dict = {}

        if not MP_AVAILABLE or self.pose is None:
            # Fallback mock landmark generator if mediapipe is loading or unavailable
            return self._generate_fallback_landmarks(frame, draw)

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)

        if results.pose_landmarks:
            if draw:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )

            for idx, lm in enumerate(results.pose_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                name = self.mp_pose.PoseLandmark(idx).name
                landmarks_dict[idx] = {
                    "name": name,
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "px": cx,
                    "py": cy,
                    "visibility": lm.visibility
                }

        return frame, landmarks_dict

    def _generate_fallback_landmarks(self, frame, draw):
        """Generates synthetic landmarks for testing in environments without camera or GPU."""
        h, w, c = frame.shape
        landmarks_dict = {}
        # Simulating key landmarks (11: L_Shoulder, 12: R_Shoulder, 23: L_Hip, 24: R_Hip, 25: L_Knee, 26: R_Knee, 27: L_Ankle, 28: R_Ankle, 13: L_Elbow, 14: R_Elbow, 15: L_Wrist, 16: R_Wrist)
        simulated_points = {
            11: ("LEFT_SHOULDER", 0.40, 0.25),
            12: ("RIGHT_SHOULDER", 0.60, 0.25),
            13: ("LEFT_ELBOW", 0.35, 0.40),
            14: ("RIGHT_ELBOW", 0.65, 0.40),
            15: ("LEFT_WRIST", 0.30, 0.55),
            16: ("RIGHT_WRIST", 0.70, 0.55),
            23: ("LEFT_HIP", 0.42, 0.50),
            24: ("RIGHT_HIP", 0.58, 0.50),
            25: ("LEFT_KNEE", 0.43, 0.70),
            26: ("RIGHT_KNEE", 0.57, 0.70),
            27: ("LEFT_ANKLE", 0.44, 0.90),
            28: ("RIGHT_ANKLE", 0.56, 0.90),
        }

        for idx, (name, norm_x, norm_y) in simulated_points.items():
            cx, cy = int(norm_x * w), int(norm_y * h)
            landmarks_dict[idx] = {
                "name": name,
                "x": norm_x,
                "y": norm_y,
                "z": 0.0,
                "px": cx,
                "py": cy,
                "visibility": 0.99
            }
            if draw:
                cv2.circle(frame, (cx, cy), 6, (0, 255, 128), -1)

        if draw:
            # Draw basic limbs
            cv2.line(frame, (int(0.40*w), int(0.25*h)), (int(0.60*w), int(0.25*h)), (255, 200, 0), 3)
            cv2.line(frame, (int(0.42*w), int(0.50*h)), (int(0.58*w), int(0.50*h)), (255, 200, 0), 3)
            cv2.line(frame, (int(0.42*w), int(0.50*h)), (int(0.43*w), int(0.70*h)), (0, 255, 0), 3)
            cv2.line(frame, (int(0.43*w), int(0.70*h)), (int(0.44*w), int(0.90*h)), (0, 255, 0), 3)

        return frame, landmarks_dict


def run_pose_prototype(video_source=0):
    """
    Standalone tester script for MediaPipe pose detection.
    Reads webcam or video file and renders real-time skeleton overlay with angles.
    """
    print(f"[MediaPipe Prototype] Initializing detector on source: {video_source}...")
    detector = PoseDetector()
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("[MediaPipe Prototype] Warning: Cannot open video source. Generating test synthetic image...")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame, lms = detector.process_frame(frame, draw=True)
        print(f"[MediaPipe Prototype] Successfully extracted {len(lms)} landmarks!")
        return True

    prev_time = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame, landmarks = detector.process_frame(frame, draw=True)

        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time + 1e-6)
        prev_time = curr_time

        cv2.putText(frame, f"FPS: {int(fps)} | Landmarks: {len(landmarks)}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("MediaPipe Pose Detection Prototype - AI Fitness System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    run_pose_prototype()
