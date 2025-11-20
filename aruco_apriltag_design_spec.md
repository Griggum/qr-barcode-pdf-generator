# ArUco & AprilTag Document Generator — Design Specification

**File:** `aruco_apriltag_design_spec.md`  
**Scope:** Extension of the QR & Barcode Document Generator to support **ArUco** and **AprilTag** marker sheets for computer vision, robotics, drone navigation, and camera calibration.

---

## 1. Overview

This design specifies a command‑line tool that generates **print‑ready A4 PDFs** containing **ArUco markers** or **AprilTags** laid out in a configurable grid. The tool is a *companion* to the existing QR & Barcode generator and shares the same codebase and architectural patterns (YAML configuration, CLI overrides, CSV input, UV‑managed Python environment, Git for version control).

Each logical item/row from the CSV results in a **label** on one of the pages. A label contains:

- One **ArUco marker** (from a selected dictionary) **or**
- One **AprilTag** (from a selected family)
- Optional **human‑readable text** (e.g., an ID, semantic label, or location code)

The tool is optimized for:

- Larger marker sizes than typical QR codes
- Reliable detection at distance, in robotics/drone/warehouse contexts
- Repeatable physical size using millimeter-based layout and fixed DPI

---

## 2. High‑Level Goals and Non‑Goals

### 2.1 Goals

- Generate **print‑ready A4 PDFs** containing ArUco markers or AprilTags arranged in a grid.
- Allow **flexible sizing** of markers (in millimeters) for different detection distances.
- Support multiple **ArUco dictionaries** and **AprilTag families** with ID validation.
- Use **YAML configuration** as the primary configuration mechanism, with **CLI options** overriding YAML.
- Read **CSV files** as the source of logical IDs and optional numeric marker IDs.
- Provide robust **validation and error handling**, with clear summaries and exit codes.
- Ensure **reproducible builds and environments** via UV and Git.
- Keep the design extensible for future marker types or output formats.

### 2.2 Non‑Goals (v1)

- Mixed ArUco + AprilTag pages (v1 is single‑mode per run).
- On‑screen interactive preview or GUI.
- Incremental PDF editing/merging; each run produces a fresh PDF.
- Real‑time marker detection or validation from camera input.

---

## 3. Modes and Core Behavior

The tool operates in **one active marker mode per run**:

- **ArUco Mode**
  - Generates labels containing **only ArUco markers**.
- **AprilTag Mode**
  - Generates labels containing **only AprilTags**.

### 3.1 Mode Selection Rules

- `aruco.enabled: true` and `apriltag.enabled: false` → **ArUco mode**
- `aruco.enabled: false` and `apriltag.enabled: true` → **AprilTag mode**
- `aruco.enabled: false` and `apriltag.enabled: false` → **configuration error**
- `aruco.enabled: true` and `apriltag.enabled: true` → **configuration error (v1)**

> Rationale: Failing fast when both are enabled avoids accidental precedence bugs and keeps behavior explicit. A future *mixed mode* could be introduced as a separate, opt‑in configuration.

---

## 4. Input Data Model

### 4.1 CSV Input (Logical IDs)

The CSV provides logical IDs and optional explicit numeric marker/tag IDs.

**Requirements:**

- Encoding: **UTF‑8**
- A **header row** is required.
- Minimum column: `id` (logical label ID).

**Minimal format example:**

```csv
id
MARKER-001
MARKER-002
MARKER-003
```

**Extended format example:**

```csv
id,aruco_id,apriltag_id,description
RACK-A-01,0,0,Entrance rack
RACK-A-02,1,1,Next to entrance
RACK-B-01,2,2,Behind pillar
RACK-C-99,,5,Custom AprilTag ID only
ZONE-X-01,10,,ArUco only
```

### 4.2 ID Rules

- `id` (string):
  - Required for every row; rows without `id` are **skipped with a warning**.
  - Used purely as **human‑readable text**; does not have to match numeric marker ID.
- `aruco_id` (int, optional):
  - Used only in **ArUco mode**.
  - If present and non‑empty, must be a non‑negative integer within the selected dictionary’s range.
- `apriltag_id` (int, optional):
  - Used only in **AprilTag mode**.
  - If present and non‑empty, must be a non‑negative integer within the selected family’s valid range.

