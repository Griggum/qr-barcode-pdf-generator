"""Layout calculation engine for label positioning."""
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LabelPosition:
    """Position information for a label."""
    row: int
    column: int
    x_mm: float
    y_mm: float


@dataclass
class ContentPosition:
    """Position information for content within a label."""
    qr_x_mm: float
    qr_y_mm: float
    barcode_x_mm: float
    barcode_y_mm: float
    barcode_width_mm: float
    qr_text_x_mm: float
    qr_text_y_mm: float
    barcode_text_x_mm: float
    barcode_text_y_mm: float


class LayoutEngine:
    """Calculates label and content positions."""
    
    # A4 dimensions in mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize layout engine with configuration."""
        self.config = config
        self.output_config = config['output']
        self.layout_config = config['layout']
        self.qr_config = config['qr']
        self.barcode_config = config['barcode']
        self.text_config = config['text']
        
        # Calculate usable page area
        margin_mm = self.output_config['margin_mm']
        self.usable_width_mm = self.A4_WIDTH_MM - (2 * margin_mm)
        self.usable_height_mm = self.A4_HEIGHT_MM - (2 * margin_mm)
        
        # Get label dimensions
        self.label_width_mm = self.layout_config['label_width_mm']
        self.label_height_mm = self.layout_config['label_height_mm']
        self.horizontal_gap_mm = self.layout_config['horizontal_gap_mm']
        self.vertical_gap_mm = self.layout_config['vertical_gap_mm']
        
        # Get grid layout
        self.labels_per_row = self.layout_config['labels_per_row']
        self.labels_per_column = self.layout_config['labels_per_column']
        
        # Calculate labels per page
        self.labels_per_page = self.labels_per_row * self.labels_per_column
    
    def get_label_position(self, index: int) -> LabelPosition:
        """Get position for label at given index.
        
        Args:
            index: Zero-based index of the label
            
        Returns:
            LabelPosition with row, column, and coordinates
        """
        # Calculate which page this label is on
        page_index = index // self.labels_per_page
        label_index_on_page = index % self.labels_per_page
        
        # Calculate row and column on current page
        row = label_index_on_page // self.labels_per_row
        column = label_index_on_page % self.labels_per_row
        
        # Calculate position
        margin_mm = self.output_config['margin_mm']
        x_mm = margin_mm + (column * (self.label_width_mm + self.horizontal_gap_mm))
        y_mm = margin_mm + (row * (self.label_height_mm + self.vertical_gap_mm))
        
        return LabelPosition(row=row, column=column, x_mm=x_mm, y_mm=y_mm)
    
    def get_page_number(self, index: int) -> int:
        """Get page number for label at given index."""
        return index // self.labels_per_page
    
    def get_content_position(self, label_pos: LabelPosition, barcode_width_mm: float) -> ContentPosition:
        """Calculate positions for QR, barcode, and text within a label.
        
        Args:
            label_pos: Position of the label
            barcode_width_mm: Actual width of the barcode in mm
            
        Returns:
            ContentPosition with all coordinates
        """
        qr_size_mm = self.qr_config['size_mm']
        barcode_height_mm = self.barcode_config['height_mm']
        code_spacing_mm = self.layout_config['code_spacing_mm']
        arrangement = self.layout_config['code_arrangement']
        text_pos = self.text_config['position']
        text_align = self.text_config['alignment']
        text_margin_mm = self.text_config['margin_mm']
        font_size_pt = self.text_config['font_size']
        
        # Convert font size from points to mm (1 point = 0.352778 mm)
        font_size_mm = font_size_pt * 0.352778
        
        if arrangement == 'horizontal':
            # QR and barcode side by side
            total_width = qr_size_mm + code_spacing_mm + barcode_width_mm
            start_x = label_pos.x_mm + (self.label_width_mm - total_width) / 2
            
            # QR position
            qr_x_mm = start_x
            if text_pos == 'bottom':
                qr_y_mm = label_pos.y_mm + (self.label_height_mm - qr_size_mm - font_size_mm - text_margin_mm) / 2
            else:  # top or none
                qr_y_mm = label_pos.y_mm + (self.label_height_mm - qr_size_mm) / 2
            
            # Barcode position
            barcode_x_mm = qr_x_mm + qr_size_mm + code_spacing_mm
            barcode_y_mm = label_pos.y_mm + (self.label_height_mm - barcode_height_mm) / 2
            
            # Text positions (below each code, aligned with the code)
            if text_pos == 'bottom':
                text_y_mm = label_pos.y_mm + self.label_height_mm - font_size_mm - text_margin_mm
                # QR text - centered under QR code
                qr_text_x_mm = qr_x_mm + qr_size_mm / 2
                # Barcode text - centered under barcode
                barcode_text_x_mm = barcode_x_mm + barcode_width_mm / 2
            elif text_pos == 'top':
                text_y_mm = label_pos.y_mm + text_margin_mm
                # QR text - centered above QR code
                qr_text_x_mm = qr_x_mm + qr_size_mm / 2
                # Barcode text - centered above barcode
                barcode_text_x_mm = barcode_x_mm + barcode_width_mm / 2
            else:  # none
                qr_text_x_mm = 0
                qr_text_y_mm = 0
                barcode_text_x_mm = 0
                barcode_text_y_mm = 0
                text_y_mm = 0
        
        else:  # vertical
            # QR on top, barcode below
            qr_x_mm = label_pos.x_mm + (self.label_width_mm - qr_size_mm) / 2
            
            if text_pos == 'top':
                # Text at top, then QR code
                qr_y_mm = label_pos.y_mm + font_size_mm + text_margin_mm + text_margin_mm
                qr_text_y_mm = label_pos.y_mm + text_margin_mm
            elif text_pos == 'bottom':
                # Calculate positions: QR, then text, then barcode, then text
                # Start from top, leaving space for barcode and its text at bottom
                space_needed_bottom = barcode_height_mm + font_size_mm + text_margin_mm
                available_for_qr = self.label_height_mm - space_needed_bottom - code_spacing_mm
                qr_y_mm = label_pos.y_mm + (available_for_qr - qr_size_mm) / 2
                qr_text_y_mm = qr_y_mm + qr_size_mm + text_margin_mm
            else:  # none
                # Center QR and barcode without text
                available_height = self.label_height_mm - code_spacing_mm
                qr_y_mm = label_pos.y_mm + (available_height - qr_size_mm - barcode_height_mm) / 2
                qr_text_y_mm = 0
            
            # Barcode position
            barcode_x_mm = label_pos.x_mm + (self.label_width_mm - barcode_width_mm) / 2
            
            if text_pos == 'bottom':
                # Barcode above its text
                barcode_y_mm = label_pos.y_mm + self.label_height_mm - barcode_height_mm - font_size_mm - text_margin_mm
                barcode_text_y_mm = label_pos.y_mm + self.label_height_mm - font_size_mm - text_margin_mm
            elif text_pos == 'top':
                # Barcode below QR text
                barcode_y_mm = qr_y_mm + qr_size_mm + code_spacing_mm
                barcode_text_y_mm = barcode_y_mm + barcode_height_mm + text_margin_mm
            else:  # none
                barcode_y_mm = qr_y_mm + qr_size_mm + code_spacing_mm
                barcode_text_y_mm = 0
            
            # Text X positions (centered under each code)
            qr_text_x_mm = qr_x_mm + qr_size_mm / 2
            barcode_text_x_mm = barcode_x_mm + barcode_width_mm / 2
        
        return ContentPosition(
            qr_x_mm=qr_x_mm,
            qr_y_mm=qr_y_mm,
            barcode_x_mm=barcode_x_mm,
            barcode_y_mm=barcode_y_mm,
            barcode_width_mm=barcode_width_mm,
            qr_text_x_mm=qr_text_x_mm if text_pos != 'none' else 0,
            qr_text_y_mm=text_y_mm if text_pos != 'none' else 0,
            barcode_text_x_mm=barcode_text_x_mm if text_pos != 'none' else 0,
            barcode_text_y_mm=text_y_mm if text_pos != 'none' else 0
        )

