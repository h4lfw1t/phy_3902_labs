import os
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Experimental constants
CONSTANTS = {
    "V_SUPPLY": 5.0,            # Supply voltage (V)
    "R_FIXED": 9955,            # Fixed resistor value (ohms)
    "STEPPER_STEPS_PER_REV": 2048,  # Steps per full revolution for stepper motor
    "ANALOG_RESOLUTION": 1023   # 10-bit ADC resolution
}

# Path configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "brewster")

def identify_perpendicular_angles(
    angles: pd.Series, 
    intensities: pd.Series, 
    window_size: int = 25,
    ) -> List[Tuple[float, float, float, int, int]]:
    """
    Identify the flat regions between two steep slopes in the intensity data,
    which correspond to where the laser is perpendicular to the reflective surface.
    
    Note: Since the angles are relative to an arbitrary starting position,
    we're looking for the pattern in the data rather than specific angle values.
    
    Args:
        angles: Series of angles in degrees (relative to arbitrary start)
        intensities: Series of corresponding intensities
        window_size: Size of the moving window for smoothing
        
    Returns:
        perpendicular_regions: List of (start_angle, middle_angle, end_angle, start_idx, end_idx) tuples
            representing the regions where the laser is perpendicular to the surface
    """
    # Calculate and smooth the gradient 
    gradient = np.gradient(intensities, angles)
    smoothed_gradient = np.convolve(gradient, np.ones(window_size)/window_size, mode='same')
    
    # Determine threshold for significant gradient changes (dynamic based on data)
    threshold = np.std(smoothed_gradient) * 1.5
    
    # Find indices where steep slopes (both positive and negative) occur
    pos_indices = np.where(smoothed_gradient > threshold)[0]
    neg_indices = np.where(smoothed_gradient < -threshold)[0]
    
    # Group consecutive indices to find contiguous regions of steep slope
    def group_consecutive(
        indices: np.ndarray,
        max_gap: int = 3,
        ) -> List[List[int]]:
        """
        Group indices that are within max_gap of each other.
        
        Args:
            indices: Array of indices to group
            max_gap: Maximum allowed gap between consecutive indices
            
        Returns:
            List of grouped indices
        """
        if len(indices) == 0:
            return []
        
        groups = []
        current_group = [indices[0]]
        
        for i in range(1, len(indices)):
            if indices[i] - indices[i-1] <= max_gap:
                current_group.append(indices[i])
            else:
                groups.append(current_group)
                current_group = [indices[i]]
                
        groups.append(current_group)
        return groups
    
    # Group consecutive indices and get the center of each group
    pos_groups = group_consecutive(pos_indices)
    neg_groups = group_consecutive(neg_indices)
    
    pos_centers = [int(np.mean(group)) for group in pos_groups if len(group) > 2]
    neg_centers = [int(np.mean(group)) for group in neg_groups if len(group) > 2]
    
    # Combine and sort all slope centers
    all_centers = sorted(pos_centers + neg_centers)
    
    # Find flat regions between consecutive steep slopes
    perpendicular_regions = []
    flat_region_threshold = threshold * 0.3  # Region is flat if average gradient < 30% of steep threshold
    min_region_width = 5  # Minimum width for a valid flat region
    
    for i in range(len(all_centers) - 1):
        start_idx = all_centers[i]
        end_idx = all_centers[i + 1]
        
        # Skip regions that are too narrow
        region_width = end_idx - start_idx
        if region_width < min_region_width:
            continue
        
        # Get angle values for this region
        middle_idx = (start_idx + end_idx) // 2
        start_angle = angles.iloc[start_idx]
        middle_angle = angles.iloc[middle_idx]
        end_angle = angles.iloc[end_idx]
        
        # Determine if region is flat by checking average gradient magnitude
        region_gradient_values = np.abs(smoothed_gradient[start_idx:end_idx])
        avg_gradient = np.mean(region_gradient_values)
        
        # Add region to results if it's flat enough
        if avg_gradient < flat_region_threshold:
            region_data = (
                start_angle,    # Start angle
                middle_angle,   # Middle angle 
                end_angle,      # End angle
                start_idx,      # Start index
                end_idx         # End index
            )
            perpendicular_regions.append(region_data)
    
    return perpendicular_regions

