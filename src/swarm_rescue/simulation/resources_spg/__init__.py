import pathlib

import arcade

#: The absolute path to this directory
SR_RESOURCE_PATH = pathlib.Path(__file__).parent.resolve()

arcade.resources.add_resource_handle("sr", SR_RESOURCE_PATH)
