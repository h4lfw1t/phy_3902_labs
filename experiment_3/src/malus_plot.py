import os
import pandas as pd
import matplotlib.pyplot as plt

# Define the path to the data files
data_dir = "../data/malus"

def plot_malus_law(data_file):
    # Load the data
    data_path = os.path.join(data_dir, data_file)
    data = pd.read_csv(data_path)
    
    # Extract angle and intensity
    angles = 360 * data['step'] / 2048  # Convert steps to degrees
    ldr_voltage_feedback = data['adc_mean'] * 5.0 / 1023.0  # Convert ADC to voltage (0-5V range)
    ldr_voltage_stddev = data['adc_stddev'] * 5.0 / 1023.0  # Convert ADC stddev to voltage stddev

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.errorbar(angles, ldr_voltage_feedback, yerr=ldr_voltage_stddev, label='LDR Voltage Feedback', marker='o', linestyle='None', markersize=3, color='blue', ecolor='lightgray', elinewidth=1, capsize=2)
    plt.title('Malus Law Experiment')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('LDR Voltage (V)')
    plt.grid()
    plt.legend()
    plt.show()

def main():
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            print(f"Processing file: {file}")
            plot_malus_law(file)

if __name__ == "__main__":
    main()