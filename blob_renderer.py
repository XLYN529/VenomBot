"""
BlobRenderer - Handles all 3D rendering logic for the chaotic blob
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QRadialGradient, QLinearGradient
import math
from opensimplex import OpenSimplex


class BlobRenderer:
    """Handles all 3D rendering logic for the chaotic blob"""
    
    def __init__(self):
        # Noise generation for organic blob movement
        self.noise_gen = OpenSimplex(seed=12345)
        self.time = 0.0
        self.time2 = 0.0
        self.time3 = 0.0
        
        # Noise parameters for layered deformation
        self.noise_scale = 0.02
        self.noise_scale2 = 0.03
        self.noise_scale3 = 0.01
        self.noise_speed = 0.02
        self.noise_speed2 = 0.015
        self.noise_speed3 = 0.025
        
        # Store current state and face position
        self.state = 'idle'
        self.face_pos = (0.5, 0.5)

    def get_state_color(self, state):
        """Get the base color for a given state"""
        if state == 'idle':
            return QColor(10, 10, 15)       # Very dark gray - user absent
        elif state == 'listening':
            return QColor(0, 200, 255)     # Very bright cyan-blue - user present
        elif state == 'thinking':
            return QColor(255, 150, 0)     # Bright orange - processing
        elif state == 'success':
            return QColor(0, 255, 100)     # Bright green - success
        elif state == 'error':
            return QColor(255, 50, 50)     # Bright red - error
        else:
            return QColor(10, 10, 15)      # Default dark

    def create_color_variations(self, base_color):
        """Create light and dark variations of the base color"""
        highlight_color = QColor(base_color)
        highlight_color.setRed(min(255, highlight_color.red() + 80))
        highlight_color.setGreen(min(255, highlight_color.green() + 80))
        highlight_color.setBlue(min(255, highlight_color.blue() + 80))
        
        mid_light_color = QColor(base_color)
        mid_light_color.setRed(min(255, mid_light_color.red() + 40))
        mid_light_color.setGreen(min(255, mid_light_color.green() + 40))
        mid_light_color.setBlue(min(255, mid_light_color.blue() + 40))
        
        mid_dark_color = QColor(base_color)
        mid_dark_color.setRed(max(0, mid_dark_color.red() - 40))
        mid_dark_color.setGreen(max(0, mid_dark_color.green() - 40))
        mid_dark_color.setBlue(max(0, mid_dark_color.blue() - 40))
        
        shadow_color = QColor(base_color)
        shadow_color.setRed(max(0, shadow_color.red() - 60))
        shadow_color.setGreen(max(0, shadow_color.green() - 60))
        shadow_color.setBlue(max(0, shadow_color.blue() - 60))
        
        return highlight_color, mid_light_color, mid_dark_color, shadow_color

    def create_main_gradient(self, center, max_distance, highlight_color, mid_light_color, base_color, mid_dark_color, shadow_color):
        """Create the main lighting gradient"""
        light_center = QPointF(center.x() - max_distance * 0.3, center.y() - max_distance * 0.3)
        main_gradient = QRadialGradient(light_center, max_distance * 1.2)
        
        main_gradient.setColorAt(0.0, highlight_color)    # Bright highlight
        main_gradient.setColorAt(0.2, mid_light_color)    # Light area
        main_gradient.setColorAt(0.5, base_color)         # Base color
        main_gradient.setColorAt(0.8, mid_dark_color)      # Shadow area
        main_gradient.setColorAt(1.0, shadow_color)        # Deep shadow
        
        return main_gradient

    def create_rim_gradient(self, center, max_distance):
        """Create the rim lighting gradient"""
        rim_gradient = QRadialGradient(center, max_distance * 1.5)
        rim_gradient.setColorAt(0.0, QColor(255, 255, 255, 0))    # Transparent center
        rim_gradient.setColorAt(0.7, QColor(255, 255, 255, 0))   # Still transparent
        rim_gradient.setColorAt(0.9, QColor(255, 255, 255, 30))  # Subtle rim
        rim_gradient.setColorAt(1.0, QColor(255, 255, 255, 60))  # Bright rim
        
        return rim_gradient

    def create_specular_gradient(self, center, max_distance):
        """Create the specular highlight gradient"""
        specular_center = QPointF(center.x() - max_distance * 0.4, center.y() - max_distance * 0.4)
        specular_gradient = QRadialGradient(specular_center, max_distance * 0.3)
        
        specular_gradient.setColorAt(0.0, QColor(255, 255, 255, 120))  # Bright highlight
        specular_gradient.setColorAt(0.3, QColor(255, 255, 255, 60))   # Fading
        specular_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))    # Transparent
        
        return specular_gradient

    def create_secondary_gradient(self, center, max_distance):
        """Create a secondary highlight gradient"""
        secondary_center = QPointF(center.x() + max_distance * 0.2, center.y() - max_distance * 0.2)
        secondary_gradient = QRadialGradient(secondary_center, max_distance * 0.2)
        
        secondary_gradient.setColorAt(0.0, QColor(255, 255, 255, 40))  # Subtle highlight
        secondary_gradient.setColorAt(0.5, QColor(255, 255, 255, 20))  # Fading
        secondary_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))    # Transparent
        
        return secondary_gradient

    def create_ambient_occlusion_gradient(self, center, max_distance):
        """Create ambient occlusion gradient"""
        ao_gradient = QRadialGradient(center, max_distance * 1.3)
        ao_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))      # Transparent center
        ao_gradient.setColorAt(0.6, QColor(0, 0, 0, 0))     # Still transparent
        ao_gradient.setColorAt(0.8, QColor(0, 0, 0, 20))    # Subtle darkening
        ao_gradient.setColorAt(1.0, QColor(0, 0, 0, 40))     # Dark edges
        
        return ao_gradient

    def create_shadow_gradient(self, center, max_distance, shadow_offset):
        """Create contact shadow gradient"""
        shadow_center = QPointF(center.x() + shadow_offset, center.y() + shadow_offset)
        shadow_gradient = QRadialGradient(shadow_center, max_distance * 0.8)
        
        shadow_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))      # Transparent center
        shadow_gradient.setColorAt(0.3, QColor(0, 0, 0, 60))    # Soft shadow
        shadow_gradient.setColorAt(0.7, QColor(0, 0, 0, 80))    # Medium shadow
        shadow_gradient.setColorAt(1.0, QColor(0, 0, 0, 100))   # Dark shadow
        
        return shadow_gradient

    def render_blob(self, painter, points, state, face_pos=(0.5, 0.5)):
        """Main rendering method - draws the complete 3D blob"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Store state and face position for helper methods
        self.state = state
        self.face_pos = face_pos
        
        # Create path from points
        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        
        # Calculate blob center and dimensions
        center_x = sum(point.x() for point in points) / len(points)
        center_y = sum(point.y() for point in points) / len(points)
        center = QPointF(center_x, center_y)
        max_distance = max(math.sqrt((point.x() - center_x)**2 + (point.y() - center_y)**2) for point in points)
        
        # Get base color and create variations
        base_color = self.get_state_color(state)
        highlight_color, mid_light_color, mid_dark_color, shadow_color = self.create_color_variations(base_color)
        
        # Create all gradients
        main_gradient = self.create_main_gradient(center, max_distance, highlight_color, mid_light_color, base_color, mid_dark_color, shadow_color)
        rim_gradient = self.create_rim_gradient(center, max_distance)
        specular_gradient = self.create_specular_gradient(center, max_distance)
        secondary_gradient = self.create_secondary_gradient(center, max_distance)
        ao_gradient = self.create_ambient_occlusion_gradient(center, max_distance)
        
        # Create shadow path
        shadow_offset = 4
        shadow_path = QPainterPath()
        shadow_points = [QPointF(point.x() + shadow_offset, point.y() + shadow_offset) for point in points]
        shadow_path.moveTo(shadow_points[0])
        for point in shadow_points[1:]:
            shadow_path.lineTo(point)
        shadow_path.closeSubpath()
        
        shadow_gradient = self.create_shadow_gradient(center, max_distance, shadow_offset)
        
        # Draw all layers in correct order
        self._draw_layer(painter, ao_gradient, path)  # Ambient occlusion first
        self._draw_layer(painter, shadow_gradient, shadow_path)  # Shadow second
        self._draw_layer(painter, main_gradient, path)  # Main blob third
        self._draw_layer(painter, rim_gradient, path)  # Rim lighting fourth
        self._draw_layer(painter, specular_gradient, path)  # Specular highlight fifth
        self._draw_layer(painter, secondary_gradient, path)  # Secondary highlight sixth
        
        # Draw parametric symbiote eyes
        self._draw_symbiote_eyes(painter)

    def _draw_layer(self, painter, gradient, path):
        """Helper method to draw a single layer"""
        painter.setPen(QPen(Qt.GlobalColor.transparent, 0))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

    # --- NEW HELPER METHOD ---
    def _create_symbiote_eye_path(self, length=120, height=80):
        """Creates sharp, hooked Venom eye shape with aggressive taper."""
        p = QPainterPath()
        steps = 32

        # start from inner corner
        p.moveTo(0, 0)

        # top arch: aggressive taper toward outer corner
        for i in range(steps + 1):
            t = i / steps
            x = t * length
            y = -math.sin(t * math.pi * 0.8) ** 1.5 * height * (0.9 - 0.3 * t)
            p.lineTo(x, y)

        # outer hook tip
        p.cubicTo(length * 0.95, -height * 0.4, length * 1.1, height * 0.2, length * 0.7, height * 0.6)

        # bottom claw back inward
        for i in range(steps, -1, -1):
            t = i / steps
            x = t * length
            y = math.sin(t * math.pi * 0.6) ** 1.5 * height * 0.3 * (0.3 + 0.7 * t)
            p.lineTo(x, y)

        p.closeSubpath()
        return p

    def _draw_symbiote_eyes(self, painter):
        """Draws sharp, hooked Venom-style eyes with solid white fill."""
        painter.save()
        w = painter.window().width()
        h = painter.window().height()
        
        # Center coordinates
        cx = w / 2
        cy = h / 2
        
        # Face tracking offsets
        look_x = (self.face_pos[0] - 0.5) * 2.0
        look_y = (self.face_pos[1] - 0.5) * 2.0
        
        # Scale eye size based on window dimensions
        eye_length = w * 0.12  # Narrow, vertical
        eye_height = h * 0.18  # Taller than wide
        
        # Create eye paths
        left_eye = self._create_symbiote_eye_path(eye_length, eye_height)
        right_eye = self._create_symbiote_eye_path(eye_length, eye_height)
        
        # Solid white fill - no transparency
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))  # solid white
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Eye positioning
        eye_spacing = w * 0.08  # Close together
        eye_y_offset = -h * 0.05  # Centered vertically
        
        # Add face tracking movement
        tracking_x = look_x * (w * 0.02)
        tracking_y = look_y * (h * 0.01)
        
        # Draw Left Eye (with inward rotation)
        painter.save()
        painter.translate(cx - eye_spacing + tracking_x, cy + eye_y_offset + tracking_y)
        painter.rotate(-8)  # inward tilt for aggression
        painter.drawPath(left_eye)
        painter.restore()
        
        # Draw Right Eye (mirrored with inward rotation)
        painter.save()
        painter.translate(cx + eye_spacing + tracking_x, cy + eye_y_offset + tracking_y)
        painter.scale(-1, 1)  # mirror horizontally
        painter.rotate(8)     # inward tilt for aggression
        painter.drawPath(right_eye)
        painter.restore()
        
        painter.restore()