### 4.3 Automatic Numeric ID Assignment

To support quick experiments, numeric IDs may be **auto-assigned** when the numeric ID columns are not specified.

Config flag:

```yaml
id_assignment:
  auto_assign_numeric_ids: true  # default: true
  start_index: 0                 # default: 0
```

Behavior per row:

- If in ArUco mode:
  - If `aruco_id` is present and valid → use it.
  - Else if `auto_assign_numeric_ids: true` → use `start_index + row_index_0_based`.
  - Else → **row is skipped with a warning**.
- If in AprilTag mode:
  - Analogous behavior using `apriltag_id`.

> Each auto-assigned ID is logged (at least in verbose mode) so users know which rows mapped to which numeric IDs.

---

## 5. Configuration Model

### 5.1 YAML Configuration (Primary)

The YAML file is the canonical configuration. CLI arguments override values in this file.

#### Example ArUco configuration

```yaml
input:
  csv: markers.csv

output:
  file: aruco_markers.pdf
  page_size: A4
  orientation: portrait        # "portrait" or "landscape"
  margin_mm: 10
  dpi: 300
  overwrite: false             # default: false

layout:
  label_width_mm: 120          # optional; see precedence rules
  label_height_mm: 120
  labels_per_row: 1
  labels_per_column: 2
  horizontal_gap_mm: 10
  vertical_gap_mm: 10
  last_row_alignment: left     # "left" or "center" (v1 may implement left only)

marker_common:
  # Geometry conventions apply to both ArUco and AprilTag.
  # See Section 6 for definitions.
  quiet_zone_mm: 5             # quiet margin OUTSIDE the pattern
  add_scale_bar: true          # optional: draw a 10 cm scale bar on each page
  scale_bar_length_mm: 100
  scale_bar_thickness_mm: 0.5
  print_scaling_note: true     # e.g. "Print at 100% / no scaling"

aruco:
  enabled: true
  dictionary: DICT_5X5_100
  pattern_size_mm: 90          # size of the black/white pattern (square)
  border_bits: 1               # OpenCV border bits
  # total marker footprint (pattern + quiet zones) must fit within label

apriltag:
  enabled: false               # must be false in ArUco mode
  family: tag36h11
  pattern_size_mm: 90
  border_mm: 2                 # solid black border around the pattern
  # total marker footprint is pattern_size_mm + 2*border_mm + 2*quiet_zone_mm

text:
  font_size_pt: 12
  font_name: Helvetica
  position: bottom             # "top", "bottom", or "none"
  alignment: center            # "left", "center", or "right"
  margin_mm: 3                 # distance between marker box and text baseline

id_assignment:
  auto_assign_numeric_ids: true
  start_index: 0

logging:
  level: info                  # "debug", "info", "warning", "error"
  summary_json: null           # e.g. "summary.json" for machine-readable summary

validation:
  require_all_ids_valid: false # if true, a single invalid ID causes fatal error
```

### 5.2 CLI Options (Override YAML)

All key YAML options have corresponding CLI flags. Examples:

```bash
# ArUco run with overrides
python generate.py \
  --config config_aruco.yaml \
  --aruco-enabled \
  --aruco-dict DICT_5X5_100 \
  --aruco-pattern-size-mm 100 \
  --label-width-mm 130 \
  --label-height-mm 130 \
  --output-file aruco_custom.pdf \
  --overwrite

# AprilTag run
python generate.py \
  --config config_apriltag.yaml \
  --apriltag-enabled \
  --apriltag-family tag36h11 \
  --apriltag-pattern-size-mm 90 \
  --csv markers.csv \
  --dpi 300 \
  --overwrite
```

General rules:

- When `--config` is provided, the YAML is loaded first.
- CLI options override individual fields from YAML.
- If no `--config` is provided, sane defaults are used where possible; some options (e.g., `--csv`, marker mode) are required.

### 5.3 Dry‑Run / Validation Mode

Optional CLI flag:

```bash
python generate.py --config config_aruco.yaml --dry-run
```

Behavior:

- Load and validate YAML, CSV, and all derived layout calculations.
- Report validation results and exit without generating a PDF.
- Exit code:
  - `0` if configuration and inputs are valid.
  - `1` if any fatal error is detected.

