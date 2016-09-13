import os

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


def create_enum(name, *members):
    members_dict = {}

    for member in members:
        members_dict[member] = member

    return type(name, (object,), members_dict)


def create_events(*events):
    return create_enum('E', *events)


def create_states(*states):
    return create_enum('S', *states)


class StateMachine(object):
    # Inspired by http://notahat.com/2014/11/07/state-machines-in-ruby.html

    def __init__(self, transitions, starting_state, starting_action):
        self._transitions = TransitionTable(transitions)

        self._state = starting_state

        # This part ensures we remember our starting state just in case
        # we call render() after one or more transitions have happened
        self._starting_state = starting_state

        self._starting_action = starting_action

    # ==========
    # PROPERTIES
    # ==========

    @property
    def state(self):
        return self._state

    # =======
    # METHODS
    # =======

    def send_event(self, event):
        self._state, action = self._transitions.call(self._state, event)
        return action

    def render(self, path, fmt='png'):
        formatter = GraphvizFormatter(self._transitions,
                                      starting_node=self._starting_state,
                                      starting_action=self._starting_action)
        formatter.save(os.path.splitext(path)[0], fmt)


class GraphvizLibraryMissing(Exception):
    pass


class GraphvizFormatter(object):
    # Based on http://matthiaseisen.com/pp/patterns/p0204/

    def __init__(self, transitions, starting_node, starting_action):
        if not HAS_GRAPHVIZ:
            raise GraphvizLibraryMissing("visualize method requires "
                                         "the graphviz library.")
        self._transitions = transitions
        self._starting_node = starting_node
        self._starting_action = starting_action

    def save(self, path, fmt):
        node_label = '%s\n---\nentry / %s'
        nodes = []
        edges = []

        values = (self._starting_node, self._starting_action.__name__)
        nodes.append((self._starting_node, {'label': node_label % values}))

        for source, target in self._transitions.items():
            node1 = str(source[0])
            edge = str(source[1])
            node2 = str(target[0])
            action = str(target[1].__name__)

            nodes.append((node1, {}))
            nodes.append((node2, {'label': node_label % (node2, action)}))
            edges.append(((node1, node2), {'label': '[%s]' % edge}))

        graph = graphviz.Digraph(format=fmt)
        graph = self.add_nodes(graph, nodes)
        graph = self.add_edges(graph, edges)
        graph.render(path)

    def add_nodes(self, graph, nodes):
        for node in nodes:
            graph.node(node[0], **node[1])
        return graph

    def add_edges(self, graph, edges):
        for edge in edges:
            graph.edge(*edge[0], **edge[1])
        return graph


class TransitionError(Exception):
    pass


class TransitionTable(object):

    def __init__(self, transitions):
        self._transitions = transitions

    def call(self, state, event):
        try:
            return self._transitions[(state, event)]
        except KeyError:
            raise TransitionError("No transition for state: %s, event: %s" %
                                  (state, event))

    def items(self):
        return self._transitions.items()
