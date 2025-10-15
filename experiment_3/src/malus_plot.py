import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt

# Define the path to the data files
data_dir = "../data/malus"

CONSTANTS = {
    "V_SUPPLY": 5.0,  # Supply voltage in volts
    "R_FIXED": 9955,  # Fixed resistor value in ohms
    "STEPPER_STEPS_PER_REV": 2048,  # Steps per revolution for the stepper motor
    "ANALOG_RESOLUTION": 1023, # 10-bit ADC resolution
}

def plot_malus_law(data_file):
    # Load the data
    data_path = os.path.join(data_dir, data_file)
    data = pd.read_csv(data_path)
    
    # Extract angle and intensity data
    angles = 360 * data['step'] / CONSTANTS["STEPPER_STEPS_PER_REV"]  # Convert steps to degrees
    ldr_voltage_feedback = data['adc_mean'] * CONSTANTS["V_SUPPLY"] / CONSTANTS["ANALOG_RESOLUTION"]  # Convert ADC to voltage (0-5V range)
    ldr_voltage_stddev = data['adc_stddev'] * CONSTANTS["V_SUPPLY"] / CONSTANTS["ANALOG_RESOLUTION"]  # Convert ADC stddev to voltage stddev

    # Find index of first maximum
    first_max_idx = np.argmax(ldr_voltage_feedback)

    # Roll arrays so first maximum is at index 0
    angles = np.roll(angles, -first_max_idx)
    ldr_voltage_feedback = np.roll(ldr_voltage_feedback, -first_max_idx)
    ldr_voltage_stddev = np.roll(ldr_voltage_stddev, -first_max_idx)

    # Shift angles so that first maximum is at 0 and wrap around
    angles = angles - angles[0]
    angles = np.mod(angles, 360)

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.errorbar(angles, ldr_voltage_feedback, yerr=ldr_voltage_stddev, label='LDR Voltage Feedback', marker='o', linestyle='None', markersize=3, color='blue', ecolor='lightgray', elinewidth=1, capsize=2)
    plt.title("Malus' Law: Angle vs LDR Voltage")
    plt.xlabel('Angle (degrees)')
    plt.ylabel('LDR Voltage (V)')
    plt.xticks(np.arange(0, 361, 30))
    plt.grid()
    plt.legend()
    # Ensure output directory exists
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../out'))
    os.makedirs(out_dir, exist_ok=True)
    # Save plot to out directory
    out_path = os.path.join(out_dir, f"malus_plot_{os.path.splitext(data_file)[0]}.png")
    plt.savefig(out_path)
    plt.show()

def main():
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            print(f"Processing file: {file}")
            plot_malus_law(file)

if __name__ == "__main__":
    main()