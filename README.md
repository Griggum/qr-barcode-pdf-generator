# QR & Barcode Document Generator

A CLI-based tool for generating print-ready A4 PDFs containing both QR codes and barcodes for a list of provided IDs.

## Features

- Generate QR codes and barcodes for multiple IDs
- Support for multiple barcode symbologies (Code 128, Code 39, EAN-13, Interleaved 2 of 5)
- Flexible layout configuration via YAML or CLI
- Print-ready output at configurable DPI (default: 300)
- Human-readable text labels
- Automatic page management for large datasets

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for package management. The virtual environment is automatically created at `./.venv`.

Dependencies are already installed. To reinstall:

```bash
uv sync
```

## Usage

### Basic Usage

Generate PDF using default configuration:

```bash
uv run python -m src.main --config config.yaml
```

### Using CLI Options

Override configuration via command line:

```bash
uv run python -m src.main --csv ids.csv --output result.pdf --barcode-symbology code39 --qr-size-mm 30
```

### Configuration File

Create a `config.yaml` file (see `config.yaml` for an example):

```yaml
input:
  csv: ids.csv

output:
  file: output.pdf
  margin_mm: 10
  dpi: 300
  overwrite: true

layout:
  label_width_mm: 60
  label_height_mm: 40
  horizontal_gap_mm: 5
  vertical_gap_mm: 5
  code_arrangement: horizontal
  code_spacing_mm: 5

qr:
  size_mm: 25
  error_correction: M
  quiet_zone: 4

barcode:
  symbology: code128
  height_mm: 15
  width_factor: 2
  quiet_zone: 10

text:
  font_size: 10
  font_name: Helvetica
  position: bottom
  alignment: center
  margin_mm: 2
```

### CSV Input Format

The CSV file must have a header row and at least an `id` column:

**Minimum format:**
```csv
id
ITEM-001
ITEM-002
```

**Extended format (optional qr_value and barcode_value):**
```csv
id,qr_value,barcode_value
ITEM-001,ITEM-001,123456789012
ITEM-002,ITEM-002,123456789013
```

If `qr_value` or `barcode_value` are missing, they default to the `id` value.

## Supported Barcode Symbologies

- **Code 128** (default) - Full ASCII support, best general-purpose choice
- **Code 39** - A-Z, 0-9, and symbols: - . $ / + % SPACE (lowercase auto-converted)
- **EAN-13** - Numeric only, exactly 12 or 13 digits
- **Interleaved 2 of 5 (i2of5/itf)** - Numeric only, even number of digits

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration loading and validation
│   ├── data_loader.py       # CSV parsing
│   ├── qr_generator.py      # QR code generation
│   ├── barcode_generator.py # Barcode generation
│   ├── layout_engine.py     # Layout calculations
│   └── pdf_exporter.py      # PDF generation
├── config.yaml              # Example configuration
├── ids.csv                  # Example input data
├── pyproject.toml           # Project configuration
└── README.md
```

## Requirements

- Python 3.10+
- UV package manager
- All dependencies are managed via `pyproject.toml`

## License

This project is provided as-is for generating print-ready label sheets.

