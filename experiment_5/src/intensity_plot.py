import json
from utils import DataProcessing, FringeAnalysis
from dataclasses import dataclass
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os


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


def plot_intensity(data_file, output_file, manifest):
    output_file = os.path.join(CONSTANTS.OUT_DIR, output_file)
    data_path = os.path.join(CONSTANTS.DATA_DIR, data_file)
    if not os.path.exists(data_path):
        print(f"{YELLOW}Warning: Data file not found: {data_file}{RESET}")
        return
    data = pd.read_csv(data_path)
    manifest_entry = manifest.get(data_file, {})
    if not manifest_entry:
        print(f"{YELLOW}Warning: No manifest entry found for {data_file}.{RESET}")
        return

    analyzer = FringeAnalysis(
        fringe_min_width=IntensityConfig.FRINGE_MIN_WIDTH)
    analyzer.analyze(data, manifest_entry, data_proc, CONSTANTS)

    baseline_info = manifest_entry.get("baseline", None)
    is_baseline = False
    parent_baseline_name = None
    baseline_analyzer = None
    if baseline_info:
        parent_baseline_name = baseline_info.get("name")
        is_baseline = baseline_info.get("parent", False)
        if not is_baseline:
            # Find parent baseline file in manifest
            parent_file = None
            for fname, entry in manifest.items():
                binfo = entry.get("baseline", {})
                if binfo.get("name") == parent_baseline_name and binfo.get("parent", False):
                    parent_file = fname
                    break
            if parent_file:
                baseline_data_path = os.path.join(
                    CONSTANTS.DATA_DIR, parent_file)
                if os.path.exists(baseline_data_path):
                    baseline_data = pd.read_csv(baseline_data_path)
                    baseline_manifest_entry = manifest.get(parent_file, {})
                    baseline_analyzer = FringeAnalysis(
                        fringe_min_width=IntensityConfig.FRINGE_MIN_WIDTH)
                    baseline_analyzer.analyze(
                        baseline_data, baseline_manifest_entry, data_proc, CONSTANTS)
                    analyzer.analyze_baseline_child(
                        baseline_analyzer, analyzer, manifest_entry, CONSTANTS)

    plt.figure(figsize=(10, 6))
    plt.errorbar(
        analyzer.position,
        analyzer.intensity,
        yerr=analyzer.intensity_error,
        label="LDR Feedback",
        color='magenta',
        markersize=2,
        fmt='o',
        ecolor='thistle',
        elinewidth=1,
        capsize=2,
    )

    fringe_regions = analyzer.center_fringe_regions + analyzer.filtered_outer
    for start_idx, end_idx in fringe_regions:
        plt.axvspan(
            analyzer.position[start_idx],
            analyzer.position[end_idx],
            color='yellow',
            alpha=0.3,
            label='Fringe Region' if start_idx == fringe_regions[0][0] else None,
        )

    summary = analyzer.summarize_fringe_analysis()
    print(f"{CYAN}--- Intensity Plot Summary for {data_file} ---{RESET}\nNotes: {analyzer.notes}\n{summary}\n")

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
