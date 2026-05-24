#!/usr/bin/env python3
#
# clip_to_path_geometry.py
#
# Inkscape 1.4 extension:
# Replace each selected <path> that has a clip-path attribute
# with a new <path> that uses:
#
#   - the geometry ("d") from the referenced clipping path
#   - the styling/transform/id/etc. from the original path
#
# Tested against Inkscape 1.4 / inkex 1.4 API.
#

import copy
import re

import inkex
from inkex import PathElement


class UseGeometryFromClipPath(inkex.EffectExtension):

    CLIP_URL_RE = re.compile(r'url\(#([^)]+)\)')

    def effect(self):
        if not self.svg.selection:
            inkex.errormsg("Select one or more path elements.")
            return

        for element in list(self.svg.selection.values()):

            # Only process <path>
            if not isinstance(element, PathElement):
                continue

            clip_attr = element.get("clip-path")
            if not clip_attr:
                continue

            clip_id = self.extract_clip_id(clip_attr)
            if not clip_id:
                continue

            clip_path_elem = self.svg.getElementById(clip_id)
            if clip_path_elem is None:
                inkex.errormsg(f"Could not find clipPath '{clip_id}'")
                continue

            clip_source_path = self.find_first_path_in_clippath(clip_path_elem)
            if clip_source_path is None:
                inkex.errormsg(
                    f"clipPath '{clip_id}' does not contain a path element"
                )
                continue

            clip_d = clip_source_path.get("d")
            if not clip_d:
                continue

            # Create replacement path
            new_path = copy.deepcopy(element)

            # Replace geometry with clipping geometry
            new_path.set("d", clip_d)

            # Remove clipping from result
            if "clip-path" in new_path.attrib:
                del new_path.attrib["clip-path"]

            # Replace original element in parent
            parent = element.getparent()
            if parent is None:
                continue

            index = parent.index(element)
            parent.remove(element)
            parent.insert(index, new_path)

    def extract_clip_id(self, clip_attr):
        """
        Extract ID from:
            url(#clipPath123)
        """
        m = self.CLIP_URL_RE.match(clip_attr.strip())
        if not m:
            return None
        return m.group(1)

    def find_first_path_in_clippath(self, clip_path_elem):
        """
        Return the first descendant <path> inside the clipPath.
        """
        xpath = ".//svg:path"
        results = clip_path_elem.xpath(
            xpath,
            namespaces=inkex.NSS
        )

        if not results:
            return None

        return results[0]


if __name__ == "__main__":
    UseGeometryFromClipPath().run()
