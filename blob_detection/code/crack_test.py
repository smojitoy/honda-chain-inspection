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



def auto_select_roi(image):
    """Automatically detect a horizontal metal bar ROI."""
    H, W = image.shape[:2]

    # Ignore the outer image border
    mx = round(W * 0.035)
    my = round(H * 0.055)

    cropped = image[my:H-my, mx:W-mx]

    # Grayscale + Gaussian blur
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu threshold: bright metal becomes white
    _, mask = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Connect nearby bright metal regions
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(15, round(W * 0.024)),
         max(3, round(H * 0.026)))
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, kernel
    )

    # Find object contours
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Prefer long horizontal objects
        if w > W * 0.4 and w / max(h, 1) > 3:
            candidates.append(
                (cv2.contourArea(contour), x, y, w, h)
            )

    if not candidates:
        return None

    # Choose the largest suitable contour
    _, x, y, w, h = max(candidates)

    # Map back to the original image
    x += mx
    y += my

    # Move inside the metal to exclude background
    pad_x = int(w * 0.03)
    pad_y = int(h * 0.20)

    x += pad_x
    y += pad_y
    w -= 2 * pad_x
    h -= 2 * pad_y

    return (x, y, w, h)



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

    selection = auto_select_roi(image)
    
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
        # Ignore components touching or near the ROI boundaries
        EDGE_MARGIN = 0.03

        if (
            bx <= w * EDGE_MARGIN
            or bx + bw >= w * (1 - EDGE_MARGIN)
        ):
            continue

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