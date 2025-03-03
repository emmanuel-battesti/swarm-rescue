import graphviz
import inspect
import ast
import os

# COPY THE CODE OF THE STATE MACHINE FUNCTION HERE
def state_update(self, found_wall, found_wounded, found_rescue_center):
        self.previous_state = self.state
        
        conditions = {
            "found_wall": found_wall,
            "lost_wall": not found_wall,
            "found_wounded": found_wounded,
            "holding_wounded": bool(self.base.grasper.grasped_entities),
            "lost_wounded": not found_wounded and not self.base.grasper.grasped_entities,
            "found_rescue_center": found_rescue_center,
            "lost_rescue_center": not self.base.grasper.grasped_entities,
            "no_frontiers_left": len(self.grid.frontiers) == 0,
            "waiting_time_over": self.step_waiting_count >= self.waiting_params.step_waiting
        }

        STATE_TRANSITIONS = {
            self.State.WAITING: {
                "found_wounded": self.State.GRASPING_WOUNDED,
                "waiting_time_over": self.State.EXPLORING_FRONTIERS
            },
            self.State.GRASPING_WOUNDED: {
                "lost_wounded": self.State.WAITING,
                "holding_wounded": self.State.SEARCHING_RESCUE_CENTER
            },
            self.State.SEARCHING_RESCUE_CENTER: {
                "lost_rescue_center": self.State.WAITING,
                "found_rescue_center": self.State.GOING_RESCUE_CENTER
            },
            self.State.GOING_RESCUE_CENTER: {
                "lost_rescue_center": self.State.WAITING
            },
            self.State.EXPLORING_FRONTIERS: {
                "found_wounded": self.State.GRASPING_WOUNDED,
                "no_frontiers_left": self.State.FOLLOWING_WALL
            },
            self.State.SEARCHING_WALL: {
                "found_wounded": self.State.GRASPING_WOUNDED,
                "found_wall": self.State.FOLLOWING_WALL
            },
            self.State.FOLLOWING_WALL: {
                "found_wounded": self.State.GRASPING_WOUNDED,
                "lost_wall": self.State.SEARCHING_WALL
            }
        }
#####---------------------------------------------------------------------#####

def extract_transitions(func):
    source = inspect.getsource(func)  # Get function source code
    tree = ast.parse(source)  # Parse with AST
    
    transitions = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):  # Look for assignments
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "STATE_TRANSITIONS":
                    transitions = parse_state_transitions(node.value)
                    return transitions

    return {}

# Convert AST dictionary to string format (handling unknown attributes)
def parse_state_transitions(node):
    if not isinstance(node, ast.Dict):
        return {}

    transitions = {}
    
    for key, value in zip(node.keys, node.values):
        state = parse_state_key(key)  # Convert self.State.XYZ -> "XYZ"
        transitions[state] = {}

        if isinstance(value, ast.Dict):  # Nested dictionary
            for cond_key, next_state in zip(value.keys, value.values):
                condition = cond_key.value if isinstance(cond_key, ast.Constant) else "UNKNOWN"
                next_state_str = parse_state_key(next_state)
                transitions[state][condition] = next_state_str

    return transitions

# Extracts "XYZ" from self.State.XYZ
def parse_state_key(node):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
        return node.attr  # Extracts "XYZ" from self.State.XYZ
    return "UNKNOWN"

# Generate FSM Graph
def create_fsm_graph(STATE_TRANSITIONS):
    fsm = graphviz.Digraph(format="png")
    fsm.attr(rankdir="LR", size="10")

    for state, transitions in STATE_TRANSITIONS.items():
        fsm.node(state, shape="circle")  # Add state nodes

        for condition, next_state in transitions.items():
            fsm.edge(state, next_state, label=condition)  # Add transition edges

    return fsm

# Extract, parse, and visualize the FSM
raw_transitions = extract_transitions(state_update)
fsm_graph = create_fsm_graph(raw_transitions)

# Render and save the FSM graph
current_directory = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
output_path = os.path.join(current_directory, "finite_state_machine")
fsm_graph.attr(rankdir="LR", nodesep="0.5", ranksep="0.75")
fsm_graph.render(output_path, format="svg", view=True, cleanup=True)