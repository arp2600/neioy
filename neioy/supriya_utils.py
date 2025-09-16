import tempfile
from functools import partialmethod
from supriya import Group, Server
from supriya.ugens import compile_synthdefs


# Override default_group so the id matches supercolliders.
@property
def _server_default_group_override(self):
    """
    Get the server's default group.
    """
    return Group(context=self, id_=(2**26) * self._client_id + 1)


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


def apply_supriya_patches():
    """
    Apply overrides of supriya functions and methods.
    """
    Server.default_group = _server_default_group_override
    Server._resolve_node = _server_resolve_node_override
    Server.connect = partialmethod(_server_connect_wrapper, Server.connect)


def add_synthdef(server, synthdef):
    """
    Add a syndef to the server, with handling for synthdefs too large to be sent via osc.
    """
    # Try using server.add_synthdef. If the synthdef is too large, this will raise an
    # OSError with a message containing 'Message too long'.
    try:
        return server.add_synthdefs(synthdef)
    except OSError as e:
        # For any error other than 'Message too long' we just reraise the error.
        if 'Message too long' not in str(e):
            raise

    # The synthdef was too large to send using server.add_synthdef, so we save it to a
    # file and tell the server to load it.
    print(
        f"SynthDef {synthdef.name} too big for sending. Retrying via synthdef file"
    )
    data = compile_synthdefs(synthdef)
    with tempfile.NamedTemporaryFile(suffix='.scsyndef') as f:
        f.write(data)
        result = server.load_synthdefs(f.name)
        server.sync()
        return result
