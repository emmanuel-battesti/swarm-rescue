# Table of Content

- [Introduction](#introduction)
- [Warning for Windows users](#warning-for-windows-users)
- [Installation on Ubuntu](#installation-on-ubuntu)
- [Installation on Windows 10](#installation-on-windows-10)
- [Contact](#contact)


# Introduction

This installation procedure has been tested with **Ubuntu** and **Windows**.

Installation on a **macOS system** seems possible, but is virtually untested and will **not be supported** in the future.

In any case, the code has had to be adapted for macOS in the past, resulting in a loss of program performance compared to a Linux machine. 


# **Warning** for Windows users

**Many problems have been observed by Windows users**, from odd behavior to program failure to launch! They all seem to be linked to the use of OpenGL shaders. 

The calculations for emulating the lidar and semantic sensors of the drones are performed, via these shaders, directly on the GPU. 
At the moment, we have only noticed these problems in some Windows users. It's probably a problem with the graphic driver or the way Windows handles OpenGL. 
The calculations for emulating the lidar and semantic sensors of the drones are performed, via these shaders, directly on the GPU. 

The initial problem doesn't seem to occur under Ubuntu. On some "more powerful" Windows machines (desktop), it also works correctly. 

We have not yet found a solution to these problems.

So, two solutions. If you can, change machine or operating system. 

Otherwise, there's a CPU version of the calculation performed by the shaders. It can be activated by changing a parameter in the code. **Simply change the *use_shaders* parameter from *True* to *False*, line 29 in the *src/swarm_reçue/spg_overlay/gui_map/close_playground.py file*.** 

The disadvantage of this manipulation is that it reduces performance. Calculations take longer when you have a lot of drones.

# Installation on Ubuntu

This installation procedure has been tested with Ubuntu 18.04 and 20.04.

## Arcade library dependencies

First, you will obviously have to use the Git tool.

And for the library *Arcade*, you might need to install *libjpeg-dev* and *zlib1g-dev*.

```bash
sudo apt update
sudo apt install git libjpeg-dev zlib1g-dev
```

## *Python* installation

We need, at least, *Python 3.8*.

- On *Ubuntu 20.04*, the default version of *Python* is 3.8.
- On *Ubuntu 18.04*, the default version of *Python* is 2.7.17. And the default version of *Python3* is 3.6.9.

But it is easy to install *Python* 3.8:
```bash
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

## *Pip* installation

- Install *Pip*:

```bash
sudo apt update
sudo apt install python3-pip 

- When the installation is complete, verify the installation by checking the *Pip* version:

```bash
pip3 --version
```

- It can be useful to upgrade *Pip* to have the last version in local directory:

```bash
/usr/bin/python3.8 -m pip install --upgrade pip
```

To use the correct version, you have to use `python3.8 -m pip` instead of `pip`, for example:

```bash
python3.8 -m pip --version
```

## Virtual environment tools

The safe way to work with *Python* is to create a virtual environment around the project.

For that, you have to install some tools:

```bash
sudo apt update
sudo apt install virtualenvwrapper
```
## Install this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).

- Git-clone the code of [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This command will create the directory *swarm-rescue* with all the code inside it.

- Create your virtual environment. This command will create a directory *env* where all dependencies will be installed:

```bash
cd swarm-rescue
python3.8 -m venv env
```

- To use this newly create virtual environment, as each time you need it, use the command:

```bash
source env/bin/activate
```

To deactivate this virtual environment, simply type: `deactivate`

- With this virtual environment activated, we can install all the dependency with the command:

```bash
python3.8 -m pip install --upgrade pip
python3.8 -m pip install -r requirements.txt
```

- To test, you can launch:

```bash
python3.8 ./src/swarm_rescue/launcher.py
```

## Python IDE

Although not mandatory, it is a good idea to use an IDE to code in *Python*. It makes programming easier.

For example, you can use the free *community* version of [*PyCharm*](https://www.jetbrains.com/pycharm/). In this case, you have to set your *interpreter* path to your venv path to make it work. 


# Installation on Windows 10

This installation procedure has been tested with Windows 10. Installation is also straightforward on Windows 11.

## *Python* installation

- Open this link in your web browser:  https://www.python.org/downloads/windows/
- The program will **not** work with a Python version greater than or equal to 12.
- Don't choose the latest version of Python, but choose the 3.11.6 version. Currently (10/2023), it is the "*Python 3.11.6 - Oct 2, 2023*".
- For modern machine, you have to choose the *Windows installer (64-bit)*.
- Once the installer is downloaded, run the Python installer.
- **Important**: you need to check the "**Add python.exe to path**" check box to include the interpreter in the execution path.

## *Git* installation

Git is a tool for source code management. [Git is used](https://www.simplilearn.com/tutorials/git-tutorial/what-is-git "Git is used") to tracking changes in the source code of *swarm-rescue*.

 - Download the [latest version of Git](https://git-scm.com/download/win) and choose the "64-bit Git for Windows Setup" version.
 - Once the file has been downloaded, install it on the system with the default configuration.
 - Once installed, select *Launch Git Bash*, then click on *finish*. The *Git Bash* is now launched.

We want to work on the project later using the *Git Bash* terminal.

## Configure *Git Bash*

- Launch the *Git Bash* terminal
- **Warning**, you may **not** be, by default, to your home directory. So to go there, just type: *cd*
- To facilitate the use of the command *python*, you have to create an alias to real position of the program python.exe: `echo "alias python='winpty py'" >> ~/.bashrc`
- Then `source .bashrc` to activate the modification.
- If things work, the command `python -V` should give the version of the Python installed, for example: `Python 3.11.6`

## Install this *swarm-rescue* repository

- To install this git repository, go to the directory you want to work in (for example: *~/code/*).
- With *Git Bash*, you have to use the Linux command, for example:
```bash
cd
mkdir code
cd code
```
- Git-clone the code of [*Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue):

```bash
git clone https://github.com/emmanuel-battesti/swarm-rescue.git
```
This command will create the directory *swarm-rescue* with all the code inside it.

- Create your virtual environment. This command will create a directory *env* where all dependencies will be installed:

```bash
cd swarm-rescue
python -m venv env
```

- To use this newly create virtual environment, as each time you need it, use the command:

```bash
source env/Scripts/activate
```

To deactivate this virtual environment, simply type: `deactivate`

- With this virtual environment activated, we can install all the dependency with the command:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

- To test, you can launch:

```bash
python ./src/swarm_rescue/launcher.py
```

# Contact

If you have questions about the code and installation, you can contact:

emmanuel . battesti at ensta-paris . fr

Or use the discord server.

