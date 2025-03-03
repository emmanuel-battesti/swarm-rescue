## Stratégie

### Exploration

La stratégie d'exploration actuelle (30/12) consiste à faire suivre les murs par la main gauche au drone. Cette stratégie d'exploration présente plusieurs défauts.

Nous avons pour objectif d'utiliser le reinforcement learning pour améliorer nos performances dans ce domaine.

### Retour au Rescue Center

La documentation de swarm-rescue précise :

> The Return Area is always near the Rescue Center and the drones always start the mission from this area.

C'est pourquoi notre stratégie de retour au rescue center lorsque le drone a attrapé un blessé consiste à faire suivre au drone un chemin menant de sa position à son point de spawn.