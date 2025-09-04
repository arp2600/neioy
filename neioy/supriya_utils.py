import supriya

"""
Connect to an existing server.
This overrides some methods and properties of supriya.Server for compatibility with supercollider.
"""
def connect_to_server(ip_address, port):
    # Override default_group so the id matches supercolliders.
    @property
    def default_group(self):
        """
        Get the server's default group.
        """
        return supriya.Group(context=self, id_=(2 ** 26) * self._client_id + 1)

    supriya.Server.default_group = default_group


    # Override the _resolve_node method to use the default_group property
    def _resolve_node(self, node):
        if node is None:
            return self.default_group.id_
        return int(node)

    supriya.Server._resolve_node = _resolve_node

    assert isinstance(port, int)
    server = supriya.Server().connect(ip_address=ip_address, port=port)

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
