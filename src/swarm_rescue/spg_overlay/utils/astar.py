import heapq
import math
import copy
import numpy as np

def octile_heuristic(a, b):
    """
    Heuristique octile pour déplacements 8 directions :
    h = dx + dy + (√2 - 2)*min(dx, dy)
    """
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return dx + dy + (math.sqrt(2) - 2)*min(dx, dy)

def a_star_search(grid, start, goal):
    """
    A* sur une grille avec déplacements diagonaux.
    Coût des mouvements :
    - Horizontal/Vertical : 1
    - Diagonal : √2

    grid: 0 = libre, 1 = obstacle
    start: (x, y)
    goal: (x, y)
    """
    if not (0 <= start[0] < len(grid) and 0 <= start[1] < len(grid[0])):
        return []
    if not (0 <= goal[0] < len(grid) and 0 <= goal[1] < len(grid[0])):
        return []
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        print("START OR GOAL NOT IN FREE GRID")
        print("start=", start)
        print("goal=", goal)
        print("grid[start[0]][start[1]]=", grid[start[0]][start[1]])
        print("grid[goal[0]][goal[1]]=", grid[goal[0]][goal[1]])
        return []

    # 8 directions : V, H, et diagonales
    neighbors = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]

    open_set = []
    heapq.heappush(open_set, (0, start[0], start[1]))

    came_from = {}
    g_score = {(start[0], start[1]): 0}
    f_score = {(start[0], start[1]): octile_heuristic(start, goal)}

    def reconstruct_path(came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    while open_set:
        _, x, y = heapq.heappop(open_set)
        current = (x, y)

        if current == goal:
            return reconstruct_path(came_from, current)

        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy

            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and grid[nx][ny] == 0:
                # Coût du mouvement : √2 si diagonale, 1 sinon
                move_cost = math.sqrt(2) if dx != 0 and dy != 0 else 1
                tentative_g_score = g_score[current] + move_cost

                if (nx, ny) not in g_score or tentative_g_score < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g_score
                    f_score[(nx, ny)] = tentative_g_score + octile_heuristic((nx, ny), goal)
                    heapq.heappush(open_set, (f_score[(nx, ny)], nx, ny))

    return []

def is_walkable(x, y, grid):
    # Vérifie que (x, y) est dans les bornes de la grille
    if x < 0 or y < 0 or y >= len(grid[0]) or x >= len(grid):
        return False
    return grid[x][y] == 0

def bresenham_line(x0, y0, x1, y1):
    """Retourne tous les points sur la ligne entre (x0,y0) et (x1,y1) en utilisant l'algorithme de Bresenham."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x1, y1))
    return points

def can_go_straight(x0, y0, x1, y1, grid):
    line_points = bresenham_line(x0, y0, x1, y1)
    for (x, y) in line_points:
        if not is_walkable(x, y, grid):
            return False
    return True

def simplify_by_line_of_sight(path, grid):
    if len(path) < 2:
        return path

    simplified = [path[0]]

    for i in range(1, len(path)):
        # On essaye d'aller directement du dernier waypoint dans simplified jusqu'à path[i]
        if not can_go_straight(simplified[-1][0], simplified[-1][1], path[i][0], path[i][1], grid):
            # Si on ne peut pas aller directement, on ajoute le point précédent (path[i-1]) comme waypoint
            simplified.append(path[i-1])
    # Le dernier point est toujours inclus
    if simplified[-1] != path[-1]:
        simplified.append(path[-1])

    return simplified

def simplify_collinear_points(path):
    if len(path) < 3:
        return path  # Pas besoin de simplifier
    
    simplified = [path[0]]  # Le premier point est toujours inclus

    # Direction initiale
    prev_dx = path[1][0] - path[0][0]
    prev_dy = path[1][1] - path[0][1]

    for i in range(2, len(path)):
        dx = path[i][0] - path[i-1][0]
        dy = path[i][1] - path[i-1][1]

        # On vérifie si la direction actuelle est la même que la direction précédente
        if dx * prev_dy != dy * prev_dx:
            # La direction a changé, on ajoute le point précédent (i-1) au chemin simplifié
            simplified.append(path[i-1])
            prev_dx = dx
            prev_dy = dy

    # Le dernier point est toujours inclus
    simplified.append(path[-1])
    return simplified

def perpendicular_distance(point, start, end):
    """Calcule la distance perpendiculaire du point à la ligne (start-end)."""
    (x0, y0) = start
    (x1, y1) = end
    (x, y) = point

    # Distance start->end
    dx = x1 - x0
    dy = y1 - y0
    if dx == 0 and dy == 0:
        return math.hypot(x - x0, y - y0)

    # Projection du point sur la ligne
    t = ((x - x0) * dx + (y - y0) * dy) / (dx*dx + dy*dy)
    closest_x = x0 + t * dx
    closest_y = y0 + t * dy

    return math.hypot(x - closest_x, y - closest_y)

def ramer_douglas_peucker(points, epsilon):
    if len(points) < 2:
        return points

    # Trouve le point le plus éloigné de la ligne start-end
    start = points[0]
    end = points[-1]
    max_dist = 0
    index = 0
    for i in range(1, len(points)-1):
        dist = perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            index = i

    # Si la distance max est supérieure à epsilon, on simplifie récursivement
    if max_dist > epsilon:
        first_part = ramer_douglas_peucker(points[:index+1], epsilon)
        second_part = ramer_douglas_peucker(points[index:], epsilon)
        return first_part[:-1] + second_part
    else:
        return [start, end]

def inflate_obstacles(grid, inflation_radius=1):
    rows = len(grid)
    cols = len(grid[0])
    # deep copy of the grid
    inflated_grid = copy.deepcopy(grid)
    print("inflated_grid=", inflated_grid)
    print("grid=", grid)

    for x in range(rows):
        for y in range(cols):
            if grid[x][y] == 1:
                for dx in range(-inflation_radius, inflation_radius+1):
                    for dy in range(-inflation_radius, inflation_radius+1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols:
                            inflated_grid[nx][ny] = 1
    
    print(f" 0 inflated  : {np.count_nonzero(inflated_grid == 0)}")
    return inflated_grid

# fonction qui cherche le point le plus proche libre dans une grille de 0 et 1(0 est libre

def next_point_free(grid, x, y):
    rows = len(grid)
    cols = len(grid[0])

    for i in range(0, rows):  # i parcourt la distance verticale
        for j in range(0, cols):  # j parcourt la distance horizontale
            # Vérification de chaque direction en s'assurant de rester dans la grille
            if (x+i < rows and y+j < cols) and grid[x+i][y+j] == 0:
                return (x+i, y+j)
            if (x-i >= 0 and y-j >= 0) and grid[x-i][y-j] == 0:
                return (x-i, y-j)
            if (x+i < rows and y-j >= 0) and grid[x+i][y-j] == 0:
                return (x+i, y-j)
            if (x-i >= 0 and y+j < cols) and grid[x-i][y+j] == 0:
                return (x-i, y+j)

    print("NO FREE POINT")
    # Si aucun point libre n'a été trouvé
    return None


def compute_relative_distance_to_droite(x0, y0, x1, y1, x, y):

    ux = x1 - x0
    uy = y1 - y0

    vx = x - x0
    vy = y - y0

    # pseudo produit vectoriel
    cross_product = ux * vy - uy * vx
    if cross_product>0:
        cross_product_signe = -1
    else:
        cross_product_signe = 1
    
    # Cas particulier : droite verticale
    if x1 == x0:
        return cross_product_signe * abs(x - x0)
    # Cas particulier : droite horizontale        

    # distance entre le point (x, y) et la droite (x0, y0) (x1, y1)
    m = (y1 - y0) / (x1 - x0)
    x_proj = (m*m*x0 + m*(y - y0) + x) / (m*m + 1)
    y_proj = m * (x_proj - x0) + y0

    return cross_product_signe * math.sqrt((x_proj - x)**2 + (y_proj - y)**2)