#!/usr/bin/env python3
"""
Intensity Plotting and Fringe Analysis Script

This script processes interferometry data from diffraction grating experiments,
analyzing fringe patterns to calculate refractive indices. It supports both
individual file processing and batch processing with automatic baseline
comparisons.

Usage
-----
Process single file:
    python intensity_plot.py filename.csv

Process all files in auto mode:
    python intensity_plot.py auto

Enable debug mode for detailed output:
    python intensity_plot.py auto debug
    python intensity_plot.py filename.csv debug

Skip displaying graphs (still saves them):
    python intensity_plot.py auto --no-show
    python intensity_plot.py filename.csv --no-show

Features
--------
- Automatic fringe detection and numbering
- Error propagation through all calculations
- Baseline comparison for refractive index determination
- Color-coded console output
- Debug mode with detailed fringe information
- Smart filtering (skips parent baselines in normal auto mode)
- Optional graph display control (--no-show flag)
"""
import json
from typing import Optional

from utils import FringeAnalysis, IntensityConfig
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)

CONSTANTS = IntensityConfig()


def plot_intensity(
    data_file: str, output_file: str, manifest: dict, debug: bool = False, show_plot: bool = True
):
    """
    Plot intensity data with fringe analysis and optional baseline comparison.

    Main processing function that loads data, performs fringe analysis,
    generates plots, and prints results. Handles both baseline parent files
    and child files with automatic baseline comparison.

    Parameters
    ----------
    data_file : str
        Name of the CSV data file to process
    output_file : str
        Name for the output plot file (will be placed in OUT_DIR)
    manifest : dict
        Manifest dictionary containing metadata for all datasets
    debug : bool, optional
        If True, print detailed debug information, by default False
    show_plot : bool, optional
        If True, display the plot window, by default True
    """
    output_file = os.path.join(CONSTANTS.OUT_DIR, output_file)
    data_path = os.path.join(CONSTANTS.DATA_DIR, data_file)

    if not os.path.exists(data_path):
        print(f"{Fore.YELLOW}Warning: Data file not found: {data_file}")
        return

    # Load and validate manifest entry
    manifest_entry = manifest.get(data_file, {})
    if not manifest_entry:
        print(
            f"{Fore.YELLOW}Warning: No manifest entry found for {data_file}."
        )
        return

    # Load data and perform basic analysis
    data = pd.read_csv(data_path)
    analyzer = FringeAnalysis(fringe_min_width=CONSTANTS.FRINGE_MIN_WIDTH)
    analyzer.analyze(data, manifest_entry, CONSTANTS)

    # Handle baseline analysis if applicable
    baseline_info = manifest_entry.get("baseline", None)
    if baseline_info:
        is_baseline = baseline_info.get("parent", False)

        if not is_baseline:
            # This is a child dataset - compare to baseline
            parent_baseline_name = baseline_info.get("name")
            parent_file = _find_baseline_file(manifest, parent_baseline_name)

            if parent_file:
                baseline_analyzer = _analyze_baseline(parent_file, manifest)
                if baseline_analyzer:
                    analyzer.analyze_baseline_child(
                        baseline_analyzer, manifest_entry, CONSTANTS
                    )

    # Generate plot
    _create_plot(analyzer, data_file, show_plot)

    # Print colorized summary
    _print_summary(analyzer, data_file, debug)


def _find_baseline_file(manifest: dict, baseline_name: str) -> Optional[str]:
    """Find the parent baseline file in the manifest.

    Parameters
    ----------
    manifest : dict
        Manifest dictionary containing all dataset metadata
    baseline_name : str
        Name identifier of the baseline to find

    Returns
    -------
    filename : str or None
        Filename of the parent baseline, or None if not found
    """
    for fname, entry in manifest.items():
        binfo = entry.get("baseline", {})
        if binfo.get("name") == baseline_name and binfo.get("parent", False):
            return fname
    return None


