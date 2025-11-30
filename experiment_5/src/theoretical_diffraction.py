#!/usr/bin/env python3
"""
Theoretical Diffraction Pattern Plotter

Generates theoretical diffraction patterns for comparison with experimental
measurements from a diffraction grating interferometry setup.

Usage
-----
    python theoretical_diffraction.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Physical Constants
GRATING_LINES_PER_METER = 527559
GRATING_SPACING = 1.0 / GRATING_LINES_PER_METER  # meters

# Default Experimental Parameters
DEFAULT_WAVELENGTH = 650e-9  # meters (650 nm red laser)
DEFAULT_SCREEN_DISTANCE = 0.045  # meters (4.5 cm)
DEFAULT_TRACK_RANGE = (-0.030, 0.030)  # meters (-30 to +30 mm)
DEFAULT_PEAK_WIDTH = 0.008  # meters
DEFAULT_BACKGROUND = 0.02  # normalized background intensity
DEFAULT_ORDER_RANGE = (-2, 3)  # diffraction orders to calculate

# Plot Parameters
DEFAULT_DPI = 300
OUTPUT_DIR = Path(__file__).parent.parent / 'out' / 'theoretical'


def calculate_diffraction_positions(wavelength, screen_distance,
                                    grating_spacing=GRATING_SPACING,
                                    order_range=DEFAULT_ORDER_RANGE):
    """
    Calculate theoretical positions of diffraction orders on the screen.

    Uses the grating equation: d sin(θ) = m λ

    Parameters
    ----------
    wavelength : float
        Wavelength of light in meters
    screen_distance : float
        Distance from grating to screen/detector in meters
    grating_spacing : float, optional
        Distance between grating lines in meters
    order_range : tuple, optional
        Range of diffraction orders to calculate (start, stop)

    Returns
    -------
    dict : Dictionary mapping order number to position in meters
    """
    positions = {}

    for m in range(*order_range):
        sin_theta = (m * wavelength) / grating_spacing

        if abs(sin_theta) <= 1.0:
            theta = np.arcsin(sin_theta)
            position = screen_distance * np.tan(theta)
            positions[m] = position

    return positions


def create_diffraction_pattern(wavelength, screen_distance,
                               track_range=DEFAULT_TRACK_RANGE,
                               peak_width=DEFAULT_PEAK_WIDTH,
                               background=DEFAULT_BACKGROUND,
                               n_points=2000):
    """
    Create a realistic diffraction intensity pattern as measured by an LDR.

    Models broad, Gaussian-shaped peaks characteristic of LDR measurements.

    Parameters
    ----------
    wavelength : float
        Wavelength in meters
    screen_distance : float
        Distance from grating to detector in meters
    track_range : tuple, optional
        Range of the track in meters (start, end)
    peak_width : float, optional
        Characteristic width of each peak (FWHM) in meters
    background : float, optional
        Background intensity level (0-1)
    n_points : int, optional
        Number of points in position array

    Returns
    -------
    position : np.ndarray
        Position array in meters
    intensity : np.ndarray
        Normalized intensity values
    peak_positions : dict
        Dictionary mapping order to peak position in meters
    """
    position = np.linspace(*track_range, n_points)
    intensity = np.zeros_like(position)

    # Calculate theoretical peak positions
    peak_positions = calculate_diffraction_positions(wavelength, screen_distance)

    # Standard deviation for Gaussian (σ = FWHM / 2.355)
    sigma = peak_width / 2.355

    # Add Gaussian peak for each order within track range
    for order, pos in peak_positions.items():
        if track_range[0] <= pos <= track_range[1]:
            # Zeroth order has maximum intensity; others decrease with order
            amplitude = 1.0 if order == 0 else 0.5 / abs(order)
            intensity += amplitude * np.exp(-((position - pos) / sigma) ** 2)

    # Normalize and add background
    intensity = intensity / np.max(intensity) * (1 - background) + background

    return position, intensity, peak_positions


def plot_theoretical_pattern(wavelength=DEFAULT_WAVELENGTH,
                            screen_distance=DEFAULT_SCREEN_DISTANCE,
                            track_range=DEFAULT_TRACK_RANGE,
                            show_plot=True):
    """
    Plot theoretical diffraction pattern matching experimental setup.

    Parameters
    ----------
    wavelength : float, optional
        Wavelength of laser in meters
    screen_distance : float, optional
        Distance from grating to detector in meters
    track_range : tuple, optional
        Range of track in meters (start, end)
    show_plot : bool, optional
        Whether to display the plot
    """
    # Generate the pattern
    position, intensity, peak_positions = create_diffraction_pattern(
        wavelength=wavelength,
        screen_distance=screen_distance,
        track_range=track_range
    )

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(position, intensity, 'b-', linewidth=1.5, label='Theoretical Pattern')

    # Mark theoretical peak positions
    for order, pos in peak_positions.items():
        if track_range[0] <= pos <= track_range[1]:
            ax.axvline(pos, color='red', linestyle='--', alpha=0.3, linewidth=1)
            ax.text(pos, 1.02, f'm={order:+d}', ha='center', fontsize=9, color='red')

    ax.set_xlabel('LDR Position (m)', fontsize=12)
    ax.set_ylabel('Normalized Intensity', fontsize=12)
    ax.set_title(
        f'Theoretical Diffraction Pattern\n'
        f'Grating: {GRATING_LINES_PER_METER} lines/m, '
        f'λ = {wavelength*1e9:.1f} nm, '
        f'L = {screen_distance*100:.1f} cm',
        fontsize=13
    )
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    ax.set_xlim(track_range)
    ax.legend(fontsize=10)

    plt.tight_layout()

    # Save plot
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / 'theoretical_diffraction.png'
    plt.savefig(output_file, dpi=DEFAULT_DPI, bbox_inches='tight')

    # Print peak positions
    print('\n' + '=' * 60)
    print('Theoretical Peak Positions:')
    print('=' * 60)
    print(f'Screen distance: {screen_distance*100:.1f} cm')
    print(f'Wavelength: {wavelength*1e9:.1f} nm')
    print('-' * 60)
    for order in sorted(peak_positions.keys()):
        pos = peak_positions[order]
        if track_range[0] <= pos <= track_range[1]:
            print(f'  Order m = {order:+2d}: {pos:8.4f} m  ({pos*1000:7.2f} mm)')
    print('=' * 60)
    print(f'\nPlot saved to: {output_file}')

    if show_plot:
        plt.show()

    plt.close()

if __name__ == '__main__':
    plot_theoretical_pattern()