---

## 6. Marker Geometry and Sizing Conventions

To avoid ambiguity around sizes, the following conventions are used:

### 6.1 Coordinate System

- All high-level layout is done in **millimeters** (mm).
- Conversion to pixels is done using `dpi`:
  - `pixels = mm / 25.4 * dpi`
- Conversion from mm to PDF points uses:
  - `points = mm / 25.4 * 72`

### 6.2 Geometry Definitions

#### 6.2.1 ArUco

Config fields:

- `pattern_size_mm`:
  - Size of the **inner black/white code pattern**, **excluding** quiet zone.
  - This pattern includes the ArUco internal border bits as generated by OpenCV.
- `quiet_zone_mm`:
  - Additional white margin around the entire pattern.
- Effective footprint:
  - `marker_footprint_mm = pattern_size_mm + 2 * quiet_zone_mm`

#### 6.2.2 AprilTag

Config fields:

- `pattern_size_mm`:
  - Size of the encoded tag pattern (the inner AprilTag code).
- `border_mm`:
  - Thickness of the solid black border around the pattern.
- `quiet_zone_mm`:
  - Additional white margin outside the border.
- Effective footprint:
  - `marker_footprint_mm = pattern_size_mm + 2 * border_mm + 2 * quiet_zone_mm`

### 6.3 Label Fit Constraints

A label has:

- `label_width_mm`
- `label_height_mm`

Text may be rendered either **above** or **below** the marker, depending on `text.position`.

The tool must validate that:

1. `marker_footprint_mm <= label_width_mm - 2 * min_label_padding_mm`
2. The vertical space allows both marker and text (if enabled), plus padding:
   - For bottom text:

     ```text
     label_height_mm >= marker_footprint_mm
                       + text_margin_mm
                       + text_height_mm
                       + min_label_padding_mm
     ```

   - For top text, symmetric logic.
3. If `text.position == "none"`, the constraint reduces to having enough space for the marker footprint with padding.

If any label size is insufficient, the configuration is considered invalid and the tool exits with a helpful error message.

---

## 7. Page and Layout Calculations

### 7.1 Page Area

For A4:

- Portrait: 210mm × 297mm
- Landscape: 297mm × 210mm

Usable area:

```text
usable_width_mm  = page_width_mm  - 2 * margin_mm
usable_height_mm = page_height_mm - 2 * margin_mm
```

Margins must be >= 0 and must leave at least `min_usable_space_mm` (e.g., 20mm) in both dimensions.

### 7.2 Label Grid

The layout is defined either by **explicit label dimensions** or by **label counts**:

1. If `label_width_mm` and `label_height_mm` are specified:
   - Compute maximum possible labels:

     ```text
     labels_per_row    = floor((usable_width_mm  + horizontal_gap_mm) /
                               (label_width_mm   + horizontal_gap_mm))
     labels_per_column = floor((usable_height_mm + vertical_gap_mm) /
                               (label_height_mm  + vertical_gap_mm))
     ```

   - If result is < 1 in either dimension, configuration is invalid.

2. If `label_width_mm` and `label_height_mm` are NOT specified, but `labels_per_row` and `labels_per_column` are:
   - Derive label dimensions:

     ```text
     label_width_mm  = (usable_width_mm  - (labels_per_row    - 1) * horizontal_gap_mm) /
                       labels_per_row

     label_height_mm = (usable_height_mm - (labels_per_column - 1) * vertical_gap_mm) /
                       labels_per_column
     ```

3. If **both** dimensions and counts are specified:
   - Dimensions take precedence; counts are recomputed.
   - A warning is logged that `labels_per_row/labels_per_column` were ignored.

### 7.3 Label Positioning

For a label at row `r` (0‑indexed) and column `c` (0‑indexed):

```text
x_label_mm = margin_mm + c * (label_width_mm  + horizontal_gap_mm)
y_label_mm = margin_mm + r * (label_height_mm + vertical_gap_mm)
```

Labels are filled **left‑to‑right, top‑to‑bottom**. On the last page, partial rows are allowed. v1 behavior for the last row is **left aligned**; a future enhancement may support `last_row_alignment: center`.

