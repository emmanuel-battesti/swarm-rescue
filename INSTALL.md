
# Table of Content
- [Table of Content](#table-of-content)
- [Introduction](#introduction)
- [Installation on macOs](#installation-on-macos)
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
- [Troubleshootings](#troubleshootings)
  - [Desactivation of OpenGL shaders](#desactivation-of-opengl-shaders)
  - [Tool to view your software versions](#tool-to-view-your-software-versions)
  - [Find OpenGL version on Ubuntu](#find-opengl-version-on-ubuntu)
  - [Update Mesa](#update-mesa)
- [Python IDE](#python-ide)
- [Contact](#contact)


# Introduction

This installation procedure has been successfully tested on **Ubuntu** and **Windows 11 with Git Bash**, but Ubuntu is recommended.

# Installation on macOs

Installation on a **macOS system** seems difficult, but is virtually untested and will **not be supported** in the future. *Swarm-Rescue* requires a recent version of *OpenGL* to work. However, recent versions of MacOs no longer use *OpenGL*, but an equivalent library called *Metal*.

In any case, the code has had to be adapted for macOS in the past, resulting in a loss of program performance compared to an Ubuntu machine. (See [Desactivation of OpenGL shaders](#desactivation-of-opengl-shaders))


# Installation on Ubuntu (recommended)

This installation procedure has been tested on Ubuntu 20.04, 22.04 and 24.04.

## **Warning** for Ubuntu users on VirtualBox

**Problems have been reported by VirtualBox users**.

*Swarm-Rescue* uses *OpenGL* via shaders to speed up calculations, and this always seems to be the case. The calculations for emulating the lidar and semantic sensors of the drones are performed, via these shaders, directly on the GPU.

VirtualBox has a problem with the graphics driver and the way it handles OpenGL.

You have several solutions:
- Change to Ubuntu operating system without VirtualBox,
- Use the manipulation describe here: [Desactivation of OpenGL shaders](#desactivation-of-opengl-shaders)

## Git and Arcade library dependencies

First, you will obviously have to install the Git tools.

And for the Python library *Arcade*, which is a library for creating 2D arcade games, you may need to install *libjpeg-dev* and *zlib1g-dev*.

```bash
sudo apt update
sudo apt install git git-gui gitk libjpeg-dev zlib1g-dev
```

## *Python* installation

We need, at least, *Python 3.8*, which is the default version of *Python* on *Ubuntu 20.04*.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-dev python3-pip 
```
You can verify the version with the command :
```bash
python3 --version
```

## Installing this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).
- With your terminal, you have to use those Linux commands, for example:
```bash
cd
mkdir code
cd code
```
- Git-clone the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This command will create the *swarm-rescue* directory with all the code inside it.

- Create your virtual environment. This command will create a *.venv* directory where all dependencies will be installed:

```bash
cd swarm-rescue
python3 -m venv .venv
```

- To use this newly created virtual environment, as each time you need it, use the command:

```bash
source .venv/bin/activate
```

To deactivate this virtual environment, just type: `deactivate`

- With this virtual environment activated, we can install all the dependencies with the command:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

- To test, you can run:

```bash
python3 ./src/swarm_rescue/launcher.py
```

# Installation on Windows 10/11 with WSL2

It's still **very experimental and untested**, but it seems possible to install *Swarm-Rescue* on WSL2 in Windows.
For this to work, certain points need to be checked:
- Use WSL 2 and not WSL 1,
- Have Windows 11 or Windows 10 with the latest updates,
- Update with the latest graphics card drivers, and reboot,
- Use Ubuntu 24.04 (doesn't work on 22.04 or less) for WSL.

Then simply follow the Ubuntu installation instructions: [Installation on Ubuntu (recommended)](#installation-on-ubuntu-recommended)

> [!NOTE]  
> To be more precise, there's no need to install a driver for the graphics card under WSL. WSL uses the Windows driver via a virtual graphics driver. OpenGL, necessary for SwarmRescue's operation, is managed by the Mesa library. The Mesa version of Ubuntu 22 on WSL does not support OpenGL 4.4 as required.

# Installation on Windows 10/11 with GitBash

This installation procedure has been tested on Windows 10 (a build number ending in 2311 or higher) and Windows 11.

## **Warning** for Windows users

**Many problems have been reported by Windows users**, ranging from strange behavior to program failure!

Sometimes it's hard to spot the problem. For example, we've had people report cases where the lidar went through walls or the semantic sensor continued to detect the wounded even though he was “grasped”...

*Swarm-Rescue* uses OpenGL via shaders to speed up calculations, and this always seems to be the case. The calculations for emulating the lidar and semantic sensors of the drones are performed, via these shaders, directly on the GPU.

At the moment, we have noticed these problems with some Windows users. It's probably a problem with the graphics driver or the way Windows handles OpenGL.

The problem doesn't seem to occur on Ubuntu. On some "more powerful" Windows machines (desktop), it also works correctly.

First things first:
- Have Windows 11 or Windows 10 with the latest updates,
- Update your graphics card drivers, and reboot,
- Check the *performance options* of your OS.

If problems persist, you have several solutions:
- Change your machine,
- Change to Ubuntu operating system,
- Use the manipulation describe here: [Desactivation of OpenGL shaders](#desactivation-of-opengl-shaders)

## *Python* installation

- Open the following link in your web browser:  https://www.python.org/downloads/windows/
- The program will **not** work with a Python version greater than or equal to 12.
- Don't choose the latest version of Python, but choose version 3.11.9. Currently (10/2023), it is "*Python 3.11.9 - April 2, 2024*".
- For modern machines, you must select the *Windows installer (64-bit)*.
- Once the installer is downloaded, run the Python installer.
- **Important**: you need to check the "**Add python.exe to path**" check box to include the interpreter in the execution path.

## *Git* installation

Git is a source code management tool. [Git is being used](https://www.simplilearn.com/tutorials/git-tutorial/what-is-git) to track changes in the *swarm-rescue* source code.

 - Download the [latest version of Git](https://git-scm.com/download/win) and select the "64-bit Git for Windows Setup" version.
 - Once the file has been downloaded, install it on your system with the default configuration.
 - Once installed, select *Launch Git Bash*, then click on *finish*. The *Git Bash* is now launched.

We will use the *Git Bash* terminal to work on the project later.

## Configure *Git Bash*

- Run the *Git Bash* terminal.
- **Warning**, by default you may **not** be in your home directory. So to get there, just type `cd`.
- To facilitate the use of the *python* command, you need to create an alias to the real location of the python.exe program: `echo "alias python='winpty python.exe'" >> ~/.bashrc`.
- Then `source .bashrc` to activate the change.
- If everything works, the command `python --version` should show the installed Python version, for example: `Python 3.11.9`.

## Install this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).
- With *Git Bash*, you have to use those Linux commands, for example:
```bash
cd
mkdir code
cd code
```
- Git-clone the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This command will create the *swarm-rescue* directory with all the code inside it.

- Create your virtual environment. This command will create a *.venv* directory where all dependencies will be installed:

```bash
cd swarm-rescue
python -m venv .venv
```

- To use this newly created virtual environment, as each time you need it, use the command:

```bash
source .venv/Scripts/activate
```

To deactivate this virtual environment, just type: `deactivate`

- With this virtual environment activated, we can install all the dependencies with the command:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

- To test, you can run:

```bash
python ./src/swarm_rescue/launcher.py
```
# Troubleshootings

## Desactivation of OpenGL shaders

 Shaders are programs that use OpenGL and are written in the C-like language GLSL. These programs exploit the power of graphics cards and greatly accelerate calculations.

Because of problems with OpenGL, our algorithms, which use shaders, also exist in non-shader versions.
This version can be activated by changing a parameter in the code:
- Open file src/swarm_rescue/spg_overlay/gui_map/closed_playground.py
- Go to line 37,
- Change parameter use_shaders from True to False.
  
The downside of this manipulation is that it reduces performance. Calculations will take longer, especially if you have a lot of drones.

## Tool to view your software versions

To work with Swarm-Rescue, you need OpenGL 4.40 or higher.
To view and check your software versions, you can use the following script: *src/swam_rescue/tools/opengl_info.py*

## Find OpenGL version on Ubuntu

Under Linux or WSL2, you can find out which version of OpenGL is supported with *glxinfo*.

Install *glxinfo*:
```bash
sudo apt update
sudo apt install mesa-utils
```

Use *glxinfo*:
```bash
glxinfo | grep "OpenGL version"
```

## Update Mesa

Under linux or wsl2, to update the Mesa library to the last (but not-official) version:
```bash
sudo add-apt-repository ppa:kisak/kisak-mesa
sudo apt update
sudo apt upgrade
```

# Python IDE

Although not required, it is a good idea to use an IDE when programming in *Python*. It makes programming easier.

For example, you can use the free *community* version of [*PyCharm*](https://www.jetbrains.com/pycharm/). In this case, you will need to set your *interpreter* path to your venv path for it to work. 

# Contact

If you have questions about the code and installation, you can contact:

emmanuel . battesti at ensta-paris . fr

Or use the discord server.

