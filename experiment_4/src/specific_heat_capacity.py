import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from utils.data_processor import load_experiment_data, load_pid_data, find_stable_power_window, mean_output_power
from utils.specific_heat_calc import output_power_to_physical_power, calc_specific_heat

# Constants (from Arduino code)
R_heater = 15.7  # ohms
V_SUPPLY = 12.0


def get_Tset():
    try:
        Tset = float(input("Enter Tset (deg C): "))
    except Exception:
        print("Invalid input. Using default Tset=30.0")
        Tset = 30.0
    return Tset

def analyze_file(data_path, tset, m_block, plot=True):
    data = load_experiment_data(data_path)
    power = data['power(W)'].to_numpy(dtype=float)
    time = data['time(s)'].to_numpy(dtype=float)
    temp = data['temp_mean(C)'].to_numpy(dtype=float)
    tset_plus = tset + 1.0
    idx_start = np.argmax(temp >= tset)
    idx_end = np.argmax(temp >= tset_plus)
    if temp[idx_start] < tset or temp[idx_end] < tset_plus or idx_start == idx_end:
        print(f"Could not find valid temperature interval for Tset={tset} and Tset+1.")
        return None
    t_start = time[idx_start]
    t_end = time[idx_end]
    dt = t_end - t_start
    mean_power = np.mean(power[idx_start:idx_end+1])
    energy = mean_power * dt  # Joules
    if plot:
        plt.figure(figsize=(10,5))
        plt.plot(time, temp, label='Temperature')
        plt.axhline(tset, color='green', linestyle='--', label=f'Tset = {tset:.2f} C')
        plt.axhline(tset_plus, color='red', linestyle='--', label=f'Tset+1 = {tset_plus:.2f} C')
        plt.axvspan(t_start, t_end, color='orange', alpha=0.2, label='Interval')
        plt.xlabel('Time (s)')
        plt.ylabel('Temperature (C)')
        plt.title('Temperature Rise by 1 Degree')
        plt.legend()
        plt.tight_layout()
        plt.show()
    return {'energy': energy, 'dt': dt, 'mean_power': mean_power, 't_start': t_start, 't_end': t_end}

def auto_mode():
    manifest_path = os.path.join('experiment_4', 'data', 'c_data', 'manifest.json')
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    for entry in manifest:
        print(f"\n--- Analyzing {entry['filename']} at Tset={entry['Tset']} ---")
        data_path = os.path.abspath(
            os.path.join('experiment_4', 'data', 'c_data', entry['filename'])
        )
        pid_path = os.path.abspath(
            os.path.join('experiment_4', 'data', 'PID_data', entry['PID_data'])
        )
        tset = entry['Tset']
        m_block = entry['m_grams']
        # Main experiment analysis
        result = analyze_file(data_path, tset, m_block, plot=True)
        if result is None:
            continue
        # PID data analysis
        pid_df = load_pid_data(pid_path)
        start_idx, end_idx = find_stable_power_window(pid_df, tset, window=30, tol=0.2)
        if start_idx is None:
            print(f"No stable window found near Tset={tset} in PID data.")
            continue
        avg_output_power = mean_output_power(pid_df, start_idx, end_idx)
        avg_physical_power = output_power_to_physical_power(avg_output_power, v_supply=V_SUPPLY, r_heater=R_heater)
        print(f"Stable PID output_power: {avg_output_power:.2f} (0-255), Physical Power: {avg_physical_power:.3f} W")
        # Specific heat calculation
        c = calc_specific_heat(result['energy'], m_block, delta_t=1.0)
        print(f"Specific heat capacity: {c:.3f} J/(g*C)")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'auto':
        auto_mode()
    else:
        # Interactive/manual mode (original behavior)
        m_block = 24.63  # grams (default)
        Tset = get_Tset()
        analyze_file('experiment_4/data/c_data/specific_heat_capacity_data_aluminium.csv', Tset, m_block, plot=True)

if __name__ == "__main__":
    main()
