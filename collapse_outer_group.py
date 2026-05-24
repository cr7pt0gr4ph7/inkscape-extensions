#!/usr/bin/env python3

import inkex
from inkex import Group


class CollapseOuterGroup(inkex.EffectExtension):

    def effect(self):
        # Copy selection because we modify the tree
        selected = list(self.svg.selection.values())

        for node in selected:

            # Only process groups
            if not isinstance(node, Group):
                continue

            # Outer group must contain exactly one child
            children = list(node)

            if len(children) != 1:
                continue

            inner = children[0]

            # Inner child must also be a group
            if not isinstance(inner, Group):
                continue

            parent = node.getparent()

            if parent is None:
                continue

            # Position of outer group in parent
            insert_index = parent.index(node)

            # Detach inner group from outer group
            node.remove(inner)

            # Insert inner group where outer group was
            parent.insert(insert_index, inner)

            # Remove outer group
            parent.remove(node)


if __name__ == "__main__":
    CollapseOuterGroup().run()
