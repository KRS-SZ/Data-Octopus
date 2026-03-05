"""
Configuration Module for Data Octopus

Contains all constants, patterns, and configurations used across the application.
Centralized here to avoid duplication and make maintenance easier.
"""

# ============================================================================
# KNOWN GROUP TYPES
# Used by simplify_param_name() to remove group prefixes from parameter names
# ============================================================================
KNOWN_GROUP_TYPES = [
    'OPTIC', 'OPTICAL',
    'DC',
    'ANLG', 'ANALOG',
    'FUNC', 'FUNCTIONAL',
    'EFUSE',
    'INIT', 'INITIALIZE',
    'DIGITAL',
    'POWER',
    'SOT',
    'TEST',
    'MEAS',
]

# ============================================================================
# MAIN GROUPS for extract_group_from_column()
# ============================================================================
MAIN_GROUPS = [
    'DC', 'ANLG', 'ANALOG', 'OPTIC', 'OPTICAL', 'FUNC', 'FUNCTIONAL',
    'EFUSE', 'INIT', 'INITIALIZE', 'DIGITAL', 'POWER', 'TEST', 'MEAS'
]

# Normalize group names to standard form
GROUP_NORMALIZATION = {
    'ANALOG': 'ANLG',
    'OPTICAL': 'OPTIC',
    'FUNCTIONAL': 'FUNC',
    'INITIALIZE': 'INIT'
}

# ============================================================================
# DETAILED GROUP PATTERNS
# Used by extract_group_from_column() for precise group detection
# Format: (pattern_to_match, group_name)
# ============================================================================
DETAILED_GROUP_PATTERNS = [
    # DC subgroups
    ('DC_CONT', 'DC_CONT'),
    ('DC_LKG', 'DC_LKG'),
    ('DC_LEAKAGE', 'DC_LKG'),
    ('DC_IDD', 'DC_IDD'),
    ('DC_VDD', 'DC_VDD'),
    ('DC_IDDQ', 'DC_IDDQ'),
    ('DC_POWER', 'DC_POWER'),
    ('DC_DIODE', 'DC_DIODE'),
    ('DC_RES', 'DC_RES'),
    ('DC_CAP', 'DC_CAP'),
    ('DC_SHORT', 'DC_SHORT'),
    ('DC_OPEN', 'DC_OPEN'),
    ('DC_CLAMP', 'DC_CLAMP'),
    ('DC_PMU', 'DC_PMU'),
    ('DC_FORCE', 'DC_FORCE'),
    ('DC_MEAS', 'DC_MEAS'),

    # ANALOG subgroups
    ('ANLG_ADC', 'ANLG_ADC'),
    ('ANLG_DAC', 'ANLG_DAC'),
    ('ANLG_BANDGAP', 'ANLG_BANDGAP'),
    ('ANLG_PLL', 'ANLG_PLL'),
    ('ANLG_OSC', 'ANLG_OSC'),
    ('ANLG_LDO', 'ANLG_LDO'),
    ('ANLG_AMP', 'ANLG_AMP'),
    ('ANLG_COMP', 'ANLG_COMP'),
    ('ANLG_REF', 'ANLG_REF'),
    ('ANLG_BIAS', 'ANLG_BIAS'),
    ('ANLG_TRIM', 'ANLG_TRIM'),
    ('ANLG_DISPLAYI', 'ANLG_DISPLAYI'),
    ('ANALOG_ADC', 'ANLG_ADC'),
    ('ANALOG_DAC', 'ANLG_DAC'),
    ('ANALOG_BANDGAP', 'ANLG_BANDGAP'),
    ('ANALOG_PLL', 'ANLG_PLL'),

    # OPTIC/OPTICAL subgroups
    ('OPTIC_ANSI', 'OPTIC_ANSI'),
    ('OPTIC_IEC', 'OPTIC_IEC'),
    ('OPTIC_POWER', 'OPTIC_POWER'),
    ('OPTIC_CURRENT', 'OPTIC_CURRENT'),
    ('OPTIC_THRESHOLD', 'OPTIC_THRESHOLD'),
    ('OPTIC_SLOPE', 'OPTIC_SLOPE'),
    ('OPTIC_LIV', 'OPTIC_LIV'),
    ('OPTIC_WAVE', 'OPTIC_WAVE'),
    ('OPTIC_SPEC', 'OPTIC_SPEC'),
    ('OPTIC_EYE', 'OPTIC_EYE'),
    ('OPTIC_MOD', 'OPTIC_MOD'),
    ('OPTIC_EXT', 'OPTIC_EXT'),
    ('OPTIC_SENS', 'OPTIC_SENS'),
    ('OPTIC_RESP', 'OPTIC_RESP'),
    ('OPTIC_DARK', 'OPTIC_DARK'),
    ('OPTIC_PREWARMUP', 'OPTIC_PREWARMUP'),
    ('OPTIC_WARMUP', 'OPTIC_WARMUP'),
    ('OPTICAL_ANSI', 'OPTIC_ANSI'),
    ('OPTICAL_IEC', 'OPTIC_IEC'),
    ('OPTICAL_POWER', 'OPTIC_POWER'),

    # FUNC/FUNCTIONAL subgroups
    ('FUNC_BIST', 'FUNC_BIST'),
    ('FUNC_SCAN', 'FUNC_SCAN'),
    ('FUNC_MBIST', 'FUNC_MBIST'),
    ('FUNC_LBIST', 'FUNC_LBIST'),
    ('FUNC_JTAG', 'FUNC_JTAG'),
    ('FUNC_GPIO', 'FUNC_GPIO'),
    ('FUNC_SPI', 'FUNC_SPI'),
    ('FUNC_I2C', 'FUNC_I2C'),
    ('FUNC_I3C', 'FUNC_I3C'),
    ('FUNC_UART', 'FUNC_UART'),
    ('FUNC_MEM', 'FUNC_MEM'),
    ('FUNC_LOGIC', 'FUNC_LOGIC'),
    ('FUNCTIONAL_BIST', 'FUNC_BIST'),
    ('FUNCTIONAL_SCAN', 'FUNC_SCAN'),

    # EFUSE subgroups
    ('EFUSE_PROG', 'EFUSE_PROG'),
    ('EFUSE_READ', 'EFUSE_READ'),
    ('EFUSE_VERIFY', 'EFUSE_VERIFY'),
    ('EFUSE_TRIM', 'EFUSE_TRIM'),

    # INIT/INITIALIZE subgroups
    ('INIT_POWER', 'INIT_POWER'),
    ('INIT_RESET', 'INIT_RESET'),
    ('INIT_CONFIG', 'INIT_CONFIG'),
    ('INITIALIZE_POWER', 'INIT_POWER'),
    ('INITIALIZE_RESET', 'INIT_RESET'),

    # DIGITAL subgroups
    ('DIGITAL_IO', 'DIGITAL_IO'),
    ('DIGITAL_TIMING', 'DIGITAL_TIMING'),
    ('DIGITAL_FREQ', 'DIGITAL_FREQ'),
    ('DIGITAL_CLK', 'DIGITAL_CLK'),

    # POWER subgroups
    ('POWER_SUPPLY', 'POWER_SUPPLY'),
    ('POWER_RAIL', 'POWER_RAIL'),
    ('POWER_CONS', 'POWER_CONS'),

    # TEST subgroups
    ('TEST_SETUP', 'TEST_SETUP'),
    ('TEST_MEAS', 'TEST_MEAS'),
]

