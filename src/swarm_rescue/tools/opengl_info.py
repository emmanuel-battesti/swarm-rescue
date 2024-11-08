import arcade
import platform
import os
import subprocess
import sys

def get_system_info():
    print("\n* Récupération des informations du système d'exploitation...")
    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    platform_details = platform.platform()  # Détails de la plateforme

    # Informations détaillées pour Linux
    if os_name == "Linux":
        try:
            with open("/etc/os-release") as f:
                os_info = {}
                for line in f:
                    key, value = line.strip().split("=", 1)
                    os_info[key] = value.strip('"')
            distro_name = os_info.get("NAME", "Unknown")
            distro_version = os_info.get("VERSION", "Unknown")
            print(f"Operating System: {distro_name} {distro_version}")
        except Exception as e:
            print("Erreur de lecture de /etc/os-release:", e)
            distro_name, distro_version = "Unknown", "Unknown"
    else:
        distro_name, distro_version = os_name, os_version

    print("OS Name:", distro_name)
    print("OS Version:", distro_version)
    print("OS Release:", os_release)
    print("platform_details:", platform_details)

def get_windows_version():
    print("\n* Récupération de la version de Windows...")

    try:
        # Exécuter la commande pour obtenir la version de Windows via cmd.exe
        if "microsoft-standard" in platform.uname().release:  # Détection de WSL
            # Change le répertoire courant vers un chemin valide
            os.chdir("/mnt/c")  # Change vers le disque C: monté sous WSL

        # Exécute la commande pour obtenir la version de Windows via cmd.exe
        windows_version = subprocess.check_output(["cmd.exe", "/c", "ver"], universal_newlines=True)
        print("Version de Windows :", windows_version.strip())
    except Exception as e:
        print("Erreur lors de la récupération de la version de Windows :", e)

def get_opengl_info():
    print("\n* Récupération des informations OpenGL...")
    window = arcade.Window(800, 600, "OpenGL Info")
    try:

	    # Récupérer le contexte
    	context = window.ctx

	    # Afficher des informations sur OpenGL
    	print("OpenGL Vendor:", context.info.VENDOR)
    	print("OpenGL Renderer:", context.info.RENDERER)
    	print("OpenGL Version:", context.gl_version)
    	#print("GLSL Version:", context.info.glsl_version)
    except Exception as e:
        print("Erreur lors de la récupération des informations OpenGL:", e)

    window.close()

def get_mesa_version():
    print("\n* Récupération de la version de Mesa avec glxinfo")
    try:
        # Exécute la commande pour obtenir la version de Mesa
        version_info = subprocess.check_output(["glxinfo"], universal_newlines=True)
        for line in version_info.splitlines():
            if "OpenGL version string" in line:
                print("Version OpenGL et Mesa:", line.split(":")[1].strip())
            if "OpenGL shading language version" in line:
                print("Version shading language:", line.split(":")[1].strip())
    except FileNotFoundError:
        if platform.system() == "Linux":
            print("Erreur : 'glxinfo' n'est pas installé. Veuillez l'installer avec la commande suivante :")
            print("sudo apt install mesa-utils")
        else:
            print("Erreur : 'glxinfo' n'est pas disponible sur ce système.")
    except Exception as e:
        print("Erreur lors de la récupération de la version de Mesa:", e)

def get_python_version():
    print("\n* Récupération de la version de Python")
    print("Version de Python :", sys.version.strip())

# Exécute la fonction pour obtenir les informations sur l'OS et OpenGL
get_system_info()
get_windows_version()
get_opengl_info()
get_mesa_version()
get_python_version()
