import json
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import label as sc_label
from dataclasses import dataclass
# from utils import DataProcessing
from data_processor import DataProcessor

@dataclass
class IntensityConfig:
    DATA_DIR: str = os.path.abspath(
        os.path.join("..", "data", "intensity_data")
    )
    R_SERIES: float = 9970     # Resistance in ohms
    V_IN: float = 5.0          # Input voltage
    RESOLUTION: int = 1023     # ADC resolution

CONSTANTS = IntensityConfig()

data_proc = DataProcessor()

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
    data = pd.read_csv(data_file)

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
        threshold=0.025,
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

    # Print distance between fringes
    fringe_distances = data_proc.get_fringe_distance(position, center_fringe_regions[0], filtered_outer) if center_fringe_regions else []
    print(f"Fringe distances from center: {fringe_distances}")

    plt.title('LDR Feedback vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('LDR Value')
    plt.grid(True)
    plt.legend()

    # Save the plot to a file
    plt.savefig(output_file)
    plt.show()
    plt.close()

def plot_gradient(data_file, output_file):
    # Read the data from CSV file
    data = pd.read_csv(data_file)

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
    plt.savefig(output_file)
    plt.show()
    plt.close()

if __name__ == "__main__":
    data_file = os.path.join(CONSTANTS.DATA_DIR, "sample.csv")
    output_file = os.path.join(CONSTANTS.DATA_DIR, "sample.png")
    gradient_output_file = os.path.join(CONSTANTS.DATA_DIR, "sample_gradient.png")
    plot_intensity(data_file, output_file)
    # plot_gradient(data_file, gradient_output_file)
