"""ArUco marker generation using OpenCV."""
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Dict
import sys
import click


class ArUcoGenerator:
    """Generates ArUco markers as PIL Images."""
    
    # ArUco dictionary mapping
    DICTIONARIES = {
        'DICT_4X4_50': (cv2.aruco.DICT_4X4_50, 50),
        'DICT_4X4_100': (cv2.aruco.DICT_4X4_100, 100),
        'DICT_4X4_250': (cv2.aruco.DICT_4X4_250, 250),
        'DICT_4X4_1000': (cv2.aruco.DICT_4X4_1000, 1000),
        'DICT_5X5_50': (cv2.aruco.DICT_5X5_50, 50),
        'DICT_5X5_100': (cv2.aruco.DICT_5X5_100, 100),
        'DICT_5X5_250': (cv2.aruco.DICT_5X5_250, 250),
        'DICT_5X5_1000': (cv2.aruco.DICT_5X5_1000, 1000),
        'DICT_6X6_50': (cv2.aruco.DICT_6X6_50, 50),
        'DICT_6X6_100': (cv2.aruco.DICT_6X6_100, 100),
        'DICT_6X6_250': (cv2.aruco.DICT_6X6_250, 250),
        'DICT_6X6_1000': (cv2.aruco.DICT_6X6_1000, 1000),
        'DICT_7X7_50': (cv2.aruco.DICT_7X7_50, 50),
        'DICT_7X7_100': (cv2.aruco.DICT_7X7_100, 100),
        'DICT_7X7_250': (cv2.aruco.DICT_7X7_250, 250),
        'DICT_7X7_1000': (cv2.aruco.DICT_7X7_1000, 1000),
    }
    
    def __init__(self, dictionary: str, pattern_size_mm: float, border_bits: int = 1, 
                 quiet_zone_mm: float = 5, dpi: int = 300):
        """Initialize ArUco generator.
        
        Args:
            dictionary: ArUco dictionary name (e.g., 'DICT_5X5_100')
            pattern_size_mm: Size of the pattern in millimeters (excluding quiet zone)
            border_bits: Border width in bits (default: 1)
            quiet_zone_mm: Quiet zone around marker in mm (default: 5)
            dpi: Resolution for image generation
        """
        if dictionary not in self.DICTIONARIES:
            click.echo(f"Error: Unknown ArUco dictionary: {dictionary}", err=True)
            click.echo(f"Supported dictionaries: {', '.join(self.DICTIONARIES.keys())}", err=True)
            sys.exit(1)
        
        self.dictionary_name = dictionary
        self.dictionary_const, self.max_id = self.DICTIONARIES[dictionary]
        # OpenCV draw/generate APIs expect a dictionary object, not the enum constant
        self.dictionary = cv2.aruco.getPredefinedDictionary(self.dictionary_const)
        self.pattern_size_mm = pattern_size_mm
        self.border_bits = border_bits
        self.quiet_zone_mm = quiet_zone_mm
        self.dpi = dpi
        
        # Calculate pattern size in pixels
        self.pattern_size_pixels = int((pattern_size_mm / 25.4) * dpi)
        self.quiet_zone_pixels = int((quiet_zone_mm / 25.4) * dpi)
        
        # Total footprint includes quiet zone on all sides
        self.footprint_size_pixels = self.pattern_size_pixels + (2 * self.quiet_zone_pixels)
    
    def validate_id(self, numeric_id: int) -> tuple[bool, Optional[str]]:
        """Validate that numeric ID is within dictionary range.
        
        Args:
            numeric_id: Numeric ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if numeric_id < 0:
            return False, f"ArUco ID must be non-negative, got {numeric_id}"
        if numeric_id >= self.max_id:
            return False, f"ArUco ID {numeric_id} exceeds maximum {self.max_id - 1} for {self.dictionary_name}"
        return True, None
    
    def generate(self, numeric_id: int) -> Optional[Image.Image]:
        """Generate ArUco marker image from numeric ID.
        
        Args:
            numeric_id: Numeric ID for the marker (0 to max_id-1)
            
        Returns:
            PIL Image of ArUco marker, or None if generation fails
        """
        # Validate ID
        is_valid, error_msg = self.validate_id(numeric_id)
        if not is_valid:
            click.echo(f"Warning: {error_msg}", err=True)
            return None
        
        try:
            # Generate marker using OpenCV
            # Use drawMarker for older OpenCV or generateImageMarker for newer versions
            try:
                # Try newer API first (OpenCV 4.7+)
                marker_img = cv2.aruco.generateImageMarker(
                    self.dictionary,
                    numeric_id,
                    self.pattern_size_pixels
                )
            except (AttributeError, TypeError):
                # Fall back to older API (OpenCV 4.x)
                # drawMarker returns the image directly
                marker_img = cv2.aruco.drawMarker(
                    self.dictionary,
                    numeric_id,
                    self.pattern_size_pixels
                )
            
            # Add quiet zone (white padding)
            if self.quiet_zone_pixels > 0:
                marker_with_quiet = np.ones(
                    (self.footprint_size_pixels, self.footprint_size_pixels),
                    dtype=np.uint8
                ) * 255  # White background
                
                # Place marker in center
                start_y = self.quiet_zone_pixels
                end_y = start_y + self.pattern_size_pixels
                start_x = self.quiet_zone_pixels
                end_x = start_x + self.pattern_size_pixels
                
                marker_with_quiet[start_y:end_y, start_x:end_x] = marker_img
                marker_img = marker_with_quiet
            
            # Convert to PIL Image (grayscale)
            pil_img = Image.fromarray(marker_img, mode='L')
            
            return pil_img
            
        except Exception as e:
            click.echo(f"Error: Failed to generate ArUco marker for ID {numeric_id}: {e}", err=True)
            return None
    
    def get_footprint_size_mm(self) -> float:
        """Get total marker footprint size including quiet zone."""
        return self.pattern_size_mm + (2 * self.quiet_zone_mm)

