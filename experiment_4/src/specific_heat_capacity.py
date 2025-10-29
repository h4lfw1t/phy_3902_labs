import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Constants (from Arduino code)
m_block = 24.63  # grams
dm_block = 0.005
R_heater = 15.7  # ohms
dR_heater = 0.1

# Load data
data = pd.read_csv(r'../data/specific_heat_capacity_data.csv')
power = data['power(W)'].to_numpy(dtype=float)
time = data['time(s)'].to_numpy(dtype=float)
temp = data['temp_mean(C)'].to_numpy(dtype=float)


def get_Tset():
	try:
		Tset = float(input("Enter Tset (deg C): "))
	except Exception:
		print("Invalid input. Using default Tset=30.0")
		Tset = 30.0
	return Tset

if __name__ == "__main__":
	Tset = get_Tset()
	Tset_plus = Tset + 1.0

	# Find indices where temp crosses Tset and Tset+1
	idx_start = np.argmax(temp >= Tset)
	idx_end = np.argmax(temp >= Tset_plus)

	if temp[idx_start] < Tset or temp[idx_end] < Tset_plus or idx_start == idx_end:
		print("Could not find valid temperature interval for Tset and Tset+1.")
		sys.exit(1)

	t_start = time[idx_start]
	t_end = time[idx_end]
	dt = t_end - t_start
	# Mean power during this interval
	mean_power = np.mean(power[idx_start:idx_end+1])
	energy = mean_power * dt  # Joules

	print(f"Tset: {Tset:.2f} C to {Tset_plus:.2f} C")
	print(f"Time interval: {t_start:.2f} s to {t_end:.2f} s (dt = {dt:.2f} s)")
	print(f"Mean power: {mean_power:.3f} W")
	print(f"Energy required to raise 1 deg: {energy:.2f} J")

	# Plot
	plt.figure(figsize=(10,5))
	plt.plot(time, temp, label='Temperature')
	plt.axhline(Tset, color='green', linestyle='--', label=f'Tset = {Tset:.2f} C')
	plt.axhline(Tset_plus, color='red', linestyle='--', label=f'Tset+1 = {Tset_plus:.2f} C')
	plt.axvspan(t_start, t_end, color='orange', alpha=0.2, label='Interval')
	plt.xlabel('Time (s)')
	plt.ylabel('Temperature (C)')
	plt.title('Temperature Rise by 1 Degree')
	plt.legend()
	plt.tight_layout()
	plt.show()
