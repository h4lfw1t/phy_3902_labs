#!/usr/bin/env python3
"""
File Manager Module

This module provides utilities for file operations across experiments.
"""

import sympy as sp
import numpy as np


class ErrorPropagation:
    """Propagates uncertainties in measurements."""

    @staticmethod
    def propagate_error(R_expr, variables, values, uncertainties):
        """
        Propagate uncertainty for a function R using the general formula:
        ΔR = sqrt(Σ [ (∂R/∂xi)^2 * (Δxi)^2 ])
        Args:
            R_expr: sympy expression for R (e.g., x*y)
            variables: list of sympy symbols (e.g., [x, y])
            values: dict mapping symbol to value (e.g., {x: 2, y: 3})
            uncertainties: dict mapping symbol to uncertainty (e.g., {x: 0.1, y: 0.2})
        Returns:
            float: propagated uncertainty ΔR
        """
        total = 0.0
        for var in variables:
            partial = sp.diff(R_expr, var)
            partial_val = float(partial.evalf(subs=values))
            delta = uncertainties[var]
            total += (partial_val ** 2) * (delta ** 2)
        return np.sqrt(total)

