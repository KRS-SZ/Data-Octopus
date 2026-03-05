"""
PLM Image Analyzer - Core Module for PLM Image Analysis
Version 6.0.0

Analyzes PLM (Per-pixel Luminance Measurement) images for defects:
- Uniformity Analysis: Hot/Cold spots, brightness deviation
- Bridged Pixel Detection: Electrically connected pixels
- Stuck Pixel Detection: Pixels that don't switch
- Cluster Detection: Groups of adjacent defects

PLM Image Format:
- Stitched: 768x568 raw pixel values (nits)
- UniformitySyn: Pre-calculated uniformity map
- Bridged-Pixels: Pre-calculated bridged pixel map
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os
import re


class DefectType(Enum):
    """Defect types for PLM analysis"""
    OK = 0
    BRIDGED_MINOR = 10
    BRIDGED_MAJOR = 11
    UNIFORMITY_MINOR = 20
    UNIFORMITY_MAJOR = 21
    STUCK_ON = 30
    STUCK_OFF = 31
    DEAD_PIXEL = 40
    CLUSTER = 50
    # NEW defect types
    GRADIENT = 60
    MURA = 70
    LINE_DEFECT = 80
    COLUMN_DEFECT = 81
    HOT_SPOT = 90
    COLD_SPOT = 91


# Default color mapping for defect types
DEFECT_COLORS = {
    DefectType.OK: '#00C853',              # Green
    DefectType.BRIDGED_MINOR: '#FF6B6B',   # Light Red
    DefectType.BRIDGED_MAJOR: '#D32F2F',   # Dark Red
    DefectType.UNIFORMITY_MINOR: '#FFD54F', # Light Yellow
    DefectType.UNIFORMITY_MAJOR: '#FF8F00', # Orange
    DefectType.STUCK_ON: '#42A5F5',        # Light Blue
    DefectType.STUCK_OFF: '#1565C0',       # Dark Blue
    DefectType.DEAD_PIXEL: '#424242',      # Dark Gray
    DefectType.CLUSTER: '#AB47BC',         # Purple
    # NEW colors
    DefectType.GRADIENT: '#00BCD4',        # Cyan
    DefectType.MURA: '#E91E63',            # Pink
    DefectType.LINE_DEFECT: '#795548',     # Brown
    DefectType.COLUMN_DEFECT: '#8D6E63',   # Light Brown
    DefectType.HOT_SPOT: '#FF5722',        # Deep Orange
    DefectType.COLD_SPOT: '#3F51B5',       # Indigo
}

DEFECT_NAMES = {
    DefectType.OK: 'OK',
    DefectType.BRIDGED_MINOR: 'Bridged (Minor)',
    DefectType.BRIDGED_MAJOR: 'Bridged (Major)',
    DefectType.UNIFORMITY_MINOR: 'Uniformity (Minor)',
    DefectType.UNIFORMITY_MAJOR: 'Uniformity (Major)',
    DefectType.STUCK_ON: 'Stuck ON',
    DefectType.STUCK_OFF: 'Stuck OFF',
    DefectType.DEAD_PIXEL: 'Dead Pixel',
    DefectType.CLUSTER: 'Cluster',
    # NEW names
    DefectType.GRADIENT: 'Gradient',
    DefectType.MURA: 'Mura',
    DefectType.LINE_DEFECT: 'Line Defect',
    DefectType.COLUMN_DEFECT: 'Column Defect',
    DefectType.HOT_SPOT: 'Hot Spot',
    DefectType.COLD_SPOT: 'Cold Spot',
}


@dataclass
class AnalysisThresholds:
    """Configurable thresholds for PLM analysis"""
    # Uniformity thresholds
    uniformity_sigma_minor: float = 2.0      # σ multiplier for minor deviation
    uniformity_sigma_major: float = 3.0      # σ multiplier for major deviation
    uniformity_local_size: int = 10          # Block size for local uniformity

    # Bridged pixel thresholds
    bridged_min_count: int = 3               # Min connected pixels for bridged
    bridged_brightness_threshold: float = 0.8  # % of max brightness to consider "on"

    # Stuck pixel thresholds (relative to data range!)
    stuck_variance_threshold: float = 5.0    # Max variance to consider stuck
    stuck_on_percentile: float = 99.5        # Percentile above which = stuck ON
    stuck_off_percentile: float = 0.5        # Percentile below which = stuck OFF
    stuck_use_percentile: bool = True        # Use percentile instead of absolute

    # Cluster thresholds
    cluster_min_size: int = 5                # Min defects to form a cluster

    # Die-level thresholds for PASS/FAIL
    die_fail_bridged: int = 5                # Max bridged pixels for PASS
    die_fail_uniformity: int = 10            # Max uniformity defects for PASS
    die_fail_stuck: int = 3                  # Max stuck pixels for PASS


@dataclass
class PixelDefect:
    """Single pixel defect"""
    x: int
    y: int
    defect_type: DefectType
    value: float = 0.0
    cluster_id: int = -1


@dataclass
class AnalysisResult:
    """Result of PLM analysis for a single die"""
    die_x: int
    die_y: int
    plm_type: str
    image_width: int = 768
    image_height: int = 568

    # Raw image data
    raw_image: Optional[np.ndarray] = None

    # Defect map (same size as image)
    defect_map: Optional[np.ndarray] = None

    # List of defects
    defects: List[PixelDefect] = field(default_factory=list)

    # Statistics
    total_pixels: int = 0
    mean_brightness: float = 0.0
    std_brightness: float = 0.0

    # Defect counts
    bridged_count: int = 0
    uniformity_count: int = 0
    stuck_count: int = 0
    dead_count: int = 0
    cluster_count: int = 0

    # Overall result
    passed: bool = True
    fail_reason: str = ""

    def get_defect_percentage(self) -> float:
        """Return percentage of defective pixels"""
        total_defects = self.bridged_count + self.uniformity_count + self.stuck_count + self.dead_count
        if self.total_pixels == 0:
            return 0.0
        return (total_defects / self.total_pixels) * 100


class PLMImage:
    """Class to load and parse PLM image files"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.width = 0  # Auto-detect from data
        self.height = 0  # Auto-detect from data
        self.data: Optional[np.ndarray] = None
        self.plm_type = self._detect_plm_type(file_path)
        self.metadata = {}

    def _detect_plm_type(self, file_path: str) -> str:
        """Detect PLM type from filename"""
        filename = os.path.basename(file_path).lower()

        if 'uniformity' in filename or 'uniformitysyn' in filename:
            return 'Uniformity'
        elif 'stitched' in filename:
            return 'Stitched'
        elif 'bridged' in filename and 'map' not in filename:
            return 'Bridged'
        else:
            return 'Unknown'

    def load(self) -> bool:
        """Load PLM file and parse pixel data"""
        try:
            if not os.path.exists(self.file_path):
                print(f"PLM file not found: {self.file_path}")
                return False

            with open(self.file_path, 'r') as f:
                lines = f.readlines()

            if not lines:
                print(f"Empty PLM file: {self.file_path}")
                return False

            # Detect file format and parse
            data_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for header lines
                if ':' in line and not line[0].isdigit():
                    # Parse header fields
                    if line.startswith('Columns:'):
                        try:
                            self.width = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif line.startswith('Rows:'):
                        try:
                            self.height = int(line.split(':')[1].strip())
                        except:
                            pass
                    continue

                # Try to parse as data line (comma-separated numbers)
                if ',' in line:
                    try:
                        values = [float(v.strip()) for v in line.split(',') if v.strip()]
                        if values:
                            data_lines.append(values)
                    except ValueError:
                        continue

            if not data_lines:
                print(f"No valid data found in PLM file: {self.file_path}")
                return False

            # Auto-detect dimensions from data
            self.height = len(data_lines)
            self.width = len(data_lines[0]) if data_lines else 0

            # Convert to numpy array
            self.data = np.array(data_lines, dtype=np.float32)

            print(f"Loaded PLM: {self.plm_type}, {self.width}x{self.height}, range: {np.min(self.data):.0f}-{np.max(self.data):.0f}")

            return True

        except Exception as e:
            print(f"Error loading PLM file {self.file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_statistics(self) -> Dict[str, float]:
        """Get basic statistics of the image"""
        if self.data is None:
            return {}

        return {
            'min': float(np.min(self.data)),
            'max': float(np.max(self.data)),
            'mean': float(np.mean(self.data)),
            'std': float(np.std(self.data)),
            'median': float(np.median(self.data)),
        }


class UniformityAnalyzer:
    """Analyze uniformity of PLM images"""

    def __init__(self, thresholds: AnalysisThresholds):
        self.thresholds = thresholds

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, List[PixelDefect]]:
        """
        Analyze uniformity of the image.
        Returns defect map and list of defects.
        """
        if image is None or image.size == 0:
            return np.zeros((568, 768), dtype=np.int32), []

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Calculate global statistics
        mean = np.mean(image)
        std = np.std(image)

        if std == 0:
            # All pixels same value - perfect uniformity (or dead image)
            return defect_map, defects

        # Calculate deviation for each pixel
        deviation = np.abs(image - mean) / std

        # Mark minor uniformity issues
        minor_mask = (deviation > self.thresholds.uniformity_sigma_minor) & \
                     (deviation <= self.thresholds.uniformity_sigma_major)
        defect_map[minor_mask] = DefectType.UNIFORMITY_MINOR.value

        # Mark major uniformity issues
        major_mask = deviation > self.thresholds.uniformity_sigma_major
        defect_map[major_mask] = DefectType.UNIFORMITY_MAJOR.value

        # Create defect list
        for y, x in zip(*np.where(minor_mask)):
            defects.append(PixelDefect(
                x=int(x), y=int(y),
                defect_type=DefectType.UNIFORMITY_MINOR,
                value=float(image[y, x])
            ))

        for y, x in zip(*np.where(major_mask)):
            defects.append(PixelDefect(
                x=int(x), y=int(y),
                defect_type=DefectType.UNIFORMITY_MAJOR,
                value=float(image[y, x])
            ))

        return defect_map, defects

    def analyze_local(self, image: np.ndarray) -> Tuple[np.ndarray, List[PixelDefect]]:
        """
        Analyze local uniformity using block-based comparison.
        More sensitive to local variations.
        """
        if image is None or image.size == 0:
            return np.zeros((568, 768), dtype=np.int32), []

        height, width = image.shape
        block_size = self.thresholds.uniformity_local_size
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Process in blocks
        for by in range(0, height, block_size):
            for bx in range(0, width, block_size):
                # Extract block
                block = image[by:min(by+block_size, height),
                             bx:min(bx+block_size, width)]

                if block.size == 0:
                    continue

                block_mean = np.mean(block)
                block_std = np.std(block)

                if block_std == 0:
                    continue

                # Check each pixel in block
                for ly in range(block.shape[0]):
                    for lx in range(block.shape[1]):
                        y, x = by + ly, bx + lx
                        deviation = abs(block[ly, lx] - block_mean) / block_std

                        if deviation > self.thresholds.uniformity_sigma_major:
                            defect_map[y, x] = DefectType.UNIFORMITY_MAJOR.value
                            defects.append(PixelDefect(
                                x=x, y=y,
                                defect_type=DefectType.UNIFORMITY_MAJOR,
                                value=float(image[y, x])
                            ))
                        elif deviation > self.thresholds.uniformity_sigma_minor:
                            defect_map[y, x] = DefectType.UNIFORMITY_MINOR.value
                            defects.append(PixelDefect(
                                x=x, y=y,
                                defect_type=DefectType.UNIFORMITY_MINOR,
                                value=float(image[y, x])
                            ))

        return defect_map, defects


