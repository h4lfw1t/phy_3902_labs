import os
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from utils import BaseConfig, BaseConstants


@dataclass
class TempConstants(BaseConstants):
    TSET: float = 55.0  # Target temperature in Celsius
    BAND: float = 3.0  # Acceptable band around target temperature
    COLS: tuple = ("time(s)", "temp_mean(C)", "temp_stddev(C)", "output_power")


@dataclass
class TempConfig(BaseConfig):
    DATA_DIR: str = "../data"


CONFIG = TempConfig()
CONSTANTS = TempConstants()



def get_data_path(file_name: str, config: TempConfig) -> str:
    """Return the absolute path to the data file."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), config.DATA_DIR, file_name))


def check_data_file(file_path: str, required_cols) -> Optional[pd.DataFrame]:
    if not os.path.isfile(file_path):
        print(f"Data file {file_path} does not exist.")
        return None
    data = pd.read_csv(file_path)
    if missing := [col for col in required_cols if col not in data.columns]:
        print(f"Missing column(s) in data file: {', '.join(missing)}")
        return None
    return data


def plot_temperature_data(file_name: str, band: Optional[float] = None, tset: Optional[float] = None):
    # Set default band and tset if not provided
    band = band if band is not None else CONSTANTS.BAND
    tset = tset if tset is not None else CONSTANTS.TSET

    # Retrieve and validate data
    file_path = get_data_path(file_name, CONFIG)
    data = check_data_file(file_path, CONSTANTS.COLS)
    if data is None:
        return

    # Plotting
    plt.figure(figsize=(10, 5))
    plt.errorbar(
        data["time(s)"],
        data["temp_mean(C)"],
        yerr=data["temp_stddev(C)"],
        label="Temperature (°C)",
        color="orange",
        markersize=2,
        fmt="o",
        ecolor="thistle",
        elinewidth=1,
        capsize=2,
    )
    plt.title("Temperature vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Temperature (°C)")
    # Add target and band lines
    plt.axhline(
        y=tset,
        color="yellow",
        linestyle="--",
        label=f"Target Temperature ({tset}°C)",
    )
    if band:
        plt.axhline(
            y=tset + band / 2,
            color="pink",
            linestyle="--",
            label=f"Upper Band ({tset + band / 2}°C)",
        )
        plt.axhline(
            y=tset - band / 2,
            color="cyan",
            linestyle="--",
            label=f"Lower Band ({tset - band / 2}°C)",
        )
    # Add max, min, final value lines
    temp_vals = data["temp_mean(C)"]
    max_val = temp_vals.max()
    max_pos = temp_vals.to_numpy().argmax()
    # Determine min value after max position to avoid initial low temps from heating phase
    if max_pos < len(temp_vals) - 1:
        min_after_max = temp_vals.iloc[max_pos+1:]
        min_val = temp_vals.iloc[-1] if min_after_max.empty else min_after_max.min()
    else:
        min_val = temp_vals.iloc[-1]
    final_val = float(temp_vals.iloc[-1])
    plt.axhline(y=max_val, color="red", linestyle=":", linewidth=1, label=f"Max ({max_val:.2f}°C)")
    plt.axhline(y=min_val, color="blue", linestyle=":", linewidth=1, label=f"Min ({min_val:.2f}°C)")
    plt.axhline(y=final_val, color="green", linestyle=":", linewidth=1, label=f"Final ({final_val:.2f}°C)")

    plt.legend()
    plt.grid(True)
    # Customize y-axis ticks to add minor ticks
    ax = plt.gca()
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.AutoLocator())
    plt.tight_layout()
    # Save plot to out directory
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../out"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_name.replace(".csv", ".png"))
    plt.savefig(out_path)
    print(f"Plot saved to {out_path}")
    plt.show()


if __name__ == "__main__":
    # Call plot_temperature_data with a file name and optional band argument.
    # plot_temperature_data('baseline.csv', band=None)
    # plot_temperature_data('simple_hysteresis.csv')
    # plot_temperature_data('proportional_0.1_offset.csv')
    # plot_temperature_data('proportional_0.165_offset.csv')
    # plot_temperature_data('proportional_0.165_offset_1_band.csv', band=1.0)
    # plot_temperature_data("integral_0.165_offset_1_band.csv", band=1.0)
    # plot_temperature_data("live_plot_20251027_164240.csv", band=1.0)

    # Allow CLI usage: python temp_plot.py <csv_file> [band]
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        band = float(sys.argv[2]) if len(sys.argv) > 2 else None
        tset = float(sys.argv[3]) if len(sys.argv) > 3 else None
    else:
        # Prompt for file name if not provided
        fname = input("File name: ")
        band_input = input("Band (optional, press Enter to skip): ")
        tset_input = input("Tset (optional, press Enter to skip): ")
        band = float(band_input) if band_input else None
        tset = float(tset_input) if tset_input else None

    plot_temperature_data(fname, band, tset)
