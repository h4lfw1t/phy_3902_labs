
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from scipy.optimize import curve_fit
from scipy.constants import k, e

data_dir = "../data/2d"

# Define column name remap for more explanatory names
csv_column_remap = {
    "out": "V_out (V)",
    "A0": "V_a0 (V)",
    "dA0": "dV_a0 (V)",
    "A1": "V_in A1 (V)",
    "dA1": "dV_in A1 (V)",
    "A0-A1": "Voltage Drop Across R (A0 - A1) (V)",
    "d(A0-A1)": "d Voltage Drop Across R (A0 - A1) (V)",
    "A1-A2": "Voltage Drop Across LED (A1 - Ground) (V)",
    "d(A1-A2)": "d Voltage Drop Across LED (A1 - Ground) (V)",
    "current (mA)": "Current Through R and LED (mA)",
    "d(current (mA))": "d Current Through R and LED (mA)",
}

# LED I-V Characteristic: I = I_s (exp(V/(nV_T)) - 1)
def led_iv_curve(V, I_s, n):
    """
    LED I-V characteristic equation.

    Args:
        V (ndarray): Voltage across the LED (V)
        I_s (float): Saturation current (A)
        n (float): Ideality factor (dimensionless)

    Returns:
        ndarray: Current through the LED (A)
    """
    V_T = k * 298.15 / e  # Thermal voltage at room temp (T=298.15K)
    return I_s * (np.exp(V / (n * V_T)) - 1)

# Function to fit and plot LED I-V data from a CSV file
def fit_and_plot_led_iv(csv_file):
    """
    Fit and plot LED I-V data from a CSV file.

    Read the CSV file and extract voltage and current data. Determine
    the best-fit parameters for the LED I-V characteristic and plot
    the measured data along with the fitted curve.

    Args:
        csv_file (str): Path to the CSV file containing LED I-V data.
    """
    # Read and rename columns for clarity
    df = pd.read_csv(csv_file).rename(columns=csv_column_remap)

    # Extract voltage, current, and current error data
    V = df["Voltage Drop Across LED (A1 - Ground) (V)"]
    I = df["Current Through R and LED (mA)"] * 1e-3  # Convert mA to A
    dI = df["d Current Through R and LED (mA)"] * 1e-3  # Convert mA to A

    try:
        # Fit the curve with bounds to ensure physical parameters
        # Note: I_s should be positive and small, n typically between 1 and 10 (Google)
        popt, _ = curve_fit(
            led_iv_curve, V, I, bounds=(0, [1e-6, 10]), maxfev=10000
        )
        I_s_fit, n_fit = popt

        print(f"{os.path.basename(csv_file)}:")
        print(f"  Fitted saturation current I_s: {I_s_fit:.2e} A")
        print(f"  Fitted ideality factor n: {n_fit:.2f}\n")

        # Clean up dI: replace nans or non-positive values with a negligible value
        dI_clean = np.where((dI > 0) & np.isfinite(dI), dI, 1e-9)

        # Plot data and fit
        plt.figure(figsize=(8,5))
        # Plot measured data with error bars
        plt.errorbar(V, I*1e3, yerr=dI_clean*1e3, fmt='o', label="Measured Data", color="blue", capsize=3, markersize=2)
        V_fit = np.linspace(V.min(), V.max(), 200)
        I_fit = led_iv_curve(V_fit, *popt)
        plt.plot(V_fit, I_fit*1e3, label="Fit", color="red")
        plt.xlabel("Voltage Across LED (V)")
        plt.ylabel("Current Through LED (mA)")
        plt.title(f"LED I-V Characteristic and Fit\n{os.path.basename(csv_file)}")
        plt.legend()
        plt.grid(True)
        plt.show()
    except Exception as ex:
        print(f"{os.path.basename(csv_file)}: Fit failed: {ex}\n")

if __name__ == "__main__":
    for fname in os.listdir(data_dir):
        if fname.endswith(".csv"):
            csv_path = os.path.join(data_dir, fname)
            fit_and_plot_led_iv(csv_path)