### 7.4 Marker and Text Inside Labels

Given a label box:

- Marker is **horizontally centered** at:

  ```text
  x_marker_mm = x_label_mm + (label_width_mm - marker_footprint_mm) / 2
  ```

- Vertical placement depends on `text.position`:

  - If `text.position == "bottom"`:
    - Text baseline Y:

      ```text
      y_text_baseline_mm = y_label_mm + label_height_mm - text_margin_mm - text_height_mm
      ```

    - Marker top Y:

      ```text
      y_marker_mm = y_label_mm + (y_text_baseline_mm - y_label_mm - text_margin_mm - marker_footprint_mm) / 2
      ```

      This centers the marker vertically in the space above the text (with padding).

  - If `text.position == "top"`:
    - Text baseline Y:

      ```text
      y_text_baseline_mm = y_label_mm + text_margin_mm + text_height_mm
      ```

    - Marker bottom aligned similarly, centered in the remaining space below.

  - If `text.position == "none"`:
    - Marker is centered vertically in the label:

      ```text
      y_marker_mm = y_label_mm + (label_height_mm - marker_footprint_mm) / 2
      ```

Horizontal text alignment follows `text.alignment` within the label box.

---

## 8. Marker Generation

### 8.1 ArUco Generation

- Library: **OpenCV** (`opencv-contrib-python`) using `cv2.aruco`.
- Steps:
  1. Map `dictionary` string (e.g., `DICT_5X5_100`) to OpenCV constant.
  2. Validate numeric ID:
     - Ensure `0 <= id < max_id_for_dictionary`.
  3. Compute pixel size:

     ```text
     pattern_pixels = round(pattern_size_mm / 25.4 * dpi)
     ```

  4. Generate marker using `aruco.drawMarker(dictionary, id, pattern_pixels)`.
  5. Add quiet zone in pixel space (white padding) according to `quiet_zone_mm`.
  6. Convert to **PIL Image** (mode "L" or "RGB") for embedding into PDF.

- Error conditions:
  - Unknown dictionary name → fatal error at startup.
  - ID out of range → row skipped (or fatal if `require_all_ids_valid: true`).

### 8.2 AprilTag Generation

- Library: `apriltag` (or a chosen AprilTag generator library).
- Steps:
  1. Map `family` string (e.g., `tag36h11`) to a supported family.
  2. Validate numeric ID against library-supported range.
  3. Generate a base tag image at a convenient resolution (e.g., pattern N pixels).
  4. Rescale to desired `pattern_size_mm` at given `dpi`.
  5. Add `border_mm` and `quiet_zone_mm` in pixel space:
     - Draw a solid black border around pattern.
     - Add white margin around border.
  6. Convert to PIL Image for PDF embedding.

- Error conditions:
  - Unknown family string → fatal error at startup.
  - ID out of valid range → row skipped (or fatal with `require_all_ids_valid: true`).

> Implementation detail: The concrete AprilTag library must be verified to support the families listed in Section 9. If not, the supported families subset should be enforced and documented at runtime (e.g., in `--help` or during startup).

---

## 9. Supported Marker Sets

### 9.1 ArUco Dictionaries

The following dictionaries are supported (via OpenCV):

- `DICT_4X4_50` (IDs 0–49)
- `DICT_4X4_100` (IDs 0–99)
- `DICT_4X4_250` (IDs 0–249)
- `DICT_4X4_1000` (IDs 0–999)
- `DICT_5X5_50` (IDs 0–49) — **recommended default**
- `DICT_5X5_100` (IDs 0–99)
- `DICT_5X5_250` (IDs 0–249)
- `DICT_5X5_1000` (IDs 0–999)
- `DICT_6X6_50` (IDs 0–49)
- `DICT_6X6_100` (IDs 0–99)
- `DICT_6X6_250` (IDs 0–249)
- `DICT_6X6_1000` (IDs 0–999)
- `DICT_7X7_50` (IDs 0–49)
- `DICT_7X7_100` (IDs 0–99)
- `DICT_7X7_250` (IDs 0–249)
- `DICT_7X7_1000` (IDs 0–999)

Validation rules:

