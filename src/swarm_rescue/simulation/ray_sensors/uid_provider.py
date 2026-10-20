"""
Interface between the ray sensors and whatever renders entity UIDs.

Why this module exists
----------------------
`RayCompute` is a *sensor*: it is model code. What it needs from the rendering
is exactly one thing: a picture in which each pixel encodes the unique id of
the object drawn on it. How that picture is produced (a framebuffer, an
offscreen buffer, a plain numpy array) is a rendering concern.

`RayCompute` only knows this protocol, and never touches the OpenGL state of
the presentation: the simulation cannot be affected by how the image is
rendered.

`TopDownView` implements `UidProvider`, so any other implementation (a CPU
rasterizer, a recorded image in a test) works just as well.

`typing.Protocol` is used rather than an ABC so that implementations do not
have to inherit from anything, and so the interface cannot be silently
bypassed: `RayCompute` annotates its parameter with it and the type checker
verifies the calls.
"""

from typing import Protocol, Tuple, runtime_checkable

import numpy as np


@runtime_checkable
class UidProvider(Protocol):
    """
    An image in which each pixel carries the uid of the object it shows.

    An implementation must draw the playground *offscreen*, at the size it
    reports through `width` and `height`, and map world coordinates to pixels
    with `center` and `zoom`.
    """

    @property
    def center(self) -> Tuple[float, float]:
        """Center of the image, in world units (not pixels)."""

    @property
    def width(self) -> int:
        """Width of the image, in pixels."""

    @property
    def height(self) -> int:
        """Height of the image, in pixels."""

    @property
    def zoom(self) -> float:
        """Scale factor from world units to pixels."""

    def render_uids(self) -> None:
        """
        Draw every entity into the uid image, with its uid as its color.

        Called before every read, because the world moves between two reads.
        """

    def read_uid_image(self) -> np.ndarray:
        """
        Return the uid image as an array of shape (height, width, 3).

        The three channels are the bytes of the entity uid, so a pixel holding
        the uid 66051 reads as (1, 2, 3) once recombined as
        `256 * 256 * b0 + 256 * b1 + b2`.
        """

    def bind_uid_texture(self) -> None:
        """
        Bind the uid image as the input texture of the compute shader.

        Only meaningful for the GPU path; a CPU implementation may leave it
        empty.
        """
