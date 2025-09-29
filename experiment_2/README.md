# PHY 3902 Experiment 2: LED Characterization and Planck’s Law

This folder contains code, data, and documentation for laboratory experiments investigating the electrical and optical properties of LEDs, including their I-V characteristics and the relationship between threshold voltage and wavelength (Planck’s law).

## Folder Structure

- **data/**
  - **2c/**: Raw I-V data for a single LED (CSV).
  - **2d/**: I-V data for blue, green, yellow, and red LEDs (CSV).
- **docs/**
  - `PHY 3902_LED_E_2023.pdf`: Lab manual and experiment description.
  - Final report files: Add your completed LaTeX source and compiled PDF here (e.g., `LED_IV_Planck_Report_v1.tex`, `LED_IV_Planck_Report_v1.pdf`).
  - Figures and supplementary documentation.
- **src/**
  - `2d_led_fit.py`: Python script to fit LED I-V curves and extract parameters from CSV data.
  - `planck_led_graph.py`: Python script to analyze threshold voltages and plot voltage vs. wavelength for LEDs.
  - `DAC_LED_experiment_2C/`, `DAC_plank_2E/`, `DAC_test_experiment_2B/`: Arduino sketches for automated data collection using a DAC and analog measurements.
- **notebooks/**
  - (Optional) Jupyter notebooks for further analysis (if present).

## Getting Started

### Prerequisites
- Python 3.x
- Poetry (for dependency management)
- Arduino IDE (for running `.ino` files)

### Python Analysis
1. Install dependencies:
   ```cmd
   poetry install
   ```
2. Run analysis scripts:
   - Fit LED I-V curves:
     ```cmd
     poetry run python src/2d_led_fit.py
     ```
   - Analyze Planck’s law relationship:
     ```cmd
     poetry run python src/planck_led_graph.py
     ```
   - Data files are loaded automatically from the `data/` folder.

### Arduino Data Collection
- Open the relevant `.ino` file in the Arduino IDE.
- Upload to your board (with DAC and LED circuit connected).
- Serial output will provide CSV data for analysis.

## Documentation
See `docs/PHY 3902_LED_E_2023.pdf` for experiment details, procedures, and background theory.
Add your final report and LaTeX source to the `docs/` folder using a descriptive filename (e.g., `LED_IV_Planck_Report_v1.tex`, `LED_IV_Planck_Report_v1.pdf`).

## Version Control Best Practices
- Track source files (code, LaTeX, CSV data) in git.
- Add generated or intermediate files (e.g., out/, *.aux, *.log) to `.gitignore`.
- Only include final publishable outputs (e.g., PDF report) in version control if needed.

## Contact
For questions, contact the course instructor or lab TA.
