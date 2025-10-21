"""
BlobRenderer - Handles all 3D rendering logic for the chaotic blob
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QRadialGradient, QLinearGradient
import math
import time
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
        
       

        # Eye tip positions for blob protection
        self.left_eye_tip_x = 0
        self.left_eye_tip_y = 0
        self.right_eye_tip_x = 0
        self.right_eye_tip_y = 0
        
    def get_eye_protection_points(self, w, h):
        """Get eye tip positions for blob protection"""
        cx = w / 2
        cy = h / 2
        eye_spacing = w * 0.2
        eye_y_offset = -h * 0.05

        left_tip = (cx - eye_spacing * 0.65, cy + eye_y_offset - h * 0.02)
        right_tip = (cx + eye_spacing * 0.65, cy + eye_y_offset - h * 0.02)
        
        return [
            left_tip,
            right_tip
        ]

    # --- Noise protection + eye motion helpers ---
    
    def eye_safe_amplitude(self, x, y, amplitude, eye_tips, protection_radius):
        """
        Reduce deformation amplitude near the eyes so the blob doesn't stretch inward there.
        eye_tips: list of (x, y) coordinates of the eyes' outermost tips.
        """
        for tip in eye_tips:
            dx = x - tip[0]
            dy = y - tip[1]
            dist = math.hypot(dx, dy)
            if dist < protection_radius:
                fade = dist / protection_radius
                amplitude *= fade ** 2  # Stronger damping for debugging
        return amplitude

    def get_eye_offset(self, tip_pos, noise_scale, noise_strength, t):
        """
        Returns a small (x, y) offset for the eye based on blob noise motion.
        Makes it feel like the eye is glued to the blob surface.
        """
        nx = tip_pos.x() * noise_scale
        ny = tip_pos.y() * noise_scale

        offset_x = self.noise_gen.noise2(x=nx, y=t) * noise_strength
        offset_y = self.noise_gen.noise2(x=ny, y=t + 50.0) * noise_strength  # offset seed for variety

        return offset_x, offset_y

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
        light_center = QPointF(center.x() - max_distance * 0.9, center.y() - max_distance * 0.9)
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
        
        # Update time for animations
        self.time += 0.01
        
        # Store state and face position for helper methods
        self.state = state
        self.face_pos = face_pos

         # Simulate blob "head tilt" toward the user
        tilt_x = (self.face_pos[0] - 0.5) * 0.5   # -0.5 to +0.5 range → left/right
        tilt_y = (self.face_pos[1] - 0.5) * 0.4   # -0.4 to +0.4 range → up/down

        
        # Calculate blob center and dimensions
        center_x = sum(point.x() for point in points) / len(points)
        center_y = sum(point.y() for point in points) / len(points)
        center = QPointF(center_x, center_y)
        max_distance = max(math.sqrt((point.x() - center_x)**2 + (point.y() - center_y)**2) for point in points)

        # Apply subtle directional bias so blob leans toward the user
        biased_points = []
        for p in points:
            dx = (p.x() - center_x)
            dy = (p.y() - center_y)
            # Shift slightly toward face direction
            new_x = p.x() + tilt_x * 40.0 * (dy / max_distance)
            new_y = p.y() + tilt_y * 40.0 * (dx / max_distance)
            biased_points.append(QPointF(new_x, new_y))

        path = QPainterPath()
        path.moveTo(biased_points[0])
        for point in biased_points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        
        # Get base color and create variations
        base_color = self.get_state_color(state)
        highlight_color, mid_light_color, mid_dark_color, shadow_color = self.create_color_variations(base_color)
        
        # Create all gradients
        # Shift lighting toward tilt direction (like a face turning)
        light_center = QPointF(center.x() - tilt_x * max_distance * 2.2,center.y() - tilt_y * max_distance * 2.2)

        main_gradient = QRadialGradient(light_center, max_distance * 1.2)
        main_gradient.setColorAt(0.0, highlight_color)
        main_gradient.setColorAt(0.2, mid_light_color)
        main_gradient.setColorAt(0.5, base_color)
        main_gradient.setColorAt(0.8, mid_dark_color)
        main_gradient.setColorAt(1.0, shadow_color)

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


    # --- Build QPainterPath from samplers ---
    def build_bezier_symbiote_eye(self, length, height):
        """
        Construct a Venom-style eye with a heavy lower curve and a sharp upper taper.
        Uses two cubic Bézier segments with C1 continuity at the tip.
        """
        p = QPainterPath()
        p.moveTo(0.0, 0.0)

        # --- Upper lid (flatter) ---
        c1 = QPointF(length * 0.25, -height * 0.45)
        c2 = QPointF(length * 0.65, -height * 0.20)
        end_outer = QPointF(length * 0.88, 0.0)
        p.cubicTo(c1, c2, end_outer)

        # --- Hook tip (small flick upward/outward) ---
        c3 = QPointF(length * 1.30, height * 0.15)
        c4 = QPointF(length * 0.85, height * 0.45)
        tip_return = QPointF(length * 0.68, height * 0.60)
        p.cubicTo(c3, c4, tip_return)

        # --- Lower lid (bulky belly) ---
        # Reflect c4 around tip_return for smooth tangent continuity
        c5 = QPointF(2*tip_return.x() - c4.x(), 2*tip_return.y() - c4.y())
        c6 = QPointF(length * 0.25, height * 0.65)
        inner_return = QPointF(0.0, 0.0)
        p.cubicTo(c5, c6, inner_return)

        p.closeSubpath()
        return p


    def _draw_symbiote_eyes(self, painter):
        """Draws Venom-style eyes using cubic Bézier curves."""
        painter.save()
        w = painter.window().width()
        h = painter.window().height()
        
        # Center coordinates
        cx = w / 2
        cy = h / 2
        
        # Face tracking offsets
        look_x = (self.face_pos[0] - 0.5) * 2.0
        look_y = (self.face_pos[1] - 0.5) * 2.0
        
        # Eye dimensions
        eye_length = w * 0.20
        eye_height = h * 0.12
        
        # Eye positioning
        eye_spacing = w * 0.2
        eye_y_offset = -h * 0.05
        
        # Face tracking movement
        tracking_x = look_x * (w * 0.03)
        tracking_y = look_y * (h * 0.03)
        
        # --- Time and breathing motion ---
        t = time.time() * 0.5
        breath_amplitude = w * 0.006   # how far they move together
        breath_speed = 2.0              # breathing speed
        breath_offset = math.sin(t * breath_speed) * breath_amplitude

        # --- Shared blob "glue" noise offset ---
        shared_noise_x = self.noise_gen.noise2(t * 0.3, 10.0) * 8.0
        shared_noise_y = self.noise_gen.noise2(t * 0.3, 20.0) * 8.0
        shared_offset = (shared_noise_x, shared_noise_y)
        
        # --- Build eye path ---
        eye = self.build_bezier_symbiote_eye(eye_length, eye_height)
        rect = eye.boundingRect()
        pivot = rect.center()
        
        # Paint settings
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.setPen(Qt.PenStyle.NoPen)

        # Shared scale (breathing size pulse)
        scale_factor = 1.0 + math.sin(t * 2.0) * 0.005

        # --- LEFT EYE ---
        painter.save()
        painter.translate(cx - eye_spacing + tracking_x - breath_offset + shared_offset[0],
                        cy + eye_y_offset + tracking_y + shared_offset[1])
        painter.translate(pivot)
        painter.rotate(50)  # inward tilt
        painter.translate(-pivot)
        painter.scale(scale_factor, scale_factor)
        painter.drawPath(eye)
        painter.restore()

        # --- RIGHT EYE ---
        painter.save()
        painter.translate(cx + eye_spacing + tracking_x + breath_offset + shared_offset[0],
                        cy + eye_y_offset + tracking_y + shared_offset[1])
        painter.scale(-1, 1)  # mirror horizontally
        painter.translate(pivot)
        painter.rotate(50)  # inward tilt
        painter.translate(-pivot)
        painter.scale(scale_factor, scale_factor)
        painter.drawPath(eye)
        painter.restore()

        painter.restore()
