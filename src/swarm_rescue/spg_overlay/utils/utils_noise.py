import math
from typing import Union, Type
import numpy as np


def vector_gaussian_noise(size: int, mean_noise: float = 0,
                          std_dev_noise: float = 1.0) -> np.ndarray:
    gaussian_noise = np.random.normal(loc=mean_noise,
                                      scale=std_dev_noise,
                                      size=size)
    return gaussian_noise


class GaussianNoise:
    def __init__(self, mean_noise: float = 0, std_dev_noise: float = 1.0):
        self._mean_noise = mean_noise
        # std_dev_noise is the standard deviation of the resulted gaussian noise
        self._std_dev_noise = std_dev_noise

        self._shape: Union[tuple, Type[None]] = None

    def add_noise(self, values: Union[np.ndarray, float]):
        if values is None:
            return None

        values2 = values
        gaussian_noise: Union[np.ndarray, float, Type[None]] = None
        if isinstance(values, np.ndarray):
            # if values.ndim == 1:
            #     # change shape from (n,) to (n, 1), ie an column vector
            #     values2 = values[:, np.newaxis]

            if self._shape is None:
                self._shape = values2.shape
            assert (self._shape == values2.shape)

            gaussian_noise = np.random.normal(loc=self._mean_noise,
                                              scale=self._std_dev_noise,
                                              size=values2.shape)
        elif isinstance(values, float):
            gaussian_noise = np.random.normal(loc=self._mean_noise,
                                              scale=self._std_dev_noise)
        return values2 + gaussian_noise


class AutoregressiveModelNoise:
    """
     We use a noise that follow an autoregressive model of order 1 : https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
     """

    def __init__(self, model_param: float, std_dev_noise: float):
        self._model_param = model_param
        # std_dev is the real standard deviation of the resulted noise
        self._std_dev_noise = std_dev_noise

        # _std_dev_wn is the standard deviation of the white noise
        self._std_dev_wn = math.sqrt(
            self._std_dev_noise ** 2 * (1 - self._model_param ** 2))

        self._last_noise: Union[np.ndarray, float, Type[None]] = None
        self._shape: Union[tuple, Type[None]] = None

    def add_noise(self, values: Union[np.ndarray, float, Type[None]]):
        if values is None:
            return None

        values2 = values
        white_noise: Union[np.ndarray, float, Type[None]] = None
        if isinstance(values, np.ndarray):
            # if values.ndim == 1:
            #     # change shape from (n,) to (n, 1), ie an column vector
            #     values2 = values[:, np.newaxis]

            white_noise = np.random.normal(0, self._std_dev_wn,
                                           size=values2.shape)

            if self._last_noise is None:
                self._last_noise = np.zeros(values2.shape)
                self._shape = values2.shape

            assert (self._shape == values2.shape)

        elif isinstance(values, float):

            white_noise = np.random.normal(0, self._std_dev_wn)

            if self._last_noise is None:
                self._last_noise = 0

        assert white_noise.all()

        additive_noise = self._model_param * self._last_noise + white_noise
        self._last_noise = additive_noise

        values2 += additive_noise
        return values2
