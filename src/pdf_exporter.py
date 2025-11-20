"""PDF export module using reportlab."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from typing import Optional, List
from io import BytesIO
import sys

from .data_loader import DataEntry
from .qr_generator import QRGenerator
from .barcode_generator import BarcodeGenerator
from .layout_engine import LayoutEngine, LabelPosition, ContentPosition, MarkerPosition
from .config import Config
from typing import Optional


class PDFExporter:
    """Exports labels to PDF using reportlab."""
    
    def __init__(self, config: Config, layout_engine: LayoutEngine, 
                 qr_gen: Optional[QRGenerator] = None, 
                 barcode_gen: Optional[BarcodeGenerator] = None,
                 aruco_gen: Optional[object] = None,
                 apriltag_gen: Optional[object] = None,
                 debug: bool = False):
        """Initialize PDF exporter.
        
        Args:
            config: Configuration object
            layout_engine: Layout calculation engine
            qr_gen: QR code generator (for QR/Barcode mode)
            barcode_gen: Barcode generator (for QR/Barcode mode)
            aruco_gen: ArUco generator (for ArUco mode)
            apriltag_gen: AprilTag generator (for AprilTag mode)
            debug: If True, save debug images to debug/ folder
        """
        self.config = config
        self.qr_gen = qr_gen
        self.barcode_gen = barcode_gen
        self.aruco_gen = aruco_gen
        self.apriltag_gen = apriltag_gen
        self.layout_engine = layout_engine
        self.output_path = config.get('output', 'file')
        self.dpi = config.get('output', 'dpi')
        self.debug = debug
        
        # Determine mode
        self.is_marker_mode = (aruco_gen is not None) or (apriltag_gen is not None)
        
        # ReportLab uses mm directly, but we need to account for DPI scaling in images
        # 1 mm = 2.83465 points (72 points/inch / 25.4 mm/inch)
        self.mm_to_points = 72.0 / 25.4
        
        self.canvas = None
        self.current_page = -1
        
        # Setup debug folder if needed
        if self.debug:
            from pathlib import Path
            self.debug_dir = Path('debug')
            self.debug_dir.mkdir(exist_ok=True)
    
    def _mm_to_points(self, mm_value: float) -> float:
        """Convert millimeters to points for reportlab."""
        return mm_value * self.mm_to_points
    
    def _start_new_page(self):
        """Start a new PDF page."""
        if self.canvas is None:
            self.canvas = canvas.Canvas(self.output_path, pagesize=A4)
        
        self.current_page += 1
        if self.current_page > 0:
            self.canvas.showPage()
    
    def _image_to_bytes(self, img: Image.Image) -> BytesIO:
        """Convert PIL Image to BytesIO for reportlab."""
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    def _draw_image(self, img: Image.Image, x_mm: float, y_mm: float, width_mm: Optional[float] = None, 
                   height_mm: Optional[float] = None):
        """Draw image on canvas at specified position.
        
        Args:
            img: PIL Image to draw
            x_mm: X position in mm (from left, top)
            y_mm: Y position in mm (from top)
            width_mm: Desired width in mm (None to use image width)
            height_mm: Desired height in mm (None to use image height)
        """
        # Use reportlab's mm unit directly
        x_pt = x_mm * mm
        
        # Get image dimensions
        img_width, img_height = img.size
        
        # Calculate dimensions in mm
        if width_mm and height_mm:
            width_pt = width_mm * mm
            height_pt = height_mm * mm
            height_mm_used = height_mm
        else:
            # Use image dimensions scaled from pixels to mm
            width_mm_calc = (img_width / self.dpi) * 25.4
            height_mm_calc = (img_height / self.dpi) * 25.4
            width_pt = width_mm_calc * mm
            height_pt = height_mm_calc * mm
            height_mm_used = height_mm_calc
        
        # ReportLab uses bottom-left origin, convert from top-left
        # A4 height is 297mm, y_mm is from top, so bottom is at (297 - y_mm)
        # But we need the bottom-left corner of the image
        y_pt = (297 - y_mm - height_mm_used) * mm
        
        # Draw image
        img_bytes = self._image_to_bytes(img)
        self.canvas.drawImage(ImageReader(img_bytes), x_pt, y_pt, width_pt, height_pt)
    
    def _draw_text(self, text: str, x_mm: float, y_mm: float, alignment: Optional[str] = None):
        """Draw text on canvas at specified position.
        
        Args:
            text: Text to draw
            x_mm: X position in mm (from left)
            y_mm: Y position in mm (from top) - this is the baseline of the text
            alignment: Override alignment ('left', 'center', 'right'), or None to use config
        """
        text_config = self.config.get('text')
        font_name = text_config['font_name']
        font_size = text_config['font_size']
        text_align = alignment if alignment is not None else text_config['alignment']
        
        # Use reportlab's mm unit directly
        x_pt = x_mm * mm
        
        # ReportLab uses bottom-left origin, convert from top-left
        # y_mm is the baseline from top, so convert to bottom-left
        y_pt = (297 - y_mm) * mm
        
        self.canvas.setFont(font_name, font_size)
        
        # Handle alignment
        if text_align == 'center':
            self.canvas.drawCentredString(x_pt, y_pt, text)
        elif text_align == 'right':
            text_width = self.canvas.stringWidth(text, font_name, font_size)
            self.canvas.drawRightString(x_pt, y_pt, text)
        else:  # left
            self.canvas.drawString(x_pt, y_pt, text)
    
    def export(self, entries: List[DataEntry]) -> tuple[int, int]:
        """Export entries to PDF.
        
        Args:
            entries: List of data entries to export
            
        Returns:
            Tuple of (successful_count, skipped_count)
        """
        if self.is_marker_mode:
            return self._export_markers(entries)
        else:
            return self._export_qr_barcode(entries)
    
    def _export_qr_barcode(self, entries: List[DataEntry]) -> tuple[int, int]:
        """Export QR codes and barcodes to PDF."""
        successful = 0
        skipped = 0
        
        for index, entry in enumerate(entries):
            # Validate barcode data
            is_valid, error_msg = self.barcode_gen.validate(entry.barcode_value)
            if not is_valid:
                import click
                click.echo(f"Warning: Skipping {entry.id}: {error_msg}", err=True)
                skipped += 1
                continue
            
            # Generate QR code
            qr_img = self.qr_gen.generate(entry.qr_value)
            if qr_img is None:
                import click
                click.echo(f"Warning: Failed to generate QR for ID: {entry.id}", err=True)
                skipped += 1
                continue
            
            # Save debug QR image
            if self.debug:
                qr_debug_path = self.debug_dir / f"qr_{entry.id}_{index}.png"
                qr_img.save(qr_debug_path)
                import click
                click.echo(f"Debug: Saved QR image to {qr_debug_path} (size: {qr_img.size})", err=True)
            
            # Generate barcode
            barcode_img = self.barcode_gen.generate(entry.barcode_value)
            if barcode_img is None:
                import click
                click.echo(f"Warning: Failed to generate barcode for ID: {entry.id}", err=True)
                skipped += 1
                continue
            
            # Save debug barcode image
            if self.debug:
                barcode_debug_path = self.debug_dir / f"barcode_{entry.id}_{index}.png"
                barcode_img.save(barcode_debug_path)
                import click
                click.echo(f"Debug: Saved barcode image to {barcode_debug_path} (size: {barcode_img.size})", err=True)
            
            # Get label position
            label_pos = self.layout_engine.get_label_position(index)
            page_num = self.layout_engine.get_page_number(index)
            
            # Start new page if needed
            if page_num != self.current_page:
                self._start_new_page()
            
            # Calculate barcode width in mm
            barcode_width_pixels = barcode_img.size[0]
            barcode_width_mm = (barcode_width_pixels / self.dpi) * 25.4
            
            # Get content positions
            content_pos = self.layout_engine.get_content_position(label_pos, barcode_width_mm)
            
            # Get text config for debug output
            text_config = self.config.get('text')
            
            # Debug output for positions
            if self.debug:
                import click
                click.echo(f"Debug: Label {index} ({entry.id}) positions:", err=True)
                click.echo(f"  Label: x={label_pos.x_mm:.2f}mm, y={label_pos.y_mm:.2f}mm", err=True)
                click.echo(f"  QR: x={content_pos.qr_x_mm:.2f}mm, y={content_pos.qr_y_mm:.2f}mm, size={self.qr_gen.size_mm}mm", err=True)
                click.echo(f"  Barcode: x={content_pos.barcode_x_mm:.2f}mm, y={content_pos.barcode_y_mm:.2f}mm, w={barcode_width_mm:.2f}mm, h={self.barcode_gen.height_mm}mm", err=True)
                if text_config['position'] != 'none':
                    click.echo(f"  QR Text: x={content_pos.qr_text_x_mm:.2f}mm, y={content_pos.qr_text_y_mm:.2f}mm", err=True)
                    click.echo(f"  Barcode Text: x={content_pos.barcode_text_x_mm:.2f}mm, y={content_pos.barcode_text_y_mm:.2f}mm", err=True)
            
            # Draw QR code
            self._draw_image(qr_img, content_pos.qr_x_mm, content_pos.qr_y_mm, 
                           self.qr_gen.size_mm, self.qr_gen.size_mm)
            
            # Draw barcode
            barcode_height_mm = self.barcode_gen.height_mm
            self._draw_image(barcode_img, content_pos.barcode_x_mm, content_pos.barcode_y_mm,
                           barcode_width_mm, barcode_height_mm)
            
            # Draw text if enabled
            if text_config['position'] != 'none':
                # Draw text for QR code (centered under/over QR)
                self._draw_text(entry.qr_value, content_pos.qr_text_x_mm, content_pos.qr_text_y_mm, alignment='center')
                # Draw text for barcode (centered under/over barcode)
                self._draw_text(entry.barcode_value, content_pos.barcode_text_x_mm, content_pos.barcode_text_y_mm, alignment='center')
            
            successful += 1
        
        # Finalize PDF
        if self.canvas:
            self.canvas.save()
        
        return successful, skipped
    
    def _export_markers(self, entries: List[DataEntry]) -> tuple[int, int]:
        """Export ArUco or AprilTag markers to PDF."""
        successful = 0
        skipped = 0
        
        # Determine which marker generator to use
        marker_gen = self.aruco_gen if self.aruco_gen else self.apriltag_gen
        marker_type = 'aruco' if self.aruco_gen else 'apriltag'
        marker_config = self.config.get('aruco') if self.aruco_gen else self.config.get('apriltag')
        id_assignment = self.config.get('id_assignment')
        auto_assign = id_assignment.get('auto_assign_numeric_ids', True)
        start_index = id_assignment.get('start_index', 0)
        
        for index, entry in enumerate(entries):
            # Determine numeric ID
            if marker_type == 'aruco':
                numeric_id = entry.aruco_id
            else:
                numeric_id = entry.apriltag_id
            
            # Auto-assign if needed
            if numeric_id is None:
                if auto_assign:
                    numeric_id = start_index + index
                else:
                    import click
                    click.echo(f"Warning: Row {index + 1} ({entry.id}) has no {marker_type}_id and auto-assignment is disabled, skipping", err=True)
                    skipped += 1
                    continue
            
            # Validate ID
            is_valid, error_msg = marker_gen.validate_id(numeric_id)
            if not is_valid:
                import click
                click.echo(f"Warning: Skipping {entry.id}: {error_msg}", err=True)
                skipped += 1
                continue
            
            # Generate marker
            marker_img = marker_gen.generate(numeric_id)
            if marker_img is None:
                import click
                click.echo(f"Warning: Failed to generate {marker_type} marker for ID: {entry.id} (numeric ID: {numeric_id})", err=True)
                skipped += 1
                continue
            
            # Save debug image
            if self.debug:
                marker_debug_path = self.debug_dir / f"{marker_type}_{entry.id}_{index}.png"
                marker_img.save(marker_debug_path)
                import click
                click.echo(f"Debug: Saved {marker_type} image to {marker_debug_path} (size: {marker_img.size})", err=True)
            
            # Get label position
            label_pos = self.layout_engine.get_label_position(index)
            page_num = self.layout_engine.get_page_number(index)
            
            # Start new page if needed
            if page_num != self.current_page:
                self._start_new_page()
            
            # Get marker footprint size
            marker_footprint_mm = marker_gen.get_footprint_size_mm()
            
            # Get marker position
            marker_pos = self.layout_engine.get_marker_position(label_pos, marker_footprint_mm)
            
            # Debug output
            if self.debug:
                import click
                click.echo(f"Debug: Label {index} ({entry.id}) positions:", err=True)
                click.echo(f"  Label: x={label_pos.x_mm:.2f}mm, y={label_pos.y_mm:.2f}mm", err=True)
                click.echo(f"  Marker: x={marker_pos.marker_x_mm:.2f}mm, y={marker_pos.marker_y_mm:.2f}mm, size={marker_footprint_mm:.2f}mm", err=True)
                if self.config.get('text').get('position') != 'none':
                    click.echo(f"  Text: x={marker_pos.text_x_mm:.2f}mm, y={marker_pos.text_y_mm:.2f}mm", err=True)
            
            # Draw marker
            self._draw_image(marker_img, marker_pos.marker_x_mm, marker_pos.marker_y_mm,
                           marker_footprint_mm, marker_footprint_mm)
            
            # Draw text if enabled
            text_config = self.config.get('text')
            if text_config.get('position') != 'none':
                self._draw_text(entry.id, marker_pos.text_x_mm, marker_pos.text_y_mm,
                              alignment=text_config.get('alignment', 'center'))
            
            successful += 1
        
        # Finalize PDF
        if self.canvas:
            self.canvas.save()
        
        return successful, skipped

