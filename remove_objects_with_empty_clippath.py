#!/usr/bin/env python3

import re
import inkex

SVG_NS = "http://www.w3.org/2000/svg"


class RemoveObjectsWithEmptyClipPath(inkex.EffectExtension):

    def effect(self):
        svg = self.document.getroot()

        # Find all clipPath elements by id
        clip_paths = {}
        for cp in svg.xpath('//svg:clipPath', namespaces=inkex.NSS):
            cp_id = cp.get('id')
            if cp_id:
                clip_paths[cp_id] = cp

        elements_to_remove = []

        # Determine search roots:
        # - selection if present
        # - otherwise whole document
        if self.svg.selection:
            search_roots = list(self.svg.selection.values())
        else:
            search_roots = [svg]

        # Collect candidate elements
        candidate_elements = []

        for root in search_roots:

            # Include root itself if it has clip-path
            if root.get('clip-path'):
                candidate_elements.append(root)

            # Include descendants with clip-path
            candidate_elements.extend(
                root.xpath('.//*[@clip-path]', namespaces=inkex.NSS)
            )

        # Process candidates
        for elem in candidate_elements:
            clip_attr = elem.get('clip-path')

            if not clip_attr:
                continue

            clip_id = self.extract_clip_id(clip_attr)

            if not clip_id:
                continue

            clip_path = clip_paths.get(clip_id)

            if clip_path is None:
                continue

            if self.clip_path_is_empty(clip_path):
                elements_to_remove.append(elem)

        # Remove duplicates
        elements_to_remove = list(set(elements_to_remove))

        # Remove marked elements
        removed_count = 0

        for elem in elements_to_remove:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)
                removed_count += 1

        inkex.utils.debug(
            f"Removed {removed_count} element(s) using empty clip paths."
        )

    def extract_clip_id(self, clip_attr):
        """
        Extract ID from:
            url(#clipPath123)
        """
        m = re.match(r'url\(#([^)]+)\)', clip_attr)
        if m:
            return m.group(1)
        return None

    def clip_path_is_empty(self, clip_path):
        """
        Determine whether a clipPath contains any drawable geometry.

        We treat it as empty if:
        - it has no children
        - OR all children are geometry-less / empty paths
        """

        children = list(clip_path)

        if not children:
            return True

        for child in children:
            if self.element_has_geometry(child):
                return False

        return True

    def element_has_geometry(self, elem):
        # Extract local tag name without namespace
        tag = elem.tag.split('}', 1)[-1]

        # Path
        if tag == 'path':
            d = elem.get('d')
            return bool(d and d.strip())

        # Rect
        if tag == 'rect':
            w = self.safe_float(elem.get('width'))
            h = self.safe_float(elem.get('height'))
            return w > 0 and h > 0

        # Circle
        if tag == 'circle':
            r = self.safe_float(elem.get('r'))
            return r > 0

        # Ellipse
        if tag == 'ellipse':
            rx = self.safe_float(elem.get('rx'))
            ry = self.safe_float(elem.get('ry'))
            return rx > 0 and ry > 0

        # Line
        if tag == 'line':
            x1 = self.safe_float(elem.get('x1'))
            y1 = self.safe_float(elem.get('y1'))
            x2 = self.safe_float(elem.get('x2'))
            y2 = self.safe_float(elem.get('y2'))
            return (x1 != x2) or (y1 != y2)

        # Polyline / Polygon
        if tag in ('polyline', 'polygon'):
            pts = elem.get('points')
            return bool(pts and pts.strip())

        # Use
        if tag == 'use':
            href = (
                elem.get('{http://www.w3.org/1999/xlink}href')
                or elem.get('href')
            )
            return bool(href)

        # Groups: recurse
        if tag == 'g':
            for child in elem:
                if self.element_has_geometry(child):
                    return True
            return False

        return False

    def safe_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


if __name__ == '__main__':
    RemoveObjectsWithEmptyClipPath().run()
