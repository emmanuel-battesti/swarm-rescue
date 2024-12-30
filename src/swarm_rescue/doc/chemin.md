## Chemin

### Carte

Se référer à la documentation sur les cartes pour plus d'informations.

#### Obtention d'une structure de graphe

Une carte binaire (0 : case libre , 1 : case obstacle) est créée grâce à la grille d'occupation maintenue par le drone en utilisant la méthode to_binary_map.

L'ensemble des 1 de la carte est ensuite dilatée. Cela a pour but d'empêcher le drone de passer trop près des murs.

#### Obtention d'un premier chemin

On cherche un chemin dans cette carte entre les points de départ et d'arrivée grâce à l'algortihme A* ayant pour heuristique une ligne (calculée par l'algorithme de Bresenham) entre les deux points.

#### Simplification du chemin

Ce chemin étant a priori constitué de nombreux points, on le simplifie en lui ôtant tous les points qui ne modifient pas l'allure de la courbe qu'il forme (si p1,p2,p3 forme un sous-chemin et sont 3 points alignés, on retire p2).

On simplifie encore ce chemin par ligne de vue pour réduire le nombre de points superflus.

On simplifie finalement le chemin par la méthode de Ramer-Douglas-Peucker.

### Asservissement du drone le long du chemin

La méthode is_near_waypoint est utilisée pour la validation des points de passage.

Pour se rendre à un point de passage, le drone est asservi en position selon le vecteur V menant du point de passage précédent au point de passage courant.

L'asservissement est :

1) angulaire (angle entre la direction du drone et la droite passant par le drone et le point de passage)

2) latéral (distance entre le drone et la droite portée par le vecteur V)

3) en distance (entre le drone et le prochain point de passage)