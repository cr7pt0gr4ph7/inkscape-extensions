#!/usr/bin/env python3

import inkex


class AssignIncrementalIds(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--prefix", type=str, default="obj_")
        pars.add_argument("--suffix", type=str, default="")
        pars.add_argument("--start", type=int, default=1)
        pars.add_argument("--step", type=int, default=1)
        pars.add_argument("--reverse", type=inkex.Boolean, default=False)

    def effect(self):
        if not self.svg.selection:
            raise inkex.AbortExtension("No objects selected.")

        prefix = self.options.prefix
        suffix = self.options.suffix
        index = self.options.start
        step = self.options.step
        reverse = self.options.reverse

        # Collect all IDs already in use
        used_ids = set()

        for elem in self.svg.iter():
            elem_id = elem.get("id")
            if elem_id:
                used_ids.add(elem_id)

        # Selected element IDs
        selected_ids = set(self.svg.selection.ids)

        # Build document-order list of selected elements
        selected_in_order = []

        for elem in self.svg.iter():
            elem_id = elem.get("id")
            if elem_id in selected_ids:
                selected_in_order.append(elem)

        if reverse:
            selected_in_order.reverse()

        for elem in selected_in_order:

            # Remove current ID from used set temporarily
            old_id = elem.get("id")
            if old_id in used_ids:
                used_ids.remove(old_id)

            # Find next free ID
            while True:
                candidate = f"{prefix}{index}{suffix}"

                if candidate not in used_ids:
                    break

                index += step

            # Assign ID
            elem.set("id", candidate)
            used_ids.add(candidate)

            # Advance to next index
            index += step


if __name__ == "__main__":
    AssignIncrementalIds().run()
