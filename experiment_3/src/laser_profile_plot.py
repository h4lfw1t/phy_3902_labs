# Import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

CONSTANTS = {
    "V_SUPPLY": 5.0,  # Supply voltage in volts
    "R_FIXED": 9955,  # Fixed resistor value in ohms, not used in current calculations
    "ANALOG_RESOLUTION": 1023, # 10-bit ADC resolution
}
DATA_PATH = '../data/laser_profile/laser_profile.csv'


def load_data(path):
    """Load CSV data and return DataFrame."""
    return pd.read_csv(path, index_col=False)


def calculate_intensity(df):
    """Calculate intensity and its standard deviation from LDR readings."""
    ldr_voltage = df['ldr_mean'] * CONSTANTS["V_SUPPLY"] / CONSTANTS["ANALOG_RESOLUTION"]
    ldr_voltage_stddev = df['ldr_stddev'] * CONSTANTS["V_SUPPLY"] / CONSTANTS["ANALOG_RESOLUTION"]
    intensity = 1 / ldr_voltage
    intensity_stddev = ldr_voltage_stddev / (ldr_voltage ** 2)
    result_df = pd.DataFrame({
        'position': df['position'],
        'intensity': intensity,
        'intensity_stddev': intensity_stddev
    })
    return result_df


def plot_laser_profile(intensity_df):
    """Plot intensity and its derivative in subplots."""
    # Sort by position
    sorted_df = intensity_df.sort_values('position')
    positions = sorted_df['position'].values
    intensities = sorted_df['intensity'].values
    intensities_stddev = sorted_df['intensity_stddev'].values

    # Calculate derivative
    intensity_derivative = np.gradient(intensities, positions)

    # Create subplots
    fig, axes = plt.subplots(2, 1, figsize=(8, 10), sharex=True)

    # Intensity plot
    axes[0].errorbar(positions, intensities, yerr=intensities_stddev, fmt='o', ecolor='red', capsize=3, label='Intensity')
    axes[0].set_ylabel('Intensity (1/V)')
    axes[0].set_title('Laser Profile: Position vs Intensity')
    axes[0].legend()
    axes[0].grid(True)

    # Derivative plot
    axes[1].plot(positions, intensity_derivative, marker='o', label='d(Intensity)/d(Position)')
    axes[1].set_xlabel('Position (degrees)')
    axes[1].set_ylabel('Derivative of Intensity')
    axes[1].set_title('Derivative of Laser Profile (True Intensity Distribution)')
    axes[1].legend()
    axes[1].grid(True)

    # Set x-ticks to increments of 5
    min_pos = positions.min()
    max_pos = positions.max()
    xticks = np.arange(min_pos, max_pos + 1, 5)
    axes[1].set_xticks(xticks)
    axes[0].set_xticks(xticks)

    plt.tight_layout()
    # Ensure output directory exists
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../out'))
    os.makedirs(out_dir, exist_ok=True)
    # Save plot to out directory
    out_path = os.path.join(out_dir, 'laser_profile_plot.png')
    plt.savefig(out_path)
    plt.show()


def main():
    df = load_data(DATA_PATH)
    intensity_df = calculate_intensity(df)
    plot_laser_profile(intensity_df)


if __name__ == "__main__":
    main()
