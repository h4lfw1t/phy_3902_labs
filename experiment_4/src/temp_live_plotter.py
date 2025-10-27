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
    ):
        super().__init__(serial_port, baud_rate, max_points)
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
        self.target_line = self.axes.axhline(
            y=55.0,
            color="yellow",
            linestyle="--",
            label="Target Temperature (55°C)",
        )
        self.upper_band = self.axes.axhline(
            y=56.5, color="pink", linestyle="--", label="Upper Band (56.5°C)"
        )
        self.lower_band = self.axes.axhline(
            y=53.5, color="cyan", linestyle="--", label="Lower Band (53.5°C)"
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
        if self.target_line is not None:
            self.target_line.set_ydata([55.0, 55.0])
        if self.upper_band is not None:
            self.upper_band.set_ydata([56.5, 56.5])
        if self.lower_band is not None:
            self.lower_band.set_ydata([53.5, 53.5])


if __name__ == "__main__":
    plotter = TempLivePlotter(
        serial_port="COM5", baud_rate=9600, max_points=2048
    )
    plotter.start_live_plot()
