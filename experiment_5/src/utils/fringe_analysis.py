#!/usr/bin/env python3
"""
Fringe analysis utilities for intensity plotting.
"""
import numpy as np
from scipy.ndimage import label as sc_label


class FringeAnalysis:
    def __init__(self, fringe_min_width=10):
        self.fringe_min_width = fringe_min_width
        self.position = None
        self.intensity = None
        self.intensity_error = None
        self.center_fringe_regions = None
        self.outer_fringe_regions = None
        self.filtered_outer = None
        self.fringe_numbered = None
        self.fringe_distances = None
        self.wavelengths = None
        self.refractive_indices = None
        self.vacuum_wavelength = None
        self.notes = None
        self.baseline_fringe_distances = None
        self.child_fringe_distances = None
        self.child_refractive_indices = None

    def analyze(self, data, manifest_entry, data_proc, constants):
        self.vacuum_wavelength = manifest_entry.get("wavelength", 650e-9)
        setup_length = manifest_entry.get("setup_length", 0.045)
        self.notes = manifest_entry.get("notes", "")

        self.position = data_proc.steps_to_linear_position(
            data['position'], max_steps=1800, linear_scale=0.05)
        self.intensity, self.intensity_error = data_proc.intensity_with_error(
            data['ldr_mean'], data['ldr_stddev'])

        self.center_fringe_regions = self.find_fringe_regions(
            self.intensity, threshold=constants.CENTER_FRINGE_THRESHOLD)
        self.outer_fringe_regions = self.find_fringe_regions(
            self.intensity, threshold=constants.OUTER_FRINGE_THRESHOLD)

        def is_outside(center, outer):
            for c_start, c_end in center:
                if not (outer[1] < c_start or outer[0] > c_end):
                    return False
            return True
        self.filtered_outer = [r for r in self.outer_fringe_regions if is_outside(
            self.center_fringe_regions, r)]

        if self.center_fringe_regions:
            self.position = data_proc.align_center_fringe(
                self.position, self.center_fringe_regions[0])

        self.fringe_numbered = self.assign_fringe_numbers(
            self.position, self.center_fringe_regions[0], self.filtered_outer) if self.center_fringe_regions else []

        self.fringe_distances = []
        self.wavelengths = []
        self.refractive_indices = []
        if self.center_fringe_regions:
            self.fringe_distances = data_proc.get_fringe_distance(
                self.position,
                self.center_fringe_regions[0],
                [region for _, region in self.fringe_numbered],
            )
            for (num, _), fringe_distance in zip(self.fringe_numbered, self.fringe_distances):
                wl = data_proc.calculate_wavelength(
                    abs(num),
                    fringe_distance,
                    1 / constants.DIFFRACTION_GRATING,
                    setup_length=setup_length,
                )
                n = data_proc.calculate_refractive_index(
                    fringe_distance,
                    1 / constants.DIFFRACTION_GRATING,
                    self.vacuum_wavelength,
                    setup_length=setup_length,
                )
                self.wavelengths.append(wl * 1e9)
                self.refractive_indices.append(n)

    def analyze_baseline_child(self, baseline_analyzer, child_analyzer, manifest_entry, constants):
        # Compute refractive index for child using baseline
        from .data_processing import DataProcessing
        data_proc = DataProcessing()
        grating_period = 1 / constants.DIFFRACTION_GRATING
        cell_width = constants.CUVETTE_WIDTH
        vacuum_wavelength = manifest_entry.get("wavelength", 650e-9)
        # Use fringe numbers from child
        fringe_orders = [abs(num) for num, _ in child_analyzer.fringe_numbered]
        baseline_distances = baseline_analyzer.fringe_distances
        child_distances = child_analyzer.fringe_distances
        self.child_refractive_indices = []
        if baseline_distances and child_distances and fringe_orders:
            for i in range(min(len(baseline_distances), len(child_distances), len(fringe_orders))):
                fringe_diff = child_distances[i] - baseline_distances[i]
                n = data_proc.calculate_refractive_index_from_baseline(
                    fringe_order=fringe_orders[i],
                    fringe_diff=fringe_diff,
                    grating_period=grating_period,
                    cell_width=cell_width,
                    vacuum_wavelength=vacuum_wavelength
                )
                self.child_refractive_indices.append(n)

    def find_fringe_regions(self, intensity, threshold=0.1):
        background = np.median(intensity)
        fringe_mask = intensity > (
            background + threshold * (intensity.max() - background))
        labeled, num_features = sc_label(fringe_mask)
        regions = []
        for i in range(1, num_features + 1):
            indices = np.where(labeled == i)[0]
            if len(indices) > self.fringe_min_width:
                regions.append((indices[0], indices[-1]))
        return regions

    def assign_fringe_numbers(self, position, center_fringe_region, outer_fringe_regions):
        center_idx = (center_fringe_region[0] + center_fringe_region[1]) // 2
        center_pos = position[center_idx]
        numbered = []
        outer_centers = [((start + end) // 2, (start, end))
                         for start, end in outer_fringe_regions]
        outer_centers.sort(key=lambda x: position[x[0]] - center_pos)
        left = [r for i, r in outer_centers if position[i] < center_pos]
        right = [r for i, r in outer_centers if position[i] > center_pos]
        for n, region in enumerate(reversed(left), 1):
            numbered.append((-n, region))
        for n, region in enumerate(right, 1):
            numbered.append((n, region))
        return numbered

    def summarize_fringe_analysis(self):
        summary = []
        if self.center_fringe_regions:
            c_start, c_end = self.center_fringe_regions[0]
            c_center = (c_start + c_end) // 2
            summary.append(
                f"Center fringe: {self.position[c_start]:.6g} m to {self.position[c_end]:.6g} m (center: {self.position[c_center]:.6g} m)")
        summary.append("Outer fringes:")
        for start, end in self.filtered_outer:
            center = (start + end) // 2
            summary.append(
                f"  {self.position[start]:.6g} m to {self.position[end]:.6g} m (center: {self.position[center]:.6g} m)")
        summary.append("\nFringe numbers and regions:")
        for number, (start, end) in self.fringe_numbered:
            center = (start + end) // 2
            summary.append(
                f"  Fringe {number}: {self.position[start]:.6g} m to {self.position[end]:.6g} m (center: {self.position[center]:.6g} m)")
        summary.append(
            f"\nVacuum wavelength: {self.vacuum_wavelength*1e9:.2f} nm")
        summary.append(
            "Calculated fringe distances, wavelengths, and refractive indices:")
        for (num, _), dist, wl, n in zip(self.fringe_numbered, self.fringe_distances, self.wavelengths, self.refractive_indices):
            summary.append(
                f"  Fringe {num}: Distance = {dist:.6g} m, Wavelength = {wl:.6g} nm, n = {n:.6g}")
        if self.child_refractive_indices:
            summary.append("\nChild refractive indices (from baseline):")
            for i, n in enumerate(self.child_refractive_indices):
                summary.append(f"  Child fringe {i+1}: n = {n:.6g}")
        return '\n'.join(summary)
