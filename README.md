# QR & Barcode Document Generator

A command-line tool that generates print-ready A4 PDFs containing QR codes and barcodes from a list of IDs. Perfect for creating label sheets for inventory, testing scanning workflows, or any scenario where you need printable codes.

## What is this?

This tool takes a simple CSV file with item IDs and automatically generates a professional PDF document with:
- **QR codes** for each item
- **Barcodes** (multiple formats supported)
- **Human-readable text labels**
- **Automatic layout** optimized for A4 printing

Each label is perfectly sized and positioned, ready to print and use. Great for warehouse labels, product testing, or any bulk code generation needs.

## Features

✨ **Easy to use** - Just provide a CSV file and run one command  
📄 **Print-ready PDFs** - High-resolution output (300 DPI default) optimized for printing  
🎨 **Flexible layout** - Customize label sizes, spacing, and arrangement  
📊 **Multiple barcode formats** - Code 128, Code 39, EAN-13, and more  
🔄 **Automatic pagination** - Handles large datasets across multiple pages  
⚙️ **Configurable** - YAML config files or command-line options  

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **UV package manager** - This project uses UV for dependency management

### Installing UV

If you don't have UV installed yet, you can install it easily:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or install via pip:
```bash
pip install uv
```

For more installation options, visit the [UV documentation](https://github.com/astral-sh/uv).

## Installation

1. **Clone or download this repository:**
   ```bash
   git clone <repository-url>
   cd GenerateCodesForPrinting
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```
   
   This will automatically create a virtual environment and install all required packages.

That's it! You're ready to go.

## Quick Start

The fastest way to get started:

1. **Prepare your CSV file** with item IDs (see example below)
2. **Run the generator:**
   ```bash
   uv run python -m src.main --csv ids.csv --output my-labels.pdf
   ```

3. **Open the generated PDF** and print!

### Example CSV File

Create a file called `ids.csv` with your items:

```csv
id
ITEM-001
ITEM-002
ITEM-003
```

Or with custom QR/barcode values:

```csv
id,qr_value,barcode_value
ITEM-001,ITEM-001,123456789012
ITEM-002,ITEM-002,123456789013
```

## Usage

### Basic Usage (with config file)

The easiest way is to use a configuration file. The project includes an example `config.yaml`:

```bash
uv run python -m src.main --config config.yaml
```

### Using Command-Line Options

You can override settings directly from the command line:

```bash
uv run python -m src.main \
  --csv ids.csv \
  --output result.pdf \
  --barcode-symbology code39 \
  --qr-size-mm 30 \
  --label-width-mm 70
```

### Configuration File

For more control, create or edit `config.yaml`. Here's what it looks like:

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
  code_arrangement: horizontal  # or "vertical"
  code_spacing_mm: 5

qr:
  size_mm: 25
  error_correction: M  # L, M, Q, or H
  quiet_zone: 4

barcode:
  symbology: code128  # code128, code39, ean13, i2of5
  height_mm: 15
  width_factor: 2
  quiet_zone: 10

text:
  font_size: 10
  font_name: Helvetica
  position: bottom  # "top", "bottom", or "none"
  alignment: center
  margin_mm: 2
```

**Tip:** Command-line options always override the config file, so you can use a base config and tweak specific settings as needed.

## CSV Input Format

Your CSV file needs a header row and at least an `id` column. The file should be saved as UTF-8.

### Minimum Format

Just IDs - QR codes and barcodes will use the same value:

```csv
id
ITEM-001
ITEM-002
ITEM-003
```

### Extended Format

Custom values for QR codes and/or barcodes:

```csv
id,qr_value,barcode_value
ITEM-001,ITEM-001,123456789012
ITEM-002,ITEM-002,123456789013
ITEM-003,,
```

**Notes:**
- If `qr_value` is missing or empty, it defaults to the `id` value
- If `barcode_value` is missing or empty, it defaults to the `id` value
- Empty cells are treated as missing values

## Supported Barcode Symbologies

Choose the barcode format that works best for your needs:

| Format | Description | Best For |
|--------|-------------|----------|
| **Code 128** (default) | Full ASCII support, no length restrictions | General purpose, most flexible |
| **Code 39** | A-Z, 0-9, and some symbols | Legacy systems, simple alphanumeric |
| **EAN-13** | Numeric only, exactly 12 or 13 digits | Retail products, UPC codes |
| **Interleaved 2 of 5** | Numeric only, even number of digits | Logistics, warehouse systems |

**Tip:** Code 128 is recommended for most use cases as it supports the widest range of characters.

## Project Structure

```
.
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration loading and validation
│   ├── data_loader.py       # CSV parsing
│   ├── qr_generator.py      # QR code generation
│   ├── barcode_generator.py # Barcode generation
│   ├── layout_engine.py     # Layout calculations
│   └── pdf_exporter.py      # PDF generation
├── config.yaml              # Example configuration file
├── ids.csv                  # Example input data
├── pyproject.toml           # Project dependencies
└── README.md
```

## Troubleshooting

### "Command not found: uv"

Make sure UV is installed and in your PATH. See the [Prerequisites](#prerequisites) section above.

### "Output file exists" error

The tool won't overwrite existing files by default. Either:
- Use `--overwrite` flag: `--overwrite`
- Set `overwrite: true` in your config file
- Delete or rename the existing file

### Barcode generation fails for some items

Some barcode formats have restrictions:
- **EAN-13**: Must be exactly 12 or 13 digits (numeric only)
- **Interleaved 2 of 5**: Must have an even number of digits (numeric only)
- **Code 39**: Lowercase letters are automatically converted to uppercase

Invalid entries are skipped with a warning, and processing continues with the remaining items.

### Labels don't fit on the page

Try adjusting:
- `label_width_mm` and `label_height_mm` (make them smaller)
- `margin_mm` (reduce margins)
- `horizontal_gap_mm` and `vertical_gap_mm` (reduce spacing)

### Low quality output

Make sure `dpi` is set to at least 300 for print quality. The default is 300 DPI, which is suitable for most printing needs.

## Requirements

- Python 3.10 or higher
- UV package manager
- All other dependencies are automatically installed via `pyproject.toml`

## Contributing

Found a bug or have a feature request? Feel free to open an issue or submit a pull request!

## License

This project is provided as-is for generating print-ready label sheets.
