# Table of Content
- [Table of Content](#table-of-content)
- [Introduction](#introduction)
- [**Warning** for Windows or VirtualBox users](#warning-for-windows-or-virtualbox-users)
- [Installation on Ubuntu (recommended)](#installation-on-ubuntu-recommended)
  - [Git and Arcade library dependencies](#git-and-arcade-library-dependencies)
  - [*Python* installation](#python-installation)
  - [Installing this *swarm-rescue* repository](#installing-this-swarm-rescue-repository)
  - [Python IDE](#python-ide)
- [Installation on Windows 10](#installation-on-windows-10)
  - [*Python* installation](#python-installation-1)
  - [*Git* installation](#git-installation)
  - [Configure *Git Bash*](#configure-git-bash)
  - [Install this *swarm-rescue* repository](#install-this-swarm-rescue-repository)
- [Contact](#contact)


# Introduction

This installation procedure has been tested with **Ubuntu** and **Windows**.

Installation on a **macOS system** seems possible, but is virtually untested and will **not be supported** in the future.

In any case, the code has had to be adapted for macOS in the past, resulting in a loss of program performance compared to a Linux machine. 

# **Warning** for Windows or VirtualBox users

**Many problems have been reported by Windows or VirtualBox users**, ranging from strange behavior to program failure! They all seem to be related to the use of OpenGL shaders.

The calculations for emulating the lidar and semantic sensors of the drones are performed directly on the GPU via these shaders.
At the moment, we have noticed these problems with some Windows users. It's probably a problem with the graphics driver or the way Windows handles OpenGL. We are also seeing the same issues with the users running Ubuntu on VirtualBox.
The calculations for emulating the lidar and semantic sensors of the drones are performed, via these shaders, directly on the GPU.

The problem doesn't seem to occur on Ubuntu (not VirtualBox). On some "more powerful" Windows machines (desktop), it also works correctly.

We have not found a solution for these problems yet.

So, two solutions. If you can, change your machine or operating system.

Otherwise, there's a CPU version of the shader calculation. It can be enabled by changing a parameter in the code. **Just change the *use_shaders* parameter from *True* to *False*, line 37 in the *src/swarm_rescue/spg_overlay/gui_map/closed_playground.py* file.**

The downside of this manipulation is that it reduces performance. Calculations will take longer especially if you have a lot of drones.

# Installation on Ubuntu (recommended)

This installation procedure has been tested on Ubuntu 20.04, 22.04 and 24.04.

## Git and Arcade library dependencies

First, you will obviously have to use the Git tool.

And for the Python library *Arcade*, you may need to install *libjpeg-dev* and *zlib1g-dev*.

```bash
sudo apt update
sudo apt install git git-gui libjpeg-dev zlib1g-dev
```

## *Python* installation

We need, at least, *Python 3.8*, which is the default version of *Python* on *Ubuntu 20.04*.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-dev python3-pip 
```

## Installing this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).

- Git-clone the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This will create the *swarm-rescue* directory with all the code inside it.

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

## Python IDE

Although not required, it is a good idea to use an IDE when programming in *Python*. It makes programming easier.

For example, you can use the free *community* version of [*PyCharm*](https://www.jetbrains.com/pycharm/). In this case, you will need to set your *interpreter* path to your venv path for it to work. 


# Installation on Windows 10

This installation procedure has been tested on Windows 10. Installation is also straightforward on Windows 11.

## *Python* installation

- Open the following link in your web browser:  https://www.python.org/downloads/windows/
- The program will **not** work with a Python version greater than or equal to 12.
- Don't choose the latest version of Python, but choose version 3.11.6. Currently (10/2023), it is "*Python 3.11.6 - Oct 2, 2023*".
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
- **Warning**, by default you may **not* be in your home directory. So to get there, just type *cd*.
- To facilitate the use of the *python* command, you need to create an alias to the real location of the python.exe program: `echo "alias python='winpty py'" >> ~/.bashrc`.
- Then `source .bashrc` to activate the change.
- If everything works, the command `python -V` should show the installed Python version, for example: `Python 3.11.6`.

## Install this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).
- With *Git Bash*, you have to use the Linux command, for example:
```bash
cd
mkdir code
cd code
```
- Git-clone the code from [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This command will create the *swarm-rescue* directory with all the code in it.

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

# Contact

If you have questions about the code and installation, you can contact:

emmanuel . battesti at ensta-paris . fr

Or use the discord server.

