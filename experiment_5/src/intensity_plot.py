import json
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass
from utils import DataProcessing, FringeAnalysis


@dataclass
class IntensityConfig:
    DATA_DIR: str = os.path.abspath(
        os.path.join("..", "data", "intensity_data")
    )
    OUT_DIR = os.path.abspath(
        os.path.join("..", "out", "intensity_plots")
    )
    MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")
    R_SERIES: float = 9970                  # Resistance in ohms
    V_IN: float = 5.0                       # Input voltage
    RESOLUTION: int = 1023                  # ADC resolution
    DIFFRACTION_GRATING: float = 527559     # lines per meter
    # Minimum width of fringe region in data points
    FRINGE_MIN_WIDTH: int = 10
    CENTER_FRINGE_THRESHOLD: float = 0.1    # Threshold for center fringe detection
    OUTER_FRINGE_THRESHOLD: float = 0.0025   # Threshold for outer fringe detection


CYAN = '\033[96m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

CONSTANTS = IntensityConfig()

data_proc = DataProcessing()


fringe_analyzer = FringeAnalysis(
    fringe_min_width=IntensityConfig.FRINGE_MIN_WIDTH)


def plot_intensity(data_file, output_file, manifest):
    # Read the data from CSV file
    data_path = os.path.join(CONSTANTS.DATA_DIR, data_file)
    output_file = os.path.join(CONSTANTS.OUT_DIR, output_file)
    data = pd.read_csv(data_path)
    manifest_entry = manifest.get(data_file, {})
    if not manifest_entry:
        print(f"{YELLOW}Warning: No manifest entry found for {data_file}.{RESET}")
        return

    # Extract relevant information from the manifest entry
    vacuum_wavelength = manifest_entry.get("wavelength", 650e-9)
    setup_length = manifest_entry.get("setup_length", 0.045)
    notes = manifest_entry.get("notes", "")

    # Extract position and intensity columns
    position = data_proc.steps_to_linear_position(
        data['position'], max_steps=1800, linear_scale=0.05)
    intensity, intensity_error = data_proc.intensity_with_error(
        data['ldr_mean'],
        data['ldr_stddev']
    )

    # Detect center and outer fringes
    center_fringe_regions = fringe_analyzer.find_fringe_regions(
        intensity, threshold=CONSTANTS.CENTER_FRINGE_THRESHOLD,)
    outer_fringe_regions = fringe_analyzer.find_fringe_regions(
        intensity, threshold=CONSTANTS.OUTER_FRINGE_THRESHOLD,)

    # Filter overlapping regions
    def is_outside(center, outer):
        for c_start, c_end in center:
            if not (outer[1] < c_start or outer[0] > c_end):
                return False
        return True
    filtered_outer = [r for r in outer_fringe_regions if is_outside(
        center_fringe_regions, r)]

    # Align position so center fringe is at 0
    if center_fringe_regions:
        position = data_proc.align_center_fringe(
            position, center_fringe_regions[0])

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        position,
        intensity,
        yerr=intensity_error,
        label="LDR Feedback",
        color='magenta',
        markersize=2,
        fmt='o',
        ecolor='thistle',
        elinewidth=1,
        capsize=2,
    )

    # Highlight fringe regions
    fringe_regions = center_fringe_regions + filtered_outer
    for start_idx, end_idx in fringe_regions:
        plt.axvspan(
            position[start_idx],
            position[end_idx],
            color='yellow',
            alpha=0.3,
            label='Fringe Region' if start_idx == fringe_regions[0][0] else None,
        )

    # Fringe numbering and analysis
    fringe_numbered = fringe_analyzer.assign_fringe_numbers(
        position, center_fringe_regions[0], filtered_outer) if center_fringe_regions else []

    # Use get_fringe_distance for all outer fringes
    fringe_distances = []
    refractive_indices = []
    wavelengths = []
    if center_fringe_regions:
        fringe_distances = data_proc.get_fringe_distance(
            position,
            center_fringe_regions[0],
            [region for _, region in fringe_numbered],
        )
        for (num, _), fringe_distance in zip(fringe_numbered, fringe_distances):
            wl = data_proc.calculate_wavelength(
                abs(num),
                fringe_distance,
                1 / CONSTANTS.DIFFRACTION_GRATING,
                setup_length=setup_length,
            )
            n = data_proc.calculate_refractive_index(
                fringe_distance,
                1 / CONSTANTS.DIFFRACTION_GRATING,
                vacuum_wavelength,
                setup_length=setup_length,
            )
            wavelengths.append(wl * 1e9)  # Convert to nm for summary
            refractive_indices.append(n)

    # Consolidated summary print
    summary = fringe_analyzer.summarize_fringe_analysis(
        position,
        center_fringe_regions,
        filtered_outer,
        fringe_numbered,
        fringe_distances,
        wavelengths,
        refractive_indices,
        vacuum_wavelength
    )
    print(
        f"{CYAN}--- Intensity Plot Summary for {data_file} ---{RESET}\nNotes: {notes}\n{summary}\n")

    plt.title('LDR Feedback vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('LDR Value')
    plt.grid(True)
    plt.legend()

    os.makedirs(CONSTANTS.OUT_DIR, exist_ok=True)
    plt.savefig(output_file)
    plt.show()
    plt.close()


if __name__ == "__main__":
    # Allow CLI usage: python intensity_plot.py <csv_file> [output_file] [auto]
    auto = False
    fname = None
    output_file = None

    # Load manifest.json and run plot_intensity for each entry
    with open(CONSTANTS.MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    def default_output_file(fname): return os.path.splitext(fname)[
        0] + "_intensity.png"

    if len(sys.argv) > 1:
        # Check if 'auto' is present as an argument
        if any(arg.lower() == "auto" for arg in sys.argv[1:]):
            auto = True
        else:
            fname = sys.argv[1]
            output_file = sys.argv[2] if len(
                sys.argv) > 2 else default_output_file(fname)
    else:
        # Prompt for file name or auto
        mode = input(
            "Enter 'auto' to plot all from manifest, or press Enter for manual: ").strip().lower()
        if mode == "auto":
            auto = True
        else:
            fname = mode if mode else input("File name: ")
            output_file = input(
                "Output file (optional, press Enter to skip): ")
            if not output_file:
                output_file = default_output_file(fname)

    if auto:
        for fname in manifest.keys():
            output_file = default_output_file(fname)
            plot_intensity(fname, output_file, manifest)
    else:
        plot_intensity(fname, output_file, manifest)
