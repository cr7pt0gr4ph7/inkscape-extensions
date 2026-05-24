#!/usr/bin/env python3

import inkex
from inkex import Group


class ReplaceGroupsWithChildren(inkex.EffectExtension):

    def effect(self):
        # Copy selection because we may modify the document tree
        selected = list(self.svg.selection.values())

        for node in selected:

            # Only process <g> elements
            if not isinstance(node, Group):
                continue

            parent = node.getparent()

            if parent is None:
                continue

            # Position of the group in the parent
            insert_index = parent.index(node)

            # Copy children list because we'll move them
            children = list(node)

            # Move children into parent at the group's position
            for child in children:
                node.remove(child)
                parent.insert(insert_index, child)
                insert_index += 1

            # Remove the empty group
            parent.remove(node)


if __name__ == "__main__":
    ReplaceGroupsWithChildren().run()
