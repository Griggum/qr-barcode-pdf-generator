# QR & Barcode Document Generator -- Design Specification

## 1. Overview

This project provides a **CLI-based tool**, managed with **UV** as the
Python package manager, for generating **print-ready A4 PDFs**
containing both QR codes and barcodes for a list of provided IDs. Each
ID will correspond to: - A QR code - A barcode (with selectable
symbology) - A human‑readable text label beneath both codes

The system allows for: - YAML configuration files (default) - CLI
arguments that override YAML - CSV input for ID lists - Scalable layout
and code sizes - Multiple entries placed efficiently on each A4 sheet -
Git version control for project management

------------------------------------------------------------------------

## 2. Goals

-   Automatically generate printable documents for testing scanning
    workflows (including drones, handhelds, warehouse cameras).
-   Support flexible sizing of labels, QR codes, and barcodes.
-   Support multiple barcode symbologies.
-   Allow easy customization via YAML.
-   Provide reproducible builds and environment isolation using UV.
-   Produce consistent, easy‑to‑print A4 PDFs.

------------------------------------------------------------------------

## 3. Input Sources

### 3.1 CSV Input (IDs)

The tool accepts a CSV file with at least one column. The file must use **UTF-8 encoding** and include a header row.

**Required format (minimum):**

    id
    ITEM-001
    ITEM-002
    ...

**Extended format (optional):**

    id,qr_value,barcode_value
    ITEM-001,ITEM-001,123456789012
    ITEM-002,ITEM-002,123456789013
    ITEM-003,,
    ITEM-004,CUSTOM-QR-VALUE,

**Rules:**
- Header row is **required** (first line must contain column names)
- If `qr_value` is missing or empty, it defaults to the `id` value
- If `barcode_value` is missing or empty, it defaults to the `id` value
- Empty cells are treated as missing values (default to `id`)
- Whitespace around values is trimmed
- Invalid rows (missing `id` column) will be skipped with a warning

------------------------------------------------------------------------

## 4. Configuration Model

### 4.1 YAML Configuration (default)

Example `config.yaml`:

``` yaml
input:
  csv: ids.csv

output:
  file: output.pdf
  page_size: A4  # A4 only (portrait)
  margin_mm: 10
  dpi: 300  # Print resolution (default: 300)
  overwrite: true  # Overwrite existing file (default: false, will error)

layout:
  # Label dimensions (takes precedence over labels_per_row/column)
  label_width_mm: 60
  label_height_mm: 40
  
  # Grid layout (used if label dimensions not specified)
  # If both specified, label dimensions take precedence
  labels_per_row: 3
  labels_per_column: 7
  
  # Spacing between labels
  horizontal_gap_mm: 5
  vertical_gap_mm: 5
  
  # Arrangement: "horizontal" (QR left, barcode right) or "vertical" (QR top, barcode bottom)
  code_arrangement: horizontal
  
  # Spacing between QR and barcode when arranged horizontally
  code_spacing_mm: 5

qr:
  size_mm: 25  # Square QR code size
  error_correction: M  # L, M, Q, or H (Low, Medium, Quartile, High)
  quiet_zone: 4  # Module size for quiet zone (default: 4)

barcode:
  symbology: code128  # code128, code39, ean13, i2of5
  height_mm: 15  # Height of barcode bars
  width_factor: 2  # Bar width multiplier (default: 2)
  quiet_zone: 10  # Quiet zone in mm on each side (default: 10)

text:
  font_size: 10  # Point size for human-readable label
  font_name: Helvetica  # Font family
  position: bottom  # "top", "bottom", or "none"
  alignment: center  # "left", "center", or "right"
  margin_mm: 2  # Margin from codes to text
```

### 4.2 CLI Options (override YAML)

Examples:

    python generate.py --config config.yaml --barcode-symbology code39
    python generate.py --qr-size-mm 35 --label-width-mm 70
    python generate.py --csv ids.csv --output result.pdf --overwrite

