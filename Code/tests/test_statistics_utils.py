"""
Tests for the statistics_utils module.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from stdf_analyzer.core.statistics_utils import (
    calculate_basic_stats,
    calculate_percentiles,
    calculate_cpk,
    calculate_yield,
    calculate_bin_summary,
    calculate_grr,
    format_stat_value,
)


class TestCalculateBasicStats:
    """Tests for calculate_basic_stats function."""

    def test_basic_stats_simple_array(self):
        """Test with simple integer array."""
        data = np.array([1, 2, 3, 4, 5])
        result = calculate_basic_stats(data)

        assert result['count'] == 5
        assert result['mean'] == 3.0
        assert result['median'] == 3.0
        assert result['min'] == 1.0
        assert result['max'] == 5.0
        assert result['range'] == 4.0
        assert abs(result['std'] - np.std(data)) < 0.0001

    def test_basic_stats_float_array(self):
        """Test with float array."""
        data = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        result = calculate_basic_stats(data)

        assert result['count'] == 5
        assert result['mean'] == 3.5
        assert result['median'] == 3.5
        assert result['min'] == 1.5
        assert result['max'] == 5.5

    def test_basic_stats_single_value(self):
        """Test with single value array."""
        data = np.array([42.0])
        result = calculate_basic_stats(data)

        assert result['count'] == 1
        assert result['mean'] == 42.0
        assert result['median'] == 42.0
        assert result['min'] == 42.0
        assert result['max'] == 42.0
        assert result['range'] == 0.0
        assert result['std'] == 0.0

    def test_basic_stats_negative_values(self):
        """Test with negative values."""
        data = np.array([-5, -3, 0, 3, 5])
        result = calculate_basic_stats(data)

        assert result['count'] == 5
        assert result['mean'] == 0.0
        assert result['min'] == -5.0
        assert result['max'] == 5.0
        assert result['range'] == 10.0

    def test_basic_stats_empty_array(self):
        """Test with empty array."""
        data = np.array([])
        result = calculate_basic_stats(data)

        assert result['count'] == 0
        assert result['mean'] == 0.0
        assert result['std'] == 0.0


class TestCalculatePercentiles:
    """Tests for calculate_percentiles function."""

    def test_percentiles_default(self):
        """Test with default percentiles."""
        data = np.arange(1, 101)  # 1 to 100
        result = calculate_percentiles(data)

        assert 'p25' in result
        assert 'p50' in result
        assert 'p75' in result
        assert abs(result['p50'] - 50.5) < 1  # Median should be around 50.5

    def test_percentiles_custom(self):
        """Test with custom percentile list."""
        data = np.arange(1, 101)
        result = calculate_percentiles(data, [10, 50, 90])

        assert 'p10' in result
        assert 'p50' in result
        assert 'p90' in result

    def test_percentiles_empty(self):
        """Test with empty array."""
        data = np.array([])
        result = calculate_percentiles(data, [25, 50, 75])

        assert result == {}


class TestCalculateCpk:
    """Tests for calculate_cpk function."""

    def test_cpk_centered_process(self):
        """Test Cpk for a centered process."""
        # Generate data centered at 50 with small std
        np.random.seed(42)
        data = np.random.normal(50, 2, 1000)

        result = calculate_cpk(data, lsl=40, usl=60)

        assert 'cp' in result
        assert 'cpk' in result
        assert 'cpl' in result
        assert 'cpu' in result
        assert result['cp'] > 1.0  # Should be capable
        assert result['cpk'] > 1.0  # Should be capable

    def test_cpk_shifted_process(self):
        """Test Cpk for a shifted process."""
        np.random.seed(42)
        data = np.random.normal(55, 2, 1000)  # Shifted toward USL

        result = calculate_cpk(data, lsl=40, usl=60)

        assert result['cpk'] < result['cp']  # Cpk should be less than Cp when shifted
        assert result['cpu'] < result['cpl']  # CPU should be worse (closer to USL)

    def test_cpk_only_lsl(self):
        """Test Cpk with only LSL."""
        data = np.array([10, 11, 12, 13, 14])
        result = calculate_cpk(data, lsl=5, usl=None)

        assert result['cpl'] is not None
        assert result['cpu'] is None
        assert result['cp'] is None
        assert result['cpk'] == result['cpl']

    def test_cpk_only_usl(self):
        """Test Cpk with only USL."""
        data = np.array([10, 11, 12, 13, 14])
        result = calculate_cpk(data, lsl=None, usl=20)

        assert result['cpl'] is None
        assert result['cpu'] is not None
        assert result['cp'] is None
        assert result['cpk'] == result['cpu']

    def test_cpk_no_limits(self):
        """Test Cpk with no limits."""
        data = np.array([10, 11, 12, 13, 14])
        result = calculate_cpk(data, lsl=None, usl=None)

        assert result['cp'] is None
        assert result['cpk'] is None

    def test_cpk_empty_data(self):
        """Test Cpk with empty data."""
        data = np.array([])
        result = calculate_cpk(data, lsl=0, usl=100)

        assert result['cp'] is None
        assert result['cpk'] is None


class TestCalculateYield:
    """Tests for calculate_yield function."""

    def test_yield_all_pass(self):
        """Test yield when all values pass."""
        data = np.array([10, 11, 12, 13, 14])
        result = calculate_yield(data, lsl=5, usl=20)

        assert result['total'] == 5
        assert result['pass_count'] == 5
        assert result['fail_count'] == 0
        assert result['pass_pct'] == 100.0
        assert result['fail_pct'] == 0.0

    def test_yield_all_fail(self):
        """Test yield when all values fail."""
        data = np.array([1, 2, 3, 4, 5])
        result = calculate_yield(data, lsl=10, usl=20)

        assert result['total'] == 5
        assert result['pass_count'] == 0
        assert result['fail_count'] == 5
        assert result['pass_pct'] == 0.0
        assert result['fail_pct'] == 100.0

    def test_yield_mixed(self):
        """Test yield with mixed pass/fail."""
        data = np.array([5, 10, 15, 20, 25])  # 10, 15, 20 pass
        result = calculate_yield(data, lsl=8, usl=22)

        assert result['total'] == 5
        assert result['pass_count'] == 3
        assert result['fail_count'] == 2
        assert result['pass_pct'] == 60.0
        assert result['fail_pct'] == 40.0

    def test_yield_only_lsl(self):
        """Test yield with only LSL."""
        data = np.array([5, 10, 15, 20, 25])
        result = calculate_yield(data, lsl=12, usl=None)

        assert result['pass_count'] == 3  # 15, 20, 25 pass
        assert result['fail_low_count'] == 2  # 5, 10 fail

    def test_yield_only_usl(self):
        """Test yield with only USL."""
        data = np.array([5, 10, 15, 20, 25])
        result = calculate_yield(data, lsl=None, usl=18)

        assert result['pass_count'] == 3  # 5, 10, 15 pass
        assert result['fail_high_count'] == 2  # 20, 25 fail

    def test_yield_empty_data(self):
        """Test yield with empty data."""
        data = np.array([])
        result = calculate_yield(data, lsl=0, usl=100)

        assert result['total'] == 0
        assert result['pass_count'] == 0


class TestCalculateBinSummary:
    """Tests for calculate_bin_summary function."""

    def test_bin_summary_basic(self):
        """Test basic bin summary."""
        bins = np.array([1, 1, 1, 2, 2, 3])
        result = calculate_bin_summary(bins)

        assert 1 in result
        assert 2 in result
        assert 3 in result
        assert result[1]['count'] == 3
        assert result[2]['count'] == 2
        assert result[3]['count'] == 1
        assert result[1]['percent'] == 50.0

    def test_bin_summary_single_bin(self):
        """Test bin summary with single bin type."""
        bins = np.array([1, 1, 1, 1, 1])
        result = calculate_bin_summary(bins)

        assert len(result) == 1
        assert result[1]['count'] == 5
        assert result[1]['percent'] == 100.0

    def test_bin_summary_empty(self):
        """Test bin summary with empty array."""
        bins = np.array([])
        result = calculate_bin_summary(bins)

        assert result == {}


class TestCalculateGRR:
    """Tests for calculate_grr function."""

    def test_grr_basic(self):
        """Test basic GRR calculation."""
        # 3 operators, 2 parts, 3 trials each
        measurements = np.array([
            [10.1, 10.2, 10.0],  # Op1, Part1
            [10.0, 10.1, 10.1],  # Op1, Part2
            [10.2, 10.1, 10.0],  # Op2, Part1
            [10.0, 10.0, 10.1],  # Op2, Part2
            [10.1, 10.0, 10.2],  # Op3, Part1
            [10.1, 10.1, 10.0],  # Op3, Part2
        ])

        result = calculate_grr(measurements)

        assert 'grr_pct' in result
        assert 'repeatability_pct' in result
        assert 'reproducibility_pct' in result
        assert 'ndc' in result
        assert result['grr_pct'] >= 0
        assert result['grr_pct'] <= 100

    def test_grr_empty(self):
        """Test GRR with empty measurements."""
        measurements = np.array([])
        result = calculate_grr(measurements)

        assert result['grr_pct'] == 0


class TestFormatStatValue:
    """Tests for format_stat_value function."""

    def test_format_large_value(self):
        """Test formatting large values."""
        result = format_stat_value(123456.789)
        assert '1.23' in result or '123' in result

    def test_format_small_value(self):
        """Test formatting small values."""
        result = format_stat_value(0.00123)
        assert '0.00123' in result or '1.23' in result

    def test_format_integer(self):
        """Test formatting integer values."""
        result = format_stat_value(42)
        assert '42' in result

    def test_format_zero(self):
        """Test formatting zero."""
        result = format_stat_value(0)
        assert '0' in result

    def test_format_none(self):
        """Test formatting None."""
        result = format_stat_value(None)
        assert result == "N/A" or result == "-"
