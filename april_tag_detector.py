#!/usr/bin/env python3
"""
AprilTag Detector

A basic program that detects AprilTags using a camera and draws bounding boxes
around detected tags. Uses the tag36h11 family by default.

Usage:
    python april_tag_detector.py              # Use webcam (device 0)
    python april_tag_detector.py --video vid.mp4  # Use video file
    python april_tag_detector.py --camera 1     # Use different webcam
"""

import argparse
import cv2
import numpy as np
from pyapriltags import Detector, Detection


def create_detector() -> Detector:
    """Create and configure an AprilTag detector with tag36h11 family."""
    detector = Detector(
        families='tag36h11',
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0,
    )
    return detector


def detect_and_draw(frame: np.ndarray, detector: Detector) -> tuple[np.ndarray, list[Detection]]:
    """
    Detect AprilTags in the frame and draw bounding boxes.

    Args:
        frame: The input image frame (BGR)
        detector: The Detector instance

    Returns:
        Tuple of (frame with bounding boxes drawn, list of detections)
    """
    # Convert to grayscale (required for AprilTag detection)
    # Keep as uint8 - pyapriltags requires uint8 dtype
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect AprilTags
    detections: list[Detection] = detector.detect(gray)

    # Draw bounding boxes and IDs for each detected tag
    for detection in detections:
        # Get the four corners of the bounding box
        # corners is a numpy array with shape (4, 2) containing (x, y) coordinates
        corners = detection.corners

        # Draw the bounding box (green line, thickness 2)
        for i in range(4):
            x1, y1 = int(corners[i][0]), int(corners[i][1])
            x2, y2 = int(corners[(i + 1) % 4][0]), int(corners[(i + 1) % 4][1])
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Get tag ID
        tag_id = detection.tag_id

        # Calculate text position (above the bounding box)
        text_x = int(corners[0][0])
        text_y = int(corners[0][1]) - 15

        # Ensure text position is within frame bounds
        text_x = max(0, text_x)
        text_y = max(15, text_y)

        # Draw a green background rectangle for the text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        text_size = cv2.getTextSize(f"ID: {tag_id}", font, font_scale, thickness)[0]
        cv2.rectangle(
            frame,
            (text_x, text_y - text_size[1] - 10),
            (text_x + text_size[0], text_y + 5),
            (0, 255, 0),
            -1
        )

        # Draw the tag ID text
        cv2.putText(
            frame,
            f"ID: {tag_id}",
            (text_x, text_y - 5),
            font,
            font_scale,
            (0, 0, 0),
            thickness
        )

        # Draw the center point of the tag
        center = detection.center
        center_x = int(center[0])
        center_y = int(center[1])
        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)

        # Draw decision margin (how clearly the tag was detected)
        decision_margin = detection.decision_margin
        cv2.putText(
            frame,
            f"Margin: {decision_margin:.1f}",
            (text_x, text_y + 20),
            font,
            0.5,
            (0, 255, 0),
            1
        )

    return frame, detections


def main():
    parser = argparse.ArgumentParser(description="AprilTag Detector with Bounding Box")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--video", type=str, default=None, help="Path to a video file")
    parser.add_argument("--width", type=int, default=640, help="Frame width (default: 640)")
    parser.add_argument("--height", type=int, default=480, help="Frame height (default: 480)")
    parser.add_argument("--family", type=str, default='tag36h11',
                        help="AprilTag family (default: tag36h11)")
    args = parser.parse_args()

    # Create the AprilTag detector with the selected family
    detector = Detector(
        families=args.family,
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0,
    )

    # Open camera or video file
    if args.video:
        cap = cv2.VideoCapture(args.video)
        source_type = "video"
    else:
        cap = cv2.VideoCapture(args.camera)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        source_type = "camera"

    if not cap.isOpened():
        print(f"Error: Could not open {source_type} source!")
        return

    print(f"AprilTag Detector Started")
    print(f"Source: {source_type}")
    print(f"Tag Family: {args.family}")
    print(f"Press 'q' to quit\n")

    frame_count = 0
    prev_time = cv2.getTickCount()

    while True:
        curr_time = cv2.getTickCount()
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame!")
            break

        # Detect and draw AprilTags
        result, detections = detect_and_draw(frame, detector)
        tag_count = len(detections)

        # Calculate and display FPS
        frame_count += 1
        elapsed = curr_time - prev_time
        if elapsed > 0:
            fps = frame_count / (elapsed / cv2.getTickFrequency())
            frame_count = 0
            prev_time = curr_time

        # Display FPS and tag count on the frame
        cv2.putText(
            result,
            f"FPS: {fps:.1f} | Tags: {tag_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # Display the result
        cv2.imshow("AprilTag Detector", result)

        # Check for quit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\nAprilTag Detector Stopped")


if __name__ == "__main__":
    main()