CLI options always override YAML values. All YAML configuration options have corresponding CLI flags.

### 4.3 Configuration Validation

The system validates configuration on startup:

- **Label dimensions**: Must fit within page margins (with gaps)
- **Label count**: If both `label_width_mm`/`label_height_mm` and `labels_per_row`/`labels_per_column` are specified, dimensions take precedence
- **QR error correction**: Must be one of: L, M, Q, H
- **Barcode symbology**: Must be a supported symbology
- **File paths**: Input CSV must exist; output directory must be writable
- **DPI**: Must be between 72 and 600 (default: 300)
- **Margins**: Must be non-negative and leave at least 20mm usable space

Invalid configurations will cause the tool to exit with an error message.

------------------------------------------------------------------------

## 5. Supported Barcode Symbologies

-   **Code 128 (recommended default)**
    - Supports full ASCII character set
    - No length restrictions (within reason)
    - Best general-purpose choice

-   **Code 39**
    - Supports: A-Z, 0-9, and symbols: - . $ / + % SPACE
    - No fixed length requirement
    - Cannot encode lowercase letters (will be converted to uppercase)

-   **EAN-13**
    - **Numeric only** (0-9)
    - **Exactly 12 or 13 digits** required
    - If 12 digits provided, check digit is auto-calculated
    - If 13 digits provided, check digit is validated

-   **Interleaved 2 of 5 (i2of5)**
    - **Numeric only** (0-9)
    - Even number of digits required
    - Commonly used in logistics

**Validation Rules:**
- Invalid characters for a symbology will cause that entry to be skipped with a warning
- EAN-13 entries with wrong length will be skipped
- Code 39 entries with lowercase letters will be auto-converted to uppercase
- Additional symbologies can be added through `python-barcode` or `treepoem` libraries

------------------------------------------------------------------------

## 6. Output Document

### 6.1 Format

-   Single **PDF file**
-   Paper size: **A4**, portrait
-   Margins configurable per YAML/CLI
-   Multiple labels automatically placed based on:
    -   Available space
    -   Label size
    -   QR + barcode + text layout

### 6.2 Label Structure

Each label contains QR code, barcode, and optional human-readable text that belongs to both QR code and barcode.

**Horizontal arrangement (default):**

    +------------------------------------+
    | [QR CODE]  [BARCODE]               |
    |  25mm       (auto-width)           |
    | ITEM-001    ITEM-001               |
    |                                    |
    +------------------------------------+

**Vertical arrangement:**

    +------------------------------------+
    |        [QR CODE]                   |
    |         25mm                       |
    |        ITEM-001                    |
    |                                    |
    |        [BARCODE]                   |
    |      (auto-width)                  |
    |        ITEM-001                    |
    +------------------------------------+

**Positioning Rules:**
- QR code and barcode are centered within the label area
- When horizontal: QR on left, barcode on right, separated by `code_spacing_mm`
- When vertical: QR on top, barcode below, separated by `code_spacing_mm`
- Text is positioned at `position` (top/bottom) with `margin_mm` spacing
- Text alignment follows `alignment` setting (left/center/right)
- Barcode width is automatically calculated based on data length and `width_factor`

**Configurable elements:**
- QR size (square)
- Barcode height and width factor
- Label width/height
- Font size, family, position, and alignment for human-readable text
- Spacing between all elements

------------------------------------------------------------------------

## 7. Layout Logic

### 7.1 Page Area Calculation

1. **Compute usable page area:**
   - A4 dimensions: 210mm × 297mm (portrait)
   - Usable width = 210mm - (2 × margin_mm)
   - Usable height = 297mm - (2 × margin_mm)

### 7.2 Label Grid Calculation

