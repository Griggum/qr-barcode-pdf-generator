"""QR code generation module."""
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image
from typing import Optional


class QRGenerator:
    """Generates QR codes as PIL Images."""
    
    ERROR_CORRECTION_MAP = {
        'L': ERROR_CORRECT_L,
        'M': ERROR_CORRECT_M,
        'Q': ERROR_CORRECT_Q,
        'H': ERROR_CORRECT_H
    }
    
    def __init__(self, size_mm: float, error_correction: str, quiet_zone: int, dpi: int = 300):
        """Initialize QR generator.
        
        Args:
            size_mm: Size of QR code in millimeters
            error_correction: Error correction level (L, M, Q, H)
            quiet_zone: Quiet zone in module units
            dpi: Resolution for image generation
        """
        self.size_mm = size_mm
        self.error_correction = error_correction.upper()
        self.quiet_zone = quiet_zone
        self.dpi = dpi
        
        # Convert mm to pixels at given DPI
        self.size_pixels = int((size_mm / 25.4) * dpi)
    
    def generate(self, data: str) -> Optional[Image.Image]:
        """Generate QR code image from data.
        
        Args:
            data: Data to encode in QR code
            
        Returns:
            PIL Image of QR code, or None if generation fails
        """
        try:
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version
                error_correction=self.ERROR_CORRECTION_MAP.get(self.error_correction, ERROR_CORRECT_M),
                box_size=10,  # Base box size
                border=self.quiet_zone
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize to exact size in pixels
            qr_img = qr_img.resize((self.size_pixels, self.size_pixels), Image.Resampling.LANCZOS)
            
            return qr_img
            
        except Exception as e:
            return None

