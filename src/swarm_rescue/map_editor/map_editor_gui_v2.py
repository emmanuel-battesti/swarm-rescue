import tkinter as tk
from tkinter import filedialog

class MapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Map Editor")
        
        # Canvas for drawing
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar for tools
        self.sidebar = tk.Frame(root, width=200, bg="lightgray")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.add_buttons()
        self.shapes = []  # To store shapes and their metadata
        self.current_tool = None

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.selected_shape = None

    def add_buttons(self):
        # Group 1: Drawing
        tk.Label(self.sidebar, text="Drawing", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        tk.Button(self.sidebar, text="Add Wall", command=lambda: self.set_tool("wall")).pack(pady=5)
        tk.Button(self.sidebar, text="Add Box", command=lambda: self.set_tool("box")).pack(pady=5)
        tk.Button(self.sidebar, text="Add Borders", command=self.add_borders).pack(pady=5)
        tk.Button(self.sidebar, text="Erase", command=lambda: self.set_tool("erase")).pack(pady=5)
        
        # Group 2: Canvas
        tk.Label(self.sidebar, text="Canvas", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        tk.Button(self.sidebar, text="Set Map Size", command=self.set_map_size).pack(pady=5)
        tk.Button(self.sidebar, text="Clear Canvas", command=self.clear_canvas).pack(pady=5)
        
        # Group 3: Export
        tk.Label(self.sidebar, text="Export", bg="lightgray", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        tk.Button(self.sidebar, text="Export Map", command=self.export_map).pack(pady=5)

    def set_tool(self, tool):
        self.current_tool = tool

    def add_shape(self, x1, y1, x2, y2):
        if self.current_tool == "wall":
            # Ensure walls are straight
            if abs(x2 - x1) > abs(y2 - y1):
                y2 = y1
            else:
                x2 = x1
            shape_id = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            self.shapes.append({"type": "wall", "id": shape_id, "start": (x1, y1), "end": (x2, y2)})
        elif self.current_tool == "box":
            shape_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=2)
            self.shapes.append({"type": "box", "id": shape_id, "corner": (x1, y1), "width": x2 - x1, "height": y2 - y1})

    def erase_shape(self, x, y):
        for shape in self.shapes:
            if self.canvas.type(shape["id"]) == "line":
                x1, y1, x2, y2 = self.canvas.coords(shape["id"])
                if x1 <= x <= x2 or x2 <= x <= x1:
                    if y1 <= y <= y2 or y2 <= y <= y1:
                        self.canvas.delete(shape["id"])
                        self.shapes.remove(shape)
                        break
            elif self.canvas.type(shape["id"]) == "rectangle":
                x1, y1, x2, y2 = self.canvas.coords(shape["id"])
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.canvas.delete(shape["id"])
                    self.shapes.remove(shape)
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
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if file_path:
            self.generate_python_code(file_path)

    def generate_python_code(self, file_path):
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
            f.write("\ndef dimensions(playground):\n")
            f.write(f"    return({width},{height})\n")

            f.write("\ndef add_walls(playground):\n\n")
            counter_wall = 0
            for shape in self.shapes:
                if shape["type"] == "wall":
                    counter_wall += 1
                    start = shape["start"]
                    end = shape["end"]
                    f.write(f"    wall = NormalWall(pos_start={start}, pos_end={end})\n")
                    f.write("    playground.add(wall, wall.wall_coordinates)\n\n")
            if not(counter_wall):    # if no walls were defined
                f.write("    pass\n\n")

            f.write("\ndef add_boxes(playground):\n\n")
            counter_box = 0
            for shape in self.shapes:
                if shape["type"] == "box":
                    counter_box += 1
                    corner = shape["corner"]
                    width = shape["width"]
                    height = shape["height"]
                    f.write(f"    box = NormalBox(up_left_point={corner}, width={width}, height={height})\n")
                    f.write("    playground.add(box, box.wall_coordinates)\n\n")
            if not(counter_box):    # if no boxes were defined
                f.write("    pass\n\n")

    def on_canvas_click(self, event):
        if self.current_tool == "erase":
            self.erase_shape(event.x, event.y)
        else:
            self.start_x = event.x
            self.start_y = event.y

    def on_canvas_release(self, event):
        if self.current_tool in ["wall", "box"]:
            self.add_shape(self.start_x, self.start_y, event.x, event.y)

if __name__ == "__main__":
    root = tk.Tk()
    editor = MapEditor(root)
    root.mainloop()
