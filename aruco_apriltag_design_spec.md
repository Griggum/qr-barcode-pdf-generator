# ArUco & AprilTag Document Generator -- Design Specification

## 1. Overview

This document extends the QR & Barcode Document Generator to support **ArUco markers** and **AprilTags** for computer vision, robotics, and camera calibration applications. This specification covers the generation of print-ready A4 PDFs containing ArUco markers or AprilTags for a list of provided IDs.

**ArUco & AprilTag markers:** Each ID corresponds to:
- An ArUco marker (with selectable dictionary) OR
- An AprilTag (with selectable family)
- A human‑readable text label beneath the marker
- Typically larger in size for distance detection (camera calibration, pose estimation, robotics)

The system allows for: - YAML configuration files (default) - CLI arguments that override YAML - CSV input for ID lists - Scalable layout and marker sizes - Multiple entries placed efficiently on each A4 sheet - Git version control for project management

**Note:** This is a companion specification to the main QR & Barcode design spec. The implementation shares the same codebase structure but operates in separate modes.

------------------------------------------------------------------------

## 2. Goals

-   Automatically generate printable documents for testing marker detection
    workflows (including robotics, camera calibration, pose estimation, augmented reality).
-   Support flexible sizing of ArUco markers and AprilTags (typically larger than QR codes).
-   Support multiple ArUco dictionaries and AprilTag families.
-   Allow easy customization via YAML.
-   Provide reproducible builds and environment isolation using UV.
-   Produce consistent, easy‑to‑print A4 PDFs.
-   Support larger marker sizes optimized for distance detection.

------------------------------------------------------------------------

## 3. Input Sources

### 3.1 CSV Input (IDs)

The tool accepts a CSV file with at least one column. The file must use **UTF-8 encoding** and include a header row.

**Required format (minimum):**

    id
    MARKER-001
    MARKER-002
    ...

**Extended format (optional):**

    id,aruco_id,apriltag_id
    MARKER-001,0,0
    MARKER-002,1,1
    MARKER-003,2,2
    MARKER-004,10,
    MARKER-005,,5

**Rules:**
- Header row is **required** (first line must contain column names)
- If `aruco_id` is missing or empty, defaults to row index (0-based) or can be explicitly set
- If `apriltag_id` is missing or empty, defaults to row index (0-based) or can be explicitly set
- Empty cells are treated as missing values (default to row index)
- Whitespace around values is trimmed
- Invalid rows (missing `id` column) will be skipped with a warning
- ArUco and AprilTag IDs must be valid integers within the dictionary/family range

------------------------------------------------------------------------

## 4. Configuration Model

### 4.1 YAML Configuration (default)

Example `config_aruco.yaml`:

``` yaml
input:
  csv: markers.csv

output:
  file: aruco_markers.pdf
  page_size: A4  # A4 only (portrait)
  margin_mm: 10
  dpi: 300  # Print resolution (default: 300)
  overwrite: true  # Overwrite existing file (default: false, will error)

layout:
  # Label dimensions (takes precedence over labels_per_row/column)
  label_width_mm: 120
  label_height_mm: 120
  
  # Grid layout (used if label dimensions not specified)
  # If both specified, label dimensions take precedence
  labels_per_row: 1
  labels_per_column: 2
  
  # Spacing between labels
  horizontal_gap_mm: 10
  vertical_gap_mm: 10

# ArUco marker configuration
aruco:
  enabled: true  # Enable ArUco marker generation
  dictionary: DICT_5X5_100  # ArUco dictionary (see supported dictionaries)
  size_mm: 100  # Square marker size (typically larger than QR codes)
  border_bits: 1  # Border width in bits (default: 1)
  quiet_zone_mm: 5  # Quiet zone around marker in mm (default: 5)

text:
  font_size: 12  # Point size for human-readable label
  font_name: Helvetica  # Font family
  position: bottom  # "top", "bottom", or "none"
  alignment: center  # "left", "center", or "right"
  margin_mm: 3  # Margin from marker to text
```

Example `config_apriltag.yaml`:

