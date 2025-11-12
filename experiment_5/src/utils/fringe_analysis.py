#!/usr/bin/env python3
"""
Fringe analysis utilities for intensity plotting.
"""
import numpy as np
from scipy.ndimage import label as sc_label

class FringeAnalysis:
    def __init__(self, fringe_min_width=10):
        self.fringe_min_width = fringe_min_width

    def find_fringe_regions(self, intensity, threshold=0.1):
        background = np.median(intensity)
        fringe_mask = intensity > (background + threshold * (intensity.max() - background))
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
        outer_centers = [((start + end) // 2, (start, end)) for start, end in outer_fringe_regions]
        outer_centers.sort(key=lambda x: position[x[0]] - center_pos)
        left = [r for i, r in outer_centers if position[i] < center_pos]
        right = [r for i, r in outer_centers if position[i] > center_pos]
        for n, region in enumerate(reversed(left), 1):
            numbered.append((-n, region))
        for n, region in enumerate(right, 1):
            numbered.append((n, region))
        return numbered

    def summarize_fringe_analysis(self, position, center_fringe_regions, outer_fringe_regions, fringe_numbered, fringe_distances, wavelengths, refractive_indices, vacuum_wavelength):
        summary = []
        if center_fringe_regions:
            c_start, c_end = center_fringe_regions[0]
            c_center = (c_start + c_end) // 2
            summary.append(f"Center fringe: {position[c_start]:.6g} m to {position[c_end]:.6g} m (center: {position[c_center]:.6g} m)")
        summary.append("Outer fringes:")
        for start, end in outer_fringe_regions:
            center = (start + end) // 2
            summary.append(f"  {position[start]:.6g} m to {position[end]:.6g} m (center: {position[center]:.6g} m)")
        summary.append("\nFringe numbers and regions:")
        for number, (start, end) in fringe_numbered:
            center = (start + end) // 2
            summary.append(f"  Fringe {number}: {position[start]:.6g} m to {position[end]:.6g} m (center: {position[center]:.6g} m)")
        summary.append(f"\nVacuum wavelength: {vacuum_wavelength*1e9:.2f} nm")
        summary.append("Calculated fringe distances, wavelengths, and refractive indices:")
        for (num, _), dist, wl, n in zip(fringe_numbered, fringe_distances, wavelengths, refractive_indices):
            summary.append(f"  Fringe {num}: Distance = {dist:.6g} m, Wavelength = {wl:.6g} nm, n = {n:.6g}")
        return '\n'.join(summary)
