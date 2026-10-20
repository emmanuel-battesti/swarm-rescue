# Table of Contents
- [Table of Contents](#table-of-contents)
- [Introduction](#introduction)
- [Installation on macOS](#installation-on-macos)
- [Installation on Ubuntu (recommended)](#installation-on-ubuntu-recommended)
  - [**Warning** for Ubuntu users on VirtualBox](#warning-for-ubuntu-users-on-virtualbox)
  - [Git and Arcade library dependencies](#git-and-arcade-library-dependencies)
  - [*Python* installation](#python-installation)
  - [Installing this *swarm-rescue* repository](#installing-this-swarm-rescue-repository)
- [Installation on Windows 10/11 with WSL2](#installation-on-windows-1011-with-wsl2)
- [Installation on Windows 10/11 with GitBash](#installation-on-windows-1011-with-gitbash)
  - [**Warning** for Windows users](#warning-for-windows-users)
  - [*Python* installation](#python-installation-1)
  - [*Git* installation](#git-installation)
  - [Configure *Git Bash*](#configure-git-bash)
  - [Install this *swarm-rescue* repository](#install-this-swarm-rescue-repository)
- [Troubleshooting](#troubleshooting)
  - [Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders)
  - [Check software versions](#check-software-versions)
  - [Find OpenGL version on Ubuntu](#find-opengl-version-on-ubuntu)
  - [Update Mesa library](#update-mesa-library)
  - [Shader behaviour in headless environments (CI, containers, no display)](#shader-behaviour-in-headless-environments-ci-containers-no-display)
- [Python IDE](#python-ide)
- [Contact](#contact)

# Introduction

This installation procedure has been successfully tested on **Ubuntu** and **Windows 11 with Git Bash**. Ubuntu is the recommended platform for optimal performance and stability.

# Installation on macOS

Installation on **macOS systems** is challenging and is **not officially supported**. *Swarm-Rescue* requires a recent version of *OpenGL* to function properly. However, recent versions of macOS no longer use *OpenGL* and instead rely on Apple's *Metal* graphics framework.

In any case, the code has had to be adapted for macOS in the past, resulting in significant performance degradation compared to Ubuntu systems. If you must use macOS, refer to [Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders).

# Installation on Ubuntu (recommended)

This installation procedure has been tested on Ubuntu 20.04, 22.04 and 24.04.

## **Warning** for Ubuntu users on VirtualBox

**VirtualBox users have reported compatibility issues**.

*Swarm-Rescue* uses *OpenGL* shaders to accelerate computations. The lidar and semantic sensor calculations are performed directly on the GPU via these shaders for optimal performance.

VirtualBox has known issues with graphics drivers and OpenGL handling, which can cause problems with *Swarm-Rescue*.

You have several solutions:
- **Recommended**: Install Ubuntu natively (not in VirtualBox)
- **Alternative**: Follow the workaround described in [Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders)

## Git and Arcade library dependencies

First, you will obviously have to install the Git tools.

The *Arcade* library (used for 2D graphics) requires *libjpeg-dev* and *zlib1g-dev* for proper functionality.

```bash
sudo apt update
sudo apt install git git-gui gitk libjpeg-dev zlib1g-dev
```

## *Python* installation

*Swarm-Rescue* requires **Python 3.10 or higher**.

> **Note:** Ubuntu 20.04 ships Python 3.8 by default, which is **not** supported anymore: the
> *Arcade* 3.x dependency requires Python >= 3.10. On Ubuntu 20.04 you must install a newer
> interpreter (for example with `pyenv`, or the *deadsnakes* PPA).

Then install a Python >= 3.10 interpreter. With `pyenv`:

```bash
curl -fsSL https://pyenv.run | bash
pyenv install 3.12
```

Verify your Python version (it must be 3.10 or higher):
```bash
python3 --version
```

## Installing this *swarm-rescue* repository

**Step 1: Prepare your workspace**
Navigate to your desired working directory (e.g., *~/code/*):

```bash
cd
mkdir code
cd code
```

**Step 2: Clone the repository**
Download the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```

This creates the *swarm-rescue* directory with all the source code.

**Step 3: Create a virtual environment**
Set up an isolated Python environment for the project:

```bash
cd swarm-rescue
# Use your Python 3.10+ interpreter explicitly (e.g. python3.12 with pyenv)
python3.12 -m venv .venv
```
It creates a *.venv* directory where all dependencies are installed.

**Step 4: Activate the virtual environment**
Activate the environment (required each time you work with the project):

```bash
source .venv/bin/activate
```

To deactivate the virtual environment when finished: `deactivate`

**Step 5: Install dependencies**
With the virtual environment activated, install all required packages:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install --editable .
```

**Step 6: Test the installation**
Verify everything works by running the launcher:

```bash
python src/swarm_rescue/launcher.py
```

# Installation on Windows 10/11 with WSL2

It's still **very experimental and untested**, but it seems possible to install *Swarm-Rescue* on WSL2 on Windows.
For this to work, certain points need to be checked:
- Use WSL 2 and not WSL 1,
- Have Windows 11 or Windows 10 with the latest updates,
- Update with the latest graphics card drivers, and reboot,
- Use Ubuntu 24.04 for WSL (Ubuntu 22.04 or earlier will not work).

Then simply follow the Ubuntu installation instructions: [Installation on Ubuntu (recommended)](#installation-on-ubuntu-recommended)

> [!NOTE]
> To be more precise, there's no need to install a driver for the graphics card under WSL. WSL uses the Windows graphics driver through a virtual interface. OpenGL support is provided by the Mesa library. Ubuntu 22.04's Mesa version in WSL does not support the required OpenGL 4.4 features, which is why Ubuntu 24.04 is mandatory.

# Installation on Windows 10/11 with GitBash

This installation procedure has been tested on Windows 11 (October 2025)

## **Warning** for Windows users

**Windows users have reported various issues**, ranging from unexpected behavior to complete program failure.

**Common Problems:**
- Lidar sensors detecting through walls
- Semantic sensors continuing to detect wounded persons even when grasped
- General simulation instabilities

**Root Cause:**

*Swarm-Rescue* uses OpenGL shaders for GPU-accelerated computations (lidar and semantic sensor calculations). These issues appear to stem from graphics driver compatibility or Windows' OpenGL implementation.
The problem doesn't seem to occur on Ubuntu. On some "more powerful" Windows machines (desktop), it also works correctly.

**Environment Requirements:**
- Windows 11 or Windows 10 with latest updates
- Up-to-date graphics card drivers (restart after installation)
- Optimal performance settings configured

If problems persist, you have several solutions:
- Change to Ubuntu operating system,
- Change your machine, more powerful desktop machines tend to have fewer issues
- Use the workaround in [Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders)

## *Python* installation

- Open the following link in your web browser: https://www.python.org/downloads/windows/
- The program requires **Python 3.10 or higher**.
- This procedure was validated with **Python 3.11** on Windows. Versions above 3.11 have not been tested on Windows yet: they should work, and any issue is worth reporting.
- For modern machines, you must select the *Windows installer (64-bit)*.
- Once the installer is downloaded, run the Python installer.
- **Important**: you need to check the "**Add python.exe to path**" check box to include the interpreter in the execution path.

## *Git* installation

Git is essential for source code management and tracking changes in the *swarm-rescue* project.

**Installation Steps:**
1. Download the [latest version of Git](https://git-scm.com/download/win)
2. Select "Git for Windows/x64 Setup" in "Standalone Installer"
3. Install with default configuration settings
4. Select "Launch Git Bash" and click "Finish"

The *Git Bash* terminal will be your primary interface for project work.

## Configure *Git Bash*

- Run the *Git Bash* terminal.
- **Warning**, by default, you may **not** be in your home directory. So to get there, just type `cd`.
- If everything works, the command `python --version` should show the installed Python version, for example: `Python 3.11.9`.

## Install this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).
- With *Git Bash*, you have to use those Linux commands, for example:
```bash
cd
mkdir code
cd code
```

Clone the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```

This creates the *swarm-rescue* directory with all the source code.

- Create your virtual environment. This command will create a *.venv* directory where all dependencies will be installed:

```bash
cd swarm-rescue
python -m venv .venv
```

- To use this newly created virtual environment, as each time you need it, use the command:

```bash
source .venv/Scripts/activate
```

To deactivate this virtual environment when finished, just type: `deactivate`

- With this virtual environment activated, we can install all the dependencies with the command:

```bash
python -m pip install --upgrade pip
python -m pip install --editable .
```

Test the installation:

```bash
python src/swarm_rescue/launcher.py
```

> **Headless environments (CI, containers, no display):** shader tests are
> unreliable when OpenGL falls back to Mesa's software renderer. See
> [Shader behaviour in headless environments](#shader-behaviour-in-headless-environments-ci-containers-no-display).

# Troubleshooting

## Deactivation of OpenGL shaders

Shaders are GPU-accelerated programs written in GLSL that significantly improve performance. However, compatibility issues may require disabling them. You can control shader usage in three ways (preferred order):

1. Environment variable (recommended for quick sessions or CI):

```bash
# Disable shaders globally for the process
export SWARM_RESCUE_USE_SHADERS=false
# Run the launcher
python src/swarm_rescue/launcher.py
```

2. Per-map parameter (apply only to a specific map instance):

```text
# Example (replace <YourDroneClass> with the drone class you use):
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
map_cpu = MapIntermediate01(drone_type=<YourDroneClass>, use_shaders=False)
```

3. Python API (programmatic, useful in tests):

```python
from swarm_rescue.simulation.utils.shader_config import ShaderConfig
# Force CPU mode for the duration of the process or test
ShaderConfig.force_cpu_mode()
# Reset auto-detection later if needed
ShaderConfig.reset()
```

**Note:** editing the source code to change defaults is discouraged. Prefer the three mechanisms above to change shader mode. Disabling shaders reduces performance (especially with many drones) but increases compatibility on systems with problematic GPU/OpenGL drivers.

## Check software versions

*Swarm-Rescue* requires **OpenGL 3.3 core** or higher to open the Arcade window.
GPU-accelerated sensors additionally need **OpenGL 4.4**, because the compute
shader (`id_compute.glsl`) declares `#version 440`. Without 4.4, disable the
shaders as described in [Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders).
Use this script to verify your system:

```bash
python src/swarm_rescue/tools/opengl_info.py
```

## Find OpenGL version on Ubuntu

Check your OpenGL version using *glxinfo*:

Install *glxinfo*:
```bash
sudo apt update
sudo apt install mesa-utils
```

Use *glxinfo*:
```bash
glxinfo | grep "OpenGL version"
```

## Update Mesa library

Under Linux or WSL2, to update the Mesa library to the latest (but unofficial) version:
```bash
sudo add-apt-repository ppa:kisak/kisak-mesa
sudo apt update
sudo apt upgrade
```

## Shader behaviour in headless environments (CI, containers, no display)

The shader path is **unreliable when the test suite runs without a real GPU**,
which is the case for most CI runners and containers. The symptom that shows up
there is `tests/test_sensor_consistency.py::test_lidar_shader_vs_cpu_similarity`
failing intermittently, with the shader reporting a hit at distance 0 where the
CPU measures a wall 200-300 px away.

> **Note:** this is **not** the same failure as the Windows one described above.
> That one is reported by users running on real GPUs and reports "lidar
> detecting through walls"; nothing reproduced here matches that behavior, and
> it has a different mechanism. Do not assume one fix covers the other.

**Why:** without a display, OpenGL falls back to Mesa's **software** renderer
(`llvmpipe` or `softpipe`). Compute shaders then run on the CPU through Mesa
instead of on the GPU. Measured on this project, the object id the shader reads
back can come back off by one, which is enough to make a drone detect its own
base as an obstacle at zero range. `xvfb-run` is not a workaround, it is exactly
what triggers the fallback:

```bash
$ .venv/bin/python -c "import arcade, pyglet; w = arcade.Window(50,50,visible=False); \
    print(pyglet.gl.gl_info.get_renderer()); w.close()"
AMD RENOIR (DRM 3.42.0)      # a real GPU: the shader tests are reliable
llvmpipe (LLVM 12.0.0)       # software rendering: the shader tests are not
```

**Check this first** whenever a shader test fails on a machine you believe to be
correct, or before reporting a shader bug:

```bash
python src/swarm_rescue/tools/opengl_info.py
glxinfo -B | grep -i renderer
```

If the renderer contains `llvmpipe` or `softpipe`, there is no GPU in use and the
failure is expected: run the suite on a machine with a real GPU, or disable
shaders with the mechanisms described in
[Deactivation of OpenGL shaders](#deactivation-of-opengl-shaders). Note that
`tests/test_shader_config.py` already skips GPU tests on CI for this reason.

The shader now tolerates that one-unit drift when matching invisible ids, which
makes the suite pass under `llvmpipe`. That is a mitigation for the measured
symptom, not a repair of the driver: an id read wrong is still wrong whenever it
identifies a visible entity.

> This failure mode is **not** a sign of a broken installation and does not
> affect the CPU fallback path used for the actual competition runs.

# Python IDE

While optional, using an IDE improves the Python development experience.

**Recommended**: [*PyCharm Community*](https://www.jetbrains.com/pycharm/) (free)
- Configure the interpreter path to your virtual environment (.venv) for proper integration 

# Contact

For questions about installation or code:

**Email**: emmanuel . battesti at ensta . fr  
**Discord**: Available on the project's Discord server
