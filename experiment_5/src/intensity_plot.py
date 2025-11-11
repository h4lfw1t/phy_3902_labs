import json
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import label as sc_label
from dataclasses import dataclass
from utils import DataProcessing

@dataclass
class IntensityConfig:
    DATA_DIR: str = os.path.abspath(
        os.path.join("..", "data", "intensity_data")
    )
    OUT_DIR = os.path.abspath(
        os.path.join("..", "out", "intensity_plots")
    )
    R_SERIES: float = 9970     # Resistance in ohms
    V_IN: float = 5.0          # Input voltage
    RESOLUTION: int = 1023     # ADC resolution

CONSTANTS = IntensityConfig()

data_proc = DataProcessing()

def find_fringe_regions(intensity, threshold=0.1):
    """
    Identify regions corresponding to interference fringes.

    Args:
        intensity: Array of intensity values.
        threshold: Fractional threshold above background to define a fringe.

    Returns:
        List of (start_idx, end_idx) tuples for each fringe region.
    """
    # Estimate background as median intensity
    background = np.median(intensity)
    # Find indices where intensity is significantly above background
    fringe_mask = intensity > (background + threshold * (intensity.max() - background))
    # Group contiguous indices
    labeled, num_features = sc_label(fringe_mask)
    regions = []
    for i in range(1, num_features + 1):
        indices = np.where(labeled == i)[0]
        if len(indices) > 0:
            regions.append((indices[0], indices[-1]))
    return regions

def log_fringe_regions(regions):
    for start, end in regions:
        center = (start + end) // 2
        print(f"Fringe region from index {start} to {end}. Center at index {center}.")

def plot_intensity(data_file, output_file):
    # Read the data from CSV file
    data_path = os.path.join(CONSTANTS.DATA_DIR, data_file)
    output_file = os.path.join(CONSTANTS.OUT_DIR, output_file)
    data = pd.read_csv(data_path)

    # Extract position and intensity columns
    position = data_proc.steps_to_linear_position(data['position'], max_steps=1800, linear_scale=0.05)
    intensity, intensity_error = data_proc.intensity_with_error(
        data['ldr_mean'],
        data['ldr_stddev']
    )

    # Detect center fringe
    center_fringe_regions = find_fringe_regions(
        intensity,
        threshold=0.1,
    )
    # Detect outer fringes
    outer_fringe_regions = find_fringe_regions(
        intensity,
        threshold=0.002,
    )

    # Filter overlapping regions
    def is_outside(center, outer):
        for c_start, c_end in center:
            if not (outer[1] < c_start or outer[0] > c_end):
                return False
        return True

    filtered_outer = [r for r in outer_fringe_regions if is_outside(center_fringe_regions, r)]

    # Align position so center fringe is at 0
    if center_fringe_regions:
        position = data_proc.align_center_fringe(position, center_fringe_regions[0])

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
    log_fringe_regions(fringe_regions)

    def assign_fringe_numbers(position, center_fringe_region, outer_fringe_regions):
        """
        Assigns fringe numbers to each outer fringe relative to the center.
        Returns a list of (fringe_number, region) tuples.
        """
        center_idx = (center_fringe_region[0] + center_fringe_region[1]) // 2
        center_pos = position[center_idx]
        numbered = []
        # Calculate center positions for each outer fringe
        outer_centers = [((start + end) // 2, (start, end)) for start, end in outer_fringe_regions]
        # Sort by position relative to center
        outer_centers.sort(key=lambda x: position[x[0]] - center_pos)
        left = [r for i, r in outer_centers if position[i] < center_pos]
        right = [r for i, r in outer_centers if position[i] > center_pos]
        # Assign negative numbers to left, positive to right
        for n, region in enumerate(reversed(left), 1):
            numbered.append((-n, region))
        for n, region in enumerate(right, 1):
            numbered.append((n, region))
        return numbered

    fringe_numbered = assign_fringe_numbers(position, center_fringe_regions[0], filtered_outer)
    print("Fringe numbers and regions:")
    for number, (start, end) in fringe_numbered:
        print(f"  Fringe {number}: {start} to {end}")

    # Use get_fringe_distance for all outer fringes
    if center_fringe_regions:
        fringe_distances = data_proc.get_fringe_distance(position, center_fringe_regions[0], [region for _, region in fringe_numbered])
        for (num, region), fringe_distance in zip(fringe_numbered, fringe_distances):
            wavelength = data_proc.calculate_wavelength(
                abs(num),
                fringe_distance,
                1 / 527559,  # Diffraction grating spacing in meters
                setup_length=0.05  # Setup length in meters
            )
            print(f"  Fringe {num}: Distance = {fringe_distance:.6g} m, Wavelength = {wavelength:.6g} nm")

    plt.title('LDR Feedback vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('LDR Value')
    plt.grid(True)
    plt.legend()

    # Save the plot to a file
    os.makedirs(CONSTANTS.OUT_DIR, exist_ok=True)
    print(f"Saving plot to {output_file}")
    plt.savefig(output_file)
    plt.show()
    plt.close()

def plot_gradient(data_file):
    # Read the data from CSV file
    data_path = os.path.join(CONSTANTS.DATA_DIR, data_file)
    # output_path = os.path.join(CONSTANTS.OUT_DIR, output_file)
    data = pd.read_csv(data_path)

    # Extract position and intensity columns using data processing module
    position = data_proc.steps_to_linear_position(data['position'], max_steps=1800, linear_scale=0.05)
    intensity, intensity_error = data_proc.intensity_with_error(
        data['ldr_mean'],
        data['ldr_stddev']
    )

    # Calculate gradient
    gradient = np.gradient(intensity, position)
    gradient_error = np.gradient(intensity_error, position)

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        position,
        gradient,
        yerr=abs(gradient_error),
        label="LDR Gradient",
        color='blue',
        markersize=2,
        fmt='o',
        ecolor='lightblue',
        elinewidth=1,
        capsize=2,
    )
    plt.title('LDR Gradient vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('LDR Gradient')
    plt.grid(True)
    plt.legend()

    # Save the plot to a file
    # plt.savefig(output_path)
    plt.show()
    plt.close()

if __name__ == "__main__":
    # Allow CLI usage: python intensity_plot.py <csv_file> [output_file] [auto]
    auto = False
    fname = None
    output_file = None
    default_output_file = lambda fname: os.path.splitext(fname)[0] + "_intensity.png"

    if len(sys.argv) > 1:
        # Check if 'auto' is present as an argument
        if any(arg.lower() == "auto" for arg in sys.argv[1:]):
            auto = True
        else:
            fname = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else default_output_file(fname)
    else:
        # Prompt for file name or auto
        mode = input("Enter 'auto' to plot all from manifest, or press Enter for manual: ").strip().lower()
        if mode == "auto":
            auto = True
        else:
            fname = mode if mode else input("File name: ")
            output_file = input("Output file (optional, press Enter to skip): ")
            if not output_file:
                output_file = default_output_file(fname)

    if auto:
        # Load manifest.json and run plot_intensity for each entry
        manifest_path = os.path.join(CONSTANTS.DATA_DIR, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for entry in manifest:
            fname = entry.get("filename")
            output_file = default_output_file(fname)
            print(f"Plotting {fname} . . .")
            plot_intensity(fname, output_file)
            # plot_gradient(fname)
    else:
        plot_intensity(fname, output_file)
