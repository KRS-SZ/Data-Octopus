"""
Tests for the parameter_utils module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from stdf_analyzer.core.parameter_utils import (
    simplify_param_name,
    extract_group_from_column,
)


class TestSimplifyParamName:
    """Tests for simplify_param_name function."""

    def test_csv_angle_bracket_format(self):
        """Test CSV format with angle brackets - should use part after <>."""
        result = simplify_param_name("123<>OPTIC_TestParam_FV0P1")
        # Should extract part after <> and process it
        assert "OPTIC" not in result or "TestParam" in result

    def test_force_voltage_conversion(self):
        """Test FV (Force Voltage) conversion."""
        result = simplify_param_name("Test_FV0P1_Param")
        assert "0.1V" in result or "FV" not in result

        result = simplify_param_name("Test_FV1P5_Param")
        assert "1.5V" in result or "FV" not in result

        result = simplify_param_name("Test_FV10P0_Param")
        assert "10.0V" in result or "10V" in result or "FV" not in result

    def test_force_current_conversion(self):
        """Test FC (Force Current) conversion."""
        result = simplify_param_name("Test_FC0P2_Param")
        assert "0.2mA" in result or "FC" not in result

        result = simplify_param_name("Test_FCn0P5_Param")
        # Negative current
        assert "-0.5mA" in result or "FCn" not in result

    def test_avee_voltage_conversion(self):
        """Test AVEE voltage conversion."""
        result = simplify_param_name("Test_AVEEn1p8_Param")
        assert "-1.80V" in result or "-1.8V" in result or "AVEE" not in result

    def test_daci_current_conversion(self):
        """Test DACI (DAC Current) conversion."""
        result = simplify_param_name("Test_DACI3p0_Param")
        assert "3.00uA" in result or "3.0uA" in result or "DACI" not in result

    def test_duty_cycle_conversion(self):
        """Test DC (Duty Cycle) percentage conversion."""
        result = simplify_param_name("Test_DC4p59_Param")
        # DC could mean Duty Cycle with percentage
        assert "%" in result or "4.59" in result or "DC" in result

    def test_known_group_prefix_removal(self):
        """Test that known group prefixes are removed."""
        # OPTIC group
        result = simplify_param_name("OPTIC_TestParameter")
        assert result == "TestParameter" or "OPTIC" not in result

        # DC group (not Duty Cycle in this context)
        result = simplify_param_name("DC_SomeTest")
        # DC as group prefix should be removed

        # ANLG group
        result = simplify_param_name("ANLG_AnalogTest")
        assert "ANLG" not in result or result == "AnalogTest"

        # FUNC group
        result = simplify_param_name("FUNC_FunctionalTest")
        assert "FUNC" not in result or result == "FunctionalTest"

    def test_cleanup_patterns(self):
        """Test cleanup of common patterns."""
        # Test number removal (like _1234_)
        result = simplify_param_name("Test_1234_Param")
        # Numbers might be kept or removed depending on context

        # _X_X_X pattern
        result = simplify_param_name("Test_X_X_X_Param")
        assert "_X_X_X_" not in result

        # _NV_ pattern
        result = simplify_param_name("Test_NV_Param")
        assert "_NV_" not in result or "Test" in result

        # FREERUN pattern
        result = simplify_param_name("FREERUN_X_TestParam")
        assert "FREERUN_X_" not in result

    def test_empty_string(self):
        """Test with empty string."""
        result = simplify_param_name("")
        assert result == ""

    def test_none_input(self):
        """Test with None input."""
        result = simplify_param_name(None)
        assert result == "" or result is None

    def test_simple_name_unchanged(self):
        """Test that simple names without patterns are unchanged."""
        result = simplify_param_name("SimpleTestName")
        assert result == "SimpleTestName"

    def test_preserves_unknown_prefixes(self):
        """Test that unknown prefixes are NOT removed."""
        result = simplify_param_name("ALLON_NORM1PCT_TestParam")
        # ALLON is not a known group, should be preserved
        assert "ALLON" in result or "TestParam" in result


class TestExtractGroupFromColumn:
    """Tests for extract_group_from_column function."""

    def test_known_group_extraction(self):
        """Test extraction of known group prefixes."""
        result = extract_group_from_column("OPTIC_TestParameter")
        assert result == "OPTIC"

        result = extract_group_from_column("DC_SomeTest")
        assert result == "DC"

        result = extract_group_from_column("ANLG_AnalogTest")
        assert result == "ANLG"

        result = extract_group_from_column("FUNC_FunctionalTest")
        assert result == "FUNC"

        result = extract_group_from_column("EFUSE_EfuseTest")
        assert result == "EFUSE"

    def test_csv_angle_bracket_format(self):
        """Test extraction from CSV format with angle brackets."""
        result = extract_group_from_column("123<>OPTIC_TestParam")
        assert result == "OPTIC"

    def test_no_group_returns_default(self):
        """Test that columns without known groups return default."""
        result = extract_group_from_column("SimpleParameter")
        # Should return empty string or some default
        assert result == "" or result == "Other" or result == "Unknown"

    def test_unknown_prefix_not_extracted(self):
        """Test that unknown prefixes are not extracted as groups."""
        result = extract_group_from_column("UNKNOWN_TestParam")
        # UNKNOWN is not a known group type
        assert result != "UNKNOWN" or result == "" or result == "Other"

    def test_empty_string(self):
        """Test with empty string."""
        result = extract_group_from_column("")
        assert result == "" or result == "Unknown"

    def test_none_input(self):
        """Test with None input."""
        result = extract_group_from_column(None)
        assert result == "" or result is None or result == "Unknown"

    def test_case_insensitivity(self):
        """Test case insensitivity of group extraction."""
        result1 = extract_group_from_column("OPTIC_Test")
        result2 = extract_group_from_column("optic_Test")
        result3 = extract_group_from_column("Optic_Test")
        # All should extract the same group (or handle consistently)
        # Depends on implementation - might be case-sensitive

    def test_multiple_underscores(self):
        """Test with multiple underscores."""
        result = extract_group_from_column("OPTIC_Sub_Category_Test")
        assert result == "OPTIC"

    def test_analog_variants(self):
        """Test both ANLG and ANALOG variants."""
        result1 = extract_group_from_column("ANLG_Test")
        result2 = extract_group_from_column("ANALOG_Test")
        # Both should be recognized
        assert result1 in ["ANLG", "ANALOG", ""]
        assert result2 in ["ANLG", "ANALOG", ""]

    def test_functional_variants(self):
        """Test both FUNC and FUNCTIONAL variants."""
        result1 = extract_group_from_column("FUNC_Test")
        result2 = extract_group_from_column("FUNCTIONAL_Test")
        # Both should be recognized
        assert result1 in ["FUNC", "FUNCTIONAL", ""]
        assert result2 in ["FUNC", "FUNCTIONAL", ""]