2. **Determine label grid:**

   **If `label_width_mm` and `label_height_mm` are specified:**
   - Labels per row = floor((usable_width + horizontal_gap_mm) / (label_width_mm + horizontal_gap_mm))
   - Labels per column = floor((usable_height + vertical_gap_mm) / (label_height_mm + vertical_gap_mm))
   - Validate that at least 1 label fits in each direction

   **If `labels_per_row` and `labels_per_column` are specified (and dimensions not):**
   - Label width = (usable_width - (labels_per_row - 1) × horizontal_gap_mm) / labels_per_row
   - Label height = (usable_height - (labels_per_column - 1) × vertical_gap_mm) / labels_per_column

   **Validation:**
   - Total required width = (labels_per_row × label_width_mm) + ((labels_per_row - 1) × horizontal_gap_mm)
   - Total required height = (labels_per_column × label_height_mm) + ((labels_per_column - 1) × vertical_gap_mm)
   - Must fit within usable page area

### 7.3 Position Calculation

3. **Calculate label positions (top-left corner of each label):**

   For label at row `r` (0-indexed) and column `c` (0-indexed):
   - X position = margin_mm + (c × (label_width_mm + horizontal_gap_mm))
   - Y position = margin_mm + (r × (label_height_mm + vertical_gap_mm))

   Labels are placed left-to-right, top-to-bottom.

### 7.4 Content Positioning Within Label

4. **Position QR code and barcode within label:**

   **Horizontal arrangement:**
   - QR X = label_x + (label_width_mm - qr_size_mm - code_spacing_mm - barcode_width) / 2
   - QR Y = label_y + (label_height_mm - qr_size_mm) / 2 (if text at bottom) or label_y + text_margin (if text at top)
   - Barcode X = QR X + qr_size_mm + code_spacing_mm
   - Barcode Y = label_y + (label_height_mm - barcode_height_mm) / 2

   **Vertical arrangement:**
   - QR X = label_x + (label_width_mm - qr_size_mm) / 2
   - QR Y = label_y + text_margin (if text at top) or calculated based on available space
   - Barcode X = label_x + (label_width_mm - barcode_width) / 2
   - Barcode Y = QR Y + qr_size_mm + code_spacing_mm

5. **Position text:**
   - If position = "bottom": Y = label_y + label_height_mm - font_size_pt - margin_mm
   - If position = "top": Y = label_y + margin_mm
   - X alignment based on `alignment` setting

### 7.5 Generation Loop

6. **Loop through ID list:**
   - For each ID:
     - Validate ID for chosen barcode symbology
     - Generate QR image (PNG format, at specified DPI)
     - Generate barcode image (PNG format, at specified DPI)
     - Calculate label position (row, column)
     - If label position exceeds current page, create new page
     - Draw QR code, barcode, and text at calculated positions
   - Handle partial rows: Last row may not be full (labels left-aligned)

### 7.6 Page Management

7. **Page overflow:**
   - When current row × labels_per_row + current_column >= labels_per_row × labels_per_column, start new page
   - Reset row and column counters
   - Continue until all IDs processed

------------------------------------------------------------------------

## 8. Libraries & Tools

-   **UV** -- package/env manager, always creating virtual environment under project root folder at ./.venv
-   **Python** -- runtime (Python 3.10+)
-   **qrcode[pil]** -- QR generation (chosen over segno for better PIL integration)
-   **python-barcode[images]** -- barcode generation (chosen over treepoem for broader symbology support)
-   **reportlab** -- PDF drawing & layout
-   **Pillow (PIL)** -- image manipulation and format conversion
-   **PyYAML** -- YAML config parsing
-   **click** -- CLI argument parsing (chosen over argparse for better UX)

**Technical Details:**
- QR codes generated as PIL Image objects, then embedded in PDF
- Barcodes generated as PIL Image objects, then embedded in PDF
- All images generated at specified DPI (default 300) for print quality
- PDF uses reportlab's Canvas for precise positioning
- Images are embedded as raster (PNG) to ensure compatibility

------------------------------------------------------------------------

## 9. Directory Structure (recommended)

    qr_barcode_generator/
    │
    ├── src/
    │   ├── main.py
    │   ├── config.py
    │   ├── data_loader.py
    │   ├── qr_generator.py
    │   ├── barcode_generator.py
    │   ├── layout_engine.py
    │   └── pdf_exporter.py
    │
    ├── config.yaml
    ├── ids.csv
    ├── README.md
    └── pyproject.toml

