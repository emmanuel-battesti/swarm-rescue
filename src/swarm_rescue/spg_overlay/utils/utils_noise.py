import math
from typing import Union, Type
import numpy as np


def vector_gaussian_noise(size: int, mean_noise: float = 0,
                          std_dev_noise: float = 1.0) -> np.ndarray:
    """
    The vector_gaussian_noise function generates a vector of Gaussian noise using the NumPy library.

    Example Usage
        noise = vector_gaussian_noise(100, mean_noise=0, std_dev_noise=1.0)
        print(noise)
        This code generates a vector of Gaussian noise with a size of 100, a mean of 0, and a standard deviation
        of 1.0. The resulting noise vector is then printed.

    Inputs
        size (int): The size of the desired noise vector.
        mean_noise (float, optional): The mean of the Gaussian distribution. Defaults to 0.
        std_dev_noise (float, optional): The standard deviation of the Gaussian distribution. Defaults to 1.0.
    """

    if not isinstance(size, int) or size <= 0:
        raise ValueError("Size must be a positive integer.")

    if std_dev_noise <= 0:
        raise ValueError("std_dev_noise must be a positive number")

    if not isinstance(mean_noise, (int, float)):
        raise ValueError("mean_noise must be a number")

    gaussian_noise = np.random.normal(loc=mean_noise,
                                      scale=std_dev_noise,
                                      size=size)
    return gaussian_noise


class GaussianNoise:
    """
    The GaussianNoise class is used to add Gaussian noise to input values. It takes in the mean and standard deviation
    of the noise as parameters and provides a method to add the noise to the input values.

    Example Usage
        # Create an instance of GaussianNoise with mean_noise = 0 and std_dev_noise = 1.0
        noise = GaussianNoise()

        # Add noise to a single float value
        value = 10.0
        noisy_value = noise.add_noise(value)
        # noisy_value will be the original value plus a random value drawn from a Gaussian distribution with mean 0 and
        standard deviation 1.0

        # Add noise to a numpy array of values
        values = np.array([1.0, 2.0, 3.0])
        noisy_values = noise.add_noise(values)
        # noisy_values will be the original values plus random values drawn from a Gaussian distribution with mean 0 and
        standard deviation 1.0

    """
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
            #     # change shape from (n,) to (n, 1), ie a column vector
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
     We use a noise that follow an autoregressive model of order 1 : https://en.wikipedia.org/wiki/Autoregressive_model#Example:_An_AR(1)_process
     We have two parameters :
     - std_dev_noise : it is the standard deviation of the resulted noise
     - model_param : value between 0 and 1 (but <1)
     noise = model_param * previous_noise + white_noise
     if model_param = 0 : the final noise is a white noise
     if model_param -> 1 : the noise get some derive
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
            #     # change shape from (n,) to (n, 1), ie a column vector
            #     values2 = values[:, np.newaxis]

            white_noise = np.random.normal(0, self._std_dev_wn,
                                           size=values2.shape)

            if self._last_noise is None:
                self._last_noise = np.zeros(values2.shape)
                self._shape = values2.shape

            assert (self._shape == values2.shape)
            assert white_noise.all()

        elif isinstance(values, float):
            white_noise = np.random.normal(0, self._std_dev_wn)
            if self._last_noise is None:
                self._last_noise = 0

        additive_noise = self._model_param * self._last_noise + white_noise
        self._last_noise = additive_noise

        values2 += additive_noise
        return values2
