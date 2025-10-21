"""
Module containing classes to generate random positions and trajectories

"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple, Union, Iterator

import numpy as np

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import Playground

Coordinate = Tuple[Tuple[float, float], float]


class CoordinateSampler(ABC):
    """
    Abstract base class for sampling coordinates in a playground.

    Attributes:
        _radius (Optional[float]): Radius for sampling.
        _width (Optional[float]): Width for sampling.
        _height (Optional[float]): Height for sampling.
        _center (Tuple[float, float]): Center for sampling.
        _playground (Playground): Playground instance.
    """

    def __init__(
            self,
            playground: Playground,
            center: Tuple[float, float],
            radius: Optional[float] = None,
            width: Optional[float] = None,
            height: Optional[float] = None,
            size: Optional[Tuple[float, float]] = None,
    ):
        """
        Initialize a CoordinateSampler.

        Args:
            playground (Playground): The playground instance.
            center (Tuple[float, float]): Center for sampling.
            radius (Optional[float]): Radius for sampling.
            width (Optional[float]): Width for sampling.
            height (Optional[float]): Height for sampling.
            size (Optional[Tuple[float, float]]): Size for sampling.
        """

        self._radius = radius

        if (not width) and size:
            width, height = size

        self._width = width
        self._height = height

        self._center = center

        assert self._radius or self._width

        self._playground = playground

    def _get_relative_positions(self):
        """
        Get relative positions for sampling.

        Returns:
            np.ndarray: Array of relative positions.
        """
        pos = None
        if self._radius:
            pos = np.indices((self._radius, self._radius))
            dist = (pos[0, :] - self._radius / 2) ** 2 + (pos[1, :] - self._radius / 2)
            pos = np.where(dist < (self._radius / 2) ** 2)
            pos = pos - np.atleast_2d((self._radius / 2, self._radius / 2)).transpose()

        elif self._width:

            if self._height:
                pos = np.indices((self._width, self._height)).reshape(2, -1)
                pos = (
                        pos - np.atleast_2d((self._width / 2, self._height / 2)).transpose()
                )

            else:
                pos = np.indices((self._width, self._width)).reshape(2, -1)
                pos = (
                        pos - np.atleast_2d((self._width / 2, self._width / 2)).transpose()
                )

        return pos

    @property
    def _rng(self):
        """
        Returns the random number generator from the playground.
        """
        return self._playground.rng

    @abstractmethod
    def _get_position_pdf(self, position_indices):
        """
        Abstract method to get the probability density function for positions.

        Args:
            position_indices: Indices of positions.

        Returns:
            np.ndarray: Probability density function values.
        """
        ...

    def _get_random_angle(self) -> float:
        """
        Get a random angle in [0, 2*pi).

        Returns:
            float: Random angle.
        """
        return self._rng.uniform(0, 2 * math.pi)

    def sample(self) -> Iterator[Coordinate]:
        """
        Sample probability for all possible coordinates,
        then sort them by order of posterior.

        Yields:
            Coordinate: Sampled coordinate (position, angle).
        """

        position_indices = self._get_relative_positions()
        position_pdf = self._get_position_pdf(position_indices)

        uniform_sampling = self._rng.uniform(size=position_pdf.size)
        posterior = uniform_sampling * position_pdf

        rr, cc = position_indices

        stacked = np.stack((rr, cc, posterior), axis=-1).reshape(-1, 3)
        sorted_coordinates = stacked[stacked[:, 2].argsort()]
        sorted_coordinates = sorted_coordinates[::-1]

        for rel_x, rel_y, _ in sorted_coordinates:
            x = self._center[0] + rel_x
            y = self._center[1] + rel_y
            angle = self._get_random_angle()

            yield (x, y), angle


InitCoord = Union[Coordinate, CoordinateSampler]