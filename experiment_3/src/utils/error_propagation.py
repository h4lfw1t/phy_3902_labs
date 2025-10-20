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

    @staticmethod
    def central_difference_error(y_values, y_uncertainties, x_step):
        """
        Calculate uncertainty for central difference derivatives using the general error propagation.

        For central differences formula: f'(x_i) ≈ (f(x_{i+1}) - f(x_{i-1})) / (2*Δx)

        Args:
            y_values: Array of function values
            y_uncertainties: Array of uncertainties in y values
            x_step: Step size between x points (assumed uniform)

        Returns:
            Array of uncertainties in the derivative values
        """
        n = len(y_values)
        derivative_errors = np.zeros(n)

        # Define symbols for the general error propagation
        y_plus = sp.Symbol("y_plus")
        y_minus = sp.Symbol("y_minus")

        # Define the central difference formula as a symbolic expression
        central_diff_expr = (y_plus - y_minus) / (2 * x_step)

        # Variables for the error propagation
        variables = [y_plus, y_minus]

        # Handle interior points using central differences and the general method
        for i in range(1, n - 1):
            values = {y_plus: y_values[i + 1], y_minus: y_values[i - 1]}
            uncertainties_dict = {
                y_plus: y_uncertainties[i + 1],
                y_minus: y_uncertainties[i - 1],
            }

            # Use the general error propagation method
            derivative_errors[i] = ErrorPropagation.propagate_error(
                central_diff_expr, variables, values, uncertainties_dict
            )

        # Handle endpoints using forward/backward differences
        # Forward difference for first point (f'(x₀) ≈ (f(x₁) - f(x₀))/Δx)
        forward_diff_expr = (y_plus - y_minus) / x_step

        # First point (forward difference)
        values = {y_plus: y_values[1], y_minus: y_values[0]}
        uncertainties_dict = {
            y_plus: y_uncertainties[1],
            y_minus: y_uncertainties[0],
        }
        derivative_errors[0] = ErrorPropagation.propagate_error(
            forward_diff_expr, variables, values, uncertainties_dict
        )

        # Last point (backward difference)
        values = {y_plus: y_values[-1], y_minus: y_values[-2]}
        uncertainties_dict = {
            y_plus: y_uncertainties[-1],
            y_minus: y_uncertainties[-2],
        }
        derivative_errors[-1] = ErrorPropagation.propagate_error(
            forward_diff_expr, variables, values, uncertainties_dict
        )

        return derivative_errors
