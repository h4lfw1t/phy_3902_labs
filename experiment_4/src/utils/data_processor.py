import numpy as np
import pandas as pd


def load_experiment_data(filename):
    """Load main experiment CSV data."""
    return pd.read_csv(filename)


def load_pid_data(filename):
    """Load PID data CSV (expects columns: time(s), temp_mean(C), output_power, etc)."""
    return pd.read_csv(filename)


def find_stable_power_window(pid_df, tset, window=30, tol=0.2):
    """
    Find a window where temperature is stable near tset (within tol deg C for at least 'window' seconds).
    Returns (start_idx, end_idx) or (None, None) if not found.
    """
    temp = pid_df['temp_mean(C)'].to_numpy(dtype=float)
    time = pid_df['time(s)'].to_numpy(dtype=float)
    mask = np.abs(temp - tset) < tol
    if not np.any(mask):
        return None, None
    # Find longest contiguous region where mask is True and duration >= window
    best = (None, None, 0)
    i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            if time[j] - time[i] >= window and (j - i) > (best[2]):
                best = (i, j, j - i)
            i = j + 1
        else:
            i += 1
    if best[0] is not None:
        return best[0], best[1]
    return None, None


def mean_output_power(pid_df, start_idx, end_idx):
    return pid_df['output_power'].iloc[start_idx:end_idx+1].mean()

