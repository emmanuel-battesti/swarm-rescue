import heapq
import math

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

# Exemple d'utilisation :
grid = [
    [0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0],
    [0,0,1,1,1,0,0,0],
    [0,0,0,0,1,0,0,0],
    [0,0,0,0,0,0,0,0]
]

path = a_star_search(grid, (0,0), (4,7))
# Chemin initial (par exemple résultat d'A*) :

# 1. Simplification des segments colinéaires
path_simplified = simplify_collinear_points(path)

# 2.1. Simplification par ligne de vue
path_line_of_sight = simplify_by_line_of_sight(path_simplified, grid)

# 2.2. Simplification par Ramer-Douglas-Peucker avec epsilon = 0.5 par exemple
path_rdp = ramer_douglas_peucker(path_line_of_sight, 0.5)

print("Path initial:", path)
print("Path simplifié (colinéaire):", path_simplified)
print("Path simplifié (line of sight):", path_line_of_sight)
print("Path simplifié (RDP):", path_rdp)