class BridgedPixelAnalyzer:
    """Detect bridged (electrically connected) pixels"""

    def __init__(self, thresholds: AnalysisThresholds):
        self.thresholds = thresholds

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, List[PixelDefect]]:
        """
        Analyze image for bridged pixels.
        Bridged pixels appear as bright connected regions.
        """
        if image is None or image.size == 0:
            return np.zeros((568, 768), dtype=np.int32), []

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Threshold for "on" pixels
        max_val = np.max(image)
        threshold = max_val * self.thresholds.bridged_brightness_threshold

        # Find bright pixels
        bright_mask = image > threshold

        # Find connected components using simple flood-fill approach
        visited = np.zeros((height, width), dtype=bool)

        for y in range(height):
            for x in range(width):
                if bright_mask[y, x] and not visited[y, x]:
                    # Start flood fill
                    component = []
                    stack = [(y, x)]

                    while stack:
                        cy, cx = stack.pop()
                        if cy < 0 or cy >= height or cx < 0 or cx >= width:
                            continue
                        if visited[cy, cx] or not bright_mask[cy, cx]:
                            continue

                        visited[cy, cx] = True
                        component.append((cy, cx))

                        # 4-connectivity
                        stack.extend([
                            (cy-1, cx), (cy+1, cx),
                            (cy, cx-1), (cy, cx+1)
                        ])

                    # Check if component is bridged (more than threshold pixels)
                    if len(component) >= self.thresholds.bridged_min_count:
                        defect_type = DefectType.BRIDGED_MAJOR if len(component) >= 5 else DefectType.BRIDGED_MINOR

                        for py, px in component:
                            defect_map[py, px] = defect_type.value
                            defects.append(PixelDefect(
                                x=px, y=py,
                                defect_type=defect_type,
                                value=float(image[py, px])
                            ))

        return defect_map, defects