def plot_brewster_angle(data_file: str) -> Tuple[pd.Series, pd.Series, List[Tuple]]:
    """
    Process and plot Brewster angle data from a CSV file.
    
    Args:
        data_file: Name of the CSV data file to analyze
        
    Returns:
        Tuple containing:
        - angles: Series of angles in degrees
        - intensities: Series of light intensities
        - perpendicular_regions: List of identified perpendicular angle regions
    """
    # Load the data
    data_path = os.path.join(DATA_DIR, data_file)
    data = pd.read_csv(data_path)

    # Extract angle and intensity
    angles = 360 * data['step'] / CONSTANTS["STEPPER_STEPS_PER_REV"]  # Convert steps to degrees

    # Convert LDR voltage to light intensity
    ldr_voltage_feedback = data['adc_mean'] * CONSTANTS["V_SUPPLY"] / CONSTANTS["ANALOG_RESOLUTION"]  # Convert ADC to voltage (0-5V range)

    # Calculate LDR resistance from voltage divider
    # V_ldr = V_SUPPLY * R_FIXED / (R_ldr + R_FIXED)
    # Solving for R_ldr: R_ldr = R_FIXED * (V_SUPPLY - ldr_voltage_feedback) / ldr_voltage_feedback
    ldr_resistance = CONSTANTS["R_FIXED"] * (CONSTANTS["V_SUPPLY"] - ldr_voltage_feedback) / ldr_voltage_feedback

    # Convert resistance to relative light intensity
    # For most LDRs: R = A * (light_intensity)^(-gamma)
    # So: light_intensity = (A/R)^(1/gamma)
    # For simplicity, use inverse relationship: I ∝ 1/R
    intensities = 1.0 / ldr_resistance

    # Identify perpendicular angles (where laser is perpendicular to surface)
    perpendicular_regions = identify_perpendicular_angles(angles, intensities)

    # Create visualization plots
    fig = plt.figure(figsize=(12, 8))
    
    def setup_subplot(pos, x_data, y_data, title, ylabel, color='blue'):
        """Helper function to setup consistent subplot formatting"""
        ax = plt.subplot(2, 2, pos)
        ax.scatter(x_data, y_data, marker='o', s=3, color=color)
        ax.set_title(title)
        ax.set_xlabel('Incident Angle (degrees)')
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 30))
        ax.grid(True)
        return ax

    # Determine the angle offset based on perpendicular regions
    angle_offset = 0
    if perpendicular_regions:
        # Use the first perpendicular region as 0 degrees incident angle
        angle_offset = perpendicular_regions[0][1]  # Middle angle of first region
    
    # Function to relabel x-axis with incident angles while keeping data in place
    def relabel_x_axis(ax, offset):
        # Current ticks (evenly spaced from 0 to 360)
        original_ticks = np.arange(0, 361, 30)
        
        # Create new tick labels that are shifted by the offset
        # First, convert to the range -180 to 180
        new_labels = [(tick - offset) % 360 for tick in original_ticks]
        new_labels = [label - 360 if label > 180 else label for label in new_labels]
        
        # Find the minimum value
        min_label = min(new_labels)
        
        # Adjust labels to start from min_label and be strictly increasing
        adjusted_labels = []
        prev_label = min_label - 1  # Start below the minimum
        
        for label in new_labels:
            # If this label would decrease, add 360 to it
            while label <= prev_label:
                label += 360
            adjusted_labels.append(label)
            prev_label = label
        
        # Set the new tick labels without moving data points
        ax.set_xticks(original_ticks)
        ax.set_xticklabels([f"{int(label)}" for label in adjusted_labels])
        
        # Update xlabel to indicate the reference
        ax.set_xlabel('Incident Angle (degrees)')
    
    # Plot 1: Raw voltage
    voltage_ax = setup_subplot(1, angles, ldr_voltage_feedback, 'LDR Voltage vs Angle', 'Voltage (V)', 'blue')
    relabel_x_axis(voltage_ax, angle_offset)
    
    # Plot 2: Calculated resistance
    resistance_ax = setup_subplot(2, angles, ldr_resistance, 'LDR Resistance vs Angle', 'Resistance (Ω)', 'green')
    relabel_x_axis(resistance_ax, angle_offset)
    
    # Calculate gradient for visualization
    gradient = np.gradient(intensities, angles)
    smoothed_gradient = np.convolve(gradient, np.ones(25)/25, mode='same')
    
    # Plot 3: Light intensity with perpendicular regions
    intensity_ax = setup_subplot(3, angles, intensities, 
                                'Light Intensity vs Angle (Brewster Angle Measurement)', 
                                'Relative Light Intensity', 'red')
    relabel_x_axis(intensity_ax, angle_offset)

    # Highlight identified perpendicular regions on intensity plot
    def highlight_regions(ax, regions, offset=0.0, alpha=0.3, show_region=False):
        """
        Helper to highlight perpendicular regions on a plot
        
        Args:
            ax: Matplotlib axis to draw on
            regions: List of perpendicular region tuples
            offset: Angle offset for 0° reference point
            alpha: Transparency for region highlighting
            show_region: Whether to show the span of the region
        """
        # Define distinct colors for each perpendicular angle line
        colors = ['green', 'blue', 'purple', 'orange', 'cyan', 'magenta']
        
        # Function to convert raw angle to incident angle label
        def get_incident_angle_label(raw_angle, region_index):
            # For perpendicular regions, use fixed labels (0°, 180°, etc.)
            # regardless of actual position on x-axis
            return f"{region_index * 180}°"
        
        # For each region, highlight and label with the appropriate angle
        for i, (start_angle, middle_angle, end_angle, _, _) in enumerate(regions):
            # Calculate the label text (0° for first, 180° for second, etc.)
            label_text = get_incident_angle_label(middle_angle, i)
            
            # Get color for this line (cycle through colors if more regions than colors)
            color = colors[i % len(colors)]
            
            # Highlight the middle angle - this is our best guess for the perpendicular angle
            line = ax.axvline(x=middle_angle, color=color, linestyle='--', label=label_text)
            
            # Add text label near the line at the top of the plot
            y_pos = ax.get_ylim()[1] * 0.95  # Position at 95% of the y-axis height
            ax.text(middle_angle, y_pos, label_text, 
                    color=color, fontweight='bold', ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))
            
            # Show the region bounds if requested
            if show_region:
                # Use a lighter version of the same color for the region
                region_color = color
                ax.axvspan(start_angle, end_angle, color=region_color, alpha=alpha)
        
        # Add a legend only if regions were found
        if regions:
            handles, labels = ax.get_legend_handles_labels()
            # Filter to only include the perpendicular angle lines we just added
            perpendicular_handles = [h for h, l in zip(handles, labels) if '°' in l]
            perpendicular_labels = [l for l in labels if '°' in l]
            if perpendicular_handles:
                ax.legend(perpendicular_handles, perpendicular_labels, loc='best')
    
    # Apply highlighting to intensity plot
    highlight_regions(intensity_ax, perpendicular_regions, offset=angle_offset)

    # Plot 4: Gradient visualization
    gradient_ax = plt.subplot(2, 2, 4)
    gradient_ax.plot(angles, smoothed_gradient, color='blue', linewidth=1)
    gradient_ax.set_title('Gradient of Intensity vs Angle')
    gradient_ax.set_ylabel('Intensity Gradient')
    gradient_ax.set_xlim(0, 360)
    gradient_ax.set_xticks(np.arange(0, 361, 30))
    gradient_ax.grid(True)
    gradient_ax.axhline(y=0, color='gray', linestyle='--')
    relabel_x_axis(gradient_ax, angle_offset)
    
    # Highlight the same regions on the gradient plot
    highlight_regions(gradient_ax, perpendicular_regions, offset=angle_offset)

    plt.tight_layout()
    plt.show()

    return angles, intensities, perpendicular_regions

