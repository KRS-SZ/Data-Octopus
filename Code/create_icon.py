#!/usr/bin/env python3
"""
Create Data Octopus icon: Octopus wrapping around a wafer
"""

from PIL import Image, ImageDraw
import math
import os

def create_octopus_wafer_icon(size=256):
    """Create an icon with an octopus wrapped around a wafer."""

    # Create transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    # === WAFER (Silicon wafer - gray circle with grid pattern) ===
    wafer_radius = int(size * 0.32)
    wafer_color = (180, 180, 190)  # Light gray/silver
    wafer_edge = (100, 100, 110)   # Darker edge

    # Wafer circle with gradient effect
    for i in range(3):
        r = wafer_radius - i * 2
        color = tuple(min(255, c + i * 15) for c in wafer_color)
        draw.ellipse(
            [center - r, center - r, center + r, center + r],
            fill=color,
            outline=wafer_edge if i == 0 else None,
            width=2
        )

    # Wafer grid pattern (dies) with colored bins
    grid_color = (140, 140, 150, 100)
    grid_size = wafer_radius // 4

    # Define which dies are green (pass) and red (fail)
    # Coordinates relative to center
    green_dies = [
        (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),  # Center cluster
        (1, 1), (-1, -1), (1, -1), (-1, 1),         # Diagonal
        (2, 0), (-2, 0), (0, 2),                     # Extended
        (2, 1), (-2, -1), (1, 2), (-1, -2),         # More greens
    ]
    red_dies = [
        (2, -2), (-2, 2), (3, 0),  # Edge failures
    ]

    for x in range(-4, 5):
        for y in range(-4, 5):
            px = center + x * grid_size
            py = center + y * grid_size
            # Only draw if inside wafer
            dist = math.sqrt((px - center)**2 + (py - center)**2)
            if dist < wafer_radius - 5:
                # Determine die color
                if (x, y) in green_dies:
                    die_fill = (34, 197, 94)  # Green (pass)
                elif (x, y) in red_dies:
                    die_fill = (239, 68, 68)  # Red (fail)
                else:
                    die_fill = (200, 200, 210)  # Default gray

                draw.rectangle(
                    [px - grid_size//2 + 1, py - grid_size//2 + 1,
                     px + grid_size//2 - 1, py + grid_size//2 - 1],
                    fill=die_fill,
                    outline=grid_color,
                    width=1
                )

    # Wafer flat/notch at bottom
    notch_size = int(size * 0.06)
    draw.polygon([
        (center - notch_size, center + wafer_radius - 2),
        (center, center + wafer_radius + notch_size // 2),
        (center + notch_size, center + wafer_radius - 2)
    ], fill=(0, 0, 0, 0))

    # === OCTOPUS (Purple/blue octopus wrapping around wafer) ===
    octo_body_color = (138, 43, 226)      # Blue-violet
    octo_dark = (75, 0, 130)              # Indigo (darker)
    octo_light = (186, 85, 211)           # Medium orchid (lighter)
    octo_sucker = (255, 182, 193, 180)    # Light pink suckers

    # Octopus body (head) at top-left
    head_x = center - int(size * 0.28)
    head_y = center - int(size * 0.28)
    head_radius = int(size * 0.18)

    # Head shadow
    draw.ellipse(
        [head_x - head_radius + 3, head_y - head_radius + 3,
         head_x + head_radius + 3, head_y + head_radius + 3],
        fill=(50, 50, 50, 100)
    )

    # Head main
    draw.ellipse(
        [head_x - head_radius, head_y - head_radius,
         head_x + head_radius, head_y + head_radius],
        fill=octo_body_color
    )

    # Head highlight
    draw.ellipse(
        [head_x - head_radius + 5, head_y - head_radius + 5,
         head_x - head_radius // 2, head_y - head_radius // 2],
        fill=octo_light
    )

    # Eyes (big cute eyes)
    eye_offset_x = int(head_radius * 0.3)
    eye_offset_y = int(head_radius * 0.1)
    eye_radius = int(head_radius * 0.35)

    for dx in [-1, 1]:
        ex = head_x + dx * eye_offset_x
        ey = head_y + eye_offset_y
        # Eye white
        draw.ellipse(
            [ex - eye_radius, ey - eye_radius,
             ex + eye_radius, ey + eye_radius],
            fill=(255, 255, 255)
        )
        # Pupil
        pupil_r = eye_radius // 2
        draw.ellipse(
            [ex - pupil_r + 2, ey - pupil_r,
             ex + pupil_r + 2, ey + pupil_r],
            fill=(20, 20, 20)
        )
        # Eye shine
        shine_r = pupil_r // 2
        draw.ellipse(
            [ex - shine_r + 4, ey - shine_r - 2,
             ex + shine_r + 2, ey + shine_r - 4],
            fill=(255, 255, 255)
        )

    # === TENTACLES (8 tentacles wrapping around wafer) ===
    def draw_tentacle(start_angle, length_factor=1.0, wrap_direction=1):
        """Draw a curved tentacle from the head around the wafer."""
        tentacle_width = int(size * 0.045)

        # Start point near head
        start_dist = head_radius * 0.8
        sx = head_x + math.cos(math.radians(start_angle)) * start_dist
        sy = head_y + math.sin(math.radians(start_angle)) * start_dist

        # Generate points along tentacle
        points = [(sx, sy)]
        wrap_radius = wafer_radius + tentacle_width

        # Bezier-like curve wrapping around wafer
        num_segments = 12
        for i in range(1, num_segments + 1):
            t = i / num_segments * length_factor

            # Spiral around the wafer
            angle = start_angle + wrap_direction * t * 200
            radius = start_dist + (wrap_radius - start_dist) * min(t * 1.5, 1.0)

            # Add some wave motion
            wave = math.sin(t * math.pi * 3) * size * 0.02

            px = head_x + math.cos(math.radians(angle)) * (radius + wave)
            py = head_y + math.sin(math.radians(angle)) * (radius + wave)

            points.append((px, py))

        # Draw tentacle as thick line segments
        for i in range(len(points) - 1):
            # Taper the tentacle
            t = i / len(points)
            width = int(tentacle_width * (1.0 - t * 0.6))

            # Draw segment
            draw.line([points[i], points[i+1]], fill=octo_body_color, width=width)

            # Add suckers on inside of curve (every other segment)
            if i % 2 == 0 and i > 0:
                mx = (points[i][0] + points[i+1][0]) / 2
                my = (points[i][1] + points[i+1][1]) / 2
                sucker_r = width // 3
                # Offset sucker toward center
                dx = center - mx
                dy = center - my
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    mx += dx/dist * width * 0.3
                    my += dy/dist * width * 0.3
                draw.ellipse(
                    [mx - sucker_r, my - sucker_r, mx + sucker_r, my + sucker_r],
                    fill=octo_sucker
                )

    # Draw 8 tentacles at different angles
    tentacle_angles = [
        (45, 0.9, 1),    # Top-right, clockwise
        (90, 1.0, 1),    # Right, clockwise
        (135, 0.85, 1),  # Bottom-right, clockwise
        (180, 0.95, 1),  # Bottom, clockwise
        (225, 0.8, -1),  # Bottom-left, counter-clockwise
        (270, 0.9, -1),  # Left, counter-clockwise
        (315, 0.75, -1), # Top-left, counter-clockwise
        (0, 0.7, 1),     # Top, clockwise
    ]

    for angle, length, direction in tentacle_angles:
        draw_tentacle(angle, length, direction)

    return img


def create_ico_file(img, output_path):
    """Save image as ICO file with multiple sizes."""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = []

    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)

    # Save as ICO
    icons[0].save(
        output_path,
        format='ICO',
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icons[1:]
    )


def main():
    print("Creating Data Octopus icon...")

    # Create the icon
    icon = create_octopus_wafer_icon(256)

    # Save paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Save as PNG
    png_path = os.path.join(project_dir, "data_octopus.png")
    icon.save(png_path, "PNG")
    print(f"Saved PNG: {png_path}")

    # Save as ICO
    ico_path = os.path.join(project_dir, "data_octopus.ico")
    create_ico_file(icon, ico_path)
    print(f"Saved ICO: {ico_path}")

    # Also save to Desktop
    desktop_ico = r"C:\Users\szenklarz\Desktop\data_octopus.ico"
    create_ico_file(icon, desktop_ico)
    print(f"Saved Desktop ICO: {desktop_ico}")

    print("\nDone! Icon created successfully.")
    print("\nTo use the icon with the batch file:")
    print("1. Right-click 'Data Octopus.bat' on Desktop")
    print("2. Click 'Create shortcut'")
    print("3. Right-click the shortcut -> Properties")
    print("4. Click 'Change Icon' -> Browse to data_octopus.ico")


if __name__ == "__main__":
    main()
