# AprilTag Detector

A Python program that detects AprilTags using a camera and draws bounding boxes around detected tags.

## Requirements

- Python 3.8+
- OpenCV (opencv-python)
- pyapriltags
- NumPy

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Using a webcam:
```bash
python april_tag_detector.py
```

### Using a specific camera:
```bash
python april_tag_detector.py --camera 1
```

### Using a video file:
```bash
python april_tag_detector.py --video path/to/video.mp4
```

### Custom resolution:
```bash
python april_tag_detector.py --width 1280 --height 720
```

### Different tag family:
```bash
python april_tag_detector.py --family tag36h11
```

Available tag families:
- `tag36h11` - Standard 36x36 family with 11 bits (default)
- `tag25h9` - Standard 25x25 family with 9 bits
- `tag16h5` - Standard 16x16 family with 5 bits
- `tagCircle49h12` - Circle 49x12 family
- `tagCircle39h11` - Circle 39x11 family

## Controls

- Press `q` to quit the application

## Output

The program displays:
- Green bounding boxes around detected AprilTags
- Tag ID labels above each bounding box
- Blue center point marker for each tag
- Detection confidence (decision margin)
- FPS and total tag count in the top-left corner

## How it Works

1. The program initializes a camera capture (webcam or video file)
2. Each frame is converted to grayscale (required for AprilTag detection)
3. The AprilTag detector searches for tags in the frame
4. For each detected tag:
   - A green bounding box is drawn at the tag corners
   - The tag ID is displayed as a label
   - A blue center point is marked
   - The decision margin (detection confidence) is shown
5. The processed frame is displayed in a window