def report_perpendicular_regions(perpendicular_regions: List[Tuple], 
                            angles: pd.Series, 
                            intensities: pd.Series) -> None:
    """
    Print detailed analysis of the identified perpendicular regions.
    
    Args:
        perpendicular_regions: List of identified perpendicular regions
        angles: Series of angle measurements
        intensities: Series of intensity measurements
    """
    # Calculate the angle offset based on the first perpendicular region
    angle_offset = perpendicular_regions[0][1] if perpendicular_regions else 0
    
    # Function to convert raw angle to incident angle with consistent range
    def to_incident_angle(raw_angle):
        # First convert to -180 to 180 range
        incident = (raw_angle - angle_offset) % 360
        incident = incident - 360 if incident > 180 else incident
        
        # Get the minimum possible angle from the x-axis range (-180 to 180)
        all_angles = [(ang - angle_offset) % 360 for ang in np.arange(0, 361, 30)]
        all_angles = [ang - 360 if ang > 180 else ang for ang in all_angles]
        min_angle = min(all_angles)
        
        # If our angle is less than the minimum displayed angle, add 360 degrees
        while incident < min_angle:
            incident += 360
            
        return incident
    
    for i, (start_angle, middle_angle, end_angle, start_idx, end_idx) in enumerate(perpendicular_regions):
        # Calculate the width of the region in degrees
        region_width = end_angle - start_angle
        
        # Calculate the flatness metric (lower is flatter)
        region_gradient = np.gradient(intensities.iloc[start_idx:end_idx], angles.iloc[start_idx:end_idx])
        flatness = np.mean(np.abs(region_gradient))
        
        # Calculate incident angles
        middle_incident = to_incident_angle(middle_angle)
        start_incident = to_incident_angle(start_angle)
        end_incident = to_incident_angle(end_angle)
        
        print(f"  Region {i+1}:")
        print(f"    Raw angle center: {middle_angle:.1f}°")
        print(f"    Incident angle center: {middle_incident:.1f}°")
        print(f"    Raw spans: {start_angle:.1f}° to {end_angle:.1f}° (width: {region_width:.1f}°)")
        print(f"    Incident spans: {start_incident:.1f}° to {end_incident:.1f}°")
        print(f"    Flatness metric: {flatness:.5f}")

        # Map to theoretical angles - assumes the first region is 0° and second is 180°
        if len(perpendicular_regions) >= 2:
            if i == 0:
                print("    Maps to theoretical incident angle: 0° (laser perpendicular to surface)")
            elif i == 1:
                print("    Maps to theoretical incident angle: 180° (laser perpendicular to surface)")

    # Calculate the relative angle between regions if we found both
    if len(perpendicular_regions) >= 2:
        angle_diff = perpendicular_regions[1][1] - perpendicular_regions[0][1]
        print(f"\n  Angle difference between perpendicular regions (raw): {angle_diff:.1f}°")
        print("  Expected difference: 180° (theoretical)")
        
        # Check if our angle difference is close to expected
        if abs(angle_diff - 180) < 30:
            print("  ✓ Angle difference is close to expected value (180°)")
        else:
            print("  ⚠ Angle difference deviates significantly from expected value (180°)")
            print("    This may indicate issues with the measurement or detection algorithm.")


