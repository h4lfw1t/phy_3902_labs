# Experiment 5: Diffraction Grating Interferometry

> Automated fringe analysis and refractive index determination using diffraction grating interferometry

## Overview

This project analyzes interference fringe patterns from diffraction grating experiments to determine the refractive indices of liquid samples. The system automatically detects fringes, assigns order numbers, and calculates refractive indices by comparing sample measurements to baseline references.

### Key Features

- ✨ **Automatic fringe detection** with configurable thresholds
- 📊 **Error propagation** using the `uncertainties` package
- 🎯 **Baseline comparison** for accurate refractive index calculations
- 🎨 **Color-coded console output** for easy result interpretation
- 📈 **Publication-quality plots** with highlighted fringe regions
- 🔍 **Debug mode** for detailed fringe analysis

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Process All Files (Auto Mode)](#process-all-files-auto-mode)
  - [Process Single File](#process-single-file)
  - [Debug Mode](#debug-mode)
  - [Interactive Mode](#interactive-mode)
- [Project Structure](#project-structure)
- [Data Format](#data-format)
- [Manifest Configuration](#manifest-configuration)
- [Output](#output)
- [Understanding the Results](#understanding-the-results)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## Installation

### Prerequisites

- Python 3.13 or higher
- Poetry (Python package manager)

### Setup

1. **Navigate to the project directory:**
   ```bash
   cd experiment_5
   ```

2. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

   This will install all required packages:
   - `numpy` - Numerical computations
   - `pandas` - Data handling
   - `matplotlib` - Plotting
   - `scipy` - Signal processing
   - `uncertainties` - Automatic error propagation
   - `colorama` - Cross-platform colored output

3. **Activate the Poetry environment:**
   ```bash
   poetry shell
   ```

---

## Quick Start

Process all data files and calculate refractive indices:

```bash
cd src
poetry run python intensity_plot.py auto
```

This will:
1. Skip parent baseline files and files without baselines
2. Process all child files that have baseline references
3. Calculate refractive indices for each sample
4. Generate plots in `../out/intensity_plots/`
5. Display color-coded results in the console

---

## Usage

### Process All Files (Auto Mode)

**Normal auto mode** (recommended for final results):
```bash
poetry run python intensity_plot.py auto
```

**Behavior:**
- ✅ Processes only child files (those with baseline comparisons)
- ❌ Skips parent baseline files
- ❌ Skips files without baseline references
- 📊 Calculates refractive indices
- 💾 Saves plots to `../out/intensity_plots/`

**Example output:**
```
Processing all files from manifest...
(Skipping parent files and files without baseline)

Skipped air_v2.csv: Parent baseline file
Skipped new_cuvette_data.csv: Parent baseline file
Skipped water_532_data.csv: No baseline reference

======================================================================
  Analysis: ethanol_v2_data.csv
======================================================================
  Ethanol at SATP with new cuvette.

Detected Fringes:
  Order -1: distance = 17.7778 mm  [range: -20.22 to -15.33 mm, ...]
  Order +1: distance = 18.8889 mm  [range: 16.44 to 21.33 mm, ...]

Refractive Index Results:
  Order -1: n = 1.672416
  Order +1: n = 1.393251

  Mean: n = 1.532833 ± 0.197399
======================================================================
```

---

### Process Single File

Process a specific data file:

```bash
poetry run python intensity_plot.py ethanol_v2_data.csv
```

**Use cases:**
- Testing on a specific sample
- Troubleshooting individual measurements
- Quick analysis during data collection

---

### Debug Mode

Enable debug mode to see detailed fringe information:

```bash
# Debug mode with auto processing
poetry run python intensity_plot.py auto debug

# Debug mode with single file
poetry run python intensity_plot.py ethanol_v2_data.csv debug

# Order doesn't matter
poetry run python intensity_plot.py debug auto
```

**Debug output includes:**
```
[DEBUG] Center fringe: -0.00244444 m to 0.00266667 m (center: 0 m)

[DEBUG] Outer fringes:
  -0.0202222 m to -0.0153333 m (center: -0.0177778 m)
  0.0164444 m to 0.0213333 m (center: 0.0188889 m)

Detected Fringes:
  Order -1: distance = 17.7778 mm  [...]
  ...
```

**Benefits:**
- View all fringe positions and boundaries
- Verify fringe detection accuracy
- Process ALL files including baselines
- Useful for troubleshooting measurements

---

### Interactive Mode

Run without arguments for interactive prompts:

```bash
poetry run python intensity_plot.py
```

**Interactive session example:**
```
=== Intensity Plot Analysis ===
Options: 'auto', 'debug', filename, or 'exit' to quit

Enter your choice (or 'exit'/'cancel' to quit): ethanol_v2_data.csv
```

**Features:**
- Choose auto mode, debug mode, or specific file
- Combine options (e.g., "auto debug")
- Safe exit with `exit`, `quit`, `cancel`, or `q` commands
- No need for keyboard interrupts (Ctrl+C)

**Exit options:**
- Type `exit`, `quit`, `cancel`, or `q` at any prompt to safely exit the program

---

## Project Structure

```
experiment_5/
├── README.md                    # This file
├── data/
│   └── intensity_data/
│       ├── manifest.json        # Experiment metadata
│       ├── air_v2.csv          # Baseline: Air reference
│       ├── new_cuvette_data.csv # Baseline: Empty cuvette
│       ├── ethanol_v2_data.csv # Sample: Ethanol measurement
│       ├── water_v2_data.csv   # Sample: Water measurement
│       └── ...                 # Additional data files
├── src/
│   ├── intensity_plot.py       # Main analysis script
│   └── utils/
│       ├── __init__.py
│       ├── data_processing.py  # ADC conversion, error propagation
│       └── fringe_analysis.py  # Fringe detection and analysis
└── out/
    └── intensity_plots/        # Generated plots (created automatically)
```

---

## Data Format

### CSV Data Files

Each data file contains experimental measurements:

| Column       | Description                          | Units  |
|--------------|--------------------------------------|--------|
| `position`   | Stepper motor step count             | steps  |
| `ldr_mean`   | Mean ADC reading from LDR sensor     | counts |
| `ldr_stddev` | Standard deviation of ADC readings   | counts |

**Example:**
```csv
position,ldr_mean,ldr_stddev
0,512.5,2.3
10,515.2,2.1
20,518.9,2.5
...
```

---

## Manifest Configuration

The `manifest.json` file contains metadata for each dataset:

```json
{
    "new_cuvette_data.csv": {
        "wavelength": 650e-9,
        "setup_length": 0.045,
        "baseline": {
            "name": "new_cuvette",
            "parent": true
        },
        "notes": "New cuvette with known refractive index."
    },
    "ethanol_v2_data.csv": {
        "wavelength": 650e-9,
        "setup_length": 0.045,
        "baseline": {
            "name": "new_cuvette",
            "parent": false
        },
        "notes": "Ethanol at SATP with new cuvette."
    }
}
```

### Manifest Fields

| Field           | Type    | Required | Description                                    |
|-----------------|---------|----------|------------------------------------------------|
| `wavelength`    | float   | Yes      | Laser wavelength in meters (e.g., 650e-9)     |
| `setup_length`  | float   | Yes      | Distance from grating to detector (meters)     |
| `baseline.name` | string  | Optional | Name identifier for baseline group             |
| `baseline.parent` | bool  | Optional | `true` = baseline, `false` = sample           |
| `notes`         | string  | Optional | Experimental notes                             |

### Baseline Relationships

- **Parent files** (`parent: true`): Reference measurements (e.g., empty cuvette)
- **Child files** (`parent: false`): Sample measurements compared to parent
- Files with the same `baseline.name` are linked for comparison

---

## Output

### Console Output

**Color coding:**
- 🔵 **Cyan** - Section headers and borders
- 🟣 **Magenta** - Filenames
- 🟢 **Green** - "Detected Fringes" section
- 🔵 **Blue** - "Refractive Index Results" section
- 🟡 **Yellow** - Distance values (highlighted)
- 🔵 **Cyan** - Individual refractive index values
- 🟣 **Magenta** - Mean refractive index (most important)
- ⚪ **Dim** - Secondary information (ranges, brackets)

### Plot Files

Plots are saved to `out/intensity_plots/` with filenames:
```
{original_filename}_intensity.png
```

Each plot includes:
- Intensity vs. position with error bars
- Yellow highlighted fringe regions
- Grid for easier reading
- Legend

---

## Understanding the Results

### Fringe Order Numbers

- **Order 0** (center fringe): Zero-order diffraction, at position 0
- **Order ±1**: First-order fringes on left (-) and right (+) sides
- **Order ±2**: Second-order fringes, etc.

### Refractive Index

The refractive index (n) is calculated by comparing fringe positions between:
1. **Baseline** measurement (e.g., empty cuvette)
2. **Sample** measurement (e.g., cuvette with liquid)

The shift in fringe positions reveals the sample's refractive index.

**Typical values:**
- Air: n ≈ 1.000
- Water: n ≈ 1.33
- Ethanol: n ≈ 1.36
- Olive oil: n ≈ 1.47

### Mean ± Standard Deviation

The mean is calculated from all detected fringe orders:
```
Mean: n = 1.532833 ± 0.197399
         ^^^^^^^^    ^^^^^^^^
         Average     Uncertainty
```

Smaller uncertainty indicates more consistent measurements across fringes.

---

## Troubleshooting

### Issue: "Data file not found"

**Solution:** Ensure you're running from the `src/` directory:
```bash
cd experiment_5/src
poetry run python intensity_plot.py auto
```

### Issue: "No manifest entry found"

**Solution:** Check that your CSV filename exists in `data/intensity_data/manifest.json`

### Issue: No fringes detected

**Possible causes:**
1. Low signal-to-noise ratio
2. Thresholds too high
3. Alignment issues during data collection

**Solution:** Run in debug mode to inspect raw fringe detection:
```bash
poetry run python intensity_plot.py your_file.csv debug
```

### Issue: Large uncertainty in refractive index

**Causes:**
- Inconsistent fringe detection
- Vibrations during measurement
- Temperature drift

**Solution:** Repeat measurement with better environmental control

### Issue: Division by zero error

**This has been fixed!** The code now clips ADC values to prevent saturation issues.

---

## Technical Details

### Error Propagation

The system uses the `uncertainties` package to automatically propagate measurement errors through:

1. **ADC → Voltage conversion**
2. **Voltage → Resistance** (voltage divider with LDR)
3. **Resistance → Intensity** (inverse relationship)

All uncertainties are tracked automatically without manual derivative calculations.

### Fringe Detection Algorithm

1. Calculate median intensity as background
2. Apply threshold: `intensity > background + threshold × (max - background)`
3. Use connected component labeling to find contiguous regions
4. Filter regions by minimum width
5. Assign order numbers based on position relative to center

### Refractive Index Calculation

Uses the theoretical formula for diffraction grating interferometry:

```
n = (m × λ₀ / S) × √[1 + (w² × τ) / (w × m × λ₀ / S - Δdₘ × √τ)²]
```

Where:
- `m` = fringe order
- `λ₀` = vacuum wavelength
- `S` = grating period (1 / lines_per_meter)
- `w` = cuvette width
- `Δdₘ` = fringe shift from baseline
- `τ` = 1 - (m × λ₀ / S)²

---

## Command Reference

### All Available Commands

```bash
# Auto mode (recommended)
poetry run python intensity_plot.py auto

# Auto mode with debug
poetry run python intensity_plot.py auto debug
poetry run python intensity_plot.py debug auto

# Single file
poetry run python intensity_plot.py filename.csv

# Single file with debug
poetry run python intensity_plot.py filename.csv debug
poetry run python intensity_plot.py debug filename.csv

# Interactive mode
poetry run python intensity_plot.py

# Exit interactive mode
# Type: exit, quit, cancel, or q at any prompt
```

### Auto Mode Behavior

| Mode   | Processes Baselines? | Processes Samples? | Shows Debug Info? |
|--------|----------------------|-------------------|-------------------|
| Normal | ❌ No                | ✅ Yes             | ❌ No             |
| Debug  | ✅ Yes               | ✅ Yes             | ✅ Yes            |

---

## Contributing

When adding new measurements:

1. Save data as CSV with columns: `position`, `ldr_mean`, `ldr_stddev`
2. Add entry to `data/intensity_data/manifest.json`
3. Specify baseline relationship if applicable
4. Run analysis: `poetry run python intensity_plot.py auto`

---

## License

Part of PHY 3902 Labs coursework.

---

## Contact

For questions or issues, please hesitate to reach out.

---

**Last Updated:** November 19, 2025

