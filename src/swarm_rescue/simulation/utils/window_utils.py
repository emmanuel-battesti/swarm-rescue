"""
Window utilities for automatic resizing and screen detection.
"""
from typing import Optional, Tuple
import tkinter as tk

from swarm_rescue.simulation.utils.constants import WINDOW_AUTO_RESIZE_RATIO

# Constants for multi-screen detection
_MULTI_SCREEN_ASPECT_RATIO_THRESHOLD = 2.5
_MULTI_SCREEN_WIDTH_THRESHOLD = 2560
_MULTI_SCREEN_WIDE_THRESHOLD = 2000
_FALLBACK_SCREEN_SIZE = (1366, 768)

# Common screen resolutions for estimation
_LOW_RES_HEIGHT_THRESHOLD = 900
_MID_RES_HEIGHT_THRESHOLD = 1200
_STANDARD_HD_WIDTH = 1920
_HIGH_RES_WIDTH = 2560


def _detect_multi_screen_and_estimate_single(raw_width: int, raw_height: int) -> Tuple[int, int]:
    """
    Detect if we have multiple screens and estimate single screen dimensions.

    Args:
        raw_width: Raw detected screen width
        raw_height: Raw detected screen height

    Returns:
        Tuple of estimated single screen (width, height)
    """
    aspect_ratio = raw_width / raw_height if raw_height > 0 else 1
    is_likely_multi_screen = (
        aspect_ratio > _MULTI_SCREEN_ASPECT_RATIO_THRESHOLD or
        raw_width > _MULTI_SCREEN_WIDTH_THRESHOLD or
        (raw_width > _MULTI_SCREEN_WIDE_THRESHOLD and aspect_ratio > 2.0)
    )

    if is_likely_multi_screen:
        # For multi-screen, use a conservative single screen estimate
        if raw_height <= _LOW_RES_HEIGHT_THRESHOLD:
            # Likely 1366x768 or 1920x1080 screens
            screen_width = min(_STANDARD_HD_WIDTH, raw_width // 2)
        elif raw_height <= _MID_RES_HEIGHT_THRESHOLD:
            # Likely 1920x1080 or similar
            screen_width = min(_STANDARD_HD_WIDTH, raw_width // 2)
        else:
            # Higher resolution screens
            screen_width = min(_HIGH_RES_WIDTH, raw_width // 2)
        return screen_width, raw_height
    else:
        return raw_width, raw_height


def auto_resize_window(initial_size: Optional[Tuple[int, int]]) -> Tuple[Optional[Tuple[int, int]], float]:
    """
    Automatically resize the window to fit the screen if it's too large.

    This function detects the screen size and adjusts the window dimensions
    to ensure it fits comfortably on the display. It also handles multi-screen
    configurations intelligently.

    Args:
        initial_size (Optional[Tuple[int, int]]): The initial window size (width, height).

    Returns:
        Tuple[Optional[Tuple[int, int]], float]: A tuple containing:
            - The adjusted window size (width, height) or None if no initial size was provided
            - The zoom factor that should be applied to maintain content visibility

    Example:
        >>> size, zoom = auto_resize_window((1920, 1080))
        >>> print(f"New size: {size}, zoom: {zoom}")
        New size: (1248, 702), zoom: 0.65
    """
    if initial_size is None:
        return None, 1.0

    initial_width, initial_height = initial_size

    # Try multiple methods to get screen dimensions
    screen_width, screen_height = None, None

    # Method 1: Try tkinter
    try:
        root = tk.Tk()
        root.withdraw()
        raw_width = root.winfo_screenwidth()
        raw_height = root.winfo_screenheight()
        root.destroy()

        screen_width, screen_height = _detect_multi_screen_and_estimate_single(raw_width, raw_height)
    except Exception:
        pass

    # Method 2: Try pygame if tkinter failed
    if screen_width is None:
        try:
            import pygame
            pygame.init()
            info = pygame.display.Info()
            pygame_width = info.current_w
            pygame_height = info.current_h
            pygame.quit()

            screen_width, screen_height = _detect_multi_screen_and_estimate_single(pygame_width, pygame_height)
        except (ImportError, Exception):
            pass

    # Method 3: Use conservative fallback
    if screen_width is None:
        screen_width, screen_height = _FALLBACK_SCREEN_SIZE

    # Calculate maximum allowed window size (configurable % of screen for comfortable fit)
    max_width = int(screen_width * WINDOW_AUTO_RESIZE_RATIO)
    max_height = int(screen_height * WINDOW_AUTO_RESIZE_RATIO)

    # Check if window is too large for the screen
    if initial_width > max_width or initial_height > max_height:
        # Calculate scale factor to fit the window on screen
        scale_x = max_width / initial_width if initial_width > max_width else 1.0
        scale_y = max_height / initial_height if initial_height > max_height else 1.0
        scale = min(scale_x, scale_y)

        new_width = int(initial_width * scale)
        new_height = int(initial_height * scale)

        print("Détection de la taille de l'écran : ")
        print(f"  Taille écran détectée : {screen_width}x{screen_height}")

        print(f"Fenêtre redimensionnée automatiquement: {initial_width}x{initial_height} -> {new_width}x{new_height}")

        return (new_width, new_height), scale

    return initial_size, 1.0

