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

# Function to read and fit LED I-V data from a CSV file
# Returns dict with all relevant info for combined plotting
def read_and_fit_led_iv(csv_file):
    """
    Read and fit LED I-V data from a CSV file.

    Args:
        csv_file (str): Path to the CSV file containing LED I-V data.

    Returns:
        dict: Dictionary containing voltage, current, fit parameters, and success flag.
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
        fit_success = True
    except Exception as ex:
        I_s_fit, n_fit = np.nan, np.nan
        fit_success = False
    # Clean up dI: replace nans or non-positive values with a negligible value
    dI_clean = np.where((dI > 0) & np.isfinite(dI), dI, 1e-9)
    return {
        "name": os.path.basename(csv_file),
        "V": V,
        "I": I,
        "dI": dI_clean,
        "fit_success": fit_success,
        "I_s_fit": I_s_fit,
        "n_fit": n_fit
    }

if __name__ == "__main__":
    # Gather all CSV files
    led_files = [fname for fname in os.listdir(data_dir) if fname.endswith(".csv")]
    led_results = []
    for fname in led_files:
        csv_path = os.path.join(data_dir, fname)
        result = read_and_fit_led_iv(csv_path)
        led_results.append(result)
        # Print fit results
        if result["fit_success"]:
            print(f"{result['name']}:")
            print(f"  Fitted saturation current I_s: {result['I_s_fit']:.2e} A")
            print(f"  Fitted ideality factor n: {result['n_fit']:.2f}\n")
        else:
            print(f"{result['name']}: Fit failed\n")
    # Combined plot
    plt.figure(figsize=(10,7))
    colors = plt.cm.tab10.colors
    for idx, result in enumerate(led_results):
        color = colors[idx % len(colors)]
        label = result["name"].replace(".csv", "").replace("2d_", "")
        # Plot measured data with error bars
        plt.errorbar(result["V"], result["I"]*1e3, yerr=result["dI"]*1e3, fmt='o', label=f"{label} Data", color=color, capsize=3, markersize=3)
        # Plot fit if successful
        if result["fit_success"]:
            V_fit = np.linspace(result["V"].min(), result["V"].max(), 200)
            I_fit = led_iv_curve(V_fit, result["I_s_fit"], result["n_fit"])
            plt.plot(V_fit, I_fit*1e3, label=f"{label} Fit", color=color, linestyle='--')
    plt.xlabel("Voltage Across LED (V)")
    plt.ylabel("Current Through LED (mA)")
    plt.title("LED I-V Characteristics and Fits (All LEDs)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
