#!/usr/bin/env python3
# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

"""
Raspberry Pi 4 Display Script for Waveshare 3.5 inch LCD (480x320)
Uses pygame to create a fullscreen window with black background.
Press Escape to exit cleanly.
"""

import pygame
import sys
import time
import json
import os
from datetime import datetime

from picamera2 import Picamera2


# 5-second delay to allow the system to boot
time.sleep(5)

# Initialize pygame
pygame.init()

# Initialize font
pygame.font.init()
font = pygame.font.Font(None, 20)

# Set up the display at 480x320 resolution in fullscreen mode
screen = pygame.display.set_mode((480, 320), pygame.FULLSCREEN)

# Set the window title
pygame.display.set_caption("Waveshare 3.5 inch LCD Display")

# Track last time update for the clock
last_time_update = 0

# Initialize time string
now = datetime.now()
time_string = now.strftime("%H:%M:%S")

# Current status - will be updated by API server later
current_status = "Idle"

# Retrieved bins - will be updated by API server later
retrieved_bins = []

# Action log - stores the 4 most recent actions
action_log = []


def load_state():
    """Load state from state.json file. Returns defaults on failure."""
    defaults = {
        "status": "Idle",
        "retrieved_bins": [],
        "action_log": [],
    }
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        state_path = os.path.join(script_dir, "state.json")
        with open(state_path, "r") as f:
            data = json.load(f)
        return {
            "status": data.get("status", "Idle"),
            "retrieved_bins": data.get("retrieved_bins", []),
            "action_log": data.get("action_log", []),
        }
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return defaults


# Initial state load
_state = load_state()
current_status = _state["status"]
retrieved_bins = _state["retrieved_bins"]
action_log = _state["action_log"]

# Status color mapping
STATUS_COLORS = {
    "Idle": (0, 255, 0),
    "Moving": (255, 255, 0),
    "Error": (255, 0, 0),
}

# Font for status text (size 22)
status_font = pygame.font.Font(None, 22)

# Button configuration
BUTTON_WIDTH = 70
BUTTON_HEIGHT = 70
BUTTON_MARGIN = 10
BUTTON_X = 480 - BUTTON_WIDTH - BUTTON_MARGIN  # 400
BUTTON_Y = 320 - BUTTON_HEIGHT - BUTTON_MARGIN  # 240
BUTTON_NORMAL_COLOR = (200, 100, 0)  # dark orange
BUTTON_PRESSED_COLOR = (255, 165, 0)  # light orange
BUTTON_CORNER_RADIUS = 10

# Font for button text (size 16)
button_font = pygame.font.Font(None, 16)

# Button state tracking
button_pressed_time = 0
button_is_pressed = False

# Camera preview window position and size (3:2 aspect ratio)
# Position below Retrieved bins, above HOME button area
# HOME button starts at Y=240, so camera goes from ~Y=160 to ~Y=240
# For 3:2 ratio: 230x154 fits nicely
CAMERA_X = 10
CAMERA_Y = 160
CAMERA_WIDTH = 230
CAMERA_HEIGHT = 154  # 3:2 aspect ratio, fits between bins and HOME button

# Camera preview
camera_preview_surface = None
cap = None
last_camera_capture = 0
CAMERA_CAPTURE_INTERVAL = 1.0 / 20  # 20 FPS for camera

try:
    cap = Picamera2()
    config = cap.create_video_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
    )
    cap.configure(config)
    cap.start()
    time.sleep(1)  # allow sensor to warm up before first capture
except Exception:
    cap = None

# Retrieved bins scrolling animation
scroll_offset = 0
SCROLL_SPEED = 40  # pixels per second

# Font for bin pill text (size 16)
bin_font = pygame.font.Font(None, 16)

# Font for retrieved bins label (size 18)
bin_label_font = pygame.font.Font(None, 18)

# Font for action log text (size 16)
action_log_font = pygame.font.Font(None, 16)

# Bin pill configuration
PILL_WIDTH = 100
PILL_HEIGHT = 35
PILL_CORNER_RADIUS = 17
PILL_SPACING = 10
PILL_COLOR = (0, 50, 120)  # dark blue
SCREEN_AVAILABLE_WIDTH = 460  # 480 - 10px left margin - 10px right margin