# Fallback prefixes for simple group detection
GROUP_PREFIXES = [
    'OPTIC', 'OPTICAL', 'DC', 'ELECTRICAL', 'ANALOG', 'ANLG', 'DIGITAL',
    'POWER', 'SIGNAL', 'TEST', 'MEAS', 'PARAM', 'FUNC', 'EFUSE', 'INIT'
]

# ============================================================================
# CLEANUP PATTERNS
# Patterns to remove from parameter names during simplification
# ============================================================================
CLEANUP_PATTERNS = [
    'FREERUN',
    'INTFRAME',
    '_NV_',
    '_PEQA_',
    '_X_X_X',
]

# ============================================================================
# VALUE CONVERSION PATTERNS
# Regular expressions for converting coded values in parameter names
# Format: (pattern, description)
# ============================================================================
VALUE_PATTERNS = {
    # FV (Force Voltage): FV0P1 → 0.1V, FV1P8 → 1.8V
    'FV': {
        'pattern': r'FV(\d+)P(\d+)',
        'format': '{0}.{1}V',
        'description': 'Force Voltage'
    },
    # FC (Force Current): FC0P2 → 0.2mA, FCn0P2 → -0.2mA
    'FC': {
        'pattern': r'FC([np]?)(\d+)P(\d+)',
        'format': '{sign}{1}.{2}mA',
        'description': 'Force Current (n=negative)'
    },
    # AVEE (Voltage): AVEEn1p8 → -1.80V
    'AVEE': {
        'pattern': r'AVEE([np]?)(\d+)p(\d+)',
        'format': '{sign}{1}.{2:02}V',
        'description': 'AVEE Voltage'
    },
    # DACI (Current): DACI3p0 → 3.00uA
    'DACI': {
        'pattern': r'DACI([np]?)(\d+)p(\d+)',
        'format': '{sign}{1}.{2:02}uA',
        'description': 'DAC Current'
    },
    # DC (Duty Cycle): DC4p59 → 4.59%
    'DC_PERCENT': {
        'pattern': r'(?<![A-Z])DC(\d+)p(\d+)',
        'format': '{0}.{1}%',
        'description': 'Duty Cycle'
    },
}

# ============================================================================
# APPLICATION DEFAULTS
# ============================================================================
DEFAULT_COLORMAP = 'RdYlGn_r'  # Red-Yellow-Green reversed (green=good)
DEFAULT_WAFER_SIZE = 300  # mm (12 inch wafer)
DEFAULT_NOTCH_ORIENTATION = 'D'  # Down

# Max values for UI
MAX_PARAMETERS_IN_DROPDOWN = 500
MAX_WAFERS_IN_LIST = 100

# File extensions
STDF_EXTENSIONS = ['.stdf', '.std']
CSV_EXTENSIONS = ['.csv', '.txt']
EXCEL_EXTENSIONS = ['.xlsx', '.xls']

# ============================================================================
# PLM (Pixel Light Measurement) TYPES
# ============================================================================
PLM_TYPES = [
    'Bridged',
    'Bridged-Pixels',
    'Stitched',
    'UniformitySyn',
    'CDMEAN',
    'CDSTDDEV',
]

# PLM Region colors for visualization
PLM_REGION_COLORS = [
    '#FF6B6B',  # Red
    '#4ECDC4',  # Teal
    '#45B7D1',  # Blue
    '#96CEB4',  # Green
    '#FFEAA7',  # Yellow
    '#DDA0DD',  # Plum
    '#98D8C8',  # Mint
    '#F7DC6F',  # Gold
    '#BB8FCE',  # Purple
    '#85C1E9',  # Light Blue
]

# ============================================================================
# GRR (Gage R&R) THRESHOLDS
# ============================================================================
GRR_THRESHOLDS = {
    'excellent': 10,    # %GRR < 10% = Excellent
    'acceptable': 30,   # 10% <= %GRR < 30% = Acceptable
    'ndc_min': 5,       # Number of Distinct Categories minimum
}