``` yaml
input:
  csv: markers.csv

output:
  file: apriltags.pdf
  page_size: A4  # A4 only (portrait)
  margin_mm: 10
  dpi: 300  # Print resolution (default: 300)
  overwrite: true  # Overwrite existing file (default: false, will error)

layout:
  # Label dimensions (takes precedence over labels_per_row/column)
  label_width_mm: 110
  label_height_mm: 110
  
  # Grid layout (used if label dimensions not specified)
  labels_per_row: 1
  labels_per_column: 2
  
  # Spacing between labels
  horizontal_gap_mm: 10
  vertical_gap_mm: 10

# AprilTag configuration
apriltag:
  enabled: true  # Enable AprilTag generation
  family: tag36h11  # AprilTag family (see supported families)
  size_mm: 90  # Square tag size (typically larger than QR codes)
  border_mm: 2  # Border width in mm (default: 2)
  quiet_zone_mm: 5  # Quiet zone around tag in mm (default: 5)

text:
  font_size: 12  # Point size for human-readable label
  font_name: Helvetica  # Font family
  position: bottom  # "top", "bottom", or "none"
  alignment: center  # "left", "center", or "right"
  margin_mm: 3  # Margin from marker to text
```

### 4.2 CLI Options (override YAML)

Examples:

    python generate.py --aruco-enabled --aruco-dict DICT_5X5_100 --aruco-size-mm 100
    python generate.py --apriltag-enabled --apriltag-family tag25h9 --apriltag-size-mm 90
    python generate.py --config config_aruco.yaml --aruco-size-mm 120 --label-width-mm 140
    python generate.py --csv markers.csv --output result.pdf --overwrite --apriltag-enabled

CLI options always override YAML values. All YAML configuration options have corresponding CLI flags.

### 4.3 Mode Selection

The system supports two marker generation modes:

- **ArUco Mode:** Generates ArUco markers only (typically larger, fewer per page)
- **AprilTag Mode:** Generates AprilTags only (typically larger, fewer per page)

**Mode Selection Rules:**
- If `aruco.enabled: true`, ArUco mode is active
- If `apriltag.enabled: true`, AprilTag mode is active
- If both ArUco and AprilTag are enabled, ArUco takes precedence (warning logged)
- Only one mode should be active per run
- Each mode uses its own layout configuration (label sizes may differ)
- Separate output files recommended for different marker types

**Example configurations:**

``` yaml
# ArUco mode
aruco:
  enabled: true
  dictionary: DICT_5X5_100
  size_mm: 100
layout:
  label_width_mm: 120
  label_height_mm: 120
  labels_per_row: 1
  labels_per_column: 2
apriltag:
  enabled: false

# AprilTag mode
apriltag:
  enabled: true
  family: tag36h11
  size_mm: 90
layout:
  label_width_mm: 110
  label_height_mm: 110
  labels_per_row: 1
  labels_per_column: 2
aruco:
  enabled: false
```

### 4.4 Configuration Validation

The system validates configuration on startup:

- **Label dimensions**: Must fit within page margins (with gaps)
- **Label count**: If both `label_width_mm`/`label_height_mm` and `labels_per_row`/`labels_per_column` are specified, dimensions take precedence
- **ArUco dictionary**: Must be a supported dictionary
- **AprilTag family**: Must be a supported family
- **ArUco/AprilTag IDs**: Must be valid integers within the dictionary/family range
- **File paths**: Input CSV must exist; output directory must be writable
- **DPI**: Must be between 72 and 600 (default: 300)
- **Margins**: Must be non-negative and leave at least 20mm usable space
- **Mode selection**: Exactly one of ArUco or AprilTag must be enabled

Invalid configurations will cause the tool to exit with an error message.

------------------------------------------------------------------------

## 5. Supported ArUco Dictionaries

ArUco markers use predefined dictionaries that determine the marker size and maximum number of unique markers.

-   **DICT_4X4_50** (recommended for small sets)
    - 4×4 bit markers
    - Up to 50 unique markers (IDs 0-49)
    - Smallest marker size, good for close-range detection

-   **DICT_4X4_100**
    - 4×4 bit markers
    - Up to 100 unique markers (IDs 0-99)

-   **DICT_4X4_250**
    - 4×4 bit markers
    - Up to 250 unique markers (IDs 0-249)

-   **DICT_4X4_1000**
    - 4×4 bit markers
    - Up to 1000 unique markers (IDs 0-999)

-   **DICT_5X5_50** (recommended default)
    - 5×5 bit markers
    - Up to 50 unique markers (IDs 0-49)
    - Better error correction than 4×4

-   **DICT_5X5_100**
    - 5×5 bit markers
    - Up to 100 unique markers (IDs 0-99)

-   **DICT_5X5_250**
    - 5×5 bit markers
    - Up to 250 unique markers (IDs 0-249)

-   **DICT_5X5_1000**
    - 5×5 bit markers
    - Up to 1000 unique markers (IDs 0-999)