def _draw_pill(surface, x, y, text_font, text):
    """Helper function to draw a pill-shaped rectangle with centered text."""
    # Main rectangle body
    pygame.draw.rect(surface, PILL_COLOR,
                     (x + PILL_CORNER_RADIUS, y,
                      PILL_WIDTH - 2 * PILL_CORNER_RADIUS, PILL_HEIGHT))
    pygame.draw.rect(surface, PILL_COLOR,
                     (x, y + PILL_CORNER_RADIUS,
                      PILL_WIDTH, PILL_HEIGHT - 2 * PILL_CORNER_RADIUS))
    # Corner circles
    pygame.draw.circle(surface, PILL_COLOR,
                     (int(x + PILL_CORNER_RADIUS), int(y + PILL_CORNER_RADIUS)),
                     PILL_CORNER_RADIUS)
    pygame.draw.circle(surface, PILL_COLOR,
                     (int(x + PILL_WIDTH - PILL_CORNER_RADIUS), int(y + PILL_CORNER_RADIUS)),
                     PILL_CORNER_RADIUS)
    pygame.draw.circle(surface, PILL_COLOR,
                     (int(x + PILL_CORNER_RADIUS), int(y + PILL_HEIGHT - PILL_CORNER_RADIUS)),
                     PILL_CORNER_RADIUS)
    pygame.draw.circle(surface, PILL_COLOR,
                     (int(x + PILL_WIDTH - PILL_CORNER_RADIUS), int(y + PILL_HEIGHT - PILL_CORNER_RADIUS)),
                     PILL_CORNER_RADIUS)

    # Render text centered in pill
    pill_text = text_font.render(text, True, (255, 255, 255))
    text_x = int(x + (PILL_WIDTH - pill_text.get_width()) // 2)
    text_y = int(y + (PILL_HEIGHT - pill_text.get_height()) // 2)
    surface.blit(pill_text, (text_x, text_y))


# Main loop
running = True
clock = pygame.time.Clock()
frame_time = 0
last_frame_surface = None

while running:
    # Get current timestamp
    current_time = time.time()
    # Calculate delta time for frame-rate independent scrolling
    delta_time = clock.tick(60) / 1000.0  # convert ms to seconds
    
    # Fill the screen with black background
    screen.fill((0, 0, 0))

    # Draw top status bar (dark gray background)
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, 480, 40))

    # Render "AutoSkadis" text on the left side
    title_text = font.render("AutoSkadis", True, (255, 255, 255))
    screen.blit(title_text, (10, 10))

    # Update time string every second and reload state
    if current_time - last_time_update >= 1:
        last_time_update = current_time
        now = datetime.now()
        time_string = now.strftime("%H:%M:%S")

        # Reload state from state.json every second
        _state = load_state()
        current_status = _state["status"]
        retrieved_bins = _state["retrieved_bins"]
        action_log = _state["action_log"]

    # Always render and blit the time text
    time_text = font.render(time_string, True, (255, 255, 255))
    # Position text on the right side with 10px padding
    screen.blit(time_text, (480 - time_text.get_width() - 10, 10))

    # Draw status section below the top bar
    # Get the status color (default to white if unknown status)
    status_color = STATUS_COLORS.get(current_status, (255, 255, 255))

    # Render "STATUS:" text in white
    status_label = status_font.render("STATUS:", True, (255, 255, 255))
    screen.blit(status_label, (10, 50))

    # Draw filled circle indicator (aligned with text baseline)
    circle_x = 10 + status_label.get_width() + 15
    circle_y = 50 + status_font.get_linesize() // 2
    pygame.draw.circle(screen, status_color, (circle_x, circle_y), 8)

    # Render status word in the status color
    status_word = status_font.render(current_status, True, status_color)
    screen.blit(status_word, (circle_x + 15, 50))

    # Draw "Retrieved bins:" label
    bins_label = bin_label_font.render("Retrieved bins:", True, (255, 255, 255))
    screen.blit(bins_label, (10, 90))

    # Draw retrieved bins pills
    pills_y = 115
    if len(retrieved_bins) == 0:
        # Display "None" in gray if no bins
        none_text = bin_font.render("None", True, (128, 128, 128))
        screen.blit(none_text, (10, pills_y))
    else:
        # Calculate total width needed for all pills
        total_pills_width = len(retrieved_bins) * PILL_WIDTH + (len(retrieved_bins) - 1) * PILL_SPACING

        # Only scroll if total width exceeds available screen width
        if total_pills_width > SCREEN_AVAILABLE_WIDTH:
            # Update scroll offset for seamless infinite loop animation (frame-rate independent)
            scroll_offset += SCROLL_SPEED * delta_time

            # Use modulo for seamless looping - wrap around after one full set of pills + spacing
            wrap_distance = total_pills_width + PILL_SPACING
            scroll_offset = scroll_offset % wrap_distance
        else:
            # No scrolling needed, reset offset
            scroll_offset = 0.0
            wrap_distance = total_pills_width + PILL_SPACING

        # Draw each pill with scrolling for seamless infinite loop
        # Draw pills at three offset positions for seamless wrapping:
        # - Original position (scroll_offset)
        # - Wrapped forward (+wrap_distance)
        # - Wrapped backward (-wrap_distance)
        for offset in [-wrap_distance, 0, wrap_distance]:
            for i, bin_name in enumerate(retrieved_bins):
                pill_x = 10 + i * (PILL_WIDTH + PILL_SPACING) - scroll_offset + offset

                # Skip pills that are off-screen
                if pill_x + PILL_WIDTH < 0 or pill_x > 480:
                    continue

                _draw_pill(screen, pill_x, pills_y, bin_font, bin_name)

    # Draw camera preview window
    camera_rect = pygame.Rect(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
    if cap is not None:
        # Check if camera overlaps with HOME button area
        if not camera_rect.colliderect(pygame.Rect(BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)):
            # Only capture new frame at 20 FPS to avoid slowing display loop
            current_time = time.time()
            if current_time - last_camera_capture >= CAMERA_CAPTURE_INTERVAL:
                last_camera_capture = current_time
                try:
                    frame = cap.capture_array()
                    frame = frame[:, :, ::-1]  # swap BGR to RGB
                    frame = frame.transpose(1, 0, 2)
                    last_frame_surface = pygame.surfarray.make_surface(frame)
                except Exception as e:
                    print(f"Camera error: {e}")

            if last_frame_surface is not None:
                screen.blit(last_frame_surface, (CAMERA_X, CAMERA_Y))
            else:
                pygame.draw.rect(screen, (30, 30, 30), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT))
                pygame.draw.rect(screen, (100, 100, 100), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT), 2)
        else:
            # Camera overlaps with HOME button - draw placeholder
            pygame.draw.rect(screen, (30, 30, 30), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT))
            pygame.draw.rect(screen, (100, 100, 100), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT), 2)
    else:
        # Draw placeholder when camera is unavailable
        pygame.draw.rect(screen, (30, 30, 30), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT))
        pygame.draw.rect(screen, (100, 100, 100), (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT), 2)
        no_cam_text = font.render("No Camera", True, (100, 100, 100))
        text_x = CAMERA_X + (CAMERA_WIDTH - no_cam_text.get_width()) // 2
        text_y = CAMERA_Y + (CAMERA_HEIGHT - no_cam_text.get_height()) // 2
        screen.blit(no_cam_text, (text_x, text_y))

    # Draw HOME button (rounded rectangle with manual drawing)
    # Determine button color based on press state
    if button_is_pressed:
        button_color = BUTTON_PRESSED_COLOR
    else:
        button_color = BUTTON_NORMAL_COLOR

    # Draw rounded rectangle for button (using multiple shapes)
    # Main rectangle body
    pygame.draw.rect(screen, button_color, 
                     (BUTTON_X + BUTTON_CORNER_RADIUS, BUTTON_Y, 
                      BUTTON_WIDTH - 2 * BUTTON_CORNER_RADIUS, BUTTON_HEIGHT))
    pygame.draw.rect(screen, button_color, 
                     (BUTTON_X, BUTTON_Y + BUTTON_CORNER_RADIUS, 
                      BUTTON_WIDTH, BUTTON_HEIGHT - 2 * BUTTON_CORNER_RADIUS))
    # Corner circles
    pygame.draw.circle(screen, button_color, (BUTTON_X + BUTTON_CORNER_RADIUS, BUTTON_Y + BUTTON_CORNER_RADIUS), BUTTON_CORNER_RADIUS)
    pygame.draw.circle(screen, button_color, (BUTTON_X + BUTTON_WIDTH - BUTTON_CORNER_RADIUS, BUTTON_Y + BUTTON_CORNER_RADIUS), BUTTON_CORNER_RADIUS)
    pygame.draw.circle(screen, button_color, (BUTTON_X + BUTTON_CORNER_RADIUS, BUTTON_Y + BUTTON_HEIGHT - BUTTON_CORNER_RADIUS), BUTTON_CORNER_RADIUS)
    pygame.draw.circle(screen, button_color, (BUTTON_X + BUTTON_WIDTH - BUTTON_CORNER_RADIUS, BUTTON_Y + BUTTON_HEIGHT - BUTTON_CORNER_RADIUS), BUTTON_CORNER_RADIUS)

    # Render "HOME" text centered in button
    home_text = button_font.render("HOME", True, (255, 255, 255))
    text_x = BUTTON_X + (BUTTON_WIDTH - home_text.get_width()) // 2
    text_y = BUTTON_Y + (BUTTON_HEIGHT - home_text.get_height()) // 2
    screen.blit(home_text, (text_x, text_y))

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if button was pressed
            if (BUTTON_X <= event.pos[0] <= BUTTON_X + BUTTON_WIDTH and
                BUTTON_Y <= event.pos[1] <= BUTTON_Y + BUTTON_HEIGHT):
                print("Home button pressed")
                button_pressed_time = time.time()
                button_is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            # Check if button was released
            if (BUTTON_X <= event.pos[0] <= BUTTON_X + BUTTON_WIDTH and
                BUTTON_Y <= event.pos[1] <= BUTTON_Y + BUTTON_HEIGHT):
                button_is_pressed = False

# Clean up pygame and camera
if cap is not None:
    cap.stop()
pygame.quit()
sys.exit()
