"""Configuration module for shader usage across the application."""

import os
import platform
from typing import Optional


class ShaderConfig:
    """Global configuration for shader usage with environment variable support."""

    _force_value: Optional[bool] = None

    @classmethod
    def get_use_shaders(cls, override: Optional[bool] = None) -> bool:
        """
        Determine if shaders should be used based on configuration hierarchy.

        Priority (highest to lowest):
        1. Explicit override parameter (for tests/benchmarks)
        2. SWARM_RESCUE_USE_SHADERS environment variable
        3. Platform detection (False on macOS, True otherwise)

        Args:
            override: Explicit value to use, bypassing all other checks

        Returns:
            bool: Whether to use shaders

        Examples:
            # Normal usage (auto-detect)
            use_shaders = ShaderConfig.get_use_shaders()

            # Force for a specific test
            use_shaders = ShaderConfig.get_use_shaders(override=False)

            # Use environment variable
            # export SWARM_RESCUE_USE_SHADERS=false
            use_shaders = ShaderConfig.get_use_shaders()
        """
        # 1. Explicit override has highest priority
        if override is not None:
            return override

        # 2. Check if user forced a value via class method
        if cls._force_value is not None:
            return cls._force_value

        # 3. Check environment variable
        env_value = os.environ.get('SWARM_RESCUE_USE_SHADERS', '').lower()
        if env_value in ('0', 'false', 'no', 'off'):
            return False
        elif env_value in ('1', 'true', 'yes', 'on'):
            return True

        # 4. Platform detection (macOS has shader issues)
        if platform.system() == "Darwin":
            return False

        # 5. Default to True
        return True

    @classmethod
    def force_cpu_mode(cls):
        """
        Force CPU mode globally for the current session.

        This is useful when a user detects shader problems and wants
        to disable them for all subsequent operations.

        Example:
            from swarm_rescue.simulation.utils.shader_config import ShaderConfig
            ShaderConfig.force_cpu_mode()
        """
        cls._force_value = False

    @classmethod
    def force_gpu_mode(cls):
        """
        Force GPU (shader) mode globally for the current session.

        Example:
            from swarm_rescue.simulation.utils.shader_config import ShaderConfig
            ShaderConfig.force_gpu_mode()
        """
        cls._force_value = True

    @classmethod
    def reset(cls):
        """Reset any forced value to allow auto-detection."""
        cls._force_value = None

    @classmethod
    def get_mode_description(cls) -> str:
        """Get a human-readable description of the current shader mode."""
        if cls._force_value is not None:
            mode = "GPU (shaders)" if cls._force_value else "CPU"
            return f"{mode} (forced via ShaderConfig)"

        env_value = os.environ.get('SWARM_RESCUE_USE_SHADERS', '').lower()
        if env_value in ('0', 'false', 'no', 'off'):
            return "CPU (from SWARM_RESCUE_USE_SHADERS env var)"
        elif env_value in ('1', 'true', 'yes', 'on'):
            return "GPU (shaders) (from SWARM_RESCUE_USE_SHADERS env var)"

        if platform.system() == "Darwin":
            return "CPU (auto-detected macOS)"

        return "GPU (shaders) (default)"

