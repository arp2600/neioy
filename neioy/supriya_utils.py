import supriya

"""
Apply overrides of supriya functions and methods.
"""
def apply_supriya_patches():
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


    # Wrap connect so that server._node_children and server._node_parents can be
    # initialized using data from server.query_tree().
    inner_connect = supriya.Server.connect

    def connect_wrapper(self, ip_address, port):
        assert isinstance(port, int)
        inner_connect(self, ip_address=ip_address, port=port)

        # Populate server._node_children and server._node_parents using the data from server.query_tree().
        def add_nodes(node, parent):
            self._node_children[node.node_id] = []
            if parent:
                self._node_parents[node.node_id] = parent.node_id

            for child in node.children:
                add_nodes(child, node)

        root = self.query_tree()
        add_nodes(root, None)

        return self

    supriya.Server.connect = connect_wrapper
