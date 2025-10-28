import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Constants (from Arduino code)
m_block = 24.63  # grams
dm_block = 0.005
R_heater = 15.7  # ohms
dR_heater = 0.1

# Load data
data = pd.read_csv(r'../data/specific_heat_capacity_data.csv')

# Find regions of constant heating/cooling by looking for changes in power
power = data['power(W)'].to_numpy(dtype=float)
time = data['time(s)'].to_numpy(dtype=float)
temp = data['temp_mean(C)'].to_numpy(dtype=float)

# Identify indices where power switches between ~0 and >0 (heating/cooling transitions)
transitions = np.where(np.abs(np.diff(power)) > 0.1)[0] + 1
regions = []
start = 0
for idx in transitions:
	regions.append((start, idx))
	start = idx
regions.append((start, len(data)))

# For each region, if power is nonzero (heating), fit dT/dt and calculate c
results = []
for i, (start, end) in enumerate(regions):
	region_power = float(np.mean(power[start:end]))
	if region_power < 0.1:
		continue  # skip cooling/zero-power
	t = np.array(time[start:end], dtype=float)
	T = np.array(temp[start:end], dtype=float)
	# Linear fit to T vs t
	slope, intercept, r, p, stderr = linregress(t, T)
	dTdt = slope
	# c = P / (m * dT/dt)
	# If dTdt is a tuple, extract the first element
	if isinstance(dTdt, tuple):
		dTdt_val = dTdt[0]
	else:
		dTdt_val = dTdt
	# Try to convert to float robustly
	dTdt_val = float(np.asarray(dTdt_val).flatten()[0])
	c = region_power / (float(m_block) * dTdt_val)
	results.append({
		'region': i+1,
		'start_time': float(t[0]),
		'end_time': float(t[-1]),
		'mean_power': region_power,
		'dTdt': dTdt,
		'c': c
	})

# Print results
for res in results:
	print(f"Region {res['region']}: t={res['start_time']:.1f}-{res['end_time']:.1f} s, "
		  f"P={res['mean_power']:.3f} W, dT/dt={res['dTdt']:.5f} C/s, c={res['c']*1000:.1f} J/kg/K")

# Optionally, plot T vs t and mark regions
plt.figure(figsize=(10,5))
plt.plot(np.array(time, dtype=float), np.array(temp, dtype=float), label='Temperature')
for res in results:
	plt.axvspan(res['start_time'], res['end_time'], color='orange', alpha=0.2)
plt.xlabel('Time (s)')
plt.ylabel('Temperature (C)')
plt.title('Specific Heat Capacity Heating Regions')
plt.legend()
plt.tight_layout()
plt.show()
