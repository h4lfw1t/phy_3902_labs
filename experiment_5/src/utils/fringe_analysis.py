#!/usr/bin/env python3
"""
Fringe Analysis Module

This module provides utilities for analyzing interference fringe patterns
from diffraction grating interferometry/spectrometry experiments. It handles fringe
detection, numbering, and refractive index calculations.
"""
from typing import Tuple, List

import numpy as np
import pandas as pd
from numpy import ndarray
from scipy.ndimage import label as sc_label
from .data_processing import DataProcessing
from .intensity_config import IntensityConfig


class FringeAnalysis:
    """Analyze interference fringe patterns from intensity data.

    This class provides methods to detect fringes in intensity profiles,
    assign order numbers, calculate fringe separations, and compute
    refractive indices from baseline comparisons.

    Parameters
    ----------
    fringe_min_width : int, optional
        Minimum width (in data points) for a valid fringe region, by default 10

    Attributes
    ----------
    fringe_min_width : int
        Minimum width threshold for fringe detection
    position : ndarray or None
        Position array (meters), aligned so center fringe is at 0
    intensity : ndarray or None
        Measured intensity values
    intensity_error : ndarray or None
        Uncertainties in intensity measurements
    data_proc : DataProcessing
        Instance of DataProcessing for conversions
    center_fringe_regions : list or None
        List of (start, end) index tuples for center fringes
    outer_fringe_regions : list or None
        List of (start, end) index tuples for all detected fringes
    filtered_outer : list or None
        Outer fringes excluding those overlapping with center
    fringe_numbered : list or None
        List of (order, region) tuples with assigned fringe numbers
    fringe_distances : list or None
        Distances from center to each numbered fringe (meters)
    notes : str or None
        Experimental notes from manifest
    refractive_indices : list or None
        List of (order, n_value) tuples for baseline child calculations
    """

    def __init__(self, fringe_min_width: int = 10):
        self.fringe_min_width = fringe_min_width
        self.position = None
        self.intensity = None
        self.intensity_error = None
        self.data_proc = DataProcessing()
        self.center_fringe_regions = None
        self.outer_fringe_regions = None
        self.filtered_outer = None
        self.fringe_numbered = None
        self.fringe_distances = None
        self.notes = None
        self.refractive_indices = None  # Only for baseline child calculations

    def analyze(
        self,
        data: pd.DataFrame,
        manifest_entry: dict,
        constants: IntensityConfig,
    ):
        """Analyze fringe data and extract fringe regions and distances.

        Performs complete fringe analysis including position conversion,
        intensity calculation with error propagation, fringe detection,
        filtering, alignment, numbering, and distance measurements.

        Parameters
        ----------
        data : pd.DataFrame
            Experimental data containing columns:
            - 'position': stepper motor step counts
            - 'ldr_mean': mean ADC values from LDR
            - 'ldr_stddev': standard deviation of ADC values
        manifest_entry : dict
            Manifest entry for this dataset containing:
            - 'notes': experimental notes (optional)
        constants : IntensityConfig
            Configuration object with attributes:
            - CENTER_FRINGE_THRESHOLD: threshold for center fringe detection
            - OUTER_FRINGE_THRESHOLD: threshold for outer fringe detection
        """
        self.notes = manifest_entry.get("notes", "")

        # Convert position steps to linear position
        self.position = self.data_proc.steps_to_linear_position(
            data["position"], max_steps=1800, linear_scale=0.05
        )

        # Calculate intensity with error propagation
        self.intensity, self.intensity_error = (
            self.data_proc.intensity_with_error(
                data["ldr_mean"], data["ldr_stddev"]
            )
        )

        # Find center and outer fringe regions
        self.center_fringe_regions = self.find_fringe_regions(
            self.intensity, threshold=constants.CENTER_FRINGE_THRESHOLD
        )
        self.outer_fringe_regions = self.find_fringe_regions(
            self.intensity, threshold=constants.OUTER_FRINGE_THRESHOLD
        )

        # Filter outer fringes to exclude those overlapping with center
        def is_outside_center(center, outer):
            for c_start, c_end in center:
                if not (outer[1] < c_start or outer[0] > c_end):
                    return False
            return True

        self.filtered_outer = [
            r
            for r in self.outer_fringe_regions
            if is_outside_center(self.center_fringe_regions, r)
        ]

        # Align position so center fringe is at position 0
        if self.center_fringe_regions:
            self.position = self.data_proc.align_center_fringe(
                self.position, self.center_fringe_regions[0]
            )

            # Assign fringe numbers
            self.fringe_numbered = self.assign_fringe_numbers(
                self.position,
                self.center_fringe_regions[0],
                self.filtered_outer,
            )

            # Calculate fringe distances
            self.fringe_distances = self.data_proc.get_fringe_distance(
                self.position,
                self.center_fringe_regions[0],
                [region for _, region in self.fringe_numbered],
            )
        else:
            self.fringe_numbered = []
            self.fringe_distances = []

    def analyze_baseline_child(
        self,
        baseline_analyzer,
        manifest_entry: dict,
        constants: IntensityConfig,
    ):
        """Calculate refractive indices for child dataset using baseline comparison.

        Compares fringe positions between this dataset (child) and a baseline
        dataset to calculate the refractive index of the sample. This method
        should only be called on child datasets that have a corresponding parent
        baseline.

        Parameters
        ----------
        baseline_analyzer : FringeAnalysis
            Analyzer instance containing baseline (reference) fringe data
        manifest_entry : dict
            Manifest entry containing:
            - 'wavelength': laser wavelength in vacuum (meters), optional
        constants : object
            Configuration object with attributes:
            - DIFFRACTION_GRATING: grating line density (lines/meter)
            - CUVETTE_WIDTH: sample cell width (meters)
        """
        grating_period = 1 / constants.DIFFRACTION_GRATING
        cell_width = constants.CUVETTE_WIDTH
        vacuum_wavelength = manifest_entry.get("wavelength", 650e-9)

        # Build dictionaries mapping fringe number to distance
        baseline_fringe_dict = {
            num: dist
            for (num, _), dist in zip(
                baseline_analyzer.fringe_numbered,
                baseline_analyzer.fringe_distances,
            )
        }
        child_fringe_dict = {
            num: dist
            for (num, _), dist in zip(
                self.fringe_numbered, self.fringe_distances
            )
        }

        # Find common fringe orders between baseline and child
        common_fringe_numbers = set(baseline_fringe_dict.keys()) & set(
            child_fringe_dict.keys()
        )

        self.refractive_indices = []
        for fringe_num in sorted(common_fringe_numbers):
            baseline_dist = baseline_fringe_dict[fringe_num]
            child_dist = child_fringe_dict[fringe_num]
            fringe_diff = baseline_dist - child_dist

            # Calculate refractive index from baseline difference
            n = self.data_proc.calculate_refractive_index_from_baseline(
                fringe_order=abs(fringe_num),
                fringe_diff=fringe_diff,
                grating_period=grating_period,
                cell_width=cell_width,
                vacuum_wavelength=vacuum_wavelength,
            )
            self.refractive_indices.append((fringe_num, n))

    def find_fringe_regions(self, intensity, threshold: float = 0.1):
        """Find regions of intensity peaks that represent fringes.

        Uses a threshold-based approach with connected component labeling
        to identify contiguous regions where intensity exceeds the background
        by a specified threshold.

        Parameters
        ----------
        intensity : array_like
            Array of intensity values
        threshold : float, optional
            Relative threshold above background for fringe detection, by default 0.1
            Threshold is applied as: background + threshold * (max - background)

        Returns
        -------
        regions : list of tuple
            List of (start_idx, end_idx) tuples defining fringe regions
            Only regions wider than `fringe_min_width` are included
        """
        background = np.median(intensity)
        fringe_mask = intensity > (
            background + threshold * (intensity.max() - background)
        )
        labeled, num_features = sc_label(fringe_mask)
        regions = []
        for i in range(1, num_features + 1):
            indices = np.where(labeled == i)[0]
            if len(indices) > self.fringe_min_width:
                regions.append((int(indices[0]), int(indices[-1])))
        return regions

    def assign_fringe_numbers(
        self,
        position: ndarray,
        center_fringe_region: Tuple[int, int],
        outer_fringe_regions: List[Tuple[int, int]],
    ) -> List[Tuple[int, tuple]]:
        """Assign order numbers to fringes based on their position relative to center.

        Fringes to the left of center are assigned negative orders (-1, -2, ...),
        fringes to the right are assigned positive orders (+1, +2, ...), and the
        center fringe is assigned order 0 (implicitly, not included in output).

        Parameters
        ----------
        position : ndarray
            Array of position values (meters), should be aligned with center at 0
        center_fringe_region : tuple of (int, int)
            Indices defining the center fringe region (start, end)
        outer_fringe_regions : list of tuple
            List of (start, end) index tuples for outer fringes

        Returns
        -------
        numbered : list of tuple
            List of (order, region) tuples where:
            - order is an integer (negative for left, positive for right)
            - region is a (start, end) index tuple
            Sorted by order: [-2, -1, +1, +2, ...]
        """
        center_idx = self.data_proc.get_region_center_idx(center_fringe_region)
        center_pos = position[center_idx]
        numbered = []

        # Calculate center positions for outer fringes
        outer_centers = [
            (self.data_proc.get_region_center_idx(region), region)
            for region in outer_fringe_regions
        ]
        outer_centers.sort(key=lambda x: position[x[0]] - center_pos)

        # Separate left and right fringes
        left = [r for i, r in outer_centers if position[i] < center_pos]
        right = [r for i, r in outer_centers if position[i] > center_pos]

        # Assign negative numbers to left fringes, positive to right
        for n, region in enumerate(reversed(left), 1):
            numbered.append((-n, region))
        for n, region in enumerate(right, 1):
            numbered.append((n, region))

        return numbered

    def summarize_fringe_analysis(self, debug: bool = False) -> str:
        """Generate a summary of the fringe analysis results.

        Creates a formatted text summary of the analysis including detected
        fringes, their positions, distances, and calculated refractive indices
        (if applicable).

        Parameters
        ----------
        debug : bool, optional
            If True, include detailed center and outer fringe information
            in the output, by default False

        Returns
        -------
        summary : str
            Multi-line formatted string containing:
            - [Debug only] Center fringe position and range
            - [Debug only] All outer fringe positions and ranges
            - Detected fringes with order numbers and distances
            - Refractive index results (if calculated from baseline)
            - Mean and standard deviation of refractive indices

        Examples
        --------
        Normal mode output:
            Detected Fringes:
              Order -1: distance = 19.3333 mm  [range: ...]
              Order +1: distance = 19.7778 mm  [range: ...]

            Refractive Index Results:
              Order -1: n = 1.393251
              Order +1: n = 2.105776

              Mean: n = 1.749514 ± 0.503831
        """

        summary = []

        # Debug mode: Show detailed center and outer fringe information
        if debug:
            if self.center_fringe_regions:
                c_start, c_end = self.center_fringe_regions[0]
                c_center = self.data_proc.get_region_center_idx(
                    self.center_fringe_regions[0]
                )
                summary.append(
                    f"[DEBUG] Center fringe: {self.position[c_start]:.6g} m to {self.position[c_end]:.6g} m "
                    f"(center: {self.position[c_center]:.6g} m)"
                )

            if self.filtered_outer:
                summary.append("\n[DEBUG] Outer fringes:")
                for region in self.filtered_outer:
                    start, end = region
                    center = self.data_proc.get_region_center_idx(region)
                    summary.append(
                        f"  {self.position[start]:.6g} m to {self.position[end]:.6g} m "
                        f"(center: {self.position[center]:.6g} m)"
                    )
                summary.append("")  # Add blank line after debug info

        # Numbered fringes with distances (focus on number and distance)
        if self.fringe_numbered:
            summary.append("Detected Fringes:")
            for (number, region), dist in zip(
                self.fringe_numbered, self.fringe_distances
            ):
                start, end = region
                center = self.data_proc.get_region_center_idx(region)
                summary.append(
                    f"  Order {number:+d}: distance = {dist*1000:.4f} mm  "
                    f"[range: {self.position[start]*1000:.2f} to {self.position[end]*1000:.2f} mm, "
                    f"center: {self.position[center]*1000:.2f} mm]"
                )

        # Refractive indices (for baseline children)
        if self.refractive_indices:
            summary.append("\nRefractive Index Results:")
            for fringe_num, n in self.refractive_indices:
                summary.append(f"  Order {fringe_num:+d}: n = {n:.6f}")

            # Calculate mean and standard deviation
            n_values = [n for _, n in self.refractive_indices]
            mean_n = np.mean(n_values)
            std_n = np.std(n_values, ddof=1) if len(n_values) > 1 else 0
            summary.append(f"\n  Mean: n = {mean_n:.6f} ± {std_n:.6f}")

        return "\n".join(summary)
