import tkinter as tk
from tkinter import simpledialog

class MapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Map Editor")
        
        # Canvas for drawing
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar for walls tools (walls file)
        self.walls_sidebar = tk.Frame(root, width=200, bg="lightgray", bd=2, relief="groove")
        self.walls_sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.add_buttons(self.walls_sidebar)

        # Sidebar for map tools (map file)
        self.map_sidebar = tk.Frame(root, width=200, bg="lightgray", bd=2, relief="groove")
        self.map_sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        self.add_buttons(self.map_sidebar)

        self.shapes = []  # To store shapes and their metadata
        self.current_tool = None

        self.nb_zones = {"rescue":0 , "return":0 , "no_com":0 , "no_gps":0 , "killing":0}
        # At most one of these zones per map

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.selected_shape = None

    def add_buttons(self,sidebar):
        if sidebar == self.walls_sidebar:
            # Group 1: Drawing
            tk.Label(sidebar, text="Drawing", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(10, 5))
            tk.Button(sidebar, text="Add Wall", command=lambda: self.set_tool("wall")).pack(pady=5)
            tk.Button(sidebar, text="Add Box", command=lambda: self.set_tool("box")).pack(pady=5)
            tk.Button(sidebar, text="Add Borders", command=self.add_borders).pack(pady=5)
            tk.Button(sidebar, text="Erase", command=lambda: self.set_tool("erase")).pack(pady=5)
            
            # Group 2: Canvas
            tk.Label(sidebar, text="Canvas", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(20, 5))
            tk.Button(sidebar, text="Set Map Size", command=self.set_map_size).pack(pady=5)
            tk.Button(sidebar, text="Clear Canvas", command=self.clear_canvas).pack(pady=5)
            
            # Group 3: Export
            tk.Label(sidebar, text="Export", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(20, 5))
            tk.Button(sidebar, text="Export Map", command=self.export_map).pack(pady=5)
        
        elif sidebar == self.map_sidebar:
            # Group 1: Agents
            tk.Label(sidebar, text="Agents", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(10, 5))
            tk.Button(sidebar, text="Add Wounded Person", command=lambda: self.set_tool("wounded"), fg=self.outline_color("wounded")).pack(pady=5)
            tk.Button(sidebar, text="Add Drone", command=lambda: self.set_tool("drone"), fg=self.outline_color("drone")).pack(pady=5)

            # Group 2: Main Zones
            tk.Label(sidebar, text="Main Zones", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(10, 5))
            tk.Button(sidebar, text="Add Rescue Center", command=lambda: self.set_tool("rescue"), fg=self.outline_color("rescue")).pack(pady=5)
            tk.Button(sidebar, text="Add Return Area", command=lambda: self.set_tool("return"), fg=self.outline_color("return")).pack(pady=5)

            # Group 3: Special Zones
            tk.Label(sidebar, text="Special Zones", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(10, 5))
            tk.Button(sidebar, text="Add No-Com Zone", command=lambda: self.set_tool("no_com"), fg=self.outline_color("no_com")).pack(pady=5)
            tk.Button(sidebar, text="Add No-GPS Zone", command=lambda: self.set_tool("no_gps"), fg=self.outline_color("no_gps")).pack(pady=5)
            tk.Button(sidebar, text="Add Killing Zone", command=lambda: self.set_tool("killing"), fg=self.outline_color("killing")).pack(pady=5)
            
    def set_tool(self, tool):
        self.current_tool = tool

    def outline_color(self, tool):
        D = {"box":"black" , "wounded":"brown" , "drone":"steelblue" , "rescue":"red" , "return":"blue" , "no_com":"yellow" , "no_gps":"orange" , "killing":"purple"}
        return D[tool]

    def add_shape(self, x1, y1, x2, y2):
        # Ensure point 1 is leftmost upmost on the canvas
        list_points = [(x1,y1),(x2,y2)]
        list_points.sort()
        x1,y1 = list_points[0]
        x2,y2 = list_points[1]
        if self.current_tool == "wall":
            # Ensure walls are straight
            if abs(x2 - x1) > abs(y2 - y1):
                y2 = y1
            else:
                x2 = x1
            shape_id = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            self.shapes.append({"type": "wall", "id": shape_id, "start": (x1, y1), "end": (x2, y2)})
        elif self.current_tool == "box":
            shape_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.outline_color(self.current_tool), width=2)
            self.shapes.append({"type": self.current_tool, "id": shape_id, "corner": (x1, y1), "width": x2 - x1, "height": y2 - y1})
        elif self.current_tool in {"wounded" , "drone"}:
            x2,y2 = x1+10,y1+10
            shape_id = self.canvas.create_oval(x1, y1, x2, y2, outline=self.outline_color(self.current_tool), width=2)
            self.shapes.append({"type": self.current_tool, "id": shape_id, "corner": (x1, y1), "width": x2 - x1, "height": y2 - y1})
        else:
            if self.current_tool in self.nb_zones:  # These zones are seen only once or never across the map
                if self.nb_zones[self.current_tool] == 0:
                    shape_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.outline_color(self.current_tool), width=2)
                    self.shapes.append({"type": self.current_tool, "id": shape_id, "corner": (x1, y1), "width": x2 - x1, "height": y2 - y1})
                    self.nb_zones[self.current_tool] = 1
            else:
                shape_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.outline_color(self.current_tool), width=2)
                self.shapes.append({"type": self.current_tool, "id": shape_id, "corner": (x1, y1), "width": x2 - x1, "height": y2 - y1})
                self.nb_zones[self.current_tool] = 1

    def erase_shape(self, x, y):
        for shape in self.shapes:
            if self.canvas.type(shape["id"]) == "line":
                x1, y1, x2, y2 = self.canvas.coords(shape["id"])
                if x1 <= x <= x2 or x2 <= x <= x1:
                    if y1 <= y <= y2 or y2 <= y <= y1:
                        self.canvas.delete(shape["id"])
                        self.shapes.remove(shape)
                        break
            elif self.canvas.type(shape["id"]) in {"rectangle" , "oval"} :
                x1, y1, x2, y2 = self.canvas.coords(shape["id"])
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.canvas.delete(shape["id"])
                    self.shapes.remove(shape)
                    if shape["type"] in {"rescue" , "return" , "no_com" , "no_gps" , "killing"}:
                        self.nb_zones[shape["type"]] = 0
                    break

    def on_canvas_drag(self, event):
        if self.current_tool == "erase":
            self.erase_shape(event.x, event.y)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.shapes.clear()

    def set_map_size(self):
        size_window = tk.Toplevel(self.root)
        size_window.title("Set Map Size")
        
        tk.Label(size_window, text="Width:").grid(row=0, column=0)
        width_entry = tk.Entry(size_window)
        width_entry.grid(row=0, column=1)

        tk.Label(size_window, text="Height:").grid(row=1, column=0)
        height_entry = tk.Entry(size_window)
        height_entry.grid(row=1, column=1)

        def apply_size():
            width = int(width_entry.get())
            height = int(height_entry.get())
            self.canvas.config(width=width, height=height)
            self.canvas_frame.config(width=width, height=height)
            self.root.update_idletasks()
            self.clear_canvas()
            size_window.destroy()

        tk.Button(size_window, text="Apply", command=apply_size).grid(row=2, column=0, columnspan=2)

    def add_borders(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        border_offset = 1 # offset to be able to see the borders in the gui
        self.set_tool("wall")
        self.add_shape(0, border_offset, canvas_width, border_offset)  # Top border
        self.add_shape(canvas_width-border_offset, 0, canvas_width-border_offset, canvas_height)  # Right border
        self.add_shape(canvas_width, canvas_height-border_offset, 0, canvas_height-border_offset)  # Bottom border
        self.add_shape(border_offset, canvas_height, border_offset, 0)  # Left border

    def export_map(self):
        map_name = simpledialog.askstring("Save File", "Enter a name for your map (without extension):")
        if map_name:
            if map_name.endswith(".py"):
                map_name = map_name[:-3]
            self.generate_python_walls_code("walls_" + map_name + ".py")
            self.generate_python_map_code(map_name, "map_" + map_name + ".py")

    # IMPORTANT : the convention used in the simulator is that the origin is at the center of the map, whereas here it is at the top left and the y axis is reversed
    def format_coords(self,pos):
        x,y = pos
        width , height = self.canvas.winfo_width() , self.canvas.winfo_height()
        return ( int( x-(width/2) ) , int( (height/2)-y) )

    def generate_python_walls_code(self, file_path):
        with open(file_path, "w") as f:
            # Header
            f.write("\"\"\"\n")
            f.write("This file was generated by the tool 'map_editor_gui.py' in the directory map_editor.\n")
            f.write("This tool permits to create this kind of file by using a graphical interface.\n")
            f.write("\"\"\"\n\n")

            # Imports
            f.write("from spg_overlay.entities.normal_wall import NormalWall, NormalBox\n\n")

            # Body
            width , height = self.canvas.winfo_width() , self.canvas.winfo_height()
            f.write("# Dimension of the map : ({}, {})\n"
                    .format(width,height))
            f.write("\ndef dimensions():\n")
            f.write(f"    return ({width},{height})\n")

            f.write("\ndef add_walls(playground):\n\n")
            counter_wall = 0
            for shape in self.shapes:
                if shape["type"] == "wall":
                    counter_wall += 1
                    start = shape["start"]
                    end = shape["end"]
                    formatted_start = self.format_coords(start)
                    formatted_end = self.format_coords(end)
                    f.write(f"    wall = NormalWall(pos_start={formatted_start}, pos_end={formatted_end})\n")
                    f.write("    playground.add(wall, wall.wall_coordinates)\n\n")
            if not(counter_wall):    # if no walls were defined
                f.write("    pass\n\n")

            f.write("\ndef add_boxes(playground):\n\n")
            counter_box = 0
            for shape in self.shapes:
                if shape["type"] == "box":
                    counter_box += 1
                    corner = shape["corner"]
                    formatted_corner = self.format_coords(corner)
                    width = shape["width"]
                    height = shape["height"]
                    f.write(f"    box = NormalBox(up_left_point={formatted_corner}, width={width}, height={height})\n")
                    f.write("    playground.add(box, box.wall_coordinates)\n\n")
            if not(counter_box):    # if no boxes were defined
                f.write("    pass\n\n")

    def generate_python_map_code(self, map_name, file_path):
        with open(file_path, "w") as f:
            # Header
            with open("snippets/map_files_header.txt", "r") as header:
                f.write(header.read())
                f.write("\n\n")
            f.write(f"from map_editor.walls_{map_name} import add_walls, add_boxes, dimensions\n\n\n")

        # Body

            # Configs
            f.write(f"class MyMap{map_name}(MapAbstract):\n\n")
            f.write(f"    def __init__(self, zones_config: ZonesConfig = ()):\n")
            f.write(f"        super().__init__(zones_config)\n")
            f.write(f"        self._max_timestep_limit = 2000\n")
            f.write(f"        self._max_walltime_limit = 120\n\n")
            f.write(f"        # PARAMETERS MAP\n")
            f.write(f"        self._size_area = dimensions()\n\n")

            # Zones
            dic_attribute = {"return":"_return_area" , "rescue" : "_rescue_center" , "no_com" : "_no_com_zone" , "no_gps" : "_no_gps_zone" , "killing" : "_kill_zone" }
            dic_class  = {"return":"ReturnArea" , "rescue" : "RescueCenter" , "no_com" : "NoComZone" , "no_gps" : "NoGpsZone" , "killing" : "KillZone" }
            for shape in self.shapes:
                type = shape["type"]
                if not( type in {"wall" , "box", "wounded", "drone"} ):
                    corner = shape["corner"]
                    formatted_corner = self.format_coords(corner)
                    width = shape["width"]
                    height = shape["height"]
                    x,y = formatted_corner
                    formatted_center = (x+width//2,y-height//2)
                    f.write(f"        self.{dic_attribute[type]} = {dic_class[type]}(size={(width,height)})\n")
                    f.write(f"        self.{dic_attribute[type]}_pos = ({formatted_center}, 0)\n\n")
            
            # Wounded Persons
            list_pos_wounded = []
            f.write("        self._wounded_persons_pos = ")
            for shape in self.shapes:
                type = shape["type"]
                if type == "wounded":
                    corner = shape["corner"]
                    formatted_corner = self.format_coords(corner)
                    list_pos_wounded.append(formatted_corner)
            f.write(f"{list_pos_wounded}\n")
            f.write("        self._number_wounded_persons = len(self._wounded_persons_pos)\n")
            f.write("        self._wounded_persons: List[WoundedPerson] = []\n\n")

            # Drones
            list_pos_drone = []
            for shape in self.shapes:
                type = shape["type"]
                if type == "drone":
                    corner = shape["corner"]
                    formatted_corner = self.format_coords(corner)
                    list_pos_drone.append(formatted_corner)
            f.write(f"        self._drones_pos = [(pos, random.uniform(-math.pi, math.pi)) for pos in {list_pos_drone}]\n")
            f.write(f"        self._number_drones = len(self._drones_pos)\n")
            f.write(f"        self._drones: List[DroneAbstract] = []\n\n")

            # Footer
            with open("snippets/map_files_footer.txt", "r") as footer:
                f.write(footer.read())
                f.write("\n")

            f.write(f"        my_map = MyMap{map_name}()\n")
            f.write(f"        my_playground = my_map.construct_playground(drone_type=DroneMotionless)\n\n")
            f.write(f"        gui = GuiSR(playground=my_playground, the_map=my_map, use_mouse_measure=True)\n")
            f.write(f"        gui.run()")

    def on_canvas_click(self, event):
        if self.current_tool == "erase":
            self.erase_shape(event.x, event.y)
        else:
            self.start_x = event.x
            self.start_y = event.y

    def on_canvas_release(self, event):
        if self.current_tool in ["wall", "box", "wounded", "drone", "rescue", "return", "no_com", "no_gps", "killing"]:
            self.add_shape(self.start_x, self.start_y, event.x, event.y)

if __name__ == "__main__":
    root = tk.Tk()
    editor = MapEditor(root)
    root.mainloop()