- Marker ID must be int in `[0, max_id]`.
- Invalid IDs are logged and skipped (or cause fatal error if configured).

### 9.2 AprilTag Families

Supported families (subject to the chosen library):

- `tag36h11` — **recommended default**
- `tag25h9`
- `tag16h5`
- `tag21h7`
- `tagStandard41h12`
- `tagStandard52h13`
- `tagCircle21h7`
- `tagCircle49h12`
- `tagCustom48h12`

Validation rules:

- Tag ID must be a non‑negative integer within the valid range for that family.
- The actual maximum ID per family is defined either:
  - By the library itself (if queryable), or
  - By a built‑in static table matching the library’s implementation.
- Invalid IDs are logged and skipped (or fatal if required).

---

## 10. Marker Size Recommendations

These recommendations guide typical usage, especially for warehouse and robotics work.

### 10.1 ArUco

- **Close range (< 1 m):** 30–50 mm `pattern_size_mm`
- **Medium range (1–3 m):** 50–100 mm
- **Long range (3–10 m):** 100–150 mm
- **Very long range (> 10 m):** 150–200 mm

Notes:

- Larger dictionaries (6×6, 7×7) require more detail and may need slightly larger pattern sizes for reliable detection.
- Use at least 300 DPI for stable edges.

### 10.2 AprilTags

Similar ranges:

- **Close range (< 1 m):** 30–50 mm pattern
- **Medium range (1–3 m):** 50–100 mm
- **Long range (3–10 m):** 100–150 mm
- **Very long range (> 10 m):** 150–200 mm

Notes:

- `tag36h11` is a robust default for robotics.
- Families with higher Hamming distances may benefit from larger sizes.

### 10.3 Layout and Count

Approximate number of labels per row for A4 portrait (assuming moderate margins and gaps):

- 80–100 mm markers → 1–2 labels per row.
- 50–70 mm markers → 2–3 labels per row.
- 30–40 mm markers → 3–4 labels per row.

The layout engine uses exact mm and gap values to compute precise limits.

---

## 11. Output Document

### 11.1 Format

- Single output **PDF file** (v1).
- Page size: A4.
- Orientation: configured (`portrait` or `landscape`).
- Margins, labels, and gaps as computed in millimeters.

Future extension (not in v1):

- Optional raster outputs (e.g., PNG per label or per page).

### 11.2 Label Structure

Each label contains:

- One marker (ArUco or AprilTag) centered in the label box.
- Optional text above or below.
- Respect for quiet zones and borders from Section 6.

Example conceptual layout (ArUco label):

```text
+----------------------------------------+
|                                        |
|                [ARUCO]                 |
|            (pattern+quiet)             |
|                                        |
|              MARKER-001                |
+----------------------------------------+
```

### 11.3 Page Decorations (Optional)

If enabled in `marker_common`:

- A **scale bar** (e.g., 100 mm) at the bottom of each page.
- A small note, e.g.:

  > "Print at 100% / no scaling. The scale bar should measure exactly 10 cm."

These elements help ensure correct physical scaling in print.

---

## 12. Layout Engine and Generation Loop

### 12.1 Core Responsibilities

The layout engine:

- Receives:
  - A sequence of `(PIL.Image, label_text, numeric_id)` tuples.
  - Layout configuration (page size, labels per row/column, mm sizes).
- Computes:
  - Page count.
  - Positions of each label on each page.
- Emits:
  - Drawing commands to the PDF exporter.

### 12.2 Generation Loop

1. Parse arguments and load YAML.
2. Resolve final configuration (apply CLI overrides).
3. Validate configuration (Section 13).
4. Load CSV rows and resolve numeric IDs.
5. For each valid row:
   - Generate marker image (ArUco or AprilTag).
   - Record `(image, id_text)` pair.
6. Initialize PDF canvas.
7. For each label index `i`:
   - Compute page, row, column.
   - Compute label position.
   - Place marker and text inside label.
   - Start new page as needed.
8. Draw scale bar and notes per page if configured.
9. Save PDF file.

---

## 13. Validation, Errors, and Logging

### 13.1 Input File Validation

- CSV:
  - Must exist and be readable.
  - Must have a header row.
  - Non‑UTF‑8 encodings are rejected or require explicit override.
