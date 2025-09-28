import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from scipy.optimize import curve_fit
from scipy.constants import k, e
from typing import Dict, Any, List, Tuple

def led_iv_curve(V: np.ndarray, I_s: float, n: float) -> np.ndarray:
    """
    LED I-V characteristic equation.

    Args:
        V (np.ndarray): Voltage across the LED (V)
        I_s (float): Saturation current (A)
        n (float): Ideality factor (dimensionless)

    Returns:
        np.ndarray: Current through the LED (A)
    """
    V_T = k * 298.15 / e  # Thermal voltage at room temp (T=298.15K)
    return I_s * (np.exp(V / (n * V_T)) - 1)

def load_led_data(csv_file: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load LED I-V data from a CSV file.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Voltage, current, and current error arrays.
    """
    df = pd.read_csv(csv_file)
    V = df["A1-A2"].values
    I = df["current (mA)"].values * 1e-3  # Convert mA to A
    dI = df["d(current (mA))"].values * 1e-3  # Convert mA to A
    return V, I, dI

def fit_led_iv(V: np.ndarray, I: np.ndarray) -> Tuple[float, float, bool]:
    """
    Fit LED I-V data to the diode equation.

    Args:
        V (np.ndarray): Voltage array.
        I (np.ndarray): Current array.

    Returns:
        Tuple[float, float, bool]: Fitted I_s, n, and success flag.
    """
    try:
        popt, _ = curve_fit(
            led_iv_curve, V, I, bounds=(0, [1e-6, 10]), maxfev=10000
        )
        I_s_fit, n_fit = popt
        return I_s_fit, n_fit, True
    except Exception:
        return np.nan, np.nan, False

def clean_current_error(dI: np.ndarray) -> np.ndarray:
    """
    Clean current error array by replacing non-positive or NaN values with a small value.

    Args:
        dI (np.ndarray): Current error array.

    Returns:
        np.ndarray: Cleaned current error array.
    """
    return np.where((dI > 0) & np.isfinite(dI), dI, 1e-9)

def process_led_file(csv_file: str) -> Dict[str, Any]:
    """
    Process a single LED CSV file: load data, fit, and clean errors.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        Dict[str, Any]: Results including voltage, current, error, fit params, and success flag.
    """
    V, I, dI = load_led_data(csv_file)
    I_s_fit, n_fit, fit_success = fit_led_iv(V, I)
    dI_clean = clean_current_error(dI)
    return {
        "name": os.path.basename(csv_file),
        "V": V,
        "I": I,
        "dI": dI_clean,
        "fit_success": fit_success,
        "I_s_fit": I_s_fit,
        "n_fit": n_fit
    }

def plot_led_results(led_results: List[Dict[str, Any]], title: str = "LED I-V Characteristics and Fits (All LEDs)") -> None:
    """
    Plot measured and fitted I-V data for multiple LEDs.

    Args:
        led_results (List[Dict[str, Any]]): List of LED result dicts.
        title (str): Plot title.
    """
    plt.figure(figsize=(10, 7))
    colors = plt.cm.tab10.colors
    for idx, result in enumerate(led_results):
        color = colors[idx % len(colors)]
        label = result["name"].replace(".csv", "").replace("2d_", "")
        plt.errorbar(result["V"], result["I"] * 1e3, yerr=result["dI"] * 1e3, fmt='o', label=f"{label} Data", color=color, capsize=3, markersize=3)
        if result["fit_success"]:
            V_fit = np.linspace(result["V"].min(), result["V"].max(), 200)
            I_fit = led_iv_curve(V_fit, result["I_s_fit"], result["n_fit"])
            plt.plot(V_fit, I_fit * 1e3, label=f"{label} Fit", color=color, linestyle='--')
    plt.xlabel("Voltage Across LED (V)")
    plt.ylabel("Current Through LED (mA)")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main(data_dir: str = "../data/2d") -> None:
    """
    Main execution function: processes all LED CSV files and plots results.

    Args:
        data_dir (str): Directory containing LED CSV files.
    """
    led_files = [fname for fname in os.listdir(data_dir) if fname.endswith(".csv")]
    led_results = []
    for fname in led_files:
        csv_path = os.path.join(data_dir, fname)
        result = process_led_file(csv_path)
        led_results.append(result)
        if result["fit_success"]:
            print(f"{result['name']}:")
            print(f"  Fitted saturation current I_s: {result['I_s_fit']:.2e} A")
            print(f"  Fitted ideality factor n: {result['n_fit']:.2f}\n")
        else:
            print(f"{result['name']}: Fit failed\n")
    plot_led_results(led_results)

if __name__ == "__main__":
    main()
