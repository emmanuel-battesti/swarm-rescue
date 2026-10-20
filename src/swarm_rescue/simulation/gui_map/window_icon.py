"""The icon shown in the window's title bar and in the task switcher.

Why pre-rendered sizes instead of the one source image
------------------------------------------------------
`drone_2_big_1.png` is 1024x1024 and 138 kB. A window icon is drawn at 16 to128
pixels; handing pyglet the full-size image would work, but every window manager
would downscale it on its own, from a file five orders of magnitude larger than
it needs to be. `resources/window_icon_{16,32,64,128}.png` are the same drawing
pre-rendered at the sizes pyglet documents as useful, cropped to the drone and
resampled with Lanczos: 27 kB for the four, a fifth of the original.

The four files rather than one 128x128 that everything is scaled down from,
because downscaling a downscaled icon compounds: the 16x16 in the list is a
direct resample of the artwork, where the 16x16 of a scaled 128x128 is a resample
of a resample, and the thin black outline of the rotors is the first thing to
disappear.

Failure is not fatal
--------------------
`apply_window_icon` returns a bool instead of raising. A missing icon file, or a
window that refuses one (some headless/EGL configurations do), must not take the
simulation down with it: the icon is decoration, and a participant whose window
never opens loses the whole round. The caller logs nothing and loses nothing but
the icon.
"""

from __future__ import annotations

import os
from typing import List, Tuple

import pyglet.image

from swarm_rescue.resources import path_resources

# The sizes pyglet documents as the useful ones. 64 and 128 are macOS-only, but
# harmless elsewhere and free to ship.
ICON_SIZES: Tuple[int, ...] = (16, 32, 64, 128)

# The artwork the icons are rendered from, kept for provenance: it is the file
# `resources/window_icon_*.png` were generated from, and the one to regenerate
# them from if the drone drawing changes. Not shipped in `package-data`: it is
# 138 kB and nothing loads it at runtime.
ICON_SOURCE_FILENAME = "drone_2_big_1.png"


def _icon_path(size: int) -> str:
    """
    Return the path of the pre-rendered icon of the given size.

    Args:
        size (int): Edge length in pixels.

    Returns:
        str: Absolute path to the PNG.
    """
    return os.path.join(path_resources, f"window_icon_{size}.png")


def available_icon_sizes() -> List[int]:
    """
    The icon sizes actually present on disk.

    Returns:
        List[int]: The sizes whose file exists, smallest first.
    """
    return [size for size in ICON_SIZES if os.path.isfile(_icon_path(size))]


def apply_window_icon(window) -> bool:
    """
    Set the drone icon on a window.

    Args:
        window: The window to iconify. Anything exposing `set_icon`, which is
            what `arcade.Window` inherits from the pyglet window.

    Returns:
        bool: True if the icon was applied, False if it could not be. Never
            raises: an icon is not worth losing a run over.
    """
    sizes = available_icon_sizes()
    if not sizes:
        return False

    images = []
    for size in sizes:
        try:
            images.append(pyglet.image.load(_icon_path(size)))
        except Exception:
            # One unreadable file must not discard the sizes that did load, so
            # this skips it instead of giving up on the whole icon.
            continue

    if not images:
        return False

    try:
        window.set_icon(*images)
    except Exception:
        # Some headless/EGL window implementations reject set_icon outright.
        return False

    return True
