#!/usr/bin/env python3

import inkex


class GradientKey:
    """Hashable representation of a gradient for deduplication."""

    def __init__(self, gradient, svg):
        self.tag = gradient.TAG
        self.attrib = self._filtered_attrib(gradient)
        self.stops = self._extract_stops(gradient, svg)

    def _filtered_attrib(self, grad):
        """Remove non-relevant attributes."""
        ignore = {
            "id",
            "{http://www.inkscape.org/namespaces/inkscape}label",
            # Ignore xlink:href for equivalence (handled via resolved gradient)
            # "{http://www.w3.org/1999/xlink}href",
        }

        return {
            k: v
            for k, v in grad.attrib.items()
            if k not in ignore
        }

    def _resolve_stops(self, grad, svg):
        """
        Resolve inherited gradients via xlink:href chain.
        Stops from base gradients are merged if current gradient has none.
        """
        all_stops = []

        visited = set()
        current = grad

        while current is not None:
            gid = current.get("id")
            if gid in visited:
                break
            visited.add(gid)

            stops = current.findall(".//{*}stop")
            if stops:
                # Only use stops from the closest defined gradient
                all_stops = stops
                break

            href = current.get("{http://www.w3.org/1999/xlink}href")
            if href and href.startswith("#"):
                current = svg.getElementById(href[1:])
            else:
                current = None

        return all_stops

    def _extract_stops(self, grad, svg):
        stops = self._resolve_stops(grad, svg)
        result = []

        for stop in stops:
            result.append(
                (
                    stop.get("offset", ""),
                    stop.get("stop-color", ""),
                    stop.get("stop-opacity", ""),
                )
            )

        return tuple(result)

    def __hash__(self):
        return hash((self.tag, tuple(sorted(self.attrib.items())), self.stops))

    def __eq__(self, other):
        return (
            self.tag == other.tag
            and self.attrib == other.attrib
            and self.stops == other.stops
        )


class MergeDuplicateGradients(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--dedup_linear",
            type=inkex.Boolean,
            default=True,
        )

        pars.add_argument(
            "--dedup_radial",
            type=inkex.Boolean,
            default=True,
        )

    def effect(self):
        defs = self.svg.defs
        if defs is None:
            return

        gradients = defs.findall(".//{*}linearGradient") + defs.findall(".//{*}radialGradient")

        if not gradients:
            return

         # Map: GradientKey -> canonical gradient element
        canonical: dict[GradientKey, inkex.LinearGradient | inkex.RadialGradient] = {}

        # Map: old gradient ID -> new gradient ID for duplicates
        duplicates: dict[str, str] = {}

        removed_linear = 0
        removed_radial = 0

        for g in gradients:
            tag = g.TAG

            if tag == "linearGradient" and not self.options.dedup_linear:
                continue
            if tag == "radialGradient" and not self.options.dedup_radial:
                continue

            key = GradientKey(g, self.svg)

            if key in canonical:
                duplicates[g.get("id")] = canonical[key].get("id")

                if tag == "linearGradient":
                    removed_linear += 1
                elif tag == "radialGradient":
                    removed_radial += 1
            else:
                canonical[key] = g

        if not duplicates:
            return

        self._rewrite_references(duplicates)
        self._remove_duplicates(defs, duplicates.keys())

        self.msg(
            f"Gradient dedup complete: "
            f"{removed_linear} linearGradient, {removed_radial} radialGradient removed."
        )

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

                    elif val == "#{old_id}":
                        elem.set(attr, f"#{new_id}")

    def _remove_duplicates(self, defs, dup_ids):
        for grad in list(defs):
            gid = grad.get("id")
            if gid in dup_ids:
                defs.remove(grad)


if __name__ == "__main__":
    MergeDuplicateGradients().run()