def main() -> None:
    """
    Main function to process and analyze all Brewster angle data files.
    """
    for file in os.listdir(DATA_DIR):
        if file.endswith('.csv'):  # Only process CSV files
            print(f"\nAnalyzing data from {file}")
            angles, intensities, perpendicular_regions = plot_brewster_angle(file)

            # Find minimum intensity (Brewster angle)
            min_idx = np.argmin(intensities)
            brewster_angle_raw = angles.iloc[min_idx]
            
            # Calculate the angle offset to get the incident angle
            angle_offset = 0
            if perpendicular_regions:
                angle_offset = perpendicular_regions[0][1]  # Middle angle of first perpendicular region
            
            # Calculate the brewster angle in the incident angle reference frame (0° at perpendicular)
            brewster_incident_angle = (brewster_angle_raw - angle_offset) % 360
            # First adjust to range from -180 to 180
            brewster_incident_angle = brewster_incident_angle - 360 if brewster_incident_angle > 180 else brewster_incident_angle
            
            # If we have perpendicular regions, ensure the brewster angle is expressed in the same range as the x-axis labels
            if perpendicular_regions:
                # Get the minimum possible angle from the x-axis range (-180 to 180)
                all_angles = [(ang - angle_offset) % 360 for ang in np.arange(0, 361, 30)]
                all_angles = [ang - 360 if ang > 180 else ang for ang in all_angles]
                min_angle = min(all_angles)
                
                # If our brewster angle is less than the minimum displayed angle, add 360 degrees
                if brewster_incident_angle < min_angle:
                    brewster_incident_angle += 360
            
            print(f"Measured Brewster angle (raw): {brewster_angle_raw:.1f}°")
            print(f"Measured Brewster angle (incident angle): {brewster_incident_angle:.1f}°")

            # Report regions where the laser is likely perpendicular to the reflective surface
            print("Identified flat regions (where laser is perpendicular to surface):")
            
            if not perpendicular_regions:
                print("  No suitable perpendicular regions found. Try adjusting the detection parameters.")
            else:
                report_perpendicular_regions(perpendicular_regions, angles, intensities)

if __name__ == "__main__":
    main()