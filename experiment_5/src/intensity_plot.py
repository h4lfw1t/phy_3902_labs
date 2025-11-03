import json
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass

@dataclass
class IntensityConfig:
    DATA_DIR: str = os.path.abspath(
        os.path.join("..", "data", "intensity_data")
    )
    R_SERIES: float = 9970     # Resistance in ohms
    V_IN: float = 5.0          # Input voltage
    RESOLUTION: int = 1023     # ADC resolution

CONSTANTS = IntensityConfig()

def plot_intensity(data_file, output_file):
    # Read the data from CSV file
    data = pd.read_csv(data_file)

    # Extract position and intensity columns
    position = data['position']
    intensity = data['ldr_mean']
    intensity_error = data['ldr_stddev']

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        position,
        intensity,
        yerr=intensity_error,
        marker='o',
        color='b',
    )
    plt.title('Intensity vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('Intensity (units)')
    plt.grid(True)

    # Save the plot to a file
    plt.savefig(output_file)
    plt.close()

def adc_to_intensity(adc_values, v_in, r_series, resolution):
    """Convert ADC values to intensity using voltage divider formula."""
    voltages = adc_values * v_in / resolution
    r_ldr = r_series * (v_in - voltages) / voltages
    intensities = 1 / r_ldr  # For intensity ∝ 1 / R_LDR
    return intensities