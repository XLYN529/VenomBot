import sys

from PySide6.QtCore import QSize, Qt, QTimer, QPointF
from PySide6.QtGui import QRegion, QPainter, QBrush, QColor, QPen, QPainterPath, QPolygonF, QRadialGradient, QLinearGradient
from PySide6.QtWidgets import QApplication, QMainWindow
from opensimplex import OpenSimplex
import math
from blob_renderer import BlobRenderer
from ambient_window import AmbientWindow
from vision import VisionManager


# Subclass QMainWindow to customize your application's main window
class ActiveWindow(QMainWindow):
    def __init__(self, shared_renderer, app_controller=None):
        super().__init__()
        self.app_controller = app_controller  # Reference to main app controller

        self.setWindowTitle("My App")
        self.setFixedSize(QSize(400, 300))
        self.setWindowFlags( Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # State machine - this is the "personality" system
        self.state = 'idle'  # Current state: idle, listening, thinking, success, error
        self.face_pos = (0.5, 0.5)  # Default to center
         
        # Animation variables for the chaotic blob
        self.time = 0.0  # Time counter for Perlin noise
        self.time2 = 0.0  # Secondary time counter for layered noise
        self.time3 = 0.0  # Tertiary time counter for complex movement
        self.base_radius = 100  # Base size of the blob
        self.noise_scale = 0.9  # Increased noise intensity for chaos
        self.noise_scale2 = 0.5  # Secondary noise layer
        self.noise_scale3 = 0.1  # Tertiary noise layer for fine details
        self.noise_speed = 0.05  # Faster noise for chaotic movement
        self.noise_speed2 = 0.03  # Different speed for secondary layer
        self.noise_speed3 = 0.08  # Fast tertiary layer for fine chaos

        # State-specific animation variables
        self.state_timer = 0  # Timer for state-specific animations
        self.jump_height = 0  # For success state "jumping"
        self.wobble_offset = 0  # For error state "wobbling"
        
        # OpenSimplex noise generator
        self.noise_gen = OpenSimplex(seed=12345)
        
        # Use the shared renderer
        self.blob_renderer = shared_renderer

        # Setup animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_blob)
        self.timer.start(20)  # 50fps for smooth animation
      
    def animate_blob(self):
        """Main animation loop - updates all animation variables"""
        # Increment multiple time counters for layered noise
        self.time += self.noise_speed
        self.time2 += self.noise_speed2
        self.time3 += self.noise_speed3
        
        # State-specific animations
        if self.state == 'success':
            # Jumping animation
            self.jump_height = math.sin(self.state_timer * 0.3) * 10
            self.state_timer += 1
            if self.state_timer > 50:  # Reset after 1 second
                self.state = 'idle'
                self.state_timer = 0
                
        elif self.state == 'error':
            # Wobbling animation
            self.wobble_offset = math.sin(self.state_timer * 0.5) * 5
            self.state_timer += 1
            if self.state_timer > 40:  # Reset after 0.8 seconds
                self.state = 'idle'
                self.state_timer = 0
        
        # Trigger redraw
        self.update()

    def keyPressEvent(self, event):
        """Handle keyboard input to change states"""
        if event.key() == Qt.Key.Key_L:
            self.state = 'listening'
            self.state_timer = 0
        elif event.key() == Qt.Key.Key_T:
            self.state = 'thinking'
            self.state_timer = 0
        elif event.key() == Qt.Key.Key_S:
            self.state = 'success'
            self.state_timer = 0
        elif event.key() == Qt.Key.Key_E:
            self.state = 'error'
            self.state_timer = 0
        elif event.key() == Qt.Key.Key_I:
            self.state = 'idle'
            self.state_timer = 0
        
        # Force redraw after state change
        self.update()
    
    def create_blob_shape(self):
        """Create chaotic Venom-like blob shape using multiple noise layers"""
        # Increased number of points for smoother irregular shapes
        num_points = 40
        
        # Create a list to store the points
        points = []
        
        # Calculate center position
        center_x = 200
        center_y = 150
        
        # Add state-specific position offsets
        if self.state == 'success':
            center_y += self.jump_height
        elif self.state == 'error':
            center_x += self.wobble_offset
        
        # Generate points around a circle with chaotic noise deformation
        for i in range(num_points):
            # Calculate angle for this point
            angle = (2 * math.pi * i) / num_points
            
            # Base radius for this point
            radius = self.base_radius
            
            # Layer 1: Primary chaotic noise (large deformations)
            noise_x1 = math.cos(angle) * self.noise_scale
            noise_y1 = math.sin(angle) * self.noise_scale
            noise_value1 = self.noise_gen.noise2(noise_x1 + self.time, noise_y1 + self.time)
            
            # Layer 2: Secondary noise (medium deformations)
            noise_x2 = math.cos(angle) * self.noise_scale2
            noise_y2 = math.sin(angle) * self.noise_scale2
            noise_value2 = self.noise_gen.noise2(noise_x2 + self.time2, noise_y2 + self.time2)
            
            # Layer 3: Tertiary noise (fine details and chaos)
            noise_x3 = math.cos(angle) * self.noise_scale3
            noise_y3 = math.sin(angle) * self.noise_scale3
            noise_value3 = self.noise_gen.noise2(noise_x3 + self.time3, noise_y3 + self.time3)
            
            # Combine all noise layers for chaotic effect
            total_noise = (noise_value1 * 0.6) + (noise_value2 * 0.3) + (noise_value3 * 0.1)
            
            # Apply chaotic noise to radius with increased intensity
            radius += total_noise * 50  # Much larger deformation for chaos
            
            # Add some randomness to make it even more chaotic
            random_factor = math.sin(self.time * 2 + i * 0.5) * 10
            radius += random_factor
            
            # Calculate final position
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            
            # Add to points list
            points.append(QPointF(x, y))
        
        return points

    def paintEvent(self, event):
        """Draw the blob using the BlobRenderer"""
        painter = QPainter(self)
        
        # Get the blob shape
        points = self.create_blob_shape()
        
        # Render the blob with all 3D effects
        self.blob_renderer.render_blob(painter, points, self.state, self.face_pos)
    
    def closeEvent(self, event):
        """Handle closing the active window and returning to ambient mode"""
        if self.app_controller:
            self.app_controller.close_active_window()
        event.accept()
    
    def set_face_position(self, norm_x, norm_y):
        """
        Public method to update the face position.
        This will be used by the renderer in the next paintEvent.
        """
        self.face_pos = (norm_x, norm_y)
        
        


# --- MAIN APPLICATION CONTROLLER ---
class AuraApp(QApplication):
    """Main controller that manages both AmbientWindow and ActiveWindow"""
    
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        
        # Create one shared renderer for both windows
        self.renderer = BlobRenderer()
        
        # Initialize vision system first
        self.vision_manager = VisionManager()
        
        # Create both windows
        self.ambient_window = AmbientWindow(self.renderer, self, self.vision_manager)  # Pass vision manager
        self.active_window = ActiveWindow(self.renderer, self)    # Pass self as controller
        
        # Start vision system first
        self.vision_manager.start_vision()
        
        # Setup vision connections AFTER starting the vision system
        self.setup_vision_connections()
        
        # Start with the ambient orb
        self.ambient_window.show()
    
    def setup_vision_connections(self):
        """Connect vision signals to window state changes"""
        if self.vision_manager.vision_thread:
            # Connect to main app handlers (for both windows)
            self.vision_manager.vision_thread.user_present.connect(self.on_user_present)
            self.vision_manager.vision_thread.user_absent.connect(self.on_user_absent)
            self.vision_manager.vision_thread.error_occurred.connect(self.on_vision_error)
            
            # Connect face position signal
            self.vision_manager.vision_thread.face_position_signal.connect(self._on_face_position_updated)
            
            # Also connect directly to ambient window for immediate response
            self.vision_manager.vision_thread.user_present.connect(self.ambient_window.on_user_present)
            self.vision_manager.vision_thread.user_absent.connect(self.ambient_window.on_user_absent)
    
    def on_user_present(self):
        """Handle user presence - wake up the orb"""
        # Change both windows to 'listening' state when user is present
        self.ambient_window.state = 'listening'
        self.active_window.state = 'listening'
        # Force redraw of both windows
        self.ambient_window.update()
        self.active_window.update()
    
    def on_user_absent(self):
        """Handle user absence - orb goes to sleep"""
        # Change both windows to 'idle' state when user is absent
        self.ambient_window.state = 'idle'
        self.active_window.state = 'idle'
        # Force redraw of both windows
        self.ambient_window.update()
        self.active_window.update()
    
    def on_vision_error(self, error_message):
        """Handle vision system errors"""
        # Could implement fallback behavior here
    
    def _on_face_position_updated(self, norm_x, norm_y):
        """
        Slot to receive normalized face coordinates from the vision thread.
        Passes them to both windows.
        """
        self.ambient_window.set_face_position(norm_x, norm_y)
        self.active_window.set_face_position(norm_x, norm_y)
    
    def show_active_window(self):
        """Switch to the active window"""
        self.ambient_window.hide()
        self.active_window.show()
    
    def show_ambient_window(self):
        """Switch back to the ambient orb"""
        self.active_window.hide()
        self.ambient_window.show()
    
    def close_active_window(self):
        """Handle closing the active window and returning to ambient mode"""
        self.show_ambient_window()
    
    def cleanup(self):
        """Clean up resources when app closes"""
        if self.vision_manager:
            self.vision_manager.stop_vision()


if __name__ == "__main__":
    app = AuraApp(sys.argv)
    try:
        sys.exit(app.exec())
    finally:
        app.cleanup()