def _analyze_baseline(
    baseline_file: str, manifest: dict
) -> Optional[FringeAnalysis]:
    """Load and analyze baseline data.

    Parameters
    ----------
    baseline_file : str
        Filename of the baseline dataset
    manifest : dict
        Manifest dictionary containing all dataset metadata

    Returns
    -------
    baseline_analyzer : FringeAnalysis or None
        Analyzer instance with baseline fringe data, or None if file not found
    """
    baseline_data_path = os.path.join(CONSTANTS.DATA_DIR, baseline_file)

    if not os.path.exists(baseline_data_path):
        print(
            f"{Fore.YELLOW}Warning: Baseline file not found: {baseline_file}"
        )
        return None

    baseline_data = pd.read_csv(baseline_data_path)
    baseline_manifest_entry = manifest.get(baseline_file, {})
    baseline_analyzer = FringeAnalysis(
        fringe_min_width=CONSTANTS.FRINGE_MIN_WIDTH
    )
    baseline_analyzer.analyze(
        baseline_data, baseline_manifest_entry, CONSTANTS
    )

    return baseline_analyzer


def _create_plot(analyzer: FringeAnalysis, data_file: str, show_plot: bool = True):
    """Create and save the intensity plot.

    Generates a matplotlib figure showing intensity vs position with
    highlighted fringe regions and error bars.

    Parameters
    ----------
    analyzer : FringeAnalysis
        Analyzer instance containing processed fringe data
    data_file : str
        Name of the data file (used for output filename)
    show_plot : bool, optional
        If True, display the plot window, by default True
    """
    plt.figure(figsize=(10, 6))

    # Plot intensity with error bars
    plt.errorbar(
        analyzer.position,
        analyzer.intensity,
        yerr=analyzer.intensity_error,
        label="LDR Feedback",
        color="magenta",
        markersize=2,
        fmt="o",
        ecolor="thistle",
        elinewidth=1,
        capsize=2,
    )

    # Highlight fringe regions
    fringe_regions = analyzer.center_fringe_regions + analyzer.filtered_outer
    for idx, (start_idx, end_idx) in enumerate(fringe_regions):
        plt.axvspan(
            analyzer.position[start_idx],
            analyzer.position[end_idx],
            color="yellow",
            alpha=0.3,
            label="Fringe Region" if idx == 0 else None,
        )

    plt.title("LDR Feedback vs Position")
    plt.xlabel("Position (m)")
    plt.ylabel("LDR Value")
    plt.grid(True)
    plt.legend()

    # Save plot
    output_file = os.path.join(
        CONSTANTS.OUT_DIR, os.path.splitext(data_file)[0] + "_intensity.png"
    )
    os.makedirs(CONSTANTS.OUT_DIR, exist_ok=True)
    plt.savefig(output_file)
    if show_plot:
        plt.show()
    plt.close()


def _print_summary(
    analyzer: FringeAnalysis, data_file: str, debug: bool = False
):
    """Print a colorized, formatted summary of the analysis.

    Outputs a formatted console summary with color-coded sections highlighting
    key results including detected fringes and refractive index calculations.

    Parameters
    ----------
    analyzer : FringeAnalysis
        Analyzer instance containing processed fringe data
    data_file : str
        Name of the data file being analyzed
    debug : bool, optional
        If True, include debug information in output, by default False
    """
    # Header
    print(f"\n{Style.BRIGHT}{Fore.CYAN}{'='*70}")
    print(f"{Style.BRIGHT}{Fore.CYAN}  Analysis: {Fore.MAGENTA}{data_file}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'='*70}")

    # Notes
    if analyzer.notes:
        print(f"{Style.DIM}  {analyzer.notes}\n")

    # Get the summary text and colorize it
    summary = analyzer.summarize_fringe_analysis(debug=debug)

    # Colorize different sections
    lines = summary.split("\n")
    for line in lines:
        if line.startswith("[DEBUG]"):
            # Debug info in dim yellow
            print(f"{Style.DIM}{Fore.YELLOW}{line}")
        elif line.startswith("Detected Fringes:"):
            # Section header in bold green
            print(f"{Style.BRIGHT}{Fore.GREEN}{line}")
        elif line.startswith("Refractive Index Results:"):
            # Section header in bold blue
            print(f"{Style.BRIGHT}{Fore.BLUE}{line}")
        elif "Order" in line and ":" in line:
            # Fringe/order lines - highlight the order number and value
            if "distance" in line:
                # Fringe distance line
                parts = line.split("distance = ")
                if len(parts) == 2:
                    order_part = parts[0]
                    value_and_rest = parts[1].split(" ", 1)
                    value = value_and_rest[0]
                    rest = value_and_rest[1] if len(value_and_rest) > 1 else ""
                    print(
                        f"{order_part}{Style.BRIGHT}{Fore.YELLOW}distance = {value}{Style.RESET_ALL} {Style.DIM}{rest}"
                    )
                else:
                    print(line)
            elif "n =" in line:
                # Refractive index line
                parts = line.split("n = ")
                if len(parts) == 2:
                    print(f"{parts[0]}{Style.BRIGHT}{Fore.CYAN}n = {parts[1]}")
                else:
                    print(line)
            else:
                print(line)
        elif line.strip().startswith("Mean:"):
            # Mean value in bold magenta
            parts = line.split("n = ")
            if len(parts) == 2:
                print(f"{parts[0]}{Style.BRIGHT}{Fore.MAGENTA}n = {parts[1]}")
            else:
                print(f"{Style.BRIGHT}{Fore.MAGENTA}{line}")
        else:
            print(line)

    print(f"{Style.BRIGHT}{Fore.CYAN}{'='*70}\n")