class StuckPixelAnalyzer:
    """Detect stuck pixels (always on or always off)"""

    def __init__(self, thresholds: AnalysisThresholds):
        self.thresholds = thresholds

    def analyze_single(self, image: np.ndarray) -> Tuple[np.ndarray, List[PixelDefect]]:
        """
        Analyze single image for stuck pixels based on extreme values.
        Uses percentile-based thresholds to work with any data range (nits, 8-bit, etc.)
        """
        if image is None or image.size == 0:
            return np.zeros((568, 768), dtype=np.int32), []

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Use PERCENTILE-based thresholds (works for any data range!)
        stuck_on_threshold = np.percentile(image, self.thresholds.stuck_on_percentile)
        stuck_off_threshold = np.percentile(image, self.thresholds.stuck_off_percentile)

        print(f"Stuck thresholds: ON > {stuck_on_threshold:.0f} (P{self.thresholds.stuck_on_percentile}), "
              f"OFF < {stuck_off_threshold:.0f} (P{self.thresholds.stuck_off_percentile})")

        # Find stuck ON pixels (above 99.5th percentile)
        stuck_on_mask = image >= stuck_on_threshold
        stuck_on_count = np.sum(stuck_on_mask)

        # Find stuck OFF pixels (below 0.5th percentile)
        stuck_off_mask = image <= stuck_off_threshold
        stuck_off_count = np.sum(stuck_off_mask)

        print(f"Found {stuck_on_count} stuck ON pixels, {stuck_off_count} stuck OFF pixels")

        # Only create defect entries if count is reasonable (< 1% of image)
        max_defects = int(image.size * 0.01)  # Max 1% of pixels

        if stuck_on_count <= max_defects:
            for y, x in zip(*np.where(stuck_on_mask)):
                defect_map[y, x] = DefectType.STUCK_ON.value
                defects.append(PixelDefect(
                    x=int(x), y=int(y),
                    defect_type=DefectType.STUCK_ON,
                    value=float(image[y, x])
                ))

        if stuck_off_count <= max_defects:
            for y, x in zip(*np.where(stuck_off_mask)):
                if defect_map[y, x] == 0:
                    defect_map[y, x] = DefectType.STUCK_OFF.value
                    defects.append(PixelDefect(
                        x=int(x), y=int(y),
                        defect_type=DefectType.STUCK_OFF,
                        value=float(image[y, x])
                    ))

        return defect_map, defects

        return defect_map, defects

    def analyze_multi(self, images: List[np.ndarray]) -> Tuple[np.ndarray, List[PixelDefect]]:
        """
        Analyze multiple images to find truly stuck pixels.
        Stuck pixels have very low variance across images.
        """
        if not images or len(images) < 2:
            if images:
                return self.analyze_single(images[0])
            return np.zeros((568, 768), dtype=np.int32), []

        # Stack images and calculate variance per pixel
        stack = np.stack(images, axis=0)
        variance = np.var(stack, axis=0)
        mean_values = np.mean(stack, axis=0)

        height, width = images[0].shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Low variance + high value = stuck ON
        stuck_on_mask = (variance < self.thresholds.stuck_variance_threshold) & \
                        (mean_values > self.thresholds.stuck_on_threshold)

        # Low variance + low value = stuck OFF
        stuck_off_mask = (variance < self.thresholds.stuck_variance_threshold) & \
                         (mean_values < self.thresholds.stuck_off_threshold)

        for y, x in zip(*np.where(stuck_on_mask)):
            defect_map[y, x] = DefectType.STUCK_ON.value
            defects.append(PixelDefect(
                x=int(x), y=int(y),
                defect_type=DefectType.STUCK_ON,
                value=float(mean_values[y, x])
            ))

        for y, x in zip(*np.where(stuck_off_mask)):
            defect_map[y, x] = DefectType.STUCK_OFF.value
            defects.append(PixelDefect(
                x=int(x), y=int(y),
                defect_type=DefectType.STUCK_OFF,
                value=float(mean_values[y, x])
            ))

        return defect_map, defects