------------------------------------------------------------------------

## 10. Error Handling & Validation

### 10.1 Input Validation

- **CSV file:**
  - File must exist and be readable
  - Must have UTF-8 encoding (auto-detect with fallback)
  - Header row required
  - Rows with missing `id` column are skipped with warning
  - Empty rows are skipped silently

- **ID validation:**
  - IDs are validated against chosen barcode symbology before generation
  - Invalid entries are logged with warning and skipped
  - Processing continues with remaining valid entries
  - Summary report at end: "Generated X labels, skipped Y invalid entries"

### 10.2 Configuration Validation

- **File paths:**
  - Input CSV must exist
  - Output directory must exist and be writable
  - If `overwrite: false` and output file exists, error with message

- **Value ranges:**
  - DPI: 72-600 (default: 300)
  - Margins: ≥ 0, must leave ≥ 20mm usable space
  - Label dimensions: Must fit within page with gaps
  - Font size: 6-72 points
  - QR error correction: Must be L, M, Q, or H

- **Conflicts:**
  - If both label dimensions and labels_per_row/column specified, dimensions take precedence
  - Warning logged when labels_per_row/column are ignored

### 10.3 Generation Errors

- **QR generation failures:**
  - Extremely long values may fail; entry skipped with error message
  - Error logged: "Failed to generate QR for ID: {id} - {error}"

- **Barcode generation failures:**
  - Invalid characters for symbology: entry skipped
  - Wrong length (EAN-13): entry skipped
  - Library errors: entry skipped with error message
  - Error logged: "Failed to generate barcode for ID: {id} - {error}"

- **PDF generation errors:**
  - Disk full: fatal error, exit with code 1
  - Permission denied: fatal error, exit with code 1
  - Invalid page dimensions: fatal error at startup

### 10.4 Error Reporting

- Warnings printed to stderr
- Errors printed to stderr
- Final summary printed to stdout:
  - Total IDs processed
  - Successfully generated labels
  - Skipped entries (with reasons)
  - Output file path
- Exit codes:
  - 0: Success (all entries processed, some may have been skipped)
  - 1: Fatal error (cannot continue)

------------------------------------------------------------------------

## 11. Output File Handling

### 11.1 File Naming

- Output file path specified in config or CLI
- If directory doesn't exist, create it (with parent directories)
- File extension should be `.pdf` (auto-added if missing)

### 11.2 Overwrite Behavior

- **If `overwrite: false` (default):**
  - If output file exists, error: "Output file exists: {path}. Use --overwrite to replace."
  - Exit with code 1

- **If `overwrite: true`:**
  - Existing file is replaced without warning
  - Previous version is lost

### 11.3 Multiple Runs

- Each run generates a complete PDF from scratch
- No incremental generation or merging
- To append, user must combine CSV files and regenerate

------------------------------------------------------------------------

## 12. Git Workflow

1.  Initialize git repo:

        git init

2.  Use feature branches:

        git checkout -b feature/barcode-support

3.  Commit frequently:

        git commit -m "Add basic barcode generation"

4.  Tag stable releases:

        git tag v0.1

------------------------------------------------------------------------

## 13. Future Enhancements (optional)

-   Export to PNG label sheets
-   Avery label template support
-   Web UI wrapper
-   Batch QR/barcode preview thumbnails
-   Drone-distance readability presets

------------------------------------------------------------------------

## 14. Summary

This design defines a flexible, scalable system for generating
print-ready A4 sheets containing QR codes, barcodes, and human-readable
text for each ID. The configuration-driven approach (with YAML and CLI
overrides) makes the tool suitable for both experimentation and
production use. Git and UV ensure reproducibility and portability.

This document serves as the foundational blueprint for implementation.

**Note:** For ArUco marker and AprilTag generation, see the separate `aruco_apriltag_design_spec.md` document.
