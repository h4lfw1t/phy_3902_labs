import serial
import serial.tools.list_ports
from matplotlib import figure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
from collections import deque
import time
from abc import ABC, abstractmethod
from typing import Union, Optional

class LivePlotter(ABC):
    def __init__(self, serial_port='COM5', baud_rate=9600, max_points=2048):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.max_points = max_points
        self.ser = None
        self.header_read = False
        self.data = []  # List of dicts or tuples, as needed
        self.fig: Optional[figure.Figure] = None
        self.axes = None
        self.lines = []
        self.setup_plot()

    @abstractmethod
    def setup_plot(self):
        """Setup matplotlib figure, axes, and lines. Must be implemented by subclass."""
        pass

    @abstractmethod
    def process_data(self, raw_line):
        """Process a line of raw serial data. Must be implemented by subclass."""
        pass

    @abstractmethod
    def update_plot(self):
        """Update plot lines with new data. Must be implemented by subclass."""
        pass

    def connect_serial(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            print(f"Connected to {self.serial_port} at {self.baud_rate} baud")
            time.sleep(2)
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            self.list_available_ports()
            return False

    def list_available_ports(self):
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
            if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'cp210', 'ftdi']):
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
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if not self.header_read:
                    if line.startswith('step'):
                        self.header_read = True
                        print("Header detected, starting data collection...")
                    return False
                if line:
                    self.process_data(line)
                    return True
            except Exception as e:
                print(f"Error parsing serial data: {e}")
        return False

    def save_data(self, filename=None):
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"live_plot_{timestamp}.csv"
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")

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
            print("Failed to connect to any serial port. Please check the connection and try again.")
            return
        print("Starting live plot. Press Ctrl+C to stop and save data.")
        try:
            if self.fig is None:
                print("Figure not set up properly.")
                return
            ani = animation.FuncAnimation(self.fig, self.update, interval=100, blit=False)
            plt.show()
        except KeyboardInterrupt:
            print("\nStopping live plot...")
        finally:
            self.save_data()
            if self.ser:
                self.ser.close()
                print("Serial connection closed.")
