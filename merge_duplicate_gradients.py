#!/usr/bin/env python3

import inkex
from copy import deepcopy


class GradientKey:
    """Hashable representation of a gradient for deduplication."""

    def __init__(self, gradient):
        self.tag = inkex.utils.QN(gradient.tag).localname
        self.attrib = self._filtered_attrib(gradient)
        self.stops = self._extract_stops(gradient)

    def _filtered_attrib(self, grad):
        """Remove non-relevant attributes."""
        ignore = {"id", "{http://www.inkscape.org/namespaces/inkscape}label"}
        return {
            k: v
            for k, v in grad.attrib.items()
            if k not in ignore
        }

    def _extract_stops(self, grad):
        stops = []
        for stop in grad.findall(".//{*}stop"):
            stops.append(
                (
                    stop.get("offset", ""),
                    stop.get("stop-color", ""),
                    stop.get("stop-opacity", ""),
                )
            )
        return tuple(stops)

    def __hash__(self):
        return hash((self.tag, tuple(sorted(self.attrib.items())), self.stops))

    def __eq__(self, other):
        return (
            self.tag == other.tag
            and self.attrib == other.attrib
            and self.stops == other.stops
        )


class MergeDuplicateGradients(inkex.EffectExtension):

    def effect(self):
        defs = self.svg.defs
        if defs is None:
            return

        gradients = defs.findall(".//{*}linearGradient") + defs.findall(".//{*}radialGradient")

        if not gradients:
            return

        # Map: GradientKey -> canonical gradient element
        canonical = {}
        duplicates = {}

        for g in gradients:
            key = GradientKey(g)

            if key in canonical:
                duplicates[g.get("id")] = canonical[key].get("id")
            else:
                canonical[key] = g

        if not duplicates:
            return

        self._rewrite_references(duplicates)
        self._remove_duplicates(defs, duplicates.keys())

    def _rewrite_references(self, duplicates):
        """Replace url(#old) with url(#new) in style and attributes."""
        for elem in self.svg.descendants():
            for attr in elem.attrib:
                val = elem.get(attr)
                if not val:
                    continue

                for old_id, new_id in duplicates.items():
                    if f"url(#{old_id})" in val:
                        elem.set(attr, val.replace(f"url(#{old_id})", f"url(#{new_id})"))

    def _remove_duplicates(self, defs, dup_ids):
        for grad in list(defs):
            gid = grad.get("id")
            if gid in dup_ids:
                defs.remove(grad)


if __name__ == "__main__":
    MergeDuplicateGradients().run()
