#!/usr/bin/env python3
#
# replace_with_clippath.py
#
# Inkscape 1.4 extension
#
# Replaces each selected element that has a clip-path attribute
# with a copy of the referenced clipping path contents.
#
# The selected object itself is removed.
#
# Example:
#   <rect clip-path="url(#clip1)"/>
#
# becomes:
#   <path d="...from clip1..."/>
#

import copy
import re

import inkex


class ReplaceWithClipPath(inkex.EffectExtension):

    CLIP_RE = re.compile(r"url\(#([^)]+)\)")

    def effect(self):

        if not self.svg.selection:
            inkex.errormsg("Select one or more clipped objects.")
            return

        for elem in list(self.svg.selection.values()):

            clip_attr = elem.get("clip-path")
            if not clip_attr:
                continue

            clip_id = self.extract_clip_id(clip_attr)
            if not clip_id:
                inkex.errormsg(
                    f"Could not parse clip-path on element '{elem.get_id()}'."
                )
                continue

            clip_path = self.svg.getElementById(clip_id)
            if clip_path is None:
                inkex.errormsg(
                    f"Referenced clipPath '{clip_id}' not found."
                )
                continue

            parent = elem.getparent()
            if parent is None:
                continue

            insert_index = parent.index(elem)

            # Insert copies of all children from the clipPath
            inserted = []

            for child in clip_path:
                new_child = copy.deepcopy(child)

                # Preserve transform from original element
                original_transform = elem.get("transform")
                child_transform = new_child.get("transform")

                if original_transform and child_transform:
                    new_child.set(
                        "transform",
                        f"{original_transform} {child_transform}"
                    )
                elif original_transform:
                    new_child.set("transform", original_transform)

                inserted.append(new_child)

            # Replace original element
            parent.remove(elem)

            for offset, node in enumerate(inserted):
                parent.insert(insert_index + offset, node)

    def extract_clip_id(self, clip_attr):
        m = self.CLIP_RE.match(clip_attr.strip())
        if not m:
            return None
        return m.group(1)


if __name__ == "__main__":
    ReplaceWithClipPath().run()