-   **DICT_6X6_50**
    - 6×6 bit markers
    - Up to 50 unique markers (IDs 0-49)
    - Higher error correction

-   **DICT_6X6_100**
    - 6×6 bit markers
    - Up to 100 unique markers (IDs 0-99)

-   **DICT_6X6_250**
    - 6×6 bit markers
    - Up to 250 unique markers (IDs 0-249)

-   **DICT_6X6_1000**
    - 6×6 bit markers
    - Up to 1000 unique markers (IDs 0-999)

-   **DICT_7X7_50**
    - 7×7 bit markers
    - Up to 50 unique markers (IDs 0-49)
    - Highest error correction, largest marker pattern

-   **DICT_7X7_100**
    - 7×7 bit markers
    - Up to 100 unique markers (IDs 0-99)

-   **DICT_7X7_250**
    - 7×7 bit markers
    - Up to 250 unique markers (IDs 0-249)

-   **DICT_7X7_1000**
    - 7×7 bit markers
    - Up to 1000 unique markers (IDs 0-999)

**Validation Rules:**
- Marker ID must be a non-negative integer within the dictionary's range (0 to max-1)
- Invalid IDs will cause that entry to be skipped with a warning
- Larger dictionaries (more bits) provide better error correction but require larger physical size for reliable detection

------------------------------------------------------------------------

## 6. Supported AprilTag Families

AprilTags use families that determine the encoding scheme and error correction capabilities.

-   **tag36h11** (recommended default)
    - 36-bit encoding
    - Hamming distance 11
    - Up to 58,797 unique tags
    - Good balance of size and error correction
    - Most commonly used family

-   **tag25h9**
    - 25-bit encoding
    - Hamming distance 9
    - Up to 35,588 unique tags
    - Smaller pattern, faster detection

-   **tag16h5**
    - 16-bit encoding
    - Hamming distance 5
    - Up to 30 unique tags
    - Smallest pattern, limited unique tags

-   **tag21h7**
    - 21-bit encoding
    - Hamming distance 7
    - Up to 127 unique tags
    - Small pattern, moderate error correction

-   **tagStandard41h12**
    - 41-bit encoding
    - Hamming distance 12
    - Up to 2,114,074 unique tags
    - Large pattern, high error correction

-   **tagStandard52h13**
    - 52-bit encoding
    - Hamming distance 13
    - Up to 58,535 unique tags
    - Very large pattern, highest error correction

-   **tagCircle21h7**
    - 21-bit encoding
    - Hamming distance 7
    - Circular marker design
    - Up to 127 unique tags

-   **tagCircle49h12**
    - 49-bit encoding
    - Hamming distance 12
    - Circular marker design
    - Up to 2,114,074 unique tags

-   **tagCustom48h12**
    - 48-bit encoding
    - Hamming distance 12
    - Custom family
    - Up to 58,535 unique tags

**Validation Rules:**
- Tag ID must be a non-negative integer within the family's valid range
- Invalid IDs will cause that entry to be skipped with a warning
- Families with higher Hamming distances provide better error correction but may require larger physical size
- Circular families (tagCircle*) have different visual appearance but same detection properties

------------------------------------------------------------------------

## 7. Marker Size Recommendations

**ArUco Markers:**
- **Close range (< 1m):** 30-50mm markers work well
- **Medium range (1-3m):** 50-100mm markers recommended
- **Long range (3-10m):** 100-150mm markers recommended
- **Very long range (> 10m):** 150-200mm markers may be required
- Larger dictionaries (6×6, 7×7) may need slightly larger physical size for reliable detection
- Consider printing resolution: 300 DPI ensures sharp edges for detection algorithms

**AprilTags:**
- **Close range (< 1m):** 30-50mm tags work well
- **Medium range (1-3m):** 50-100mm tags recommended
- **Long range (3-10m):** 100-150mm tags recommended
- **Very long range (> 10m):** 150-200mm tags may be required
- tag36h11 is the most commonly used family and works well at various distances
- Higher Hamming distance families (tagStandard41h12, tagStandard52h13) may require larger physical size

**Layout Considerations:**
- For 80-100mm markers, typically 1-2 markers per row on A4 (portrait)
- For 50-70mm markers, typically 2-3 markers per row
- For 30-40mm markers, typically 3-4 markers per row
- Always ensure adequate quiet zone and border for reliable detection
- Test with your specific camera and detection algorithm to determine optimal size

------------------------------------------------------------------------

## 8. Output Document

### 8.1 Format

