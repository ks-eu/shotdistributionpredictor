"""Utilities to generate normalised y values over a dataframe with unpacked location data."""

import numpy as np
import pandas as pd
from statsbombpy import sb


def average_y(event_df, step_length = 1, window_rad = 2.5, x_name = 'x', y_name = 'y'):
    df = event_df.copy()
    df = df.sort_values(by = ['x']).reset_index(drop=True)
    x_grid = np.arange(0, 121, step=step_length)

    x_arr = df[x_name].values
    y_arr = df[y_name].values

    y_cumsum = np.cumsum(np.insert(y_arr, 0, 0))
    left_indices = np.searchsorted(x_arr, x_grid - window_rad, side="left")
    right_indices = np.searchsorted(x_arr, x_grid + window_rad, side="right")

    counts = right_indices - left_indices
    sums = y_cumsum[right_indices] - y_cumsum[left_indices]

    with np.errstate(divide="ignore", invalid="ignore"):
        avg_y = np.where(counts > 0, sums / counts, np.nan)

    return np.column_stack((x_grid, avg_y))


def y_quad_average(event_df, step_length = 1, window_rad = 2.5, x_name = 'x', y_name = 'y'):
    df = event_df.copy()
    xy_grid = average_y(df, step_length=step_length, window_rad=window_rad, x_name=x_name, y_name=y_name)

    x_vals = xy_grid[:, 0]
    y_vals = xy_grid[:, 1]
    
    fit_mask = ~np.isnan(y_vals)
    fit_x = x_vals[fit_mask]
    fit_y = y_vals[fit_mask]

    if len(fit_x) < 3:
        raise ValueError("Not enough valid window averages to fit a quadratic curve.")

    a, b, c = np.polyfit(fit_x, fit_y, deg=2)
    return [a, b, c]


def get_normalised_y(event_df, step_length = 1, window_rad = 2.5, x_name = 'x', y_name = 'y'):
    UPPER = 120
    LOWER = 0

    df = event_df.copy()
    coeffs = y_quad_average(df, step_length=step_length, window_rad=window_rad, x_name=x_name, y_name=y_name)

    df['curve_y'] = (coeffs[0] * (df['x']**2)) + (coeffs[1] * df['x']) + (coeffs[2])
    df["y_distance"] = df["y"] - df["curve_y"]

    above_curve = df["y"] >= df["curve_y"]
    df["boundary_distance"] = np.where(
        above_curve,
        np.abs(UPPER - df["curve_y"]),
        np.abs(df["curve_y"] - LOWER),
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        df["normalised_y"] = np.where(
            df["boundary_distance"] > 0,
            np.abs(df["y_distance"] / df["boundary_distance"]),
            0,
        )

    return df
