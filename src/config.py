"""Configuration loading and validation module."""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import click


class Config:
    """Configuration manager with YAML and CLI support."""
    
    # A4 dimensions in mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    def __init__(self, config_path: Optional[str] = None, cli_overrides: Optional[Dict[str, Any]] = None):
        """Initialize configuration from YAML and CLI overrides."""
        self.config = self._load_defaults()
        
        if config_path:
            yaml_config = self._load_yaml(config_path)
            self.config = self._merge_config(self.config, yaml_config)
        
        if cli_overrides:
            self.config = self._merge_config(self.config, cli_overrides)
        
        self._validate()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            'input': {
                'csv': 'ids.csv'
            },
            'output': {
                'file': 'output.pdf',
                'page_size': 'A4',
                'margin_mm': 10,
                'dpi': 300,
                'overwrite': False
            },
            'layout': {
                'label_width_mm': None,
                'label_height_mm': None,
                'labels_per_row': 3,
                'labels_per_column': 7,
                'horizontal_gap_mm': 5,
                'vertical_gap_mm': 5,
                'code_arrangement': 'horizontal',
                'code_spacing_mm': 5
            },
            'qr': {
                'size_mm': 25,
                'error_correction': 'M',
                'quiet_zone': 4
            },
            'barcode': {
                'symbology': 'code128',
                'height_mm': 15,
                'width_factor': 2,
                'quiet_zone': 10
            },
            'text': {
                'font_size': 10,
                'font_name': 'Helvetica',
                'position': 'bottom',
                'alignment': 'center',
                'margin_mm': 2
            }
        }
    
    def _load_yaml(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            click.echo(f"Error: Configuration file not found: {config_path}", err=True)
            sys.exit(1)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            click.echo(f"Error: Invalid YAML in configuration file: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: Failed to read configuration file: {e}", err=True)
            sys.exit(1)
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def _validate(self):
        """Validate configuration values."""
        # Validate DPI
        dpi = self.config['output']['dpi']
        if not (72 <= dpi <= 600):
            click.echo(f"Error: DPI must be between 72 and 600, got {dpi}", err=True)
            sys.exit(1)
        
        # Validate margins
        margin_mm = self.config['output']['margin_mm']
        if margin_mm < 0:
            click.echo(f"Error: Margin must be non-negative, got {margin_mm}", err=True)
            sys.exit(1)
        
        usable_width = self.A4_WIDTH_MM - (2 * margin_mm)
        usable_height = self.A4_HEIGHT_MM - (2 * margin_mm)
        
        if usable_width < 20 or usable_height < 20:
            click.echo(f"Error: Margins too large, must leave at least 20mm usable space", err=True)
            sys.exit(1)
        
        # Validate QR error correction
        qr_ec = self.config['qr']['error_correction'].upper()
        if qr_ec not in ['L', 'M', 'Q', 'H']:
            click.echo(f"Error: QR error correction must be L, M, Q, or H, got {qr_ec}", err=True)
            sys.exit(1)
        self.config['qr']['error_correction'] = qr_ec
        
        # Validate barcode symbology
        symbology = self.config['barcode']['symbology'].lower()
        valid_symbologies = ['code128', 'code39', 'ean13', 'i2of5', 'itf']
        if symbology not in valid_symbologies:
            click.echo(f"Error: Unsupported barcode symbology: {symbology}. Supported: {', '.join(valid_symbologies)}", err=True)
            sys.exit(1)
        # Normalize i2of5 to itf for python-barcode
        if symbology == 'i2of5':
            symbology = 'itf'
        self.config['barcode']['symbology'] = symbology
        
        # Validate font size
        font_size = self.config['text']['font_size']
        if not (6 <= font_size <= 72):
            click.echo(f"Error: Font size must be between 6 and 72 points, got {font_size}", err=True)
            sys.exit(1)
        
        # Validate text position
        text_pos = self.config['text']['position'].lower()
        if text_pos not in ['top', 'bottom', 'none']:
            click.echo(f"Error: Text position must be 'top', 'bottom', or 'none', got {text_pos}", err=True)
            sys.exit(1)
        self.config['text']['position'] = text_pos
        
        # Validate text alignment
        text_align = self.config['text']['alignment'].lower()
        if text_align not in ['left', 'center', 'right']:
            click.echo(f"Error: Text alignment must be 'left', 'center', or 'right', got {text_align}", err=True)
            sys.exit(1)
        self.config['text']['alignment'] = text_align
        
        # Validate code arrangement
        arrangement = self.config['layout']['code_arrangement'].lower()
        if arrangement not in ['horizontal', 'vertical']:
            click.echo(f"Error: Code arrangement must be 'horizontal' or 'vertical', got {arrangement}", err=True)
            sys.exit(1)
        self.config['layout']['code_arrangement'] = arrangement
        
        # Validate label dimensions vs grid
        layout = self.config['layout']
        has_dimensions = layout['label_width_mm'] is not None and layout['label_height_mm'] is not None
        has_grid = layout['labels_per_row'] is not None and layout['labels_per_column'] is not None
        
        if has_dimensions and has_grid:
            click.echo("Warning: Both label dimensions and grid layout specified. Dimensions take precedence.", err=True)
        
        if has_dimensions:
            # Validate dimensions fit on page
            label_w = layout['label_width_mm']
            label_h = layout['label_height_mm']
            gap_h = layout['horizontal_gap_mm']
            gap_v = layout['vertical_gap_mm']
            
            # Calculate how many fit
            labels_per_row = int((usable_width + gap_h) / (label_w + gap_h))
            labels_per_column = int((usable_height + gap_v) / (label_h + gap_v))
            
            if labels_per_row < 1 or labels_per_column < 1:
                click.echo(f"Error: Label dimensions too large for page. At least one label must fit.", err=True)
                sys.exit(1)
            
            # Update calculated values
            layout['labels_per_row'] = labels_per_row
            layout['labels_per_column'] = labels_per_column
        elif has_grid:
            # Calculate dimensions from grid
            labels_per_row = layout['labels_per_row']
            labels_per_column = layout['labels_per_column']
            gap_h = layout['horizontal_gap_mm']
            gap_v = layout['vertical_gap_mm']
            
            label_w = (usable_width - (labels_per_row - 1) * gap_h) / labels_per_row
            label_h = (usable_height - (labels_per_column - 1) * gap_v) / labels_per_column
            
            if label_w <= 0 or label_h <= 0:
                click.echo(f"Error: Grid layout results in invalid label dimensions.", err=True)
                sys.exit(1)
            
            layout['label_width_mm'] = label_w
            layout['label_height_mm'] = label_h
        else:
            click.echo("Error: Must specify either label dimensions or grid layout.", err=True)
            sys.exit(1)
        
        # Validate file paths
        csv_path = self.config['input']['csv']
        if not Path(csv_path).exists():
            click.echo(f"Error: Input CSV file not found: {csv_path}", err=True)
            sys.exit(1)
        
        output_path = Path(self.config['output']['file'])
        output_dir = output_path.parent
        
        # Create output directory if it doesn't exist
        if output_dir and not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                click.echo(f"Error: Cannot create output directory: {e}", err=True)
                sys.exit(1)
        
        # Check if output file exists and overwrite setting
        if output_path.exists() and not self.config['output']['overwrite']:
            click.echo(f"Error: Output file exists: {output_path}. Use --overwrite to replace.", err=True)
            sys.exit(1)
        
        # Ensure .pdf extension
        if output_path.suffix.lower() != '.pdf':
            self.config['output']['file'] = str(output_path.with_suffix('.pdf'))
    
    def get(self, *keys):
        """Get configuration value using dot notation."""
        value = self.config
        for key in keys:
            value = value[key]
        return value
    
    def __getitem__(self, key):
        """Allow dictionary-style access."""
        return self.config[key]

