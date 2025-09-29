import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.constants import c, e
from scipy.stats import linregress
from typing import Tuple, List, Dict

# --- Configuration ---
DATA_DIR = '../data/2d'
OUT_DIR = '../out'
# LED wavelength specs: (central, lower, upper)
LED_WAVELENGTHS_NM = {
    'blue': (470, 460, 475),
    'green': (522.5, 520, 525),
    'yellow': (589, 585, 595),
    'red': (623, 620, 630),
}
LED_COLOR_MAP = {
    '2d_blue_led.csv': 'blue',
    '2d_green_led.csv': 'green',
    '2d_yellow_led.csv': 'yellow',
    '2d_red_led.csv': 'red'
}
os.makedirs(OUT_DIR, exist_ok=True)

# --- Data Extraction Functions ---
def get_threshold_voltage(csv_path: str) -> Tuple[float, float]:
    """
    Extract the threshold voltage and its error from a CSV file.
    The threshold voltage is defined as the first voltage where all subsequent currents > 0.01 mA.
    The error is taken from the d(A1-A2) column at the threshold index.
    Args:
        csv_path: Path to the CSV file.
    Returns:
        (threshold_voltage, threshold_voltage_error)
    """
    df = pd.read_csv(csv_path)
    voltage_col = 'A1-A2'
    current_col = 'current (mA)'
    voltage_error_col = 'd(A1-A2)'
    V = df[voltage_col].values
    I = df[current_col].values
    dV = df[voltage_error_col].values
    for i in range(len(I)):
        if np.all(I[i:] > 0.01):
            return V[i], dV[i]
    return np.nan, np.nan

# --- Gather LED Data ---
def gather_led_data(data_dir: str, color_map: Dict[str, str], wavelengths_nm: Dict[str, Tuple[float, float, float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Gather threshold voltages, errors, wavelengths, and colors for all LED CSV files in the directory.
    Args:
        data_dir: Directory containing CSV files.
        color_map: Mapping from filename to LED color.
        wavelengths_nm: Mapping from color to wavelength (nm).
    Returns:
        vths: Array of threshold voltages.
        vth_errs: Array of threshold voltage errors.
        wavelengths_nm_arr: Array of wavelengths (nm).
        wl_err_low_arr: Array of lower wavelength errors (nm).
        wl_err_high_arr: Array of upper wavelength errors (nm).
        colors: List of LED colors.
    """
    vths, vth_errs, wavelengths_nm_arr, wl_err_low_arr, wl_err_high_arr, colors = [], [], [], [], [], []
    for fname in os.listdir(data_dir):
        if fname.endswith('.csv') and fname in color_map:
            color = color_map[fname]
            csv_path = os.path.join(data_dir, fname)
            vth, err = get_threshold_voltage(csv_path)
            central, low, high = wavelengths_nm[color]
            vths.append(vth)
            vth_errs.append(err)
            wavelengths_nm_arr.append(central)
            wl_err_low_arr.append(central - low)
            wl_err_high_arr.append(high - central)
            colors.append(color)
    return (np.array(vths), np.array(vth_errs), np.array(wavelengths_nm_arr), np.array(wl_err_low_arr), np.array(wl_err_high_arr), colors)

# --- Analysis Functions ---
def calculate_plancks_constant(slope: float) -> float:
    """
    Calculate Planck's constant from the slope of the fit.
    Args:
        slope: Slope from linear fit (V*m).
    Returns:
        Experimental Planck's constant (J*s).
    """
    return slope * e / c

# --- Plotting Function ---
def plot_led_data(inv_wavelengths: np.ndarray, inv_wavelengths_err_low: np.ndarray, inv_wavelengths_err_high: np.ndarray, vths: np.ndarray, vth_errs: np.ndarray, slope: float, intercept: float, colors: List[str],) -> None:
    """
    Plot threshold voltage vs inverse wavelength with error bars and linear fit.
    Args:
        inv_wavelengths: Array of inverse wavelengths (1/m).
        inv_wavelengths_err_low: Array of lower inverse wavelength errors.
        inv_wavelengths_err_high: Array of upper inverse wavelength errors.
        vths: Array of threshold voltages (V).
        vth_errs: Array of threshold voltage errors.
        slope: Slope from linear fit.
        intercept: Intercept from linear fit.
        colors: List of LED colors for annotation.
    """
    plt.figure(figsize=(8,6))
    # Asymmetric error bars for x (inverse wavelength)
    plt.errorbar(inv_wavelengths, vths, xerr=[inv_wavelengths_err_low, inv_wavelengths_err_high], yerr=vth_errs, fmt='o', color='blue', label='LED Data (with error)')
    plt.plot(inv_wavelengths, slope * inv_wavelengths + intercept, 'r--', label='Linear Fit')
    for i, color in enumerate(colors):
        plt.annotate(color.capitalize(), (inv_wavelengths[i], vths[i]), textcoords="offset points", xytext=(5,5), ha='left')
    plt.xlabel('Inverse Wavelength (1/m)')
    plt.ylabel('Threshold Voltage Vth (V)')
    plt.title("LED Threshold Voltage vs. Inverse Wavelength\nExperimental Determination of Planck's Constant")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, 'led_threshold_vs_inv_wavelength.png')
    plt.savefig(out_path)
    plt.close()

# --- Main Execution ---
def main():
    """
    Main function to orchestrate LED data analysis and plotting.
    """
    vths, vth_errs, wavelengths_nm, wl_err_low, wl_err_high, colors = gather_led_data(DATA_DIR, LED_COLOR_MAP, LED_WAVELENGTHS_NM)
    wavelengths_m = wavelengths_nm * 1e-9
    wl_err_low_m = wl_err_low * 1e-9
    wl_err_high_m = wl_err_high * 1e-9
    inv_wavelengths = 1 / wavelengths_m
    # Asymmetric error propagation for inverse wavelength
    inv_wavelengths_err_low = wl_err_low_m / wavelengths_m**2
    inv_wavelengths_err_high = wl_err_high_m / wavelengths_m**2
    # Linear regression
    slope, intercept, r_value, p_value, std_err = linregress(inv_wavelengths, vths)
    h_exp = calculate_plancks_constant(slope)
    plot_led_data(inv_wavelengths, inv_wavelengths_err_low, inv_wavelengths_err_high, vths, vth_errs, slope, intercept, colors)
    print(f"Experimental Planck's constant: h = {h_exp:.3e} J*s")
    print(f"Literature value: h = 6.626e-34 J*s")
    print(f"Slope (hc/e): {slope:.3e} V*m +/- {std_err:.2e}")
    print(f"R^2 of fit: {r_value**2:.3f}")
    print(f"Percent error in h: {abs((h_exp - 6.626e-34) / 6.626e-34) * 100:.2f}%")

if __name__ == "__main__":
    main()
