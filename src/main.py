"""Main CLI entry point."""
import click
import sys
from pathlib import Path

from .config import Config
from .data_loader import DataLoader
from .qr_generator import QRGenerator
from .barcode_generator import BarcodeGenerator
from .layout_engine import LayoutEngine
from .pdf_exporter import PDFExporter


@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to YAML configuration file')
@click.option('--csv', type=click.Path(exists=True), help='Input CSV file path')
@click.option('--output', '-o', type=str, help='Output PDF file path')
@click.option('--overwrite', is_flag=True, help='Overwrite existing output file')
@click.option('--margin-mm', type=float, help='Page margin in millimeters')
@click.option('--dpi', type=int, help='Output resolution (72-600)')
@click.option('--label-width-mm', type=float, help='Label width in millimeters')
@click.option('--label-height-mm', type=float, help='Label height in millimeters')
@click.option('--labels-per-row', type=int, help='Number of labels per row')
@click.option('--labels-per-column', type=int, help='Number of labels per column')
@click.option('--horizontal-gap-mm', type=float, help='Horizontal gap between labels in mm')
@click.option('--vertical-gap-mm', type=float, help='Vertical gap between labels in mm')
@click.option('--code-arrangement', type=click.Choice(['horizontal', 'vertical']), help='Code arrangement')
@click.option('--code-spacing-mm', type=float, help='Spacing between QR and barcode in mm')
@click.option('--qr-size-mm', type=float, help='QR code size in millimeters')
@click.option('--qr-error-correction', type=click.Choice(['L', 'M', 'Q', 'H']), help='QR error correction level')
@click.option('--qr-quiet-zone', type=int, help='QR quiet zone in module units')
@click.option('--barcode-symbology', type=click.Choice(['code128', 'code39', 'ean13', 'i2of5', 'itf']), help='Barcode symbology')
@click.option('--barcode-height-mm', type=float, help='Barcode height in millimeters')
@click.option('--barcode-width-factor', type=float, help='Barcode width factor')
@click.option('--barcode-quiet-zone', type=float, help='Barcode quiet zone in mm')
@click.option('--text-font-size', type=int, help='Text font size in points')
@click.option('--text-font-name', type=str, help='Text font family name')
@click.option('--text-position', type=click.Choice(['top', 'bottom', 'none']), help='Text position')
@click.option('--text-alignment', type=click.Choice(['left', 'center', 'right']), help='Text alignment')
@click.option('--text-margin-mm', type=float, help='Text margin from codes in mm')
@click.option('--aruco-enabled', is_flag=True, help='Enable ArUco marker generation')
@click.option('--aruco-dict', type=str, help='ArUco dictionary (e.g., DICT_5X5_100)')
@click.option('--aruco-pattern-size-mm', type=float, help='ArUco pattern size in mm')
@click.option('--aruco-border-bits', type=int, help='ArUco border bits')
@click.option('--aruco-quiet-zone-mm', type=float, help='ArUco quiet zone in mm')
@click.option('--apriltag-enabled', is_flag=True, help='Enable AprilTag generation')
@click.option('--apriltag-family', type=str, help='AprilTag family (e.g., tag36h11)')
@click.option('--apriltag-pattern-size-mm', type=float, help='AprilTag pattern size in mm')
@click.option('--apriltag-border-mm', type=float, help='AprilTag border in mm')
@click.option('--apriltag-quiet-zone-mm', type=float, help='AprilTag quiet zone in mm')
@click.option('--auto-assign-numeric-ids', is_flag=True, default=None, help='Auto-assign numeric IDs from row index')
@click.option('--start-index', type=int, help='Starting index for auto-assigned numeric IDs')
@click.option('--debug', is_flag=True, help='Save debug images to debug/ folder')
@click.option('--dry-run', is_flag=True, help='Validate configuration without generating PDF')
def main(**kwargs):
    """Generate print-ready A4 PDFs with QR codes and barcodes."""
    
    # Build CLI overrides dictionary
    cli_overrides = {}
    
    if kwargs.get('csv'):
        cli_overrides.setdefault('input', {})['csv'] = kwargs['csv']
    
    if kwargs.get('output'):
        cli_overrides.setdefault('output', {})['file'] = kwargs['output']
    
    # Only override overwrite when flag explicitly provided (avoid forcing False by default)
    if kwargs.get('overwrite'):
        cli_overrides.setdefault('output', {})['overwrite'] = True
    
    if kwargs.get('margin_mm') is not None:
        cli_overrides.setdefault('output', {})['margin_mm'] = kwargs['margin_mm']
    
    if kwargs.get('dpi') is not None:
        cli_overrides.setdefault('output', {})['dpi'] = kwargs['dpi']
    
    if kwargs.get('label_width_mm') is not None:
        cli_overrides.setdefault('layout', {})['label_width_mm'] = kwargs['label_width_mm']
    
    if kwargs.get('label_height_mm') is not None:
        cli_overrides.setdefault('layout', {})['label_height_mm'] = kwargs['label_height_mm']
    
    if kwargs.get('labels_per_row') is not None:
        cli_overrides.setdefault('layout', {})['labels_per_row'] = kwargs['labels_per_row']
    
    if kwargs.get('labels_per_column') is not None:
        cli_overrides.setdefault('layout', {})['labels_per_column'] = kwargs['labels_per_column']
    
    if kwargs.get('horizontal_gap_mm') is not None:
        cli_overrides.setdefault('layout', {})['horizontal_gap_mm'] = kwargs['horizontal_gap_mm']
    
    if kwargs.get('vertical_gap_mm') is not None:
        cli_overrides.setdefault('layout', {})['vertical_gap_mm'] = kwargs['vertical_gap_mm']
    
    if kwargs.get('code_arrangement'):
        cli_overrides.setdefault('layout', {})['code_arrangement'] = kwargs['code_arrangement']
    
    if kwargs.get('code_spacing_mm') is not None:
        cli_overrides.setdefault('layout', {})['code_spacing_mm'] = kwargs['code_spacing_mm']
    
    if kwargs.get('qr_size_mm') is not None:
        cli_overrides.setdefault('qr', {})['size_mm'] = kwargs['qr_size_mm']
    
    if kwargs.get('qr_error_correction'):
        cli_overrides.setdefault('qr', {})['error_correction'] = kwargs['qr_error_correction']
    
    if kwargs.get('qr_quiet_zone') is not None:
        cli_overrides.setdefault('qr', {})['quiet_zone'] = kwargs['qr_quiet_zone']
    
    if kwargs.get('barcode_symbology'):
        cli_overrides.setdefault('barcode', {})['symbology'] = kwargs['barcode_symbology']
    
    if kwargs.get('barcode_height_mm') is not None:
        cli_overrides.setdefault('barcode', {})['height_mm'] = kwargs['barcode_height_mm']
    
    if kwargs.get('barcode_width_factor') is not None:
        cli_overrides.setdefault('barcode', {})['width_factor'] = kwargs['barcode_width_factor']
    
    if kwargs.get('barcode_quiet_zone') is not None:
        cli_overrides.setdefault('barcode', {})['quiet_zone'] = kwargs['barcode_quiet_zone']
    
    if kwargs.get('text_font_size') is not None:
        cli_overrides.setdefault('text', {})['font_size'] = kwargs['text_font_size']
    
    if kwargs.get('text_font_name'):
        cli_overrides.setdefault('text', {})['font_name'] = kwargs['text_font_name']
    
    if kwargs.get('text_position'):
        cli_overrides.setdefault('text', {})['position'] = kwargs['text_position']
    
    if kwargs.get('text_alignment'):
        cli_overrides.setdefault('text', {})['alignment'] = kwargs['text_alignment']
    
    if kwargs.get('text_margin_mm') is not None:
        cli_overrides.setdefault('text', {})['margin_mm'] = kwargs['text_margin_mm']
    
    # Marker mode CLI overrides
    # Only enable marker modes when flags are explicitly passed; don't override config defaults
    if kwargs.get('aruco_enabled'):
        cli_overrides.setdefault('aruco', {})['enabled'] = True
    if kwargs.get('aruco_dict'):
        cli_overrides.setdefault('aruco', {})['dictionary'] = kwargs['aruco_dict']
    if kwargs.get('aruco_pattern_size_mm') is not None:
        cli_overrides.setdefault('aruco', {})['pattern_size_mm'] = kwargs['aruco_pattern_size_mm']
    if kwargs.get('aruco_border_bits') is not None:
        cli_overrides.setdefault('aruco', {})['border_bits'] = kwargs['aruco_border_bits']
    if kwargs.get('aruco_quiet_zone_mm') is not None:
        cli_overrides.setdefault('aruco', {})['quiet_zone_mm'] = kwargs['aruco_quiet_zone_mm']
    
    if kwargs.get('apriltag_enabled'):
        cli_overrides.setdefault('apriltag', {})['enabled'] = True
    if kwargs.get('apriltag_family'):
        cli_overrides.setdefault('apriltag', {})['family'] = kwargs['apriltag_family']
    if kwargs.get('apriltag_pattern_size_mm') is not None:
        cli_overrides.setdefault('apriltag', {})['pattern_size_mm'] = kwargs['apriltag_pattern_size_mm']
    if kwargs.get('apriltag_border_mm') is not None:
        cli_overrides.setdefault('apriltag', {})['border_mm'] = kwargs['apriltag_border_mm']
    if kwargs.get('apriltag_quiet_zone_mm') is not None:
        cli_overrides.setdefault('apriltag', {})['quiet_zone_mm'] = kwargs['apriltag_quiet_zone_mm']
    
    if kwargs.get('auto_assign_numeric_ids') is not None:
        cli_overrides.setdefault('id_assignment', {})['auto_assign_numeric_ids'] = kwargs['auto_assign_numeric_ids']
    if kwargs.get('start_index') is not None:
        cli_overrides.setdefault('id_assignment', {})['start_index'] = kwargs['start_index']
    
    # Load configuration
    try:
        config = Config(config_path=kwargs.get('config'), cli_overrides=cli_overrides)
    except SystemExit:
        sys.exit(1)
    
    # Determine mode
    aruco_enabled = config.get('aruco', 'enabled')
    apriltag_enabled = config.get('apriltag', 'enabled')
    is_marker_mode = aruco_enabled or apriltag_enabled
    
    # Load data
    try:
        data_loader = DataLoader(config.get('input', 'csv'))
        entries = data_loader.load()
    except SystemExit:
        sys.exit(1)
    
    # Handle auto-assignment of numeric IDs if needed
    if is_marker_mode:
        id_assignment = config.get('id_assignment')
        auto_assign = id_assignment.get('auto_assign_numeric_ids', True)
        start_index = id_assignment.get('start_index', 0)
        
        for index, entry in enumerate(entries):
            if aruco_enabled and entry.aruco_id is None and auto_assign:
                entry.aruco_id = start_index + index
            elif apriltag_enabled and entry.apriltag_id is None and auto_assign:
                entry.apriltag_id = start_index + index
    
    # Initialize generators based on mode
    qr_gen = None
    barcode_gen = None
    aruco_gen = None
    apriltag_gen = None
    
    if is_marker_mode:
        if aruco_enabled:
            from .markers.aruco_generator import ArUcoGenerator
            aruco_gen = ArUcoGenerator(
                dictionary=config.get('aruco', 'dictionary'),
                pattern_size_mm=config.get('aruco', 'pattern_size_mm'),
                border_bits=config.get('aruco', 'border_bits'),
                quiet_zone_mm=config.get('aruco', 'quiet_zone_mm'),
                dpi=config.get('output', 'dpi')
            )
        elif apriltag_enabled:
            from .markers.apriltag_generator import AprilTagGenerator
            apriltag_gen = AprilTagGenerator(
                family=config.get('apriltag', 'family'),
                pattern_size_mm=config.get('apriltag', 'pattern_size_mm'),
                border_mm=config.get('apriltag', 'border_mm'),
                quiet_zone_mm=config.get('apriltag', 'quiet_zone_mm'),
                dpi=config.get('output', 'dpi')
            )
    else:
        # QR/Barcode mode
        qr_gen = QRGenerator(
            size_mm=config.get('qr', 'size_mm'),
            error_correction=config.get('qr', 'error_correction'),
            quiet_zone=config.get('qr', 'quiet_zone'),
            dpi=config.get('output', 'dpi')
        )
        
        barcode_gen = BarcodeGenerator(
            symbology=config.get('barcode', 'symbology'),
            height_mm=config.get('barcode', 'height_mm'),
            width_factor=config.get('barcode', 'width_factor'),
            quiet_zone_mm=config.get('barcode', 'quiet_zone'),
            dpi=config.get('output', 'dpi')
        )
    
    # Initialize layout engine
    layout_engine = LayoutEngine(config.config)
    
    # Initialize PDF exporter
    debug_mode = kwargs.get('debug', False)
    pdf_exporter = PDFExporter(
        config, layout_engine,
        qr_gen=qr_gen,
        barcode_gen=barcode_gen,
        aruco_gen=aruco_gen,
        apriltag_gen=apriltag_gen,
        debug=debug_mode
    )
    
    # Dry-run mode
    if kwargs.get('dry_run', False):
        click.echo("Dry-run: Configuration validated successfully")
        click.echo(f"Mode: {'ArUco' if aruco_enabled else 'AprilTag' if apriltag_enabled else 'QR/Barcode'}")
        click.echo(f"Entries to process: {len(entries)}")
        sys.exit(0)
    
    # Generate PDF
    try:
        successful, skipped = pdf_exporter.export(entries)
        
        # Print summary
        click.echo(f"Generated {successful} labels, skipped {skipped} invalid entries")
        click.echo(f"Output saved to: {config.get('output', 'file')}")
        
        if skipped > 0:
            sys.exit(0)  # Success but with warnings
        else:
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"Error: Failed to generate PDF: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