- Output:
  - Parent directory must exist or be creatable.
  - If `overwrite: false` and file exists → fatal error.
  - If `overwrite: true` → existing file is replaced.

### 13.2 Configuration Validation

Checks on startup:

- Only one of `aruco.enabled` / `apriltag.enabled` is true.
- `dpi` in `[72, 600]` (configurable range).
- Margins >= 0 and leave at least 20 mm usable space.
- Label sizing valid; at least 1 label fits in both dimensions.
- Marker footprint fits into label along both axes with padding.
- Text (if enabled) fits into label together with marker.
- Dictionary/family names are recognized by the respective generator.
- If `validation.require_all_ids_valid: true`, any invalid numeric ID aborts the run.

### 13.3 ID Validation

For each row:

- If numeric ID is required (depending on mode/config) and invalid:
  - If `require_all_ids_valid: true` → fatal error.
  - Else → row is skipped with a warning.

### 13.4 Generation Errors

- Marker generation errors (library exceptions) → row skipped with error log.
- PDF generation errors (I/O, permissions, invalid geometry) → fatal error (exit 1).

### 13.5 Logging and Summary

Logging config:

- `logging.level`: `"debug"`, `"info"`, `"warning"`, `"error"`.

Runtime behavior:

- INFO: general progress, ID mapping, summary.
- WARNING: skipped rows, non‑fatal issues.
- ERROR: fatal errors before exit.

On completion, a summary is printed:

- Number of CSV rows processed.
- Number of labels generated.
- Number of rows skipped and reasons (aggregated).
- Output PDF path.

Optional machine‑readable summary:

- If `logging.summary_json` is set:
  - A JSON file is written with:
    - `rows_total`
    - `labels_generated`
    - `rows_skipped`
    - `skipped_reasons` (grouped counts)
    - `output_file`
    - `mode` ("aruco" or "apriltag")

---

## 14. Libraries, Tools, and Directory Structure

### 14.1 Libraries and Tools

- **UV** — environment and dependency manager (virtualenv at `./.venv`).
- **Python** — 3.10+ recommended.
- **opencv-contrib-python** — ArUco marker generation (`cv2.aruco`).
- **apriltag** (or compatible) — AprilTag generation.
- **reportlab** — PDF drawing and layout.
- **Pillow (PIL)** — image manipulation and conversion.
- **PyYAML** — YAML config parsing.
- **click** — CLI argument parsing.
- **numpy** — required by OpenCV / AprilTag libraries.

### 14.2 Directory Structure (Recommended)

```text
qr_barcode_generator/
│
├── src/
│   ├── main.py                 # CLI entrypoint
│   ├── config.py               # config loading and validation
│   ├── data_loader.py          # CSV/ID loading
│   ├── markers/
│   │   ├── base.py             # MarkerGenerator interface
│   │   ├── aruco_generator.py  # ArUco implementation
│   │   └── apriltag_generator.py   # AprilTag implementation
│   ├── layout_engine.py        # Label/grid calculations
│   ├── pdf_exporter.py         # PDF drawing using reportlab
│   └── logging_utils.py        # logging & summary support
│
├── config_aruco.yaml
├── config_apriltag.yaml
├── markers.csv
├── README.md
└── pyproject.toml
```

`markers/base.py` defines a minimal interface, e.g.:

```python
class MarkerGenerator:
    def generate(self, numeric_id: int, dpi: int) -> "PIL.Image.Image":
        ...
```

ArUco and AprilTag generator classes implement this interface.

---

## 15. Summary

This refined specification describes a **configuration-driven, robust, and extensible** ArUco & AprilTag document generator that integrates cleanly with an existing QR & Barcode generator project.

Key properties:

- **Single-mode per run** (ArUco or AprilTag) with clear validation.
- Millimeter-based, DPI‑aware **layout engine** for reproducible physical sizes.
- Flexible **YAML + CLI configuration** with detailed validation and dry-run mode.
- Explicit **geometry conventions** separating pattern, border, and quiet zone.
- Strong emphasis on **error handling, logging, and summarization**.

The spec is designed for practical use in **robotics, drones, and warehouse scanning** scenarios where physical accuracy, marker robustness, and good developer ergonomics all matter.
