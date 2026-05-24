#!/usr/bin/env python3

import inkex


class PromoteChildTransform(inkex.EffectExtension):

    def effect(self):
        if not self.svg.selection:
            raise inkex.AbortExtension("Please select one or more groups.")

        for element in self.svg.selection.values():

            if not isinstance(element, inkex.Group):
                inkex.errormsg(
                    f"Skipping '{element.get_id()}': selection is not a group."
                )
                continue

            children = [
                child for child in element
                if isinstance(child, inkex.BaseElement)
            ]

            if len(children) != 1:
                inkex.errormsg(
                    f"Skipping group '{element.get_id()}': "
                    f"group must contain exactly one child element."
                )
                continue

            child = children[0]

            existing_transform = child.get("transform", "").strip()

            x = child.get("x")
            y = child.get("y")

            translate_parts = []

            if x is not None:
                translate_parts.append(x)

            if y is not None:
                translate_parts.append(y)
            elif x is not None:
                translate_parts.append("0")

            translate_transform = None

            if translate_parts:
                translate_transform = (
                    f"translate({', '.join(translate_parts)})"
                )

            final_transform_parts = []

            if existing_transform:
                final_transform_parts.append(existing_transform)

            if translate_transform:
                final_transform_parts.append(translate_transform)

            final_transform = " ".join(final_transform_parts).strip()

            if not final_transform:
                inkex.errormsg(
                    f"Skipping group '{element.get_id()}': "
                    f"child has no transform/x/y attributes."
                )
                continue

            # Move resulting transform to parent group
            element.set("transform", final_transform)

            # Remove attributes from child
            child.attrib.pop("transform", None)
            child.attrib.pop("x", None)
            child.attrib.pop("y", None)


if __name__ == "__main__":
    PromoteChildTransform().run()
