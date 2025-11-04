import json
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import sympy as sp
from dataclasses import dataclass
from utils import ErrorPropagation

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
    position = step_to_linear_position(data['position'], max_steps=2048, linear_scale=0.05)
    intensity, intensity_error = intensity_with_error(
        data['ldr_mean'],
        data['ldr_stddev'],
        CONSTANTS.V_IN,
        CONSTANTS.R_SERIES,
        CONSTANTS.RESOLUTION
    )

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        position,
        data['ldr_mean'],   # intensity,
        yerr=data['ldr_stddev'],  # intensity_error,
        label="LDR Feedback",
        color='magenta',
        markersize=2,
        fmt='o',
        ecolor='thistle',
        elinewidth=1,
        capsize=2,
    )
    plt.title('LDR Feedback vs Position')
    plt.xlabel('Position (m)')
    plt.ylabel('LDR Value')
    plt.grid(True)

    # Save the plot to a file
    plt.savefig(output_file)
    plt.show()
    plt.close()

def intensity_with_error(adc_values, adc_stddev, v_in, r_series, resolution):
    """Return intensity and propagated error from ADC values and stddev."""
    adc = sp.Symbol('adc')
    v_ldr = adc * v_in / resolution
    r_ldr = r_series * (v_in - v_ldr) / v_ldr
    intensity_expr = 1 / r_ldr

    # Calculate intensity values
    voltages = adc_values * v_in / resolution
    r_ldr_vals = r_series * (v_in - voltages) / voltages
    intensities = 1 / r_ldr_vals

    # Calculate propagated errors
    intensity_errors = []
    for val, std in zip(adc_values, adc_stddev):
        values = {adc: val}
        uncertainties = {adc: std}
        err = ErrorPropagation.propagate_error(intensity_expr, [adc], values, uncertainties)
        intensity_errors.append(err)

    return intensities, intensity_errors

def step_to_linear_position(step_counts, max_steps, linear_scale):
    """Convert step counts to linear position using a scale factor."""
    return (step_counts / max_steps) * linear_scale

if __name__ == "__main__":
    data_file = os.path.join(CONSTANTS.DATA_DIR, "sample.csv")
    output_file = os.path.join(CONSTANTS.DATA_DIR, "sample.png")
    plot_intensity(data_file, output_file)