class ClusterAnalyzer:
    """Detect clusters of defective pixels"""

    def __init__(self, thresholds: AnalysisThresholds):
        self.thresholds = thresholds

    def find_clusters(self, defect_map: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Find clusters of defects in the defect map.
        Returns updated map with cluster IDs and cluster count.
        """
        if defect_map is None:
            return np.zeros((568, 768), dtype=np.int32), 0

        height, width = defect_map.shape
        visited = np.zeros((height, width), dtype=bool)
        cluster_map = defect_map.copy()
        cluster_id = 0

        for y in range(height):
            for x in range(width):
                if defect_map[y, x] > 0 and not visited[y, x]:
                    # Found a defect - flood fill to find cluster
                    cluster_pixels = []
                    stack = [(y, x)]

                    while stack:
                        cy, cx = stack.pop()
                        if cy < 0 or cy >= height or cx < 0 or cx >= width:
                            continue
                        if visited[cy, cx] or defect_map[cy, cx] == 0:
                            continue

                        visited[cy, cx] = True
                        cluster_pixels.append((cy, cx))

                        # 8-connectivity for clusters
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if dy != 0 or dx != 0:
                                    stack.append((cy + dy, cx + dx))

                    # Mark as cluster if large enough
                    if len(cluster_pixels) >= self.thresholds.cluster_min_size:
                        cluster_id += 1
                        for py, px in cluster_pixels:
                            cluster_map[py, px] = DefectType.CLUSTER.value

        return cluster_map, cluster_id


class PLMAnalyzer:
    """Main PLM Analyzer class - coordinates all analysis types"""

    def __init__(self, thresholds: Optional[AnalysisThresholds] = None):
        self.thresholds = thresholds or AnalysisThresholds()
        self.uniformity_analyzer = UniformityAnalyzer(self.thresholds)
        self.bridged_analyzer = BridgedPixelAnalyzer(self.thresholds)
        self.stuck_analyzer = StuckPixelAnalyzer(self.thresholds)
        self.cluster_analyzer = ClusterAnalyzer(self.thresholds)

    def analyze_die(self, plm_files: List[str], die_x: int, die_y: int,
                    analysis_type: str = "all",
                    use_precalculated: bool = False) -> AnalysisResult:
        """
        Analyze PLM files for a single die.

        Args:
            plm_files: List of PLM file paths for this die
            die_x, die_y: Die coordinates
            analysis_type: "all", "uniformity", "bridged", "stuck"
            use_precalculated: If True, use pre-calculated PLM files (UniformitySyn, Bridged)
                              If False, calculate from Stitched (raw) image

        Returns:
            AnalysisResult with defect map and statistics
        """
        result = AnalysisResult(die_x=die_x, die_y=die_y, plm_type=analysis_type)

        # Load appropriate PLM file(s)
        stitched_image = None
        uniformity_image = None
        bridged_image = None

        for file_path in plm_files:
            plm = PLMImage(file_path)
            if plm.load():
                if plm.plm_type == 'Stitched':
                    stitched_image = plm.data
                elif plm.plm_type == 'Uniformity':
                    uniformity_image = plm.data
                elif plm.plm_type == 'Bridged':
                    bridged_image = plm.data

        # Choose which image to analyze
        if use_precalculated:
            # Use pre-calculated images if available
            analysis_image = uniformity_image if uniformity_image is not None else stitched_image
        else:
            # Use Stitched (raw) for self-calculation
            analysis_image = stitched_image if stitched_image is not None else uniformity_image

        if analysis_image is None:
            result.fail_reason = "No valid PLM image found"
            result.passed = False
            return result

        result.raw_image = analysis_image
        result.image_height, result.image_width = analysis_image.shape
        result.total_pixels = result.image_width * result.image_height
        result.mean_brightness = float(np.mean(analysis_image))
        result.std_brightness = float(np.std(analysis_image))

        # Initialize combined defect map
        combined_defect_map = np.zeros_like(analysis_image, dtype=np.int32)
        all_defects = []

        # Run analyses based on type
        if analysis_type in ["all", "uniformity"]:
            if use_precalculated and uniformity_image is not None:
                # Use pre-calculated uniformity
                defect_map, defects = self.uniformity_analyzer.analyze(uniformity_image)
            else:
                # Calculate from stitched
                defect_map, defects = self.uniformity_analyzer.analyze(analysis_image)

            combined_defect_map = np.maximum(combined_defect_map, defect_map)
            all_defects.extend(defects)
            result.uniformity_count = len(defects)

        if analysis_type in ["all", "bridged"]:
            if use_precalculated and bridged_image is not None:
                # Use pre-calculated bridged
                defect_map, defects = self.bridged_analyzer.analyze(bridged_image)
            else:
                # Calculate from stitched
                defect_map, defects = self.bridged_analyzer.analyze(analysis_image)

            # Only update where no defect yet (priority to uniformity)
            mask = combined_defect_map == 0
            combined_defect_map[mask] = defect_map[mask]
            all_defects.extend(defects)
            result.bridged_count = len(defects)

        if analysis_type in ["all", "stuck"]:
            defect_map, defects = self.stuck_analyzer.analyze_single(analysis_image)
            mask = combined_defect_map == 0
            combined_defect_map[mask] = defect_map[mask]
            all_defects.extend(defects)
            result.stuck_count = len(defects)

        # Find clusters
        if analysis_type == "all":
            combined_defect_map, cluster_count = self.cluster_analyzer.find_clusters(combined_defect_map)
            result.cluster_count = cluster_count

        result.defect_map = combined_defect_map
        result.defects = all_defects

        # Determine pass/fail
        result.passed = (
            result.bridged_count <= self.thresholds.die_fail_bridged and
            result.uniformity_count <= self.thresholds.die_fail_uniformity and
            result.stuck_count <= self.thresholds.die_fail_stuck
        )

        if not result.passed:
            reasons = []
            if result.bridged_count > self.thresholds.die_fail_bridged:
                reasons.append(f"Bridged: {result.bridged_count}")
            if result.uniformity_count > self.thresholds.die_fail_uniformity:
                reasons.append(f"Uniformity: {result.uniformity_count}")
            if result.stuck_count > self.thresholds.die_fail_stuck:
                reasons.append(f"Stuck: {result.stuck_count}")
            result.fail_reason = ", ".join(reasons)

        return result

    def analyze_wafer(self, plm_directory: str, die_coordinates: List[Tuple[int, int]],
                      analysis_type: str = "all",
                      use_precalculated: bool = False,
                      progress_callback=None) -> Dict[Tuple[int, int], AnalysisResult]:
        """
        Analyze all dies on a wafer.

        Args:
            plm_directory: Directory containing PLM files
            die_coordinates: List of (x, y) die coordinates to analyze
            analysis_type: Analysis type
            use_precalculated: Use pre-calculated PLM files
            progress_callback: Function(current, total) for progress updates

        Returns:
            Dictionary mapping (die_x, die_y) to AnalysisResult
        """
        results = {}
        total = len(die_coordinates)

        for i, (die_x, die_y) in enumerate(die_coordinates):
            if progress_callback:
                progress_callback(i, total)

            # Find PLM files for this die
            plm_files = self._find_plm_files_for_die(plm_directory, die_x, die_y)

            if plm_files:
                result = self.analyze_die(plm_files, die_x, die_y, analysis_type, use_precalculated)
                results[(die_x, die_y)] = result

        if progress_callback:
            progress_callback(total, total)

        return results

    def _find_plm_files_for_die(self, plm_dir: str, die_x: int, die_y: int) -> List[str]:
        """Find all PLM files for a specific die"""
        if not os.path.exists(plm_dir):
            return []

        matching_files = []

        # Patterns to match die coordinates in filename
        patterns = [
            rf'Die_X{die_x}_Y{die_y}[_\.]',
            rf'-X{die_x}-Y{die_y}[_\-]',
            rf'[_\-]X{die_x}[_\-]Y{die_y}[_\-\.]',
        ]

        try:
            for filename in os.listdir(plm_dir):
                if filename.lower().endswith(('.txt', '.plm', '.csv', '.dat')):
                    for pattern in patterns:
                        if re.search(pattern, filename, re.IGNORECASE):
                            matching_files.append(os.path.join(plm_dir, filename))
                            break
        except Exception as e:
            print(f"Error scanning PLM directory: {e}")

        return matching_files

    def generate_wafer_binning(self, results: Dict[Tuple[int, int], AnalysisResult]) -> Dict[Tuple[int, int], int]:
        """
        Generate wafer binning map from analysis results.

        Returns:
            Dictionary mapping (die_x, die_y) to bin number
        """
        binning = {}

        for (die_x, die_y), result in results.items():
            if result.passed:
                binning[(die_x, die_y)] = 1  # PASS
            elif result.bridged_count > self.thresholds.die_fail_bridged:
                if result.bridged_count >= 5:
                    binning[(die_x, die_y)] = 11  # BRIDGED_MAJOR
                else:
                    binning[(die_x, die_y)] = 10  # BRIDGED_MINOR
            elif result.uniformity_count > self.thresholds.die_fail_uniformity:
                if result.uniformity_count >= 10:
                    binning[(die_x, die_y)] = 21  # UNIFORMITY_MAJOR
                else:
                    binning[(die_x, die_y)] = 20  # UNIFORMITY_MINOR
            elif result.stuck_count > self.thresholds.die_fail_stuck:
                binning[(die_x, die_y)] = 30  # STUCK
            else:
                binning[(die_x, die_y)] = 50  # CLUSTER or other

        return binning


class GradientAnalyzer:
    """Analyze systematic brightness gradients across the image"""

    def __init__(self, zone_type: str = "quadrants", threshold_percent: float = 5.0):
        self.zone_type = zone_type  # "quadrants", "rings", "grid"
        self.threshold_percent = threshold_percent

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Analyze image for systematic brightness gradients.

        Returns:
            - defect_map: Pixels marked as gradient issues
            - metrics: Dictionary with gradient measurements
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.int32), {}

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        metrics = {}

        global_mean = np.mean(image)

        if self.zone_type == "quadrants":
            # Divide into 4 quadrants
            mid_y, mid_x = height // 2, width // 2

            zones = {
                'top_left': image[:mid_y, :mid_x],
                'top_right': image[:mid_y, mid_x:],
                'bottom_left': image[mid_y:, :mid_x],
                'bottom_right': image[mid_y:, mid_x:],
            }

            zone_means = {k: np.mean(v) for k, v in zones.items()}
            metrics['zone_means'] = zone_means

            # Calculate gradient metrics
            metrics['left_right'] = ((zone_means['top_right'] + zone_means['bottom_right']) / 2 -
                                     (zone_means['top_left'] + zone_means['bottom_left']) / 2) / global_mean * 100
            metrics['top_bottom'] = ((zone_means['bottom_left'] + zone_means['bottom_right']) / 2 -
                                     (zone_means['top_left'] + zone_means['top_right']) / 2) / global_mean * 100

            max_dev = max(abs(m - global_mean) / global_mean * 100 for m in zone_means.values())
            metrics['max_deviation_percent'] = max_dev
            metrics['has_gradient'] = max_dev > self.threshold_percent

            # Mark affected zones
            if metrics['has_gradient']:
                for zone_name, zone_mean in zone_means.items():
                    if abs(zone_mean - global_mean) / global_mean * 100 > self.threshold_percent:
                        if zone_name == 'top_left':
                            defect_map[:mid_y, :mid_x] = DefectType.GRADIENT.value
                        elif zone_name == 'top_right':
                            defect_map[:mid_y, mid_x:] = DefectType.GRADIENT.value
                        elif zone_name == 'bottom_left':
                            defect_map[mid_y:, :mid_x] = DefectType.GRADIENT.value
                        elif zone_name == 'bottom_right':
                            defect_map[mid_y:, mid_x:] = DefectType.GRADIENT.value

        elif self.zone_type == "rings":
            # Concentric rings from center
            center_y, center_x = height // 2, width // 2
            max_radius = min(center_y, center_x)

            ring_means = []
            ring_masks = []
            for i, r in enumerate([0.25, 0.5, 0.75, 1.0]):
                radius = int(max_radius * r)
                y, x = np.ogrid[:height, :width]
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)

                inner_r = int(max_radius * (r - 0.25)) if r > 0.25 else 0
                mask = (dist >= inner_r) & (dist < radius)

                if np.any(mask):
                    ring_means.append(np.mean(image[mask]))
                    ring_masks.append(mask)

            if ring_means:
                metrics['ring_means'] = ring_means
                metrics['center_to_edge'] = (ring_means[-1] - ring_means[0]) / global_mean * 100

                # Check each ring for deviation
                max_ring_dev = 0
                for i, (ring_mean, ring_mask) in enumerate(zip(ring_means, ring_masks)):
                    ring_dev = abs(ring_mean - global_mean) / global_mean * 100
                    max_ring_dev = max(max_ring_dev, ring_dev)
                    if ring_dev > self.threshold_percent:
                        # Mark this ring as gradient defect
                        defect_map[ring_mask] = DefectType.GRADIENT.value

                metrics['max_ring_deviation'] = max_ring_dev
                metrics['has_gradient'] = max_ring_dev > self.threshold_percent

        return defect_map, metrics


class CircularPatternDetector:
    """Detect circular/ring patterns in image (like vignetting or interference)"""

    def __init__(self, num_rings: int = 8, threshold_percent: float = 3.0):
        self.num_rings = num_rings
        self.threshold_percent = threshold_percent

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Detect circular patterns by analyzing radial brightness profile.

        Returns:
            - defect_map: Pixels marked as part of circular pattern
            - metrics: Dictionary with ring analysis
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.int32), {}

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)

        center_y, center_x = height // 2, width // 2
        max_radius = np.sqrt(center_x**2 + center_y**2)

        # Create distance map from center
        y, x = np.ogrid[:height, :width]
        dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)

        # Analyze radial profile
        ring_width = max_radius / self.num_rings
        ring_means = []
        global_mean = np.mean(image)

        for i in range(self.num_rings):
            inner_r = i * ring_width
            outer_r = (i + 1) * ring_width
            mask = (dist_from_center >= inner_r) & (dist_from_center < outer_r)

            if np.any(mask):
                ring_mean = np.mean(image[mask])
                ring_means.append(ring_mean)

                # Check for deviation
                deviation = abs(ring_mean - global_mean) / global_mean * 100
                if deviation > self.threshold_percent:
                    defect_map[mask] = DefectType.GRADIENT.value

        # Calculate metrics
        metrics = {
            'ring_means': ring_means,
            'global_mean': float(global_mean),
            'num_rings': self.num_rings,
        }

        if len(ring_means) >= 2:
            # Check for systematic gradient (center vs edge)
            metrics['center_brightness'] = ring_means[0]
            metrics['edge_brightness'] = ring_means[-1]
            metrics['center_to_edge_percent'] = (ring_means[-1] - ring_means[0]) / global_mean * 100

            # Check for ring pattern (alternating high/low)
            diffs = [ring_means[i+1] - ring_means[i] for i in range(len(ring_means)-1)]
            sign_changes = sum(1 for i in range(len(diffs)-1) if diffs[i] * diffs[i+1] < 0)
            metrics['ring_pattern_detected'] = sign_changes >= 2
            metrics['sign_changes'] = sign_changes

        return defect_map, metrics


class RingContourDetector:
    """
    Detect ring/circular structures and return CONTOUR LINES (not filled areas).
    Uses edge detection to find the boundaries of brightness variations.
    """

    def __init__(self, blur_sigma: float = 3.0, edge_threshold_low: float = 0.02,
                 edge_threshold_high: float = 0.05, min_contour_length: int = 50,
                 auto_detect: bool = False):
        self.blur_sigma = blur_sigma
        self.edge_threshold_low = edge_threshold_low  # Percentage of max gradient
        self.edge_threshold_high = edge_threshold_high
        self.min_contour_length = min_contour_length
        self.auto_detect = auto_detect

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray], Dict]:
        """
        Detect ring contours using edge detection.

        Returns:
            - contour_mask: Binary mask where contour pixels = 1
            - contours: List of contour coordinates [(y1,x1), (y2,x2), ...]
            - metrics: Dictionary with detection statistics
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.uint8), [], {}

        # AUTO-DETECT MODE: Find optimal parameters automatically
        if self.auto_detect:
            best_result = None
            best_params = {}
            best_score = float('inf')

            # Try different parameter combinations
            for blur in [3.0, 5.0, 8.0, 12.0]:
                for edge_pct in [5, 10, 15, 20, 25, 30]:
                    edge_low = edge_pct / 100.0
                    edge_high = edge_pct / 100.0 * 2.5

                    mask, contours, metrics = self._analyze_with_params(
                        image, blur, edge_low, edge_high, self.min_contour_length
                    )

                    num_contours = metrics.get('num_contours', 0)
                    total_pixels = metrics.get('total_contour_pixels', 0)
                    image_pixels = image.shape[0] * image.shape[1]
                    coverage_pct = (total_pixels / image_pixels) * 100

                    # Scoring: We want 5-50 contours and 0.5%-5% coverage (not too much, not too little)
                    if 5 <= num_contours <= 100 and 0.5 <= coverage_pct <= 10:
                        # Score based on how close to ideal (20 contours, 2% coverage)
                        score = abs(num_contours - 30) + abs(coverage_pct - 3) * 10

                        if score < best_score:
                            best_score = score
                            best_result = (mask, contours, metrics)
                            best_params = {'blur': blur, 'edge_pct': edge_pct}

            if best_result:
                print(f"Ring Contour AUTO-DETECT: {best_result[2].get('num_contours', 0)} contours with blur={best_params['blur']}, edge={best_params['edge_pct']}%")
                return best_result
            else:
                # Fallback to default if no good parameters found
                print("Ring Contour AUTO-DETECT: No optimal parameters found, using defaults")
                return self._analyze_with_params(image, 5.0, 0.15, 0.375, 30)

        return self._analyze_with_params(
            image, self.blur_sigma, self.edge_threshold_low,
            self.edge_threshold_high, self.min_contour_length
        )

    def _analyze_with_params(self, image: np.ndarray, blur_sigma: float,
                              edge_low: float, edge_high: float,
                              min_contour_length: int) -> Tuple[np.ndarray, List, Dict]:
        """Internal analysis with specific parameters"""
        height, width = image.shape

        # Step 1: Normalize image to 0-1 range
        img_norm = (image - np.min(image)) / (np.max(image) - np.min(image) + 1e-10)

        # Step 2: Apply Gaussian blur to reduce noise
        try:
            from scipy.ndimage import gaussian_filter
            img_smooth = gaussian_filter(img_norm, sigma=blur_sigma)
        except ImportError:
            img_smooth = img_norm  # Fallback: no smoothing

        # Step 3: Calculate gradients using Sobel-like operators
        # Gradient in X direction
        grad_x = np.zeros_like(img_smooth)
        grad_x[:, 1:-1] = (img_smooth[:, 2:] - img_smooth[:, :-2]) / 2

        # Gradient in Y direction
        grad_y = np.zeros_like(img_smooth)
        grad_y[1:-1, :] = (img_smooth[2:, :] - img_smooth[:-2, :]) / 2

        # Gradient magnitude
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)

        # Step 4: Normalize gradient and apply threshold
        grad_max = np.max(gradient_mag)
        if grad_max > 0:
            gradient_norm = gradient_mag / grad_max
        else:
            gradient_norm = gradient_mag

        # Double threshold (like Canny edge detection)
        edge_strong = gradient_norm > edge_high
        edge_weak = (gradient_norm > edge_low) & ~edge_strong

        # Step 5: Edge linking - connect weak edges that are adjacent to strong edges
        contour_mask = edge_strong.copy().astype(np.uint8)

        # Simple edge linking: add weak edges adjacent to strong edges
        for _ in range(3):  # Iterate a few times
            dilated = np.zeros_like(contour_mask)
            dilated[1:, :] |= contour_mask[:-1, :]
            dilated[:-1, :] |= contour_mask[1:, :]
            dilated[:, 1:] |= contour_mask[:, :-1]
            dilated[:, :-1] |= contour_mask[:, 1:]
            contour_mask = contour_mask | (edge_weak.astype(np.uint8) & dilated)

        # Step 6: Extract contour coordinates
        contours = self._extract_contours(contour_mask)

        # Step 7: Filter by minimum length
        contours = [c for c in contours if len(c) >= min_contour_length]

        metrics = {
            'num_contours': len(contours),
            'total_contour_pixels': int(np.sum(contour_mask)),
            'gradient_max': float(grad_max),
            'contour_lengths': [len(c) for c in contours]
        }

        return contour_mask, contours, metrics

        return contour_mask, contours, metrics

    def _extract_contours(self, binary_mask: np.ndarray) -> List[List[Tuple[int, int]]]:
        """Extract connected contour segments from binary mask"""
        height, width = binary_mask.shape
        visited = np.zeros((height, width), dtype=bool)
        contours = []

        for y in range(height):
            for x in range(width):
                if binary_mask[y, x] and not visited[y, x]:
                    # Start new contour
                    contour = []
                    stack = [(y, x)]

                    while stack:
                        cy, cx = stack.pop()
                        if cy < 0 or cy >= height or cx < 0 or cx >= width:
                            continue
                        if visited[cy, cx] or not binary_mask[cy, cx]:
                            continue

                        visited[cy, cx] = True
                        contour.append((cy, cx))

                        # 8-connectivity for contour following
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if dy == 0 and dx == 0:
                                    continue
                                stack.append((cy + dy, cx + dx))

                    if contour:
                        contours.append(contour)

        return contours


