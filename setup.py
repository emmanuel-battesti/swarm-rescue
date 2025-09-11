from setuptools import setup, find_packages
from os import path

# Read the requirements from the file
def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()

# Read the README file for the long description
def read_long_description():
    this_directory = path.abspath(path.dirname(__file__))
    with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        return f.read()

    
setup(
    name='swarm-rescue',
    version='5.0.0',
    description='Set up a team of drones to rescue wounded people in different locations...',
    author='Emmanuel Battesti',
    author_email='emmanuel.battesti@ensta.fr',
    url='https://github.com/emmanuel-battesti/swarm-rescue',
    license='MIT',
    packages=find_packages(where="src"),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=read_requirements(),
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
)
