#!/usr/bin/env python3
"""
Raspberry Pi 4 Display Script for Waveshare 3.5 inch LCD (480x320)
Uses pygame to create a fullscreen window with black background.
Press Escape to exit cleanly.
"""

import pygame
import sys
import time
from datetime import datetime


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

# Main loop
running = True
while running:
    # Get current timestamp
    current_time = time.time()
    
    # Fill the screen with black background
    screen.fill((0, 0, 0))

    # Draw top status bar (dark gray background)
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, 480, 40))

    # Render "AutoSkadis" text on the left side
    title_text = font.render("AutoSkadis", True, (255, 255, 255))
    screen.blit(title_text, (10, 10))

    # Update time string every second
    if current_time - last_time_update >= 1:
        last_time_update = current_time
        now = datetime.now()
        time_string = now.strftime("%H:%M:%S")

    # Always render and blit the time text
    time_text = font.render(time_string, True, (255, 255, 255))
    # Position text on the right side with 10px padding
    screen.blit(time_text, (480 - time_text.get_width() - 10, 10))

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