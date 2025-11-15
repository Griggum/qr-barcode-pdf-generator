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

The tool accepts a CSV file with at least one column:

    id
    ITEM-001
    ITEM-002
    ...

Optional extended format:

    id,qr_value,barcode_value
    ITEM-001,ITEM-001,123456789012
    ITEM-002,ITEM-002,123456789013

If `qr_value` or `barcode_value` is missing, they default to the `id`.

------------------------------------------------------------------------

## 4. Configuration Model

### 4.1 YAML Configuration (default)

Example `config.yaml`:

``` yaml
input:
  csv: ids.csv

output:
  file: output.pdf
  page_size: A4
  margin_mm: 10

layout:
  label_width_mm: 60
  label_height_mm: 40
  labels_per_row: 3
  labels_per_column: 7

qr:
  size_mm: 25
  error_correction: M

barcode:
  symbology: code128
  height_mm: 15
```

### 4.2 CLI Options (override YAML)

Examples:

    python generate.py --config config.yaml --barcode-symbology code39
    python generate.py --qr-size-mm 35 --label-width-mm 70

CLI options always override YAML values.

------------------------------------------------------------------------

## 5. Supported Barcode Symbologies

-   **Code 128 (recommended default)**
-   **Code 39**
-   **EAN-13** (for numeric-only)
-   **Interleaved 2 of 5**
-   Additional symbologies can be added through `python-barcode` or
    `treepoem`.

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

Each label contains:

    +------------------------------------+
    | [QR CODE]    [BARCODE]             |
    |                                    |
    | ITEM-001                           |
    +------------------------------------+

Configurable elements: - QR size - Barcode height/width - Label
width/height - Font size for human-readable ID

------------------------------------------------------------------------

## 7. Layout Logic

1.  Compute usable page area based on margins.
2.  Determine how many labels fit horizontally and vertically based on
    specified sizes.
3.  Loop through ID list:
    -   Generate QR image
    -   Generate barcode image (chosen symbology)
    -   Draw both on the PDF at computed positions
4.  When a page is full, create a new page.

------------------------------------------------------------------------

## 8. Libraries & Tools

-   **UV** -- package/env manager
-   **Python** -- runtime
-   **qrcode / segno** -- QR generation
-   **python-barcode or treepoem** -- barcode generation
-   **reportlab** -- PDF drawing & layout
-   **Pillow (PIL)** -- image manipulation if needed
-   **PyYAML** -- YAML config parsing
-   **argparse or typer** -- CLI argument parsing

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

## 10. Git Workflow

1.  Initialize git repo:

        git init

2.  Use feature branches:

        git checkout -b feature/barcode-support

3.  Commit frequently:

        git commit -m "Add basic barcode generation"

4.  Tag stable releases:

        git tag v0.1

------------------------------------------------------------------------

## 11. Future Enhancements (optional)

-   Export to PNG label sheets
-   Avery label template support
-   Web UI wrapper
-   Batch QR/barcode preview thumbnails
-   Drone-distance readability presets

------------------------------------------------------------------------

## 12. Summary

This design defines a flexible, scalable system for generating
print-ready A4 sheets containing QR codes, barcodes, and human-readable
text for each ID. The configuration-driven approach (with YAML and CLI
overrides) makes the tool suitable for both experimentation and
production use. Git and UV ensure reproducibility and portability.

This document serves as the foundational blueprint for implementation.
