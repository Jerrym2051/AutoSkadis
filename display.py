#!/usr/bin/env python3
"""
Raspberry Pi 4 Display Script for Waveshare 3.5 inch LCD (480x320)
Uses pygame to create a fullscreen window with black background.
Press Escape to exit cleanly.
"""

import pygame
import sys
import time


# 5-second delay to allow the system to boot
time.sleep(5)

# Initialize pygame
pygame.init()

# Set up the display at 480x320 resolution
screen = pygame.display.set_mode((480, 320))

# Set the window title
pygame.display.set_caption("Waveshare 3.5 inch LCD Display")

# Main loop
running = True
while running:
    # Fill the screen with black background
    screen.fill((0, 0, 0))

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

# Clean up pygame
pygame.quit()
sys.exit()