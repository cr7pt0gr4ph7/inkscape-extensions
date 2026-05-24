#!/usr/bin/env python3

import inkex
from inkex import Transform


class AlignToGrid(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--align_mode",
            default="bbox",
        )

        pars.add_argument(
            "--measurement_unit",
            default="document",
        )

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

    def convert_to_user_units(self, value, unit):
        if unit == "user":
            return value

        if unit == "document":
            document_unit = self.svg.unit
            return self.svg.unittouu(f"{value}{document_unit}")

        if unit == "display":
            display_unit = self.svg.document_unit
            return self.svg.unittouu(f"{value}{display_unit}")


        return self.svg.unittouu(f"{value}{unit}")

    def get_alignment_coordinates(self, element, align_mode):
        bbox = element.bounding_box()

        if align_mode == "xy":
            x_attr = element.get("x")
            y_attr = element.get("y")

            x = float(x_attr) if x_attr is not None else bbox.left
            y = float(y_attr) if y_attr is not None else bbox.top

            return x, y

        return bbox.left, bbox.top

    def move_element(self, element, dx, dy, align_mode):
        if align_mode == "xy":
            x_attr = element.get("x")
            y_attr = element.get("y")

            if x_attr is not None:
                element.set("x", str(float(x_attr) + dx))

            if y_attr is not None:
                element.set("y", str(float(y_attr) + dy))

            if x_attr is None and y_attr is None:
                transform = Transform.translate(dx, dy)
                element.transform = transform @ element.transform

            return

        transform = Transform.translate(dx, dy)
        element.transform = transform @ element.transform

    def effect(self):
        if not self.svg.selection:
            inkex.errormsg("Please select at least one object.")
            return

        align_vertical = self.options.align_vertical
        align_horizontal = self.options.align_horizontal

        if not align_vertical and not align_horizontal:
            inkex.errormsg(
                "Enable at least one alignment direction."
            )
            return

        align_mode = self.options.align_mode
        unit = self.options.measurement_unit

        vertical_distance = self.convert_to_user_units(
            self.options.vertical_distance,
            unit,
        )

        horizontal_distance = self.convert_to_user_units(
            self.options.horizontal_distance,
            unit,
        )

        items = []

        for element in self.svg.selection.values():
            x, y = self.get_alignment_coordinates(
                element,
                align_mode,
            )

            items.append((element, x, y))

        min_x = min(x for _, x, _ in items)
        min_y = min(y for _, _, y in items)

        for element, current_x, current_y in items:
            dx = 0.0
            dy = 0.0

            if align_vertical and vertical_distance > 0:
                relative_x = current_x - min_x

                snapped_x = (
                    round(relative_x / vertical_distance)
                    * vertical_distance
                    + min_x
                )

                dx = snapped_x - current_x

            if align_horizontal and horizontal_distance > 0:
                relative_y = current_y - min_y

                snapped_y = (
                    round(relative_y / horizontal_distance)
                    * horizontal_distance
                    + min_y
                )

                dy = snapped_y - current_y

            self.move_element(element, dx, dy, align_mode)


if __name__ == "__main__":
    AlignToGrid().run()
