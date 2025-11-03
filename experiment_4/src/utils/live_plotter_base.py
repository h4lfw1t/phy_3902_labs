import os
import time
from abc import ABC, abstractmethod
from typing import Optional

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
import serial
import serial.tools.list_ports
from matplotlib import figure


class LivePlotter(ABC):
    """
    Base class for live plotting data from a serial port.
    Subclasses must implement methods for setting up the plot, processing
    data, and updating the plot.

    Attributes:
        serial_port (: The serial port to connect to (e.g., 'COM5').
        baud_rate: The baud rate for the serial connection.
        max_points: Maximum number of data points to retain for plotting.
        ser: The serial connection object.
        header_read: Flag indicating if the header has been read.
        awaiting_header: Flag indicating if waiting for header start.
        data: List to store incoming data points.
        fig: Matplotlib figure object.
        axes: Matplotlib axes object(s).
        lines: List of line objects for updating the plot.
    """

    def __init__(
        self,
        serial_port: str = "COM5",
        baud_rate: int = 9600,
        max_points: int = 2048,
    ):
        """
        Initialize the LivePlotter.

        Args:
            serial_port: The serial port to connect to (e.g., 'COM5').
            baud_rate: The baud rate for the serial connection.
            max_points: Maximum number of data points to retain for plotting.
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.max_points = max_points
        self.ser = None
        self.header_read = False
        self.awaiting_header = True
        self.data = []  # List of dicts or tuples, as needed
        self.fig: Optional[figure.Figure] = None
        self.axes = None
        self.lines = []

    @abstractmethod
    def setup_plot(self):
        """
        Setup matplotlib figure, axes, and lines. Must be implemented by
        subclass.
        """
        pass

    @abstractmethod
    def process_data(self, raw_line):
        """
        Process a line of raw serial data. Must be implemented by subclass.
        """
        pass

    @abstractmethod
    def update_plot(self):
        """Update plot lines with new data. Must be implemented by subclass."""
        pass

    def connect_serial(self):
        try:
            self.ser = serial.Serial(
                self.serial_port, self.baud_rate, timeout=1
            )
            print(f"Connected to {self.serial_port} at {self.baud_rate} baud")
            time.sleep(2)
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            self.list_available_ports()
            return False

    @staticmethod
    def list_available_ports():
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("  No COM ports found")

    def try_auto_connect(self):
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        for port in ports:
            if any(
                keyword in port.description.lower()
                for keyword in ["arduino", "ch340", "cp210", "ftdi"]
            ):
                arduino_ports.append(port.device)
        if arduino_ports:
            print(f"Found potential Arduino ports: {arduino_ports}")
            for port in arduino_ports:
                print(f"Trying to connect to {port}...")
                self.serial_port = port
                if self.connect_serial():
                    return True
        return False

    def read_serial_data(self):
        """
        Read and parse data from the serial port.
        Incoming data is expected to be in csv format, preceded by an
        indicator line '---DATA START---' and a header line.
        """
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode("utf-8").strip()
                if not self.header_read:
                    if self.awaiting_header:
                        self.header_read = True
                        self.awaiting_header = False
                        self.header_read = True
                        print("Header detected, starting data collection...")
                        return False
                    if line.startswith("---DATA START---"):
                        self.awaiting_header = True
                        print("Data start marker detected, awaiting header...")
                        return False
                    return False
                if line:
                    self.process_data(line)
                    return True
            except Exception as e:
                print(f"Error parsing serial data: {e}")
        return False

    def save_data(self, filename=None, out_dir=None):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if out_dir is None:
            out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        else:
            out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)
        if not filename:
            filename = f"live_plot_{timestamp}.csv"
        else:
            filename = f"{filename}_{timestamp}.csv"
        out_path = os.path.join(out_dir, filename)
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(out_path, index=False)
            print(f"Data saved to {out_path}")

    def update(self, frame):
        self.read_serial_data()
        self.update_plot()
        return self.lines

    def start_live_plot(self):
        connected = self.connect_serial()
        if not connected:
            print("\nTrying auto-detection...")
            connected = self.try_auto_connect()
        if not connected:
            print(
                "Failed to connect to any serial port. Please check the connection and try again."
            )
            return
        print("Starting live plot. Press Ctrl+C to stop and save data.")
        try:
            if self.fig is None:
                print("Figure not set up properly.")
                return
            ani = animation.FuncAnimation(
                self.fig, self.update, interval=100, blit=False
            )
            plt.show()
        except KeyboardInterrupt:
            print("\nStopping live plot...")
        finally:
            self.save_data()
            if self.ser:
                self.ser.close()
                print("Serial connection closed.")
