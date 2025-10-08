import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

V_SUPPLY = 5.0  # Supply voltage
R_FIXED = 9955  # Fixed resistor value in ohms
STEPPER_STEPS_PER_REV = 2048  # Steps per full revolution for the stepper motor
ANALOG_RESOLUTION = 1023  # 10-bit ADC resolution

# Define the path to the data files
data_dir = "../data/brewster"

def plot_brewster_angle(data_file):
    # Load the data
    data_path = os.path.join(data_dir, data_file)
    data = pd.read_csv(data_path)

    # Extract angle and intensity
    angles = 360 * data['step'] / STEPPER_STEPS_PER_REV  # Convert steps to degrees

    # Convert LDR voltage to light intensity
    # Method 1: Simple voltage-based intensity
    ldr_voltage_feedback = data['adc_mean'] * V_SUPPLY / ANALOG_RESOLUTION  # Convert ADC to voltage (0-5V range)

    # Calculate LDR resistance from voltage divider
    # V_ldr = V_SUPPLY * R_FIXED / (R_ldr + R_FIXED)
    # Solving for R_ldr: R_ldr = R_FIXED * (V_SUPPLY - ldr_voltage_feedback) / ldr_voltage_feedback
    ldr_resistance = R_FIXED * (V_SUPPLY - ldr_voltage_feedback) / ldr_voltage_feedback

    # Convert resistance to relative light intensity
    # For most LDRs: R = A * (light_intensity)^(-gamma)
    # So: light_intensity = (A/R)^(1/gamma)
    # For simplicity, use inverse relationship: I ∝ 1/R
    intensities = 1.0 / ldr_resistance
    
    # Method 2: Normalized intensity
    normalized_intensities = (ldr_voltage_feedback - ldr_voltage_feedback.min()) / (ldr_voltage_feedback.max() - ldr_voltage_feedback.min())

    # Plotting
    plt.figure(figsize=(12, 8))
    
    # Plot 1: Raw voltage
    plt.subplot(2, 2, 1)
    plt.scatter(angles, ldr_voltage_feedback, marker='o', s=3, color='blue')
    plt.title('LDR Voltage vs Angle')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Voltage (V)')
    plt.xlim(0, 360)
    plt.xticks(np.arange(0, 361, 30))
    plt.grid(True)
    
    # Plot 2: Calculated resistance
    plt.subplot(2, 2, 2)
    plt.scatter(angles, ldr_resistance, marker='o', s=3, color='green')
    plt.title('LDR Resistance vs Angle')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Resistance (Ω)')
    plt.xlim(0, 360)
    plt.xticks(np.arange(0, 361, 30))
    plt.grid(True)
    
    # Plot 3: Light intensity
    plt.subplot(2, 2, 3)
    plt.scatter(angles, intensities, marker='o', s=3, color='red')
    plt.title('Light Intensity vs Angle (Brewster Angle Measurement)')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Relative Light Intensity')
    plt.xlim(0, 360)
    plt.xticks(np.arange(0, 361, 30))
    plt.grid(True)
    # plt.axvline(x=56.3, color='r', linestyle='--', label='Theoretical Brewster Angle')
    plt.legend()
    
    # Plot 4: Normalized intensity
    plt.subplot(2, 2, 4)
    plt.scatter(angles, normalized_intensities, marker='o', s=3, color='purple')
    plt.title('Normalized Light Intensity vs Angle')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Normalized Intensity (0-1)')
    plt.xlim(0, 360)
    plt.xticks(np.arange(0, 361, 30))
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return angles, intensities

def main():
    for file in os.listdir(data_dir):
        if file.endswith('.csv'):  # Only process CSV files
            print(f"Plotting data from {file}")
            angles, intensities = plot_brewster_angle(file)
            
            # Find minimum intensity (Brewster angle)
            min_idx = np.argmin(intensities)
            brewster_angle = angles.iloc[min_idx]
            print(f"Measured Brewster angle: {brewster_angle:.1f}°")

if __name__ == "__main__":
    main()