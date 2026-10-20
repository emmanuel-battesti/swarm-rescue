"""Test pour démontrer l'utilisation de ShaderConfig."""

import os
import pytest

from swarm_rescue.simulation.utils.shader_config import ShaderConfig
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless


def test_shader_config_default():
    """Test que ShaderConfig retourne la valeur par défaut."""
    ShaderConfig.reset()

    # Devrait être True sauf sur macOS
    result = ShaderConfig.get_use_shaders()
    assert isinstance(result, bool)

    # Vérifier la description
    desc = ShaderConfig.get_mode_description()
    assert desc in [
        "GPU (shaders) (default)",
        "CPU (auto-detected macOS)",
        "CPU (from SWARM_RESCUE_USE_SHADERS env var)",
        "GPU (shaders) (from SWARM_RESCUE_USE_SHADERS env var)",
    ] or "forced" in desc


def test_shader_config_force_cpu():
    """Test forcer le mode CPU."""
    ShaderConfig.force_cpu_mode()

    assert ShaderConfig.get_use_shaders() is False
    assert "CPU" in ShaderConfig.get_mode_description()
    assert "forced" in ShaderConfig.get_mode_description()

    ShaderConfig.reset()


def test_shader_config_force_gpu():
    """Test forcer le mode GPU."""
    ShaderConfig.force_gpu_mode()

    assert ShaderConfig.get_use_shaders() is True
    assert "GPU" in ShaderConfig.get_mode_description()
    assert "forced" in ShaderConfig.get_mode_description()

    ShaderConfig.reset()


def test_shader_config_override():
    """Test que le paramètre override a la priorité."""
    ShaderConfig.force_cpu_mode()

    # Même avec force_cpu_mode, override=True doit fonctionner
    assert ShaderConfig.get_use_shaders(override=True) is True
    assert ShaderConfig.get_use_shaders(override=False) is False

    ShaderConfig.reset()


@pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS", "") == "true", reason="CI does not support GPU shaders"
)
def test_map_with_explicit_shader_mode():
    """Test créer une carte avec un mode shader explicite."""
    # Mode CPU explicite
    map_cpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=False)
    assert map_cpu.playground._use_shaders is False

    # Mode GPU explicite
    map_gpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=True)
    assert map_gpu.playground._use_shaders is True


def test_map_with_global_config():
    """Test que la configuration globale affecte les cartes."""
    ShaderConfig.reset()
    ShaderConfig.force_cpu_mode()

    # Sans paramètre explicite, devrait utiliser la config globale (CPU)
    map_default = MapIntermediate01(drone_type=DroneMotionless)
    assert map_default.playground._use_shaders is False

    ShaderConfig.reset()


@pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS", "") == "true", reason="CI does not support GPU shaders"
)
def test_benchmark_scenario():
    """Test le scénario du benchmark : tester les deux modes."""
    ShaderConfig.reset()

    # Test CPU
    map_cpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=False)
    assert map_cpu.playground._use_shaders is False
    playground_cpu = map_cpu.playground

    # Warm-up
    playground_cpu.step()

    # Test GPU
    map_gpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=True)
    assert map_gpu.playground._use_shaders is True
    playground_gpu = map_gpu.playground

    # Warm-up
    playground_gpu.step()

    print(f"\n✓ CPU mode: {map_cpu.playground._use_shaders}")
    print(f"✓ GPU mode: {map_gpu.playground._use_shaders}")


if __name__ == "__main__":
    print("Testing ShaderConfig...")
    test_shader_config_default()
    print("✓ test_shader_config_default")

    test_shader_config_force_cpu()
    print("✓ test_shader_config_force_cpu")

    test_shader_config_force_gpu()
    print("✓ test_shader_config_force_gpu")

    test_shader_config_override()
    print("✓ test_shader_config_override")

    test_map_with_explicit_shader_mode()
    print("✓ test_map_with_explicit_shader_mode")

    test_map_with_global_config()
    print("✓ test_map_with_global_config")

    test_benchmark_scenario()
    print("✓ test_benchmark_scenario")

    print("\n✅ All tests passed!")
