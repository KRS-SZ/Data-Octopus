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

    # Stuck pixel thresholds
    stuck_variance_threshold: float = 5.0    # Max variance to consider stuck
    stuck_on_threshold: float = 250          # Value to consider "stuck on"
    stuck_off_threshold: float = 5           # Value to consider "stuck off"

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
        self.width = 768
        self.height = 568
        self.data: Optional[np.ndarray] = None
        self.plm_type = self._detect_plm_type(file_path)

    def _detect_plm_type(self, file_path: str) -> str:
        """Detect PLM type from filename"""
        filename = os.path.basename(file_path).lower()

        if 'uniformity' in filename or 'uniformitysyn' in filename:
            return 'Uniformity'
        elif 'bridged' in filename:
            return 'Bridged'
        elif 'stitched' in filename:
            return 'Stitched'
        else:
            return 'Unknown'

    def load(self) -> bool:
        """Load PLM file and parse pixel data"""
        try:
            if not os.path.exists(self.file_path):
                print(f"PLM file not found: {self.file_path}")
                return False

            # Read the file
            with open(self.file_path, 'r') as f:
                content = f.read()

            # Parse the data - PLM files contain pixel values
            # Format varies but typically: one value per pixel, row by row
            lines = content.strip().split('\n')

            # Skip header lines (if any) - look for numeric data
            data_lines = []
            for line in lines:
                # Skip empty lines and obvious headers
                line = line.strip()
                if not line:
                    continue
                # Check if line contains mostly numbers
                try:
                    values = [float(v) for v in line.replace(',', ' ').replace('\t', ' ').split() if v]
                    if values:
                        data_lines.append(values)
                except ValueError:
                    continue

            if not data_lines:
                print(f"No valid data found in PLM file: {self.file_path}")
                return False

            # Convert to numpy array
            # Handle different formats:
            # 1. One row per image row (width values per line)
            # 2. All values in sequence

            if len(data_lines) == self.height and len(data_lines[0]) == self.width:
                # Format 1: Matrix format
                self.data = np.array(data_lines, dtype=np.float32)
            else:
                # Format 2: Flat format - reshape
                flat_data = []
                for row in data_lines:
                    flat_data.extend(row)

                expected_size = self.width * self.height
                if len(flat_data) >= expected_size:
                    self.data = np.array(flat_data[:expected_size], dtype=np.float32).reshape(self.height, self.width)
                elif len(flat_data) > 0:
                    # Partial data - pad with zeros
                    padded = np.zeros(expected_size, dtype=np.float32)
                    padded[:len(flat_data)] = flat_data
                    self.data = padded.reshape(self.height, self.width)
                    print(f"Warning: PLM file has {len(flat_data)} values, expected {expected_size}")
                else:
                    return False

            return True

        except Exception as e:
            print(f"Error loading PLM file {self.file_path}: {e}")
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
        For proper stuck pixel detection, multiple images should be compared.
        """
        if image is None or image.size == 0:
            return np.zeros((568, 768), dtype=np.int32), []

        height, width = image.shape
        defect_map = np.zeros((height, width), dtype=np.int32)
        defects = []

        # Find stuck ON pixels (very bright)
        stuck_on_mask = image >= self.thresholds.stuck_on_threshold
        for y, x in zip(*np.where(stuck_on_mask)):
            defect_map[y, x] = DefectType.STUCK_ON.value
            defects.append(PixelDefect(
                x=int(x), y=int(y),
                defect_type=DefectType.STUCK_ON,
                value=float(image[y, x])
            ))

        # Find stuck OFF pixels (very dark)
        stuck_off_mask = image <= self.thresholds.stuck_off_threshold
        for y, x in zip(*np.where(stuck_off_mask)):
            if defect_map[y, x] == 0:  # Don't overwrite stuck_on
                defect_map[y, x] = DefectType.STUCK_OFF.value
                defects.append(PixelDefect(
                    x=int(x), y=int(y),
                    defect_type=DefectType.STUCK_OFF,
                    value=float(image[y, x])
                ))

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
]
