"""
Vision System - Computer vision for detecting user presence
Uses MediaPipe Face Mesh for precise face tracking and proper threading for responsive UI
"""

import os
import warnings
import logging

# Suppress MediaPipe warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
warnings.filterwarnings('ignore', category=UserWarning)
logging.getLogger('absl').setLevel(logging.ERROR)

import cv2
import mediapipe as mp
from PySide6.QtCore import QThread, Signal, Qt
import time

# Solves a common macOS camera permissions issue
os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'

class VisionThread(QThread):
    """
    A QThread that runs the computer vision model (MediaPipe Face Mesh)
    in a separate thread to avoid freezing the GUI.
    """
    
    # --- Signals ---
    # Emitted when the camera fails to open
    error_occurred = Signal(str)
    
    # Emitted when a user is first detected
    user_present = Signal()
    
    # Emitted when a user is no longer detected
    user_absent = Signal()
    
    # NEW SIGNAL: Emits the normalized (x, y) coordinates of the face
    # (0.0, 0.0) is top-left, (1.0, 1.0) is bottom-right.
    face_position_signal = Signal(float, float)

    # --- Initialization ---
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._user_was_present = False # Internal state tracking

    # --- Main Thread Logic ---
    def run(self):
        self.running = True
        
        # Initialize MediaPipe Face Mesh
        mp_face_mesh = mp.solutions.face_mesh
        
        # We use 'with' to auto-manage resources.
        # max_num_faces=1 makes it faster.
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:

            try:
                # Attempt to open the default camera (index 0)
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise IOError("Cannot open webcam")
            except Exception as e:
                self.error_occurred.emit(f"Camera Error: {e}")
                self.running = False
                return # Exit the run method

            # --- Main Processing Loop ---
            while self.running:
                success, image = cap.read()
                if not success:
                    # If we fail to grab a frame, wait and try again
                    time.sleep(0.1)
                    continue

                # Get frame dimensions
                frame_height, frame_width, _ = image.shape

                # To improve performance, mark the image as not writeable
                image.setflags(write=False)
                # Convert from BGR (OpenCV) to RGB (MediaPipe)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Process the image and find face landmarks
                results = face_mesh.process(rgb_image)

                # --- State Detection ---
                user_is_present = False
                
                if results.multi_face_landmarks:
                    user_is_present = True
                    
                    # --- NEW: Face Position Tracking ---
                    
                    # We only requested 1 face, so get the first one
                    face_landmarks = results.multi_face_landmarks[0].landmark
                    
                    # Let's use landmark #1 (the tip of the nose) as our tracking point
                    nose_tip = face_landmarks[1]
                    
                    # The coordinates are already normalized (0.0 to 1.0)
                    # We just need to flip the x-axis because the camera is a mirror
                    norm_x = 1.0 - nose_tip.x
                    norm_y = nose_tip.y

                    # Emit the new signal with the coordinates
                    self.face_position_signal.emit(norm_x, norm_y)
                    
                else:
                    pass  # No face detected
                
                # --- State Change Emission ---
                # This logic ensures we only emit signals on a *change* of state
                if user_is_present and not self._user_was_present:
                    # User has just appeared
                    self.user_present.emit()
                elif not user_is_present and self._user_was_present:
                    # User has just disappeared
                    self.user_absent.emit()
                
                # Update the internal state
                self._user_was_present = user_is_present
                
                # Small sleep to yield the thread and not max out the CPU
                # MediaPipe is fast, but we don't need 1000fps
                time.sleep(1/60) # Aim for 60fps

            # --- Cleanup ---
            cap.release()
            
    # --- Stop Method ---
    def stop(self):
        """Stops the vision thread safely."""
        self.running = False
        self.wait() # Wait for the run() method to finish


class VisionManager:
    """
    High-level manager for the vision system
    Provides easy interface for the main application
    """
    
    def __init__(self):
        self.vision_thread = None
        self.is_active = False
    
    def start_vision(self):
        """Start the vision system"""
        if self.is_active:
            return
        
        self.vision_thread = VisionThread()
        
        # Don't connect signals here - let the main app handle them
        # This prevents signal conflicts
        
        # Start the thread
        self.vision_thread.start()
        self.is_active = True
        print("Vision system started")
    
    def stop_vision(self):
        """Stop the vision system"""
        if not self.is_active:
            return
        
        if self.vision_thread:
            self.vision_thread.stop()
            self.vision_thread = None
        
        self.is_active = False
        print("Vision system stopped")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_vision()
    
    def set_sensitivity(self, sensitivity):
        """Set detection sensitivity"""
        if self.vision_thread:
            # MediaPipe doesn't have the same sensitivity controls as Haar cascades
            # This is a placeholder for future implementation
            pass
    
    def set_timeout(self, timeout_seconds):
        """Set how long to wait before declaring user absent"""
        if self.vision_thread:
            # MediaPipe handles this differently
            # This is a placeholder for future implementation
            pass
    
    def set_camera_index(self, camera_index):
        """Manually set the camera index"""
        if self.vision_thread:
            # Would need to restart the thread with new camera index
            # This is a placeholder for future implementation
            pass