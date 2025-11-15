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
@click.option('--debug', is_flag=True, help='Save debug images to debug/ folder')
def main(**kwargs):
    """Generate print-ready A4 PDFs with QR codes and barcodes."""
    
    # Build CLI overrides dictionary
    cli_overrides = {}
    
    if kwargs.get('csv'):
        cli_overrides.setdefault('input', {})['csv'] = kwargs['csv']
    
    if kwargs.get('output'):
        cli_overrides.setdefault('output', {})['file'] = kwargs['output']
    
    if kwargs.get('overwrite') is not None:
        cli_overrides.setdefault('output', {})['overwrite'] = kwargs['overwrite']
    
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
    
    # Load configuration
    try:
        config = Config(config_path=kwargs.get('config'), cli_overrides=cli_overrides)
    except SystemExit:
        sys.exit(1)
    
    # Load data
    try:
        data_loader = DataLoader(config.get('input', 'csv'))
        entries = data_loader.load()
    except SystemExit:
        sys.exit(1)
    
    # Initialize generators
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
    pdf_exporter = PDFExporter(config, qr_gen, barcode_gen, layout_engine, debug=debug_mode)
    
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