class MuraDetector:
    """Detect Mura (large-area brightness variations / "clouds")"""

    def __init__(self, blur_sigma: float = 15.0, threshold_percent: float = 10.0, auto_detect: bool = False):
        self.blur_sigma = blur_sigma
        self.threshold_percent = threshold_percent
        self.auto_detect = auto_detect

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect Mura defects using low-pass filtering.

        Returns:
            - defect_map: Pixels marked as mura
            - spots: List of detected mura spots with position and size
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.int32), []

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        spots = []

        # AUTO-DETECT MODE: Find optimal parameters automatically
        if self.auto_detect:
            # Try multiple blur scales
            best_spots = []
            best_params = {}

            for blur_sigma in [5, 10, 15, 20]:
                for thresh in [2, 3, 5, 7]:
                    temp_map, temp_spots = self._analyze_with_params(image, blur_sigma, thresh)
                    # Score: prefer finding 1-20 spots (not too few, not too many)
                    spot_count = len(temp_spots)
                    if 1 <= spot_count <= 20:
                        if len(temp_spots) > len(best_spots):
                            best_spots = temp_spots
                            best_params = {'blur_sigma': blur_sigma, 'threshold': thresh}
                            defect_map = temp_map

            if best_params:
                print(f"Mura AUTO-DETECT: Found {len(best_spots)} spots with blur={best_params['blur_sigma']}, thresh={best_params['threshold']}%")
            return defect_map, best_spots

        return self._analyze_with_params(image, self.blur_sigma, self.threshold_percent)

    def _analyze_with_params(self, image: np.ndarray, blur_sigma: float, threshold_percent: float) -> Tuple[np.ndarray, List[Dict]]:
        """Internal analysis with specific parameters"""
        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        spots = []

        # Apply Gaussian blur (low-pass filter)
        try:
            from scipy.ndimage import gaussian_filter
            blurred = gaussian_filter(image.astype(np.float64), sigma=blur_sigma)
        except ImportError:
            # Fallback: simple box filter
            kernel_size = int(blur_sigma * 3)
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = np.zeros_like(image, dtype=np.float64)
            for y in range(height):
                for x in range(width):
                    y_start = max(0, y - kernel_size // 2)
                    y_end = min(height, y + kernel_size // 2 + 1)
                    x_start = max(0, x - kernel_size // 2)
                    x_end = min(width, x + kernel_size // 2 + 1)
                    blurred[y, x] = np.mean(image[y_start:y_end, x_start:x_end])

        # Difference from smoothed image
        global_mean = np.mean(image)
        deviation = np.abs(blurred - global_mean) / global_mean * 100

        # Mark mura regions
        mura_mask = deviation > threshold_percent
        defect_map[mura_mask] = DefectType.MURA.value

        # Find connected mura regions
        visited = np.zeros((height, width), dtype=bool)

        for y in range(height):
            for x in range(width):
                if mura_mask[y, x] and not visited[y, x]:
                    # Flood fill to find connected region
                    region_pixels = []
                    stack = [(y, x)]

                    while stack:
                        cy, cx = stack.pop()
                        if cy < 0 or cy >= height or cx < 0 or cx >= width:
                            continue
                        if visited[cy, cx] or not mura_mask[cy, cx]:
                            continue

                        visited[cy, cx] = True
                        region_pixels.append((cy, cx))

                        stack.extend([(cy-1, cx), (cy+1, cx), (cy, cx-1), (cy, cx+1)])

                    if len(region_pixels) > 100:  # Minimum size for mura
                        ys = [p[0] for p in region_pixels]
                        xs = [p[1] for p in region_pixels]
                        spots.append({
                            'center_y': int(np.mean(ys)),
                            'center_x': int(np.mean(xs)),
                            'size': len(region_pixels),
                            'intensity': float(np.mean([deviation[p[0], p[1]] for p in region_pixels]))
                        })

        return defect_map, spots


class LineColumnAnalyzer:
    """Detect defective lines or columns (driver issues)"""

    def __init__(self, sigma_threshold: float = 3.0):
        self.sigma_threshold = sigma_threshold

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Detect lines/columns that deviate systematically.

        Returns:
            - defect_map: Pixels on defective lines/columns marked
            - results: Dictionary with defective line/column indices
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.int32), {}

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)

        # Calculate mean brightness per row and column
        row_means = np.mean(image, axis=1)
        col_means = np.mean(image, axis=0)

        global_mean = np.mean(image)
        row_std = np.std(row_means)
        col_std = np.std(col_means)

        # Find defective rows (lines)
        defective_rows = []
        if row_std > 0:
            row_z = np.abs(row_means - global_mean) / row_std
            defective_rows = np.where(row_z > self.sigma_threshold)[0].tolist()

            for row in defective_rows:
                defect_map[row, :] = DefectType.LINE_DEFECT.value

        # Find defective columns
        defective_cols = []
        if col_std > 0:
            col_z = np.abs(col_means - global_mean) / col_std
            defective_cols = np.where(col_z > self.sigma_threshold)[0].tolist()

            for col in defective_cols:
                defect_map[:, col] = DefectType.COLUMN_DEFECT.value

        results = {
            'defective_rows': defective_rows,
            'defective_cols': defective_cols,
            'row_count': len(defective_rows),
            'col_count': len(defective_cols),
        }

        return defect_map, results


class HotColdSpotAnalyzer:
    """Detect hot spots (bright regions) and cold spots (dark regions)"""

    def __init__(self, min_spot_size: int = 10, threshold_sigma: float = 2.5):
        self.min_spot_size = min_spot_size
        self.threshold_sigma = threshold_sigma

    def analyze(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Detect hot and cold spots as regional extrema.

        Returns:
            - defect_map: Pixels marked as hot/cold spots
            - results: Dictionary with spot counts and positions
        """
        if image is None or image.size == 0:
            return np.zeros((1, 1), dtype=np.int32), {}

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)

        mean = np.mean(image)
        std = np.std(image)

        if std == 0:
            return defect_map, {'hot_spots': [], 'cold_spots': []}

        # Threshold for hot/cold
        hot_threshold = mean + self.threshold_sigma * std
        cold_threshold = mean - self.threshold_sigma * std

        hot_mask = image > hot_threshold
        cold_mask = image < cold_threshold

        hot_spots = []
        cold_spots = []

        # Find connected hot regions
        visited = np.zeros((height, width), dtype=bool)

        for y in range(height):
            for x in range(width):
                if hot_mask[y, x] and not visited[y, x]:
                    region = self._flood_fill(y, x, hot_mask, visited, height, width)
                    if len(region) >= self.min_spot_size:
                        for py, px in region:
                            defect_map[py, px] = DefectType.HOT_SPOT.value
                        ys = [p[0] for p in region]
                        xs = [p[1] for p in region]
                        hot_spots.append({
                            'center_y': int(np.mean(ys)),
                            'center_x': int(np.mean(xs)),
                            'size': len(region),
                            'mean_value': float(np.mean([image[p[0], p[1]] for p in region]))
                        })

        # Find connected cold regions
        visited = np.zeros((height, width), dtype=bool)

        for y in range(height):
            for x in range(width):
                if cold_mask[y, x] and not visited[y, x]:
                    region = self._flood_fill(y, x, cold_mask, visited, height, width)
                    if len(region) >= self.min_spot_size:
                        for py, px in region:
                            defect_map[py, px] = DefectType.COLD_SPOT.value
                        ys = [p[0] for p in region]
                        xs = [p[1] for p in region]
                        cold_spots.append({
                            'center_y': int(np.mean(ys)),
                            'center_x': int(np.mean(xs)),
                            'size': len(region),
                            'mean_value': float(np.mean([image[p[0], p[1]] for p in region]))
                        })

        return defect_map, {'hot_spots': hot_spots, 'cold_spots': cold_spots}

    def _flood_fill(self, start_y, start_x, mask, visited, height, width):
        """Flood fill to find connected region"""
        region = []
        stack = [(start_y, start_x)]

        while stack:
            y, x = stack.pop()
            if y < 0 or y >= height or x < 0 or x >= width:
                continue
            if visited[y, x] or not mask[y, x]:
                continue

            visited[y, x] = True
            region.append((y, x))

            stack.extend([(y-1, x), (y+1, x), (y, x-1), (y, x+1)])

        return region


class HomogenityCalculator:
    """Calculate global homogenity score (Coefficient of Variation)"""

    @staticmethod
    def calculate(image: np.ndarray) -> Dict[str, float]:
        """
        Calculate homogenity metrics for the image.

        Returns:
            Dictionary with CV, homogenity percentage, and other metrics
        """
        if image is None or image.size == 0:
            return {'homogenity_percent': 0, 'cv': 0, 'mean': 0, 'std': 0}

        mean = np.mean(image)
        std = np.std(image)

        if mean == 0:
            cv = 0
        else:
            cv = std / mean  # Coefficient of Variation

        # Homogenity = 1 - CV (capped at 0-100%)
        homogenity = max(0, min(100, (1 - cv) * 100))

        return {
            'homogenity_percent': homogenity,
            'cv': cv,
            'cv_percent': cv * 100,
            'mean': float(mean),
            'std': float(std),
            'min': float(np.min(image)),
            'max': float(np.max(image)),
            'range': float(np.max(image) - np.min(image)),
        }


# Export public API
__all__ = [
    'PLMAnalyzer',
    'PLMImage',
    'AnalysisResult',
    'AnalysisThresholds',
    'DefectType',
    'DEFECT_COLORS',
    'DEFECT_NAMES',
    'PixelDefect',
    'UniformityAnalyzer',
    'BridgedPixelAnalyzer',
    'StuckPixelAnalyzer',
    'ClusterAnalyzer',
    # NEW analyzers
    'GradientAnalyzer',
    'MuraDetector',
    'LineColumnAnalyzer',
    'HotColdSpotAnalyzer',
    'HomogenityCalculator',
    'CircularPatternDetector',
    'RingContourDetector',
]
