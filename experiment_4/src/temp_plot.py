import os
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from utils import BaseConfig, BaseConstants


@dataclass
class TempConstants(BaseConstants):
    TSET = 55.0  # Target temperature in Celsius
    BAND = 3.0  # Acceptable band around target temperature
    COLS = ["time(s)", "temp_mean(C)", "temp_stddev(C)", "output_power"]


@dataclass
class TempConfig(BaseConfig):
    DATA_DIR: str = "../data"


CONFIG = TempConfig()
CONSTANTS = TempConstants()


def plot_temperature_data(
    file_name: str, band: Optional[float] = CONSTANTS.BAND
):
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), CONFIG.DATA_DIR, file_name)
    )
    if not os.path.isfile(file_path):
        print(f"Data file {file_path} does not exist.")
        return

    data = pd.read_csv(file_path)
    missing_col = None
    for col in CONSTANTS.COLS:
        if col not in data.columns:
            missing_col = col
    if missing_col:
        print(f"Column(s) '{missing_col}' missing in data file.")
        return

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
    plt.axhline(
        y=CONSTANTS.TSET,
        color="yellow",
        linestyle="--",
        label=f"Target Temperature ({CONSTANTS.TSET}°C)",
    )
    if band:
        plt.axhline(
            y=CONSTANTS.TSET + band / 2,
            color="pink",
            linestyle="--",
            label=f"Upper Band ({CONSTANTS.TSET + band / 2}°C)",
        )
        plt.axhline(
            y=CONSTANTS.TSET - band / 2,
            color="cyan",
            linestyle="--",
            label=f"Lower Band ({CONSTANTS.TSET - band / 2}°C)",
        )
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # plot_temperature_data('baseline.csv', band=None)
    # plot_temperature_data('simple_hysteresis.csv')
    # plot_temperature_data('proportional_0.1_offset.csv')
    # plot_temperature_data('proportional_0.165_offset.csv')
    # plot_temperature_data('proportional_0.165_offset_1_band.csv', band=1.0)
    plot_temperature_data("integral_0.165_offset_1_band.csv", band=1.0)
