import sys
import matplotlib.pyplot as plt
from utils.live_plotter_base import LivePlotter

class TempLivePlotter(LivePlotter):
    """
    Live plotter for temperature data from serial port.
    Expects CSV lines: time(s), temp_mean(C), temp_stddev(C), output_power

    Attributes:
        target_line: Line object for target temperature.
        upper_band: Line object for upper temperature band.
        lower_band: Line object for lower temperature band.
        temp_errs: List of temperature standard deviations for error bars.
        errbar: Errorbar object for temperature data.
    """

    def __init__(
        self,
        serial_port: str = "COM5",
        baud_rate: int = 9600,
        max_points: int = 2048,
        tset: float = 55.0,
        band: float = 3.0,
    ):
        super().__init__(serial_port, baud_rate, max_points)
        self.tset = tset
        self.band = band
        self.target_line = None
        self.upper_band = None
        self.lower_band = None
        self.temp_errs = []
        self.errbar = None

    def setup_plot(self):
        self.fig, self.axes = plt.subplots(figsize=(10, 5))
        self.lines = []
        # Main temperature line with error bars
        (line,) = self.axes.plot(
            [], [], "o", color="orange", label="Temperature (°C)", markersize=2
        )
        self.lines.append(line)
        # Target and band lines
        tset = self.tset
        band = self.band
        self.target_line = self.axes.axhline(
            y=tset,
            color="yellow",
            linestyle="--",
            label=f"Target Temperature ({tset}°C)",
        )
        self.upper_band = self.axes.axhline(
            y=tset + band / 2,
            color="pink",
            linestyle="--",
            label=f"Upper Band ({tset + band / 2}°C)"
        )
        self.lower_band = self.axes.axhline(
            y=tset - band / 2,
            color="cyan",
            linestyle="--",
            label=f"Lower Band ({tset - band / 2}°C)"
        )
        self.axes.set_title("Temperature vs Time (Live)")
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Temperature (°C)")
        self.axes.legend()
        self.axes.grid(True)
        self.temp_errs = []

    def process_data(self, raw_line):
        # Expecting CSV: time(s), temp_mean(C), temp_stddev(C), output_power
        try:
            parts = [x.strip() for x in raw_line.split(",")]
            if len(parts) != 4:
                return
            # Skip header or non-numeric lines
            try:
                time_val = float(parts[0])
                temp_mean = float(parts[1])
                temp_std = float(parts[2])
                output_power = float(parts[3])
            except ValueError:
                # Likely a header line, skip
                return
            self.data.append(
                {
                    "time(s)": time_val,
                    "temp_mean(C)": temp_mean,
                    "temp_stddev(C)": temp_std,
                    "output_power": output_power,
                }
            )
            # Keep only max_points
            if len(self.data) > self.max_points:
                self.data.pop(0)
        except Exception as e:
            print(f"Error processing data: {e}")

    def update_plot(self):
        if not self.data:
            return
        times = [d["time(s)"] for d in self.data]
        temps = [d["temp_mean(C)"] for d in self.data]
        temp_errs = [d["temp_stddev(C)"] for d in self.data]
        self.lines[0].set_data(times, temps)
        self.axes.relim()
        self.axes.autoscale_view()
        # Remove previous errorbars if any
        if hasattr(self, "errbar") and self.errbar:
            for bar in self.errbar[2]:
                bar.remove()
        self.errbar = self.axes.errorbar(
            times,
            temps,
            yerr=temp_errs,
            fmt="o",
            color="orange",
            markersize=2,
            ecolor="thistle",
            elinewidth=1,
            capsize=2,
        )
        # Update band lines if they exist
        tset = self.tset
        band = self.band
        if self.target_line is not None:
            self.target_line.set_ydata([tset, tset])
        if self.upper_band is not None:
            self.upper_band.set_ydata([tset + band / 2, tset + band / 2])
        if self.lower_band is not None:
            self.lower_band.set_ydata([tset - band / 2, tset - band / 2])


if __name__ == "__main__":
    # Usage: python temp_live_plotter.py [serial_port] [baud_rate] [max_points] [tset] [band]
    serial_port = "COM5"
    baud_rate = 9600
    max_points = 2048
    tset = 55.0
    band = 3.0
    if len(sys.argv) > 1:
        serial_port = sys.argv[1]
    if len(sys.argv) > 2:
        baud_rate = int(sys.argv[2])
    if len(sys.argv) > 3:
        max_points = int(sys.argv[3])
    if len(sys.argv) > 4:
        tset = float(sys.argv[4])
    if len(sys.argv) > 5:
        band = float(sys.argv[5])
    plotter = TempLivePlotter(
        serial_port=serial_port,
        baud_rate=baud_rate,
        max_points=max_points,
        tset=tset,
        band=band,
    )
    plotter.start_live_plot()
