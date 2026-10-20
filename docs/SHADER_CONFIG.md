# Shader Configuration (GPU vs CPU)

## Overview

The shader system can operate in two modes:
- **GPU (shaders)**: Uses OpenGL shaders to compute sensors (faster)
- **CPU**: Computes sensors in Python/NumPy (slower but more compatible)

## Default configuration

By default the system auto-detects:
- **macOS** → CPU (known issues with shaders)
- **Linux/Windows** → GPU (shaders)

## How to force CPU mode

### 1. Using an environment variable (recommended for normal use)

```bash
# Disable shaders for the whole session
export SWARM_RESCUE_USE_SHADERS=false

# Run your script
python your_script.py

# Or in one line
SWARM_RESCUE_USE_SHADERS=false python your_script.py
```

### 2. Using Python code (to force globally)

```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig

# Force CPU mode for the whole session
ShaderConfig.force_cpu_mode()

# Now all maps will use CPU mode
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
map1 = MapIntermediate01(drone_type=DroneMotionless)  # → CPU
map2 = MapIntermediate01(drone_type=DroneMotionless)  # → CPU
```

### 3. Using a parameter (for a specific map)

```python
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

# Force CPU for this map only
map_cpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=False)

# Use GPU for this map only
map_gpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=True)
```

## Tests and benchmarks

### CPU vs GPU benchmark

The benchmark automatically tests both modes:

```bash
python bench_ray_compute.py --steps 100 --repeats 5
```

### Forcing a mode in tests

```python
# In a pytest test
def test_with_cpu():
    from swarm_rescue.simulation.utils.shader_config import ShaderConfig
    
    # Reset the current state
    ShaderConfig.reset()
    
    # Force CPU for this test
    ShaderConfig.force_cpu_mode()
    
    # Your test...
    map = MapIntermediate01(drone_type=DroneMotionless)
    # ...
    
    # Restore auto-detection
    ShaderConfig.reset()
```

## Checking the current mode

```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig

# Print the current mode
print(ShaderConfig.get_mode_description())
# → "GPU (shaders) (default)" or "CPU (auto-detected macOS)" etc.

# Check whether shaders are used
if ShaderConfig.get_use_shaders():
    print("GPU mode enabled")
else:
    print("CPU mode enabled")
```

## Configuration priority

The system checks in this order:
1. **Explicit parameter** (`use_shaders=True/False`)
2. **Forced via code** (`ShaderConfig.force_cpu_mode()`)
3. **Environment variable** (`SWARM_RESCUE_USE_SHADERS`)
4. **Platform detection** (macOS → CPU)
5. **Default** (GPU)

## Usage examples

### User who encounters shader issues

```bash
# In .bashrc or .zshrc
export SWARM_RESCUE_USE_SHADERS=false
```

Or at the start of the Python script:

```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig
ShaderConfig.force_cpu_mode()

# Everything else will automatically use the CPU
```

### Developer who wants to test both modes

```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

# CPU test
map_cpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=False)
print(f"CPU mode: {map_cpu.playground._use_shaders}")  # False

# GPU test
map_gpu = MapIntermediate01(drone_type=DroneMotionless, use_shaders=True)
print(f"GPU mode: {map_gpu.playground._use_shaders}")  # True
```

### Benchmark script

```python
import os
os.environ['SWARM_RESCUE_USE_SHADERS'] = 'false'

# Now everything will use the CPU
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
```

## Technical architecture

The shader configuration system is centralized in the base class `Playground`:

```
MapIntermediate01 (or any other map)
  └─ Creates ClosedPlayground(use_shaders=...)
       └─ Calls Playground.__init__(use_shaders=...)
            └─ self._use_shaders = ShaderConfig.get_use_shaders(override=use_shaders)
                 └─ Applies the priority hierarchy
```

**Key points:**
- The logic lives in `Playground.__init__()` (base class)
- `ClosedPlayground` simply forwards the parameter to the parent
- All maps automatically benefit from the system
- There is a single place to change if the logic evolves

For more details about the refactor, see `REFACTOR_SHADER_TO_PLAYGROUND.md`.

## Troubleshooting

**Q: Shaders do not work on my Linux machine**

A: Force CPU mode globally:
```bash
export SWARM_RESCUE_USE_SHADERS=false
```

**Q: I want to test both modes in the same script**

A: Use the explicit parameter:
```python
map_cpu = MapIntermediate01(..., use_shaders=False)
map_gpu = MapIntermediate01(..., use_shaders=True)
```

**Q: How can I check which mode is being used?**

A:
```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig
print(ShaderConfig.get_mode_description())
```
