import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def plot_temperature_data(file_name: str):
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.isfile(file_path):
        print(f"Data file {file_path} does not exist.")
        return

    data = pd.read_csv(file_path)
    if 'Elapsed_time_(sec)' not in data.columns or 'Measured_temperature_(C)' not in data.columns:
        print("Data file must contain 'Elapsed_time_(sec)' and 'Measured_temperature_(C)' columns.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(data['Elapsed_time_(sec)'], data['Measured_temperature_(C)'], label='Temperature (°C)', color='orange')
    plt.title('Temperature vs Time')
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_temperature_data('setup_temp.csv')