if __name__ == "__main__":
    # Load manifest
    with open(CONSTANTS.MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Parse command line arguments
    auto_mode = False
    debug_mode = False
    show_plots = True
    target_file = None

    # Check for debug and no-show flags
    args = [arg.lower() for arg in sys.argv[1:]]
    if "debug" in args:
        debug_mode = True
        args = [arg for arg in args if arg != "debug"]

    if "--no-show" in args:
        show_plots = False
        args = [arg for arg in args if arg != "--no-show"]

    if len(args) > 0:
        if "auto" in args:
            auto_mode = True
        else:
            target_file = (
                sys.argv[1]
                if sys.argv[1].lower() not in ["debug", "--no-show"]
                else (sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].lower() not in ["debug", "--no-show"] else (sys.argv[3] if len(sys.argv) > 3 else None))
            )
    else:
        # Interactive mode
        print(
            f"{Style.BRIGHT}{Fore.CYAN}=== Intensity Plot Analysis ==={Style.RESET_ALL}"
        )
        print("Options: 'auto', 'debug', filename, or 'exit' to quit\n")

        user_input = (
            input("Enter your choice (or 'exit'/'cancel' to quit): ")
            .strip()
            .lower()
        )

        # Check for exit commands
        if user_input in ["exit", "quit", "cancel", "q"]:
            sys.exit(0)

        if "debug" in user_input:
            debug_mode = True
            user_input = user_input.replace("debug", "").strip()

        if user_input == "auto":
            auto_mode = True
        else:
            target_file = user_input if user_input else None

            # If no file provided, prompt again with exit option
            if not target_file:
                target_file = input("File name (or 'exit' to quit): ").strip()

                # Check for exit on second prompt
                if target_file.lower() in ["exit", "quit", "cancel", "q"]:
                    sys.exit(0)

    # Execute based on mode
    if auto_mode:
        print(
            f"{Style.BRIGHT}{Fore.GREEN}Processing all files from manifest..."
        )
        if debug_mode:
            print(f"{Fore.YELLOW}Debug mode: ON (processing all files)\n")
        else:
            print(
                f"{Style.DIM}(Skipping parent files and files without baseline)\n"
            )

        for fname in manifest.keys():
            manifest_entry = manifest.get(fname, {})
            baseline_info = manifest_entry.get("baseline", None)

            # Skip logic (only in non-debug mode)
            if not debug_mode:
                if baseline_info:
                    is_parent = baseline_info.get("parent", False)
                    if is_parent:
                        print(
                            f"{Style.DIM}Skipped {fname}: Parent baseline file"
                        )
                        continue
                else:
                    print(f"{Style.DIM}Skipped {fname}: No baseline reference")
                    continue

            output_file = os.path.splitext(fname)[0] + "_intensity.png"
            plot_intensity(fname, output_file, manifest, debug=debug_mode, show_plot=show_plots)
    else:
        if target_file:
            output_file = os.path.splitext(target_file)[0] + "_intensity.png"
            if debug_mode:
                print(f"{Fore.YELLOW}Debug mode: ON")
            plot_intensity(
                target_file, output_file, manifest, debug=debug_mode, show_plot=show_plots
            )
        else:
            print(f"{Fore.RED}Error: No file specified")
