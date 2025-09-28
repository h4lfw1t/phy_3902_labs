# PHY 3902 Arduino-Based Physics Experiments

This repository contains a collection of physics laboratory experiments built around a shared Arduino-based measurement and control platform. Each experiment investigates different physical phenomena using custom hardware setups, automated data collection, and Python-based analysis.

## Repository Structure

- **experiment_X/**: Each experiment is organized in its own folder (e.g., `experiment_2`).
  - **data/**: Raw and processed data files (CSV, etc.).
  - **docs/**: Experiment-specific documentation and lab manuals.
  - **src/**: Python analysis scripts and Arduino code (`.ino` files) for hardware control and data acquisition.
  - **notebooks/**: (Optional) Jupyter notebooks for interactive analysis.
  - **README.md**: Details and instructions specific to the experiment.
- **pyproject.toml**, **poetry.lock**: Python dependency management (Poetry).
- **README.md** (this file): General project overview and setup instructions.

## Getting Started

### Prerequisites
- Python 3.x
- Poetry (for Python dependency management)
- Arduino IDE (for uploading `.ino` files)

### Python Environment Setup
1. Install Poetry if not already installed: https://python-poetry.org/docs/#installation
2. Install dependencies:
   ```cmd
   poetry install
   ```
3. Run analysis scripts for each experiment as described in their respective README files.

### Arduino Platform Setup
- Open the relevant `.ino` file in the Arduino IDE (see each experiment's `src/` folder).
- Upload to your Arduino board with the required hardware setup.
- Use the serial output for data collection and analysis.

## Adding New Experiments
- Create a new folder (e.g., `experiment_3`) following the structure above.
- Include a dedicated README in each experiment folder with specific instructions.
- Reuse and extend the Arduino platform and Python analysis tools as needed.

## Documentation
- See each experiment's `docs/` folder and README for details, procedures, and background theory.

## Contact
Nah, actually don't.

