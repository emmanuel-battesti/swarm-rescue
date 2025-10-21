import pathlib
import sys
import numpy as np

import pytest

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.utils.utils_noise import vector_gaussian_noise, GaussianNoise



class TestVectorGaussianNoise:

    #  Tests that the function raises a ValueError when
    #  size is not a positive integer
    def test_positive_size(self):
        with pytest.raises(ValueError):
            vector_gaussian_noise(-10)
            vector_gaussian_noise(0)
            vector_gaussian_noise(10.5)
            vector_gaussian_noise('size')

    #  Tests that the function raises a ValueError when
    #  std_dev_noise is a negative number
    def test_negative_std_dev_noise(self):
        with pytest.raises(ValueError):
            vector_gaussian_noise(100, std_dev_noise=-1)
            vector_gaussian_noise(100, std_dev_noise=-10.5)

    #  Tests that the function raises a ValueError when
    #  mean_noise is not a number
    def test_non_numeric_mean_noise(self):
        with pytest.raises(ValueError):
            vector_gaussian_noise(100, mean_noise='mean')
            vector_gaussian_noise(100, mean_noise=[1, 2, 3])
            vector_gaussian_noise(100, mean_noise={'mean': 0})

    #  Tests that the output of the function is a numpy array
    def test_output_type(self):
        noise = vector_gaussian_noise(100)
        assert isinstance(noise, np.ndarray)

    #  Tests that the output of the function has the correct size
    def test_output_size(self):
        size = 100
        noise = vector_gaussian_noise(size)
        assert len(noise) == size

    #  Tests that the output of the function has the correct
    #  mean and standard deviation
    def test_output_stats(self):
        size = 1000
        mean_noise = 0
        std_dev_noise = 1.0
        noise = vector_gaussian_noise(size, mean_noise, std_dev_noise)
        assert abs(np.mean(noise) - mean_noise) < 0.2
        assert abs(np.std(noise) - std_dev_noise) < 0.2


class TestGaussianNoise:

    #  Tests that adding noise to an array of shape (n,) with
    #  default mean and std_dev values
    def test_add_noise_to_array_with_default_values(self):
        noise = GaussianNoise()
        values = np.array([1, 2, 3, 4, 5])
        result = noise.add_noise(values)
        assert len(result) == len(values)
        assert isinstance(result, np.ndarray)

    #  Tests that adding noise to an array of shape (n, m) with
    #  custom mean and std_dev values
    def test_add_noise_to_array_with_custom_values(self):
        noise = GaussianNoise(mean_noise=2, std_dev_noise=0.5)
        values = np.array([[1, 2], [3, 4], [5, 6]])
        result = noise.add_noise(values)
        assert result.shape == values.shape
        assert isinstance(result, np.ndarray)

    #  Tests that adding noise to a float value with default
    #  mean and std_dev values
    def test_add_noise_to_float_with_default_values(self):
        noise = GaussianNoise()
        value = 5.0
        result = noise.add_noise(value)
        assert isinstance(result, float)

    #  Tests that adding noise to a float value with custom
    #  mean and std_dev values
    def test_add_noise_to_float_with_custom_values(self):
        noise = GaussianNoise(mean_noise=2, std_dev_noise=0.5)
        value = 5.0
        result = noise.add_noise(value)
        assert isinstance(result, float)

    #  Tests that adding noise to an empty array
    def test_add_noise_to_empty_array(self):
        noise = GaussianNoise()
        values = np.array([])
        result = noise.add_noise(values)
        assert len(result) == 0
        assert isinstance(result, np.ndarray)

    #  Tests that adding noise to a None value
    def test_add_noise_to_none_value(self):
        noise = GaussianNoise()
        value = None
        result = noise.add_noise(value)
        assert result is None
