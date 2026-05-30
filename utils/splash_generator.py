from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QSplashScreen, QProgressBar, QApplication, 
                            QLabel, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QBrush, QLinearGradient

class ModernProgressBar(QProgressBar):
    """Custom progress bar with smooth animations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self._pulse_value = 0.0  # Initialize before creating animation
        self._pulse_animation = QPropertyAnimation(self, b"pulseValue")
       
    @pyqtProperty(float)
    def pulseValue(self):
        return self._pulse_value
    
    @pulseValue.setter
    def pulseValue(self, value):
        self._pulse_value = value
        self.update()
        
    def start_pulse(self):
        """Start pulse animation for loading states"""
        self._pulse_animation.setDuration(1500)
        self._pulse_animation.setStartValue(0.0)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        self._pulse_animation.start()

class AnimatedLabel(QLabel):
    """Label with fade-in animation"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animation setup
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def fade_in(self, delay=0):
        """Fade in the label with optional delay"""
        QTimer.singleShot(delay, self.animation.start)

class ProfessionalSplashScreen(QSplashScreen):
    """Modern, professional splash screen with standard color palette and no overlap"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)

    def __init__(self, pixmap=None):
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QSplashScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.97), stop:0.3 rgba(245,245,245,0.93),
                    stop:0.7 rgba(235,235,235,0.89), stop:1 rgba(225,225,225,0.85));
                border-radius: 16px;
                border: 1px solid rgba(200, 200, 200, 0.4);
            }
        """)
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        # Title
        self.title_label = AnimatedLabel("Wind Wise Insights Pro", self)
        self.title_label.setFont(QFont("Times Roman New", 28, QFont.Bold))
        self.title_label.setStyleSheet("""
            color: #222;
            background: transparent;
            padding: 5px;
        """)
        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(15)
        title_glow.setColor(QColor(180, 180, 180, 120))
        title_glow.setOffset(0, 1)
        self.title_label.setGraphicsEffect(title_glow)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(50, 160, 500, 50)

        # Subtitle
        self.subtitle_label = AnimatedLabel("Advanced Wind Analytics Platform", self)
        self.subtitle_label.setFont(QFont("Times Roman New", 14, QFont.Normal))
        self.subtitle_label.setStyleSheet("""
            color: #555;
            background: transparent;
            letter-spacing: 1px;
        """)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setGeometry(50, 220, 500, 25)

        # Status label
        self.status_label = AnimatedLabel("Initializing...", self)
        self.status_label.setFont(QFont("Times Roman New", 11))
        self.status_label.setStyleSheet("""
            color: #444;
            background: transparent;
            font-weight: 500;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setGeometry(50, 270, 500, 20)

        # Progress bar
        self.progress_bar = ModernProgressBar(self)
        self.progress_bar.setGeometry(100, 330, 400, 8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255,255,255,0.3);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #bdbdbd, stop:0.5 #757575, stop:1 #424242);
                border-radius: 4px;
                margin: 0px;
            }
        """)

        # Version info
        version = f"Version 1.30.02 • Build {datetime.now().strftime('%Y%m%d')}"
        self.version_label = AnimatedLabel(version, self)
        self.version_label.setFont(QFont("Times Roman New", 10))
        self.version_label.setStyleSheet("""
            color: #888;
            background: transparent;
        """)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setGeometry(50, 370, 500, 20)

        self.status_updated.connect(self.status_label.setText)
        self.progress_updated.connect(self.progress_bar.setValue)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        
    def _setup_animations(self):
        """Setup entrance animations"""
        # Staggered fade-in animations
        self.title_label.fade_in(200)
        self.subtitle_label.fade_in(400)
        self.status_label.fade_in(600)
        self.version_label.fade_in(800)
        
        # Start progress bar pulse
        QTimer.singleShot(1000, self.progress_bar.start_pulse)
        
    def animate_progress(self, steps=None):
        """Smooth progress animation with status updates"""
        if steps is None:
            steps = [
                (10, "Loading configuration..."),
                (25, "Initializing wind models..."),
                (45, "Setting up analytics engine..."),
                (65, "Loading weather data..."),
                (80, "Preparing user interface..."),
                (95, "Finalizing setup..."),
                (100, "Ready to login!")
            ]
        
        self.current_step = 0
        self.steps = steps
        
        # Create smooth animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_progress)
        self.animation_timer.start(100)  # Update every 100ms
        
    def _update_progress(self):
        """Update progress smoothly"""
        if self.current_step < len(self.steps):
            target_value, status = self.steps[self.current_step]
            current_value = self.progress_bar.value()
            
            if current_value < target_value:
                # Smooth increment
                new_value = min(current_value + 2, target_value)
                self.progress_updated.emit(new_value)
                
                if new_value == target_value:
                    self.status_updated.emit(status)
                    self.current_step += 1
            else:
                self.current_step += 1
        else:
            self.animation_timer.stop()
            
            # Make sure we're at 100% before closing
            if self.progress_bar.value() < 100:
                self.progress_updated.emit(100)
                
            # Show "Ready to login!" for a moment before closing
            QTimer.singleShot(1000, self.close)
            
    def show_with_fade(self):
        """Show splash screen with fade effect"""
        self.show()
        self.raise_()
        self.activateWindow()

