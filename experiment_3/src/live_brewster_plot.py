import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
from collections import deque
import time

class LiveBrewsterPlotter:
    def __init__(self, serial_port='COM3', baud_rate=9600, max_points=2048):
        """
        Initialize the live plotter for Brewster angle measurements
        
        Args:
            serial_port (str): COM port for Arduino (adjust as needed)
            baud_rate (int): Serial communication baud rate
            max_points (int): Maximum number of data points to display
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.max_points = max_points
        
        # Data storage
        self.steps = deque(maxlen=max_points)
        self.adc_values = deque(maxlen=max_points)
        self.adc_errors = deque(maxlen=max_points)
        
        # Processed data
        self.angles = deque(maxlen=max_points)
        self.voltages = deque(maxlen=max_points)
        self.resistances = deque(maxlen=max_points)
        self.intensities = deque(maxlen=max_points)
        
        # Circuit parameters
        self.V_supply = 5.0
        self.R_fixed = 9955  # Adjust based on your circuit
        
        # Initialize serial connection
        self.ser = None
        self.header_read = False
        
        # Setup plots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle('Live Brewster Angle Measurement', fontsize=16)
        
        # Initialize plot lines
        self.voltage_line, = self.axes[0, 0].plot([], [], 'b-o', markersize=3)
        self.resistance_line, = self.axes[0, 1].plot([], [], 'g-o', markersize=3)
        self.intensity_line, = self.axes[1, 0].plot([], [], 'r-o', markersize=3)
        self.normalized_line, = self.axes[1, 1].plot([], [], 'm-o', markersize=3)
        
        # Setup axes
        self.setup_axes()
        
    def setup_axes(self):
        """Configure the plot axes"""
        # Voltage plot
        self.axes[0, 0].set_title('LDR Voltage vs Angle')
        self.axes[0, 0].set_xlabel('Angle (degrees)')
        self.axes[0, 0].set_ylabel('Voltage (V)')
        self.axes[0, 0].set_xlim(0, 360)
        self.axes[0, 0].set_ylim(0, 5)
        self.axes[0, 0].set_xticks(np.arange(0, 361, 30))
        self.axes[0, 0].grid(True)
        
        # Resistance plot
        self.axes[0, 1].set_title('LDR Resistance vs Angle')
        self.axes[0, 1].set_xlabel('Angle (degrees)')
        self.axes[0, 1].set_ylabel('Resistance (Ω)')
        self.axes[0, 1].set_xlim(0, 360)
        self.axes[0, 1].set_xticks(np.arange(0, 361, 30))
        self.axes[0, 1].grid(True)
        
        # Intensity plot
        self.axes[1, 0].set_title('Light Intensity vs Angle')
        self.axes[1, 0].set_xlabel('Angle (degrees)')
        self.axes[1, 0].set_ylabel('Relative Light Intensity')
        self.axes[1, 0].set_xlim(0, 360)
        self.axes[1, 0].set_xticks(np.arange(0, 361, 30))
        self.axes[1, 0].grid(True)
        
        # Normalized intensity plot
        self.axes[1, 1].set_title('Normalized Light Intensity vs Angle')
        self.axes[1, 1].set_xlabel('Angle (degrees)')
        self.axes[1, 1].set_ylabel('Normalized Intensity (0-1)')
        self.axes[1, 1].set_xlim(0, 360)
        self.axes[1, 1].set_ylim(0, 1)
        self.axes[1, 1].set_xticks(np.arange(0, 361, 30))
        self.axes[1, 1].grid(True)
        
        plt.tight_layout()
    
    def connect_serial(self):
        """Establish serial connection with better error handling"""
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            print(f"Connected to {self.serial_port} at {self.baud_rate} baud")
            time.sleep(2)  # Wait for Arduino to initialize
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            print("\nTroubleshooting steps:")
            print("1. Close Arduino IDE Serial Monitor if it's open")
            print("2. Close any other programs using the serial port")
            print("3. Try a different COM port")
            print("4. Check if Arduino is properly connected")
            print("\nAvailable COM ports:")
            self.list_available_ports()
            return False
    
    def list_available_ports(self):
        """List all available COM ports"""
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("  No COM ports found")
    
    def try_auto_connect(self):
        """Try to automatically connect to an Arduino"""
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        
        for port in ports:
            # Look for Arduino-like devices
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
    
    def process_data(self, step, adc_mean, adc_stddev):
        """Process raw data into physical quantities"""
        # Convert step to angle
        angle = 360 * step / 2048
        
        # Convert ADC to voltage
        voltage = adc_mean * self.V_supply / 1023.0
        
        # Calculate LDR resistance
        if voltage > 0.01:  # Avoid division by zero
            resistance = self.R_fixed * (self.V_supply - voltage) / voltage
        else:
            resistance = float('inf')
        
        # Calculate relative light intensity
        if resistance > 0 and resistance != float('inf'):
            intensity = 1.0 / resistance
        else:
            intensity = 0
        
        return angle, voltage, resistance, intensity
    
    def read_serial_data(self):
        """Read and parse data from serial port"""
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                
                # Skip header line
                if not self.header_read:
                    if line.startswith('step'):
                        self.header_read = True
                        print("Header detected, starting data collection...")
                    return False
                
                # Parse CSV data
                if line and ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        step = float(parts[0])
                        adc_mean = float(parts[1])
                        adc_stddev = float(parts[2])
                        
                        # Process the data
                        angle, voltage, resistance, intensity = self.process_data(step, adc_mean, adc_stddev)
                        
                        # Store data
                        self.steps.append(step)
                        self.adc_values.append(adc_mean)
                        self.adc_errors.append(adc_stddev)
                        self.angles.append(angle)
                        self.voltages.append(voltage)
                        self.resistances.append(resistance)
                        self.intensities.append(intensity)
                        
                        print(f"Angle: {angle:.1f}°, Voltage: {voltage:.3f}V, Intensity: {intensity:.6f}")
                        return True
                        
            except (ValueError, UnicodeDecodeError) as e:
                print(f"Error parsing serial data: {e}")
        
        return False
    
    def update_plots(self, frame):
        """Update the live plots"""
        # Read new data
        self.read_serial_data()
        
        if len(self.angles) > 1:
            angles_list = list(self.angles)
            voltages_list = list(self.voltages)
            resistances_list = list(self.resistances)
            intensities_list = list(self.intensities)
            
            # Update voltage plot
            self.voltage_line.set_data(angles_list, voltages_list)
            
            # Update resistance plot
            self.resistance_line.set_data(angles_list, resistances_list)
            if resistances_list:
                self.axes[0, 1].set_ylim(0, max(resistances_list) * 1.1)
            
            # Update intensity plot
            self.intensity_line.set_data(angles_list, intensities_list)
            if intensities_list:
                self.axes[1, 0].set_ylim(0, max(intensities_list) * 1.1)
            
            # Update normalized intensity plot
            if len(intensities_list) > 1:
                intensities_array = np.array(intensities_list)
                normalized = (intensities_array - intensities_array.min()) / (intensities_array.max() - intensities_array.min())
                self.normalized_line.set_data(angles_list, normalized)
        
        return self.voltage_line, self.resistance_line, self.intensity_line, self.normalized_line
    
    def save_data(self, filename=None):
        """Save collected data to CSV file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"../data/brewster/live_brewster_{timestamp}.csv"
        
        if len(self.steps) > 0:
            df = pd.DataFrame({
                'step': list(self.steps),
                'adc_mean': list(self.adc_values),
                'adc_stddev': list(self.adc_errors)
            })
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
    
    def start_live_plot(self):
        """Start the live plotting"""
        connected = self.connect_serial()
        
        if not connected:
            print("\nTrying auto-detection...")
            connected = self.try_auto_connect()
        
        if not connected:
            print("Failed to connect to any serial port. Please check the connection and try again.")
            return
        
        print("Starting live plot. Press Ctrl+C to stop and save data.")
        
        try:
            # Create animation
            ani = animation.FuncAnimation(self.fig, self.update_plots, interval=100, blit=False)
            plt.show()
            
        except KeyboardInterrupt:
            print("\nStopping live plot...")
        finally:
            # Save data and close serial connection
            self.save_data()
            if self.ser:
                self.ser.close()
                print("Serial connection closed.")

def main():
    # Configuration - adjust these parameters as needed
    SERIAL_PORT = 'COM5'  # Change to your Arduino's COM port
    BAUD_RATE = 9600
    
    print("Live Brewster Angle Plotter")
    print("=" * 30)
    print(f"Trying Serial Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print()
    print("IMPORTANT: Make sure to close Arduino IDE Serial Monitor!")
    print("Make sure your Arduino is connected and running the brewster measurement code.")
    print()
    print("Available COM ports:")
    
    # List available ports
    ports = serial.tools.list_ports.comports()
    if ports:
        for port in ports:
            print(f"  {port.device}: {port.description}")
    else:
        print("  No COM ports found")
    
    print("\nPress Enter to start, or Ctrl+C to exit...")
    
    try:
        input()
        plotter = LiveBrewsterPlotter(SERIAL_PORT, BAUD_RATE)
        plotter.start_live_plot()
        
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()