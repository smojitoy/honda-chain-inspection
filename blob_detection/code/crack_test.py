from pathlib import Path
import csv

import cv2
import numpy as np


# ---------- Paths ----------
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent.parent

input_dir = project_dir / "blob_detection" / "data" / "boxed_background"
output_dir = project_dir / "results" / "crack_roi"
output_dir.mkdir(parents=True, exist_ok=True)


# ---------- Initial screening settings ----------
# These are starting values, not validated crack criteria.
MIN_AREA = 30
MIN_HEIGHT_FRACTION = 0.65
MAX_WIDTH_FRACTION = 0.20
MIN_HEIGHT_WIDTH_RATIO = 1.5


def select_roi(image):
    """Select on a smaller preview, then map back to original pixels."""
    height, width = image.shape[:2]
    scale = min(1.0, 1200 / width, 750 / height)

    preview = cv2.resize(
        image, None, fx=scale, fy=scale,
        interpolation=cv2.INTER_AREA
    )

    window = "Select metal bar: ENTER confirm, C cancel"
    selection = cv2.selectROI(
        window, preview,
        showCrosshair=True,
        fromCenter=False
    )
    cv2.destroyAllWindows()

    px, py, pw, ph = selection
    if pw == 0 or ph == 0:
        return None

    preview_h, preview_w = preview.shape[:2]
    sx = width / preview_w
    sy = height / preview_h

    x = max(0, int(round(px * sx)))
    y = max(0, int(round(py * sy)))
    x2 = min(width, int(round((px + pw) * sx)))
    y2 = min(height, int(round((py + ph) * sy)))

    if x2 <= x or y2 <= y:
        return None

    return x, y, x2 - x, y2 - y


photos = sorted(
    path for path in input_dir.rglob("*")
    if path.is_file() and path.suffix.lower() == ".png"
)

if not photos:
    raise SystemExit(f"No PNG images found in {input_dir}")

records = []

for photo in photos:
    image = cv2.imread(str(photo))
    if image is None:
        print(f"Cannot read: {photo.name}")
        continue

    print(f"\nProcessing: {photo.name}")
    print("Select a horizontal strip INSIDE the metal bar.")
    print("Include the gap and metal on both sides; exclude the background.")

    selection = select_roi(image)
    if selection is None:
        print("Skipped.")
        continue

    x, y, w, h = selection
    roi = image[y:y + h, x:x + w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Dark pixels become white foreground in the binary mask.
    threshold, mask = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )

    # Preserve vertically continuous regions.
    kernel_height = max(3, int(round(h * 0.5)))
    vertical_kernel = np.ones((kernel_height, 1), dtype=np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )

    annotated = image.copy()
    accepted_mask = np.zeros_like(mask)

    # Blue rectangle indicates the manually selected inspection region.
    cv2.rectangle(
        annotated, (x, y), (x + w - 1, y + h - 1),
        (255, 0, 0), 2
    )

    candidates = 0

    # Label 0 is the binary background.
    for label in range(1, count):
        bx, by, bw, bh, area = stats[label]

        height_fraction = bh / h
        width_fraction = bw / w
        aspect_ratio = bh / max(bw, 1)

        # Look for narrow dark regions spanning most of the selected strip.

        if area >= MIN_AREA:
            print(
                f"area={area}, "
                f"height_fraction={height_fraction:.2f}, "
                f"width_fraction={width_fraction:.2f}, "
                f"aspect_ratio={aspect_ratio:.2f}"
            )
        if (
            area < MIN_AREA
            or height_fraction < MIN_HEIGHT_FRACTION
            or width_fraction > MAX_WIDTH_FRACTION
            or aspect_ratio < MIN_HEIGHT_WIDTH_RATIO
        ):
            continue

        candidates += 1
        accepted_mask[labels == label] = 255

        left = x + int(bx)
        top = y + int(by)
        right = left + int(bw) - 1
        bottom = top + int(bh) - 1

        cv2.rectangle(
            annotated, (left, top), (right, bottom),
            (0, 0, 255), 3
        )
        cv2.putText(
            annotated,
            f"Gap candidate {candidates}",
            (left, max(20, top - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

    # Preserve input subfolders to avoid filename collisions.
    relative = photo.relative_to(input_dir)
    destination = output_dir / relative.parent
    destination.mkdir(parents=True, exist_ok=True)

    outputs = {
        f"{photo.stem}_result.png": annotated,
        f"{photo.stem}_roi.png": roi,
        f"{photo.stem}_binary.png": mask,
        f"{photo.stem}_candidates.png": accepted_mask,
    }

    for filename, output in outputs.items():
        path = destination / filename
        if not cv2.imwrite(str(path), output):
            raise OSError(f"Failed to save {path}")

    records.append({
        "image": str(relative),
        "roi_x": x,
        "roi_y": y,
        "roi_width": w,
        "roi_height": h,
        "otsu_threshold": float(threshold),
        "gap_candidates": candidates,
    })

    print(f"Detected gap candidates: {candidates}")
    print(f"Saved to: {destination}")

if records:
    with (output_dir / "summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

print("\nFinished.")