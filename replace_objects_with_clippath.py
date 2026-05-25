#!/usr/bin/env python3
#
# clip_path_tools.py
#
# Inkscape 1.4 extension
#
# Modes:
#
# 1. geometry_from_clip
#    Replace selected path geometry with the first path inside
#    the referenced clipPath while preserving styling/transforms.
#
# 2. replace_with_clip_contents
#    Replace the selected object entirely with copies of the
#    clipPath children.
#

import copy
import re

import inkex
from inkex import PathElement

CLIP_URL_RE = re.compile(r"url\(#([^)]+)\)")

MODE_GEOMETRY = "geometry_from_clip"
MODE_REPLACE = "replace_with_clip_contents"

class ClipPathTools(inkex.EffectExtension):
    def add_arguments(self, pars):

        pars.add_argument(
            "--mode",
            default=self.MODE_GEOMETRY,
            help="Operation mode",
        )

        pars.add_argument(
            "--only_paths",
            type=inkex.Boolean,
            default=True,
            help="Only modify path elements",
        )

        pars.add_argument(
            "--remove_clip",
            type=inkex.Boolean,
            default=True,
            help="Remove clip-path attribute after operation",
        )

        pars.add_argument(
            "--preserve_transform",
            type=inkex.Boolean,
            default=True,
            help="Preserve original transform when replacing with clip contents",
        )

    def effect(self):

        if not self.svg.selection:
            inkex.errormsg("Select one or more clipped objects.")
            return

        for element in list(self.svg.selection.values()):

            # Restrict to paths if requested
            if self.options.only_paths and not isinstance(element, PathElement):
                continue

            clip_attr = element.get("clip-path")
            if not clip_attr:
                continue

            clip_id = self.extract_clip_id(clip_attr)

            if not clip_id:
                inkex.errormsg(
                    f"Could not parse clip-path on element '{element.get_id()}'."
                )
                continue

            clip_path_elem = self.svg.getElementById(clip_id)

            if clip_path_elem is None:
                inkex.errormsg(
                    f"Could not find clip-path '{clip_id}' "
                    f"referenced by element '{element.get_id()}'."
                )
                continue

            if self.options.mode == self.MODE_GEOMETRY:
                self.replace_geometry_from_clip(element, clip_path_elem)

            elif self.options.mode == self.MODE_REPLACE:
                self.replace_with_clip_contents(element, clip_path_elem)

            else:
                inkex.errormsg(f"Unknown mode: {self.options.mode}")

    # ------------------------------------------------------------
    # MODE 1
    # ------------------------------------------------------------

    def replace_geometry_from_clip(self, element, clip_path_elem):

        clip_source_path = self.find_first_path_in_clippath(
            clip_path_elem
        )

        if clip_source_path is None:
            inkex.errormsg(
                f"clipPath '{clip_path_elem.get_id()}' "
                f"does not contain a path element."
            )
            return

        clip_d = clip_source_path.get("d")

        if not clip_d:
            inkex.errormsg(
                f"Path inside clipPath '{clip_path_elem.get_id()}' "
                f"has no geometry."
            )
            return

        new_path = copy.deepcopy(element)

        # Replace geometry
        new_path.set("d", clip_d)

        # Remove clipping if requested
        if self.options.remove_clip:
            self.remove_clip_path_attr(new_path)

        parent = element.getparent()

        if parent is None:
            return

        index = parent.index(element)

        parent.remove(element)
        parent.insert(index, new_path)

    # ------------------------------------------------------------
    # MODE 2
    # ------------------------------------------------------------

    def replace_with_clip_contents(self, element, clip_path_elem):

        parent = element.getparent()

        if parent is None:
            return

        insert_index = parent.index(element)

        inserted = []

        for child in clip_path_elem:

            new_child = copy.deepcopy(child)

            if self.options.preserve_transform:

                original_transform = element.get("transform")
                child_transform = new_child.get("transform")

                if original_transform and child_transform:
                    new_child.set(
                        "transform",
                        f"{original_transform} {child_transform}"
                    )

                elif original_transform:
                    new_child.set(
                        "transform",
                        original_transform
                    )

            if self.options.remove_clip:
                self.remove_clip_path_attr(new_child)

            inserted.append(new_child)

        parent.remove(element)

        for offset, node in enumerate(inserted):
            parent.insert(insert_index + offset, node)

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    def extract_clip_id(self, clip_attr):
        m = CLIP_URL_RE.match(clip_attr.strip())
        if not m:
            return None

        return m.group(1)

    def find_first_path_in_clippath(self, clip_path_elem):
        xpath = ".//svg:path"

        results = clip_path_elem.xpath(
            xpath,
            namespaces=inkex.NSS
        )

        if not results:
            return None

        return results[0]

    def remove_clip_path_attr(self, node):
        if "clip-path" in node.attrib:
            del node.attrib["clip-path"]


if __name__ == "__main__":
    ClipPathTools().run()
