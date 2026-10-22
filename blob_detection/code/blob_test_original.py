from pathlib import Path
import cv2

script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent.parent

input_dir = project_dir / "blob_detection" / "data" / "boxed_background"
output_dir = project_dir / "results" / "boxed_background_original"

photos = sorted(
    path for path in input_dir.rglob("*")
    if path.is_file() and path.suffix.lower() == ".png"
)

if not photos:
    raise SystemExit("No PNG images found in data/.")

# Original tutorial parameters for the initial test.
params = cv2.SimpleBlobDetector_Params()

# Brightness threshold sweep.
params.minThreshold = 20
params.maxThreshold = 250
params.thresholdStep = 5

# Dark regions.
params.filterByColor = True
params.blobColor = 0

# Area in pixels; initial trial values.
params.filterByArea = True
params.minArea = 50
params.maxArea = 20000

# Allow narrow, irregular shapes.
params.filterByCircularity = False
params.filterByConvexity = False

# Prefer elongated regions.
params.filterByInertia = True
params.minInertiaRatio = 0.001
params.maxInertiaRatio = 0.3

detector = cv2.SimpleBlobDetector_create(params)

detector = cv2.SimpleBlobDetector_create(params)

for photo in photos:
    image = cv2.imread(str(photo), cv2.IMREAD_GRAYSCALE)

    if image is None:
        print(f"Skipped unreadable image: {photo.name}")
        continue

    keypoints = detector.detect(image)

    output = cv2.drawKeypoints(
        image,
        keypoints,
        None,
        (0, 0, 255),
        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
    )

    relative_path = photo.relative_to(input_dir)
    result_path = (
        output_dir
        / relative_path.parent
        / f"{photo.stem}_blobs.png"
    )
    result_path.parent.mkdir(parents=True, exist_ok=True)

    if cv2.imwrite(str(result_path), output):
        print(f"{relative_path}: {len(keypoints)} blobs")
        print(f"  Saved: {result_path}")
    else:
        print(f"Failed to save: {result_path}")

print("Finished.")