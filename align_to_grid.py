#!/usr/bin/env python3

import inkex
from inkex import Transform


class AlignToGrid(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--align_vertical",
            type=inkex.Boolean,
            default=False,
        )

        pars.add_argument(
            "--vertical_distance",
            type=float,
            default=10.0,
        )

        pars.add_argument(
            "--align_horizontal",
            type=inkex.Boolean,
            default=False,
        )

        pars.add_argument(
            "--horizontal_distance",
            type=float,
            default=10.0,
        )

    def effect(self):
        if not self.svg.selection:
            inkex.errormsg("Please select at least one object.")
            return

        align_vertical = self.options.align_vertical
        align_horizontal = self.options.align_horizontal

        vertical_distance = self.options.vertical_distance
        horizontal_distance = self.options.horizontal_distance

        if not align_vertical and not align_horizontal:
            inkex.errormsg(
                "Enable at least one alignment direction."
            )
            return

        # Gather bounding boxes
        items = []

        for element in self.svg.selection.values():
            bbox = element.bounding_box()
            items.append((element, bbox))

        # Determine origin from topmost-leftmost selected element
        min_x = min(bbox.left for _, bbox in items)
        min_y = min(bbox.top for _, bbox in items)

        for element, bbox in items:
            dx = 0.0
            dy = 0.0

            if align_vertical and vertical_distance > 0:
                current_x = bbox.left

                relative_x = current_x - min_x

                snapped_x = (
                    round(relative_x / vertical_distance)
                    * vertical_distance
                    + min_x
                )

                dx = snapped_x - current_x

            if align_horizontal and horizontal_distance > 0:
                current_y = bbox.top

                relative_y = current_y - min_y

                snapped_y = (
                    round(relative_y / horizontal_distance)
                    * horizontal_distance
                    + min_y
                )

                dy = snapped_y - current_y

            transform = Transform.translate(dx, dy)
            element.transform = transform @ element.transform


if __name__ == "__main__":
    AlignToGrid().run()
