"""
AmbientWindow - Small floating orb that appears in the corner when not actively using the app
"""

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QScreen
from PySide6.QtWidgets import QWidget, QApplication
from opensimplex import OpenSimplex
import math


class AmbientWindow(QWidget):
    """Small floating orb that appears in the corner when not actively using the app"""
    
    def __init__(self, renderer, app_controller=None, vision_manager=None):
        super().__init__()
        self.renderer = renderer
        self.app_controller = app_controller  # Reference to main app controller
        self.vision_manager = vision_manager  # Reference to vision system
        self.state = 'idle'  # Start in idle state
        self.face_pos = (0.5, 0.5)  # Default to center
        
        # Animation variables for the chaotic blob
        self.time = 0.0
        self.time2 = 0.0
        self.time3 = 0.0
        self.base_radius = 50  # Smaller radius for ambient orb
        self.noise_scale = 0.9
        self.noise_scale2 = 0.5
        self.noise_scale3 = 0.1
        self.noise_speed = 0.05
        self.noise_speed2 = 0.03
        self.noise_speed3 = 0.08
        
        # OpenSimplex noise generator
        self.noise_gen = OpenSimplex(seed=12345)
        
        # --- Set Window Flags for Ambient Mode ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # --- Position the Window in Bottom Right Corner ---
        screen_geometry = QApplication.primaryScreen().geometry()
        orb_size = 150  # Small orb size
        margin = 30
        
        self.setGeometry(
            screen_geometry.width() - orb_size - margin,
            screen_geometry.height() - orb_size - margin,
            orb_size,
            orb_size
        )
        
        # --- Animation Timer ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_blob)
        self.timer.start(20)  # 50fps
        
    def animate_blob(self):
        """Animation loop for the ambient orb"""
        # Increment time counters for layered noise
        self.time += self.noise_speed
        self.time2 += self.noise_speed2
        self.time3 += self.noise_speed3
        
        # Trigger redraw
        self.update()
    
    def create_blob_shape(self):
        """Create chaotic blob shape for the ambient orb"""
        num_points = 30  # Fewer points for smaller orb
        
        points = []
        center_x = 75  # Center of 150x150 window
        center_y = 75
        
        # Generate points around a circle with chaotic noise deformation
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            radius = self.base_radius
            
            # Layer 1: Primary chaotic noise
            noise_x1 = math.cos(angle) * self.noise_scale
            noise_y1 = math.sin(angle) * self.noise_scale
            noise_value1 = self.noise_gen.noise2(noise_x1 + self.time, noise_y1 + self.time)
            
            # Layer 2: Secondary noise
            noise_x2 = math.cos(angle) * self.noise_scale2
            noise_y2 = math.sin(angle) * self.noise_scale2
            noise_value2 = self.noise_gen.noise2(noise_x2 + self.time2, noise_y2 + self.time2)
            
            # Layer 3: Tertiary noise
            noise_x3 = math.cos(angle) * self.noise_scale3
            noise_y3 = math.sin(angle) * self.noise_scale3
            noise_value3 = self.noise_gen.noise2(noise_x3 + self.time3, noise_y3 + self.time3)
            
            # Combine noise layers
            total_noise = (noise_value1 * 0.6) + (noise_value2 * 0.3) + (noise_value3 * 0.1)
            radius += total_noise * 25  # Smaller deformation for ambient orb
            
            # Add randomness
            random_factor = math.sin(self.time * 2 + i * 0.5) * 5
            radius += random_factor
            
            # Calculate final position
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            points.append(QPointF(x, y))
        
        return points
    
    def paintEvent(self, event):
        """Draw the ambient orb using the shared renderer"""
        painter = QPainter(self)
        points = self.create_blob_shape()
        self.renderer.render_blob(painter, points, self.state, self.face_pos)
    
    def keyPressEvent(self, event):
        """Handle keyboard input for testing"""
        if event.key() == Qt.Key.Key_L:
            self.state = 'listening'
        elif event.key() == Qt.Key.Key_T:
            self.state = 'thinking'
        elif event.key() == Qt.Key.Key_I:
            self.state = 'idle'
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse click to switch to active window"""
        if self.app_controller:
            self.app_controller.show_active_window()
    
    def on_user_present(self):
        """Handle user presence detection - wake up ambient orb"""
        if self.state != 'listening':
            self.state = 'listening'
            self.update()  # Force redraw
    
    def on_user_absent(self):
        """Handle user absence detection - ambient orb goes to sleep"""
        if self.state != 'idle':
            self.state = 'idle'
            self.update()  # Force redraw
    
    def set_face_position(self, norm_x, norm_y):
        """
        Public method to update the face position.
        This will be used by the renderer in the next paintEvent.
        """
        self.face_pos = (norm_x, norm_y)
