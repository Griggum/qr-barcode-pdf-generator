"""Base marker generator interface."""
from abc import ABC, abstractmethod
from PIL import Image
from typing import Optional


class MarkerGenerator(ABC):
    """Base interface for marker generators."""
    
    @abstractmethod
    def generate(self, numeric_id: int, dpi: int) -> Optional[Image.Image]:
        """Generate marker image from numeric ID.
        
        Args:
            numeric_id: Numeric ID for the marker
            dpi: Resolution for image generation
            
        Returns:
            PIL Image of marker, or None if generation fails
        """
        pass
    
    @abstractmethod
    def validate_id(self, numeric_id: int) -> tuple[bool, Optional[str]]:
        """Validate that numeric ID is within valid range.
        
        Args:
            numeric_id: Numeric ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

