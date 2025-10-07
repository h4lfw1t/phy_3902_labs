# Import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

R = 9955  # Fixed resistor value in ohms (adjust based on your circuit)

# Load the CSV data
data_path = '../data/laser_profile/laser_profile.csv'
df = pd.read_csv(data_path, index_col=False)

# Extract columns
position = df['position']
ldr_mean = df['ldr_mean']
ldr_stddev = df['ldr_stddev']

ldr_voltage_feedback = df['ldr_mean'] * 5.0 / 1023.0
ldr_voltage_stddev = df['ldr_stddev'] * 5.0 / 1023.0

intensities = 1 / ldr_voltage_feedback
intensities_stddev = ldr_voltage_stddev / (ldr_voltage_feedback ** 2)

intensities_df = pd.DataFrame({
    'position': df['position'],
    'intensity': intensities,
    'intensity_stddev': intensities_stddev
})
# intensities_df.to_csv('../data/laser_profile_intensity.csv', index=False)

# intensities_limited = intensities_df.drop(intensities_df[intensities_df['position'] > 60].index)
intensities_limited = intensities_df

# print(df_limited)
intensities_limited_position = df['position']
intensities_limited_mean = intensities_limited['intensity']
intensities_limited_stddev = intensities_limited['intensity_stddev']

# min_intensity_value = intensities_limited_mean.min()
# min_intensity_index = intensities_limited_mean.idxmin()
# print(f"Minimum Intensity: {min_intensity_value} at Position: {intensities_limited_position[min_intensity_index]}")

# max_intensity_value = intensities_limited_mean.max()
# print(f"Maximum Intensity: {max_intensity_value} at Position: {intensities_limited_position[intensities_limited_mean.idxmax()]}")

# Plot with error bars
plt.errorbar(intensities_limited_position, intensities_limited_mean, yerr=intensities_limited_stddev, fmt='o', ecolor='red', capsize=3, label='Intensity')
plt.xlim(intensities_limited_position[intensities_limited_mean.idxmax()], intensities_limited_position[intensities_limited_mean.idxmin()])
plt.xlabel('Position (degrees)')
plt.ylabel('Intensity (1/V)')
plt.title('Laser Profile: Position vs Intensity')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Ensure data is sorted by position
df_limited_sorted = intensities_limited.sort_values('position')
intensities_limited_position = df_limited_sorted['position'].values
intensities_limited_mean = df_limited_sorted['intensity'].values

# Use np.gradient for more accurate differentiation
intensities_derivative = np.gradient(intensities_limited_mean, intensities_limited_position)
mid_positions = intensities_limited_position  # np.gradient returns derivative at each point

# Plot the derivative
plt.figure()
plt.plot(mid_positions, intensities_derivative, marker='o', label='d(Intensity)/d(Position)')
plt.xlabel('Position (degrees)')
plt.ylabel('Derivative of Intensity')
plt.title('Derivative of Laser Profile (True Intensity Distribution)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()