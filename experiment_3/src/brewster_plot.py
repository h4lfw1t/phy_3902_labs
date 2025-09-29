import os
import pandas as pd
import matplotlib.pyplot as plt

# Define the path to the data files
data_dir = "../data/brewster"

def plot_brewster_angle(data_file):
    # Load the data
    data_path = os.path.join(data_dir, data_file)
    data = pd.read_csv(data_path)

    # Extract angle and intensity
    angles = data['step']
    intensities = data['adc_mean']

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(angles, intensities, marker='o', linestyle='-')
    plt.title('Brewster Angle Measurement')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Intensity (a.u.)')
    plt.axvline(x=56.3, color='r', linestyle='--', label='Theoretical Brewster Angle')
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    for file in os.listdir(data_dir):
        if file:
            print(f"Plotting data from {file}")
            plot_brewster_angle(file)

if __name__ == "__main__":
    main()