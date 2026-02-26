"""
Statistics Utilities Module for Data Octopus

Contains statistical calculation functions used by Statistics Tab,
Boxplot, Distribution, and GRR analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats


def calculate_basic_stats(values: np.ndarray) -> Dict[str, float]:
    """
    Calculate basic statistics for a numeric array.

    Args:
        values: NumPy array of numeric values

    Returns:
        Dict with keys: count, mean, std, min, max, median, range
    """
    valid = values[~np.isnan(values)]

    if len(valid) == 0:
        return {
            'count': 0,
            'mean': np.nan,
            'std': np.nan,
            'min': np.nan,
            'max': np.nan,
            'median': np.nan,
            'range': np.nan,
        }

    return {
        'count': len(valid),
        'mean': np.mean(valid),
        'std': np.std(valid),
        'min': np.min(valid),
        'max': np.max(valid),
        'median': np.median(valid),
        'range': np.max(valid) - np.min(valid),
    }


def calculate_percentiles(values: np.ndarray,
                          percentiles: List[float] = [1, 5, 10, 25, 50, 75, 90, 95, 99]
                          ) -> Dict[str, float]:
    """
    Calculate percentiles for a numeric array.

    Args:
        values: NumPy array of numeric values
        percentiles: List of percentile values (0-100)

    Returns:
        Dict with keys like 'p1', 'p5', 'p10', etc.
    """
    valid = values[~np.isnan(values)]

    if len(valid) == 0:
        return {f'p{p}': np.nan for p in percentiles}

    return {f'p{p}': np.percentile(valid, p) for p in percentiles}


def calculate_cpk(values: np.ndarray,
                  lower_limit: Optional[float] = None,
                  upper_limit: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate process capability indices (Cp, Cpk, Cpl, Cpu).

    Args:
        values: NumPy array of numeric values
        lower_limit: Lower specification limit (LSL)
        upper_limit: Upper specification limit (USL)

    Returns:
        Dict with keys: cp, cpk, cpl, cpu
    """
    valid = values[~np.isnan(values)]

    if len(valid) < 2:
        return {'cp': np.nan, 'cpk': np.nan, 'cpl': np.nan, 'cpu': np.nan}

    mean = np.mean(valid)
    std = np.std(valid, ddof=1)  # Sample standard deviation

    if std == 0:
        return {'cp': np.inf, 'cpk': np.inf, 'cpl': np.inf, 'cpu': np.inf}

    cp = np.nan
    cpl = np.nan
    cpu = np.nan
    cpk = np.nan

    if lower_limit is not None and upper_limit is not None:
        cp = (upper_limit - lower_limit) / (6 * std)

    if lower_limit is not None:
        cpl = (mean - lower_limit) / (3 * std)

    if upper_limit is not None:
        cpu = (upper_limit - mean) / (3 * std)

    # Cpk is the minimum of Cpl and Cpu
    cpk_values = [v for v in [cpl, cpu] if not np.isnan(v)]
    if cpk_values:
        cpk = min(cpk_values)

    return {'cp': cp, 'cpk': cpk, 'cpl': cpl, 'cpu': cpu}


def calculate_yield(values: np.ndarray,
                    lower_limit: Optional[float] = None,
                    upper_limit: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate yield statistics (pass/fail counts and percentages).

    Args:
        values: NumPy array of numeric values
        lower_limit: Lower specification limit
        upper_limit: Upper specification limit

    Returns:
        Dict with: total, pass_count, fail_count, pass_pct, fail_pct,
                   fail_low_count, fail_high_count
    """
    valid = values[~np.isnan(values)]
    total = len(valid)

    if total == 0:
        return {
            'total': 0,
            'pass_count': 0,
            'fail_count': 0,
            'pass_pct': 0.0,
            'fail_pct': 0.0,
            'fail_low_count': 0,
            'fail_high_count': 0,
        }

    # Determine pass/fail
    pass_mask = np.ones(total, dtype=bool)
    fail_low = np.zeros(total, dtype=bool)
    fail_high = np.zeros(total, dtype=bool)

    if lower_limit is not None:
        fail_low = valid < lower_limit
        pass_mask &= ~fail_low

    if upper_limit is not None:
        fail_high = valid > upper_limit
        pass_mask &= ~fail_high

    pass_count = np.sum(pass_mask)
    fail_count = total - pass_count

    return {
        'total': total,
        'pass_count': int(pass_count),
        'fail_count': int(fail_count),
        'pass_pct': 100.0 * pass_count / total,
        'fail_pct': 100.0 * fail_count / total,
        'fail_low_count': int(np.sum(fail_low)),
        'fail_high_count': int(np.sum(fail_high)),
    }


def calculate_bin_summary(bin_values: np.ndarray) -> Dict[int, Dict[str, Any]]:
    """
    Calculate bin distribution summary.

    Args:
        bin_values: NumPy array of bin numbers

    Returns:
        Dict mapping bin number to {count, percentage}
    """
    valid = bin_values[~np.isnan(bin_values)].astype(int)
    total = len(valid)

    if total == 0:
        return {}

    unique, counts = np.unique(valid, return_counts=True)

    return {
        int(bin_num): {
            'count': int(count),
            'percentage': 100.0 * count / total
        }
        for bin_num, count in zip(unique, counts)
    }


def calculate_grr(measurements: np.ndarray,
                  parts: np.ndarray,
                  operators: np.ndarray) -> Dict[str, float]:
    """
    Calculate Gage R&R (Repeatability and Reproducibility) statistics.

    Args:
        measurements: Array of measurement values
        parts: Array of part identifiers (same length as measurements)
        operators: Array of operator identifiers (same length as measurements)

    Returns:
        Dict with: repeatability, reproducibility, grr, grr_pct, ndc,
                   part_variation, total_variation
    """
    # Create DataFrame for easier grouping
    df = pd.DataFrame({
        'measurement': measurements,
        'part': parts,
        'operator': operators
    })

    # Remove NaN values
    df = df.dropna()

    if len(df) < 2:
        return {
            'repeatability': np.nan,
            'reproducibility': np.nan,
            'grr': np.nan,
            'grr_pct': np.nan,
            'ndc': np.nan,
            'part_variation': np.nan,
            'total_variation': np.nan,
        }

    # Calculate variance components using ANOVA approach
    grand_mean = df['measurement'].mean()

    # Part variation (between parts)
    part_means = df.groupby('part')['measurement'].mean()
    n_parts = len(part_means)
    part_ss = sum((part_means - grand_mean) ** 2) * len(df) / n_parts

    # Operator variation (between operators)
    operator_means = df.groupby('operator')['measurement'].mean()
    n_operators = len(operator_means)
    operator_ss = sum((operator_means - grand_mean) ** 2) * len(df) / n_operators

    # Within variation (repeatability)
    within_var = df.groupby(['part', 'operator'])['measurement'].var().mean()
    if np.isnan(within_var):
        within_var = 0

    # Calculate standard deviations
    repeatability = np.sqrt(within_var)
    reproducibility = np.sqrt(max(0, operator_ss / len(df)))

    # GRR
    grr = np.sqrt(repeatability**2 + reproducibility**2)

    # Part variation
    part_variation = np.sqrt(max(0, part_ss / len(df)))

    # Total variation
    total_variation = np.sqrt(grr**2 + part_variation**2)

    # %GRR
    grr_pct = 100.0 * grr / total_variation if total_variation > 0 else np.nan

    # Number of Distinct Categories (ndc)
    ndc = 1.41 * (part_variation / grr) if grr > 0 else np.inf

    return {
        'repeatability': repeatability,
        'reproducibility': reproducibility,
        'grr': grr,
        'grr_pct': grr_pct,
        'ndc': ndc,
        'part_variation': part_variation,
        'total_variation': total_variation,
    }


def format_stat_value(value: float, precision: int = 4) -> str:
    """
    Format a statistical value for display.

    Args:
        value: Numeric value
        precision: Number of significant digits

    Returns:
        Formatted string
    """
    if np.isnan(value):
        return "N/A"
    elif np.isinf(value):
        return "∞" if value > 0 else "-∞"
    elif abs(value) >= 1e6 or (abs(value) < 1e-4 and value != 0):
        return f"{value:.{precision}e}"
    else:
        return f"{value:.{precision}g}"
