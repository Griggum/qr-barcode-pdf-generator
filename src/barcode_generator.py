"""Barcode generation module."""
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from typing import Optional, Tuple
import sys


class BarcodeGenerator:
    """Generates barcodes as PIL Images."""
    
    SUPPORTED_SYMBOLOGIES = {
        'code128': barcode.get_barcode_class('code128'),
        'code39': barcode.get_barcode_class('code39'),
        'ean13': barcode.get_barcode_class('ean13'),
        'i2of5': barcode.get_barcode_class('itf'),  # Interleaved 2 of 5 is 'itf' in python-barcode
        'itf': barcode.get_barcode_class('itf')  # Also support direct 'itf' name
    }
    
    def __init__(self, symbology: str, height_mm: float, width_factor: float, 
                 quiet_zone_mm: float, dpi: int = 300):
        """Initialize barcode generator.
        
        Args:
            symbology: Barcode symbology name
            height_mm: Height of barcode bars in millimeters
            width_factor: Bar width multiplier
            quiet_zone_mm: Quiet zone in millimeters on each side
            dpi: Resolution for image generation
        """
        self.symbology_name = symbology.lower()
        self.height_mm = height_mm
        self.width_factor = width_factor
        self.quiet_zone_mm = quiet_zone_mm
        self.dpi = dpi
        
        if self.symbology_name not in self.SUPPORTED_SYMBOLOGIES:
            raise ValueError(f"Unsupported symbology: {symbology}")
        
        self.barcode_class = self.SUPPORTED_SYMBOLOGIES[self.symbology_name]
        
        # Convert mm to pixels
        self.height_pixels = int((height_mm / 25.4) * dpi)
        self.quiet_zone_pixels = int((quiet_zone_mm / 25.4) * dpi)
    
    def validate(self, data: str) -> Tuple[bool, Optional[str]]:
        """Validate data for the chosen symbology.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.symbology_name == 'code39':
            # Code 39: A-Z, 0-9, and symbols: - . $ / + % SPACE
            # Lowercase letters are auto-converted
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.$/+% ')
            if not all(c.upper() in valid_chars for c in data):
                return False, f"Code 39 only supports: A-Z, 0-9, and symbols: - . $ / + % SPACE"
        
        elif self.symbology_name == 'ean13':
            # EAN-13: Numeric only, exactly 12 or 13 digits
            if not data.isdigit():
                return False, "EAN-13 requires numeric only (0-9)"
            if len(data) not in [12, 13]:
                return False, f"EAN-13 requires exactly 12 or 13 digits, got {len(data)}"
        
        elif self.symbology_name in ['i2of5', 'itf']:
            # Interleaved 2 of 5: Numeric only, even number of digits
            if not data.isdigit():
                return False, "Interleaved 2 of 5 requires numeric only (0-9)"
            if len(data) % 2 != 0:
                return False, f"Interleaved 2 of 5 requires even number of digits, got {len(data)}"
        
        # Code 128 supports full ASCII, no validation needed
        
        return True, None
    
    def normalize(self, data: str) -> str:
        """Normalize data for symbology (e.g., uppercase for Code 39)."""
        if self.symbology_name == 'code39':
            return data.upper()
        return data
    
    def generate(self, data: str) -> Optional[Image.Image]:
        """Generate barcode image from data.
        
        Args:
            data: Data to encode in barcode
            
        Returns:
            PIL Image of barcode, or None if generation fails
        """
        try:
            # Normalize data
            normalized_data = self.normalize(data)
            
            # Create barcode
            barcode_instance = self.barcode_class(normalized_data, writer=ImageWriter())
            
            # Generate image with custom settings
            options = {
                'module_height': self.height_pixels,
                'module_width': self.width_factor,
                'quiet_zone': self.quiet_zone_pixels,
                'font_size': 0,  # No text below barcode
                'text_distance': 0,
                'write_text': False
            }
            
            # Generate as PIL Image
            img = barcode_instance.render(options)
            
            # Ensure it's a PIL Image
            if not isinstance(img, Image.Image):
                img = Image.fromarray(img) if hasattr(img, '__array__') else Image.open(img)
            
            return img
            
        except Exception as e:
            return None
    
    def get_width(self, data: str) -> float:
        """Estimate barcode width in mm based on data length.
        
        This is an approximation. Actual width depends on the symbology
        and specific characters used.
        """
        # Rough estimation: each character adds approximately width_factor * base_width
        # Base width per character varies by symbology
        base_chars = len(data)
        
        if self.symbology_name == 'code128':
            # Code 128: roughly 11 modules per character + start/stop
            estimated_modules = (base_chars * 11) + 11
        elif self.symbology_name == 'code39':
            # Code 39: roughly 13 modules per character + start/stop
            estimated_modules = (base_chars * 13) + 13
        elif self.symbology_name == 'ean13':
            # EAN-13: fixed 95 modules
            estimated_modules = 95
        elif self.symbology_name in ['i2of5', 'itf']:
            # I2OF5: roughly 7 modules per 2 digits + start/stop
            estimated_modules = ((base_chars // 2) * 7) + 7
        else:
            estimated_modules = base_chars * 10
        
        # Convert modules to mm (approximate)
        module_width_mm = (self.width_factor / 25.4) * (300 / self.dpi)  # Rough conversion
        width_mm = (estimated_modules * module_width_mm) + (2 * self.quiet_zone_mm)
        
        return width_mm

