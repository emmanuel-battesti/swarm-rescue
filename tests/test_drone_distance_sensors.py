import numpy as np

import pytest

from spg_overlay.entities.drone_distance_sensors import compute_ray_angles


class TestComputeRayAngles:

    #  Tests that the function returns the correct array of ray angles for a given field of view and number of rays
    def test_happy_path_1(self):
        fov_rad = 1.0
        nb_rays = 5
        expected_angles = np.array([-0.5, -0.25, 0.0, 0.25, 0.5])

        result = compute_ray_angles(fov_rad, nb_rays)

        np.testing.assert_array_almost_equal(result, expected_angles, decimal=8)

    #  Tests that the function returns the correct array of ray angles for a different field of view and number of rays
    def test_happy_path_2(self):
        fov_rad = 0.8
        nb_rays = 3
        expected_angles = np.array([-0.4, 0.0, 0.4])
    
        result = compute_ray_angles(fov_rad, nb_rays)
    
        assert np.array_equal(result, expected_angles)

    #  Tests that the function returns the correct array of ray angles when the number of rays is 1
    def test_edge_case_1(self):
        fov_rad = 0.6
        nb_rays = 1
        expected_angles = np.array([0.0])
    
        result = compute_ray_angles(fov_rad, nb_rays)
    
        assert np.array_equal(result, expected_angles)

    #  Tests that the function returns the correct array of ray angles when the number of rays is 2
    def test_edge_case_2(self):
        fov_rad = 0.4
        nb_rays = 2
        expected_angles = np.array([-0.2, 0.2])
    
        result = compute_ray_angles(fov_rad, nb_rays)
    
        assert np.array_equal(result, expected_angles)

    #  Tests that the function returns the correct array of ray angles when the number of rays is very large
    def test_edge_case_3(self):
        fov_rad = 1.2
        nb_rays = 1000
        expected_angles = np.linspace(-0.6, 0.6, nb_rays)
    
        result = compute_ray_angles(fov_rad, nb_rays)
    
        assert np.array_equal(result, expected_angles)

    #  Tests that the function raises a ValueError when fov_rad is not a positive float
    def test_other_case_1(self):
        fov_rad_1 = 0.0
        fov_rad_2 = -5.0
        nb_rays = 10
        with pytest.raises(ValueError):
            compute_ray_angles(fov_rad_1, nb_rays)
            compute_ray_angles(fov_rad_2, nb_rays)
