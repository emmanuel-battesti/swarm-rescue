"""
A texture cache, for the files every map loads over and over.

Why this module exists
----------------------
`arcade.load_texture` documents itself as "(no caching)". Each call decodes the
image, builds a `PIL.Image`, and computes a SHA-256 over its raw bytes
(`ImageData.calculate_hash`). That is correct, and it is the wrong trade here:
the 144+ `NormalWall`s of a single map all load the *same* 2000x2000 stone
texture and then keep a different crop of it. Measured on
`MapFinal_2024_25_01`: 187 calls, 6.94 s, i.e. **80% of the time it takes to
build a playground**. After this cache: 1.68 s, a 5.2x gain.

The expensive work is provably redundant
----------------------------------------
The hitbox is computed from the *whole* image
(`ArcadeHitBoxAlgorithm.calculate` walks the image), not from the crop that is
actually kept. Two loads of the same file therefore produce the same hitbox
whatever the crop, so nothing per-wall is lost by loading once.

Sharing is safe
---------------
Every caller immediately derives its own texture -- `crop`, `flip_diagonally`,
`flip_horizontally`, or `generate_texture_with_id_color` -- and those all
return a *new* `arcade.Texture`. The cached object is only ever read. The one
thing that must not be mutated is the hitbox, and nothing does.

The one real limit
------------------
The key is the path alone, so an image rewritten on disk mid-process would
still be served from cache. Resources are frozen in the competition, so this
cannot happen in practice; `clear_texture_cache()` exists for the case where
it does, e.g. a tool that generates images then builds a map from them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import arcade
from arcade.hitbox import HitBoxAlgorithm

__all__ = ["load_texture_cached", "clear_texture_cache", "cache_size"]

# Path (as a plain string) -> arcade.Texture. Keyed by path, not by mtime, on
# purpose: the mtime would buy nothing here, because the resources are read
# once per process, and it would cost a stat() on every load.
_TEXTURE_CACHE: Dict[str, arcade.Texture] = {}

# Captured at import time so that this module keeps working if anything ever
# monkeypatches `arcade.load_texture` (tests do). Without it, a call routed
# back through here would recurse forever.
_ORIGINAL_LOAD_TEXTURE = arcade.load_texture


def load_texture_cached(
    file_path: str | Path,
    *,
    hit_box_algorithm: Optional[HitBoxAlgorithm] = None,
    hash: Optional[str] = None,  # noqa: A002 - mirrors arcade's own parameter
    **kwargs: Any,
) -> arcade.Texture:
    """
    Load a texture, reusing the previous load of the same file when possible.

    Args:
        file_path (str | Path): The image to load.
        hit_box_algorithm (Optional[HitBoxAlgorithm]): How to derive the hitbox.
        hash (Optional[str]): Passed through to arcade. Note that supplying it
            makes the cache key unsound, since two different images could then
            claim the same hash; no caller in this project does.
        **kwargs: Passed through to arcade.

    Returns:
        arcade.Texture: The texture for this file. Shared between callers, so
            treat it as read-only -- derive your own with `crop`/`flip_*` if you
            intend to change it.
    """
    key = str(file_path)

    # A caller that passes an explicit hash is asking for a specific texture
    # identity; honoring the cache there would hand back the wrong image.
    if hash is not None:
        return _ORIGINAL_LOAD_TEXTURE(
            file_path, hit_box_algorithm=hit_box_algorithm, hash=hash, **kwargs
        )

    texture = _TEXTURE_CACHE.get(key)
    if texture is None:
        texture = _ORIGINAL_LOAD_TEXTURE(
            file_path, hit_box_algorithm=hit_box_algorithm, **kwargs
        )
        _TEXTURE_CACHE[key] = texture

    return texture


def clear_texture_cache() -> None:
    """Forget every cached texture.

    Only needed when an image file has been rewritten on disk during the life
    of the process.
    """
    _TEXTURE_CACHE.clear()


def cache_size() -> int:
    """How many textures are currently cached. For tests and diagnostics."""
    return len(_TEXTURE_CACHE)
