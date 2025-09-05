from functools import partialmethod
from supriya import Group, Server


# Override default_group so the id matches supercolliders.
@property
def _server_default_group_override(self):
    """
    Get the server's default group.
    """
    return Group(context=self, id_=(2 ** 26) * self._client_id + 1)


# Override the _resolve_node method to use the default_group property
def _server_resolve_node_override(self, node):
    if node is None:
        return self.default_group.id_
    return int(node)


def _server_connect_wrapper(server, connect_func, ip_address, port):
    assert isinstance(port, int)
    connect_func(server, ip_address=ip_address, port=port)

    # Populate server._node_children and server._node_parents using the data from server.query_tree().
    def add_nodes(node, parent):
        server._node_children[node.node_id] = []
        if parent:
            server._node_parents[node.node_id] = parent.node_id

        for child in node.children:
            add_nodes(child, node)

    root = server.query_tree()
    add_nodes(root, None)

    return server


"""
Apply overrides of supriya functions and methods.
"""
def apply_supriya_patches():
    Server.default_group = _server_default_group_override
    Server._resolve_node = _server_resolve_node_override
    Server.connect = partialmethod(_server_connect_wrapper, Server.connect)