-   Single **PDF file**
-   Paper size: **A4**, portrait
-   Margins configurable per YAML/CLI
-   Multiple labels automatically placed based on:
    -   Available space
    -   Label size
    -   ArUco/AprilTag + text layout

### 8.2 Label Structure

Each label contains a single ArUco marker or AprilTag, and optional human-readable text beneath the marker. These markers are typically larger than QR codes for distance detection.

**ArUco marker label:**

    +------------------------------------+
    |                                    |
    |        [ARUCO MARKER]              |
    |         100mm × 100mm               |
    |                                    |
    |        MARKER-001                  |
    |                                    |
    +------------------------------------+

**AprilTag label:**

    +------------------------------------+
    |                                    |
    |        [APRILTAG]                  |
    |         90mm × 90mm                 |
    |                                    |
    |        MARKER-001                  |
    |                                    |
    +------------------------------------+

**Positioning Rules:**
- Marker is centered within the label area
- Text is positioned at `position` (top/bottom) with `margin_mm` spacing
- Text alignment follows `alignment` setting (left/center/right)
- Markers are square (size_mm × size_mm)
- Quiet zone is included around the marker for reliable detection

**Configurable elements:**
- ArUco/AprilTag size (square, typically larger than QR codes)
- Label width/height
- Font size, family, position, and alignment for human-readable text
- Spacing between all elements
- ArUco dictionary and AprilTag family selection

------------------------------------------------------------------------

## 9. Layout Logic

### 9.1 Page Area Calculation

1. **Compute usable page area:**
   - A4 dimensions: 210mm × 297mm (portrait)
   - Usable width = 210mm - (2 × margin_mm)
   - Usable height = 297mm - (2 × margin_mm)

### 9.2 Label Grid Calculation

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

### 9.3 Position Calculation

3. **Calculate label positions (top-left corner of each label):**

   For label at row `r` (0-indexed) and column `c` (0-indexed):
   - X position = margin_mm + (c × (label_width_mm + horizontal_gap_mm))
   - Y position = margin_mm + (r × (label_height_mm + vertical_gap_mm))

   Labels are placed left-to-right, top-to-bottom.

### 9.4 Content Positioning Within Label

4. **Position ArUco/AprilTag marker within label:**
   - Marker X = label_x + (label_width_mm - marker_size_mm) / 2
   - Marker Y = label_y + text_margin + font_height (if text at top) or calculated based on available space (if text at bottom)
   - Marker is centered horizontally
   - Quiet zone is included in the marker_size_mm (internal to marker generation)

5. **Position text:**
   - If position = "bottom": Y = label_y + label_height_mm - font_size_pt - margin_mm
   - If position = "top": Y = label_y + margin_mm
   - X alignment based on `alignment` setting
   - Text is typically placed below the marker

### 9.5 Generation Loop

6. **Loop through ID list:**
   - For each ID:
     - **If ArUco mode enabled:**
       - Validate ArUco ID is within dictionary range
       - Generate ArUco marker image (PNG format, at specified DPI)
     - **If AprilTag mode enabled:**
       - Validate AprilTag ID is within family range
       - Generate AprilTag image (PNG format, at specified DPI)
     - Calculate label position (row, column)
     - If label position exceeds current page, create new page
     - Draw marker and text at calculated positions
   - Handle partial rows: Last row may not be full (labels left-aligned)

### 9.6 Page Management

7. **Page overflow:**
   - When current row × labels_per_row + current_column >= labels_per_row × labels_per_column, start new page
   - Reset row and column counters
   - Continue until all IDs processed
   - **For ArUco/AprilTag:** Typically fewer markers per page due to larger sizes (e.g., 2×2 or 1×2 grid for 80-100mm markers)

------------------------------------------------------------------------

## 10. Libraries & Tools

-   **UV** -- package/env manager, always creating virtual environment under project root folder at ./.venv
-   **Python** -- runtime (Python 3.10+)
-   **opencv-python** -- ArUco marker generation (cv2.aruco module)
-   **apriltag** -- AprilTag generation (Python wrapper for AprilTag library)
-   **reportlab** -- PDF drawing & layout
-   **Pillow (PIL)** -- image manipulation and format conversion
-   **PyYAML** -- YAML config parsing
-   **click** -- CLI argument parsing (chosen over argparse for better UX)
-   **numpy** -- numerical operations (required by opencv-python and apriltag)

**Technical Details:**
- ArUco markers generated using OpenCV's aruco module, converted to PIL Image
- AprilTags generated using apriltag library, converted to PIL Image
- All images generated at specified DPI (default 300) for print quality
- PDF uses reportlab's Canvas for precise positioning
- Images are embedded as raster (PNG) to ensure compatibility
- ArUco markers include border bits and quiet zone for reliable detection
- AprilTags include border and quiet zone for reliable detection

------------------------------------------------------------------------

## 11. Directory Structure (recommended)

    qr_barcode_generator/
    │
    ├── src/
    │   ├── main.py
    │   ├── config.py
    │   ├── data_loader.py
    │   ├── aruco_generator.py
    │   ├── apriltag_generator.py
    │   ├── layout_engine.py
    │   └── pdf_exporter.py
    │
    ├── config_aruco.yaml
    ├── config_apriltag.yaml
    ├── markers.csv
    ├── README.md
    └── pyproject.toml

**Note:** This structure is shared with the QR/Barcode generator. The `aruco_generator.py` and `apriltag_generator.py` modules are specific to marker generation.

------------------------------------------------------------------------

## 12. Error Handling & Validation

### 12.1 Input Validation

- **CSV file:**
  - File must exist and be readable
  - Must have UTF-8 encoding (auto-detect with fallback)
  - Header row required
  - Rows with missing `id` column are skipped with warning
  - Empty rows are skipped silently

- **ID validation:**
  - ArUco IDs are validated against dictionary range (0 to max-1)
  - AprilTag IDs are validated against family range
  - Invalid entries are logged with warning and skipped
  - Processing continues with remaining valid entries
  - Summary report at end: "Generated X labels, skipped Y invalid entries"

### 12.2 Configuration Validation

- **File paths:**
  - Input CSV must exist
  - Output directory must exist and be writable
  - If `overwrite: false` and output file exists, error with message

- **Value ranges:**
  - DPI: 72-600 (default: 300)
  - Margins: ≥ 0, must leave ≥ 20mm usable space
  - Label dimensions: Must fit within page with gaps
  - Font size: 6-72 points
  - ArUco size: 10-200mm (recommended: 50-150mm for distance detection)
  - AprilTag size: 10-200mm (recommended: 50-150mm for distance detection)
  - ArUco border bits: 1-3 (default: 1)
  - AprilTag border: 1-5mm (default: 2mm)

- **Conflicts:**
  - If both label dimensions and labels_per_row/column specified, dimensions take precedence
  - Warning logged when labels_per_row/column are ignored
  - If both ArUco and AprilTag enabled, ArUco takes precedence (warning logged)

### 12.3 Generation Errors

- **ArUco generation failures:**
  - ID out of dictionary range: entry skipped
  - Dictionary not found: fatal error at startup
  - Library errors: entry skipped with error message
  - Error logged: "Failed to generate ArUco marker for ID: {id} - {error}"

- **AprilTag generation failures:**
  - ID out of family range: entry skipped
  - Family not found: fatal error at startup
  - Library errors: entry skipped with error message
  - Error logged: "Failed to generate AprilTag for ID: {id} - {error}"

- **PDF generation errors:**
  - Disk full: fatal error, exit with code 1
  - Permission denied: fatal error, exit with code 1
  - Invalid page dimensions: fatal error at startup

### 12.4 Error Reporting

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

## 13. Output File Handling

### 13.1 File Naming

- Output file path specified in config or CLI
- If directory doesn't exist, create it (with parent directories)
- File extension should be `.pdf` (auto-added if missing)

### 13.2 Overwrite Behavior

- **If `overwrite: false` (default):**
  - If output file exists, error: "Output file exists: {path}. Use --overwrite to replace."
  - Exit with code 1

- **If `overwrite: true`:**
  - Existing file is replaced without warning
  - Previous version is lost

### 13.3 Multiple Runs

- Each run generates a complete PDF from scratch
- No incremental generation or merging
- To append, user must combine CSV files and regenerate

------------------------------------------------------------------------

## 14. Summary

This design defines a flexible, scalable system for generating
print-ready A4 sheets containing ArUco markers, AprilTags, and human-readable
text for each ID. The configuration-driven approach (with YAML and CLI
overrides) makes the tool suitable for both experimentation and
production use. Git and UV ensure reproducibility and portability.

**Key Features:**
- ArUco markers for computer vision and camera calibration applications
- AprilTags for robotics, pose estimation, and augmented reality
- Larger marker sizes optimized for distance detection
- Flexible configuration supporting multiple use cases
- Consistent PDF output format
- Support for multiple dictionaries and families

This document serves as the foundational blueprint for implementation, working in conjunction with the main QR & Barcode design specification.

