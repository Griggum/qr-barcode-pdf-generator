"""AprilTag generation using moms_apriltag library."""
try:
    from moms_apriltag import TagGenerator2
except ImportError:
    TagGenerator2 = None

import math
import numpy as np
from PIL import Image, ImageDraw
from typing import Optional, Dict
import sys
import click


class AprilTagGenerator:
    """Generates AprilTags as PIL Images."""
    
    # AprilTag family mapping and max IDs
    # Note: Actual max IDs depend on the library implementation
    FAMILIES = {
        'tag36h11': {'max_id': 58797},
        'tag25h9': {'max_id': 35588},
        'tag16h5': {'max_id': 30},
        'tag21h7': {'max_id': 127},
        'tagStandard41h12': {'max_id': 2114074},
        'tagStandard52h13': {'max_id': 58535},
        'tagCircle21h7': {'max_id': 127},
        'tagCircle49h12': {'max_id': 2114074},
        'tagCustom48h12': {'max_id': 58535},
    }
    
    def __init__(self, family: str, pattern_size_mm: float, border_mm: float = 2,
                 quiet_zone_mm: float = 5, dpi: int = 300):
        """Initialize AprilTag generator.
        
        Args:
            family: AprilTag family name (e.g., 'tag36h11')
            pattern_size_mm: Size of the pattern in millimeters (excluding border and quiet zone)
            border_mm: Border width in mm (default: 2)
            quiet_zone_mm: Quiet zone around marker in mm (default: 5)
            dpi: Resolution for image generation
        """
        if TagGenerator2 is None:
            click.echo("Error: moms_apriltag library not installed. Install with: pip install moms-apriltag", err=True)
            sys.exit(1)
        
        if family not in self.FAMILIES:
            click.echo(f"Error: Unknown AprilTag family: {family}", err=True)
            click.echo(f"Supported families: {', '.join(self.FAMILIES.keys())}", err=True)
            sys.exit(1)
        
        self.family = family
        self.max_id = self.FAMILIES[family]['max_id']
        self.pattern_size_mm = pattern_size_mm
        self.border_mm = border_mm
        self.quiet_zone_mm = quiet_zone_mm
        self.dpi = dpi
        
        # Calculate sizes in pixels
        self.pattern_size_pixels = int((pattern_size_mm / 25.4) * dpi)
        self.border_pixels = int((border_mm / 25.4) * dpi)
        self.quiet_zone_pixels = int((quiet_zone_mm / 25.4) * dpi)
        
        # Total footprint
        self.footprint_size_pixels = (self.pattern_size_pixels + 
                                       (2 * self.border_pixels) + 
                                       (2 * self.quiet_zone_pixels))
        
        # Initialize AprilTag generator for this family
        try:
            self.tag_generator = TagGenerator2(family)
        except Exception as e:
            click.echo(f"Error: Failed to initialize AprilTag generator for {family}: {e}", err=True)
            sys.exit(1)

        # Determine an appropriate scale factor so the generated tag is close to the desired size
        base_tag = self.tag_generator.generate(0)  # small base image
        base_size = base_tag.shape[0]
        self.scale = max(1, math.ceil(self.pattern_size_pixels / base_size))
    
    def validate_id(self, numeric_id: int) -> tuple[bool, Optional[str]]:
        """Validate that numeric ID is within family range.
        
        Args:
            numeric_id: Numeric ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if numeric_id < 0:
            return False, f"AprilTag ID must be non-negative, got {numeric_id}"
        if numeric_id >= self.max_id:
            return False, f"AprilTag ID {numeric_id} exceeds maximum {self.max_id - 1} for {self.family}"
        return True, None
    
    def generate(self, numeric_id: int) -> Optional[Image.Image]:
        """Generate AprilTag image from numeric ID.
        
        Args:
            numeric_id: Numeric ID for the tag
            
        Returns:
            PIL Image of AprilTag, or None if generation fails
        """
        # Validate ID
        is_valid, error_msg = self.validate_id(numeric_id)
        if not is_valid:
            click.echo(f"Warning: {error_msg}", err=True)
            return None
        
        try:
            # Generate tag using moms_apriltag library at scaled resolution, then resize
            tag_array = self.tag_generator.generate(numeric_id, scale=self.scale)
            
            # Convert numpy array to PIL Image
            # moms_apriltag returns 0-255 grayscale array
            pattern_pil = Image.fromarray(tag_array, mode='L')
            
            # Resize pattern to desired size
            pattern_pil = pattern_pil.resize((self.pattern_size_pixels, self.pattern_size_pixels), 
                                           Image.Resampling.LANCZOS)
            
            # Create full image with border and quiet zone
            full_size = self.footprint_size_pixels
            full_img = Image.new('L', (full_size, full_size), 255)  # White background
            
            # Draw border
            if self.border_pixels > 0:
                border_start = self.quiet_zone_pixels
                border_end = border_start + self.pattern_size_pixels + (2 * self.border_pixels)
                draw = ImageDraw.Draw(full_img)
                draw.rectangle([border_start, border_start, border_end - 1, border_end - 1], 
                             fill=0)  # Black border
            
            # Place pattern in center (inside border)
            pattern_x = self.quiet_zone_pixels + self.border_pixels
            pattern_y = self.quiet_zone_pixels + self.border_pixels
            full_img.paste(pattern_pil, (pattern_x, pattern_y))
            
            return full_img
            
        except Exception as e:
            click.echo(f"Error: Failed to generate AprilTag for ID {numeric_id}: {e}", err=True)
            return None
    
    def get_footprint_size_mm(self) -> float:
        """Get total marker footprint size including border and quiet zone."""
        return self.pattern_size_mm + (2 * self.border_mm) + (2 * self.quiet_zone_mm)