class ModernSplashGenerator:
    def __init__(self, size: Tuple[int, int] = (600, 350)):
        self.size = size

    def generate(self, app_logo: Optional[str] = None, brand_logo: Optional[str] = None) -> Path:
        img = Image.new('RGBA', self.size, (255, 255, 255, 255))
        self._create_glass_background(img)
        self._add_glass_elements(img)
        # Branding logo (top right)
        if brand_logo and os.path.exists(brand_logo):
            self._add_logo(img, brand_logo, (self.size[0] - 70, 40), (80, 40))
        # App logo (centered above title)
        if app_logo and os.path.exists(app_logo):
            self._add_logo(img, app_logo, (self.size[0] // 2, 110), (220, 220))
        Path("resources/images").mkdir(parents=True, exist_ok=True)
        path = Path("resources/images/modern_splash.png")
        img.save(path, "PNG", optimize=True)
        return path

    def _create_glass_background(self, img: Image):
        draw = ImageDraw.Draw(img)
        width, height = self.size
        for y in range(height):
            progress = y / height
            gray = int(255 - (30 * progress))
            color = (max(220, min(255, gray)),) * 3
            draw.line([(0, y), (width, y)], fill=color)

    def _add_glass_elements(self, img: Image):
        width, height = self.size
        glass_specs = [
            (width * 0.85, height * 0.15, 45),
            (width * 0.15, height * 0.85, 35),
            (width * 0.9, height * 0.7, 28),
            (width * 0.1, height * 0.3, 32),
            (width * 0.5, height * 0.5, 80)
        ]
        for i, (x, y, radius) in enumerate(glass_specs):
            color = (255, 255, 255, 60) if i % 2 == 0 else (200, 200, 200, 45)
            glass_img = Image.new('RGBA', self.size, (0, 0, 0, 0))
            glass_draw = ImageDraw.Draw(glass_img)
            glass_draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
            glass_img = glass_img.filter(ImageFilter.GaussianBlur(8))
            img.alpha_composite(glass_img)

    def _add_logo(self, img: Image, logo_path: str, center: Tuple[int, int], max_size: Tuple[int, int]):
        try:
            logo = Image.open(logo_path).convert('RGBA')
            logo.thumbnail(max_size, Image.Resampling.LANCZOS)
            shadow = Image.new('RGBA', logo.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rectangle([0, 0, logo.size[0], logo.size[1]], fill=(0, 0, 0, 60))
            shadow = shadow.filter(ImageFilter.GaussianBlur(6))
            x, y = center[0] - logo.width // 2, center[1] - logo.height // 2
            img.alpha_composite(shadow, (x + 2, y + 2))
            img.alpha_composite(logo, (x, y))
        except Exception as e:
            print(f"Logo processing error: {e}")

def create_professional_splash(app_logo_path=None, brand_logo_path=None):
    """Create modern professional splash screen with Fusion styling"""
    
    # Set Fusion style for the application
    app = QApplication.instance()
    if app:
        app.setStyle('Fusion')
        
        # Apply dark palette
        dark_palette = app.palette()
        dark_palette.setColor(dark_palette.Window, QColor(53, 53, 53))
        dark_palette.setColor(dark_palette.WindowText, QColor(255, 255, 255))
        app.setPalette(dark_palette)
    
    # Generate background
    generator = ModernSplashGenerator()
    splash_path = generator.generate(app_logo_path, brand_logo_path)
    pixmap = QPixmap(str(splash_path))
    
    # Create splash screen
    splash = ProfessionalSplashScreen(pixmap)
    return splash

def demo_splash():
    """Demo function to show the splash screen"""
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Apply Fusion style
    
    splash = create_professional_splash()
    splash.show_with_fade()
    
    # Start progress animation
    splash.animate_progress()
    
    # Keep splash visible for demo
    QTimer.singleShot(80000, app.quit)  # Close after 8 seconds
    
    return app.exec_()

if __name__ == "__main__":
    demo_splash()