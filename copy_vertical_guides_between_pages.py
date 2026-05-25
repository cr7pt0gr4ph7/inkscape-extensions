#!/usr/bin/env python3

import re
import inkex
from lxml import etree


SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

NSMAP = {
    "svg": SVG_NS,
    "inkscape": INKSCAPE_NS,
}


class CopyVerticalGuidesBetweenPages(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--source_page",
            type=int,
            default=1,
            help="1-based index of the source page",
        )

        pars.add_argument(
            "--target_pages",
            type=str,
            default="2",
            help='Target page list/ranges like "1,2-4,7"',
        )

        pars.add_argument(
            "--remove_existing",
            type=inkex.Boolean,
            default=False,
            help="Remove existing vertical guides from target pages",
        )

    def effect(self):
        pages = self.get_pages()

        if not pages:
            raise inkex.AbortExtension("Document contains no pages.")

        source_index = self.options.source_page - 1

        if source_index < 0 or source_index >= len(pages):
            raise inkex.AbortExtension(
                f"Source page {self.options.source_page} does not exist."
            )

        target_indices = self.parse_page_range(
            self.options.target_pages,
            len(pages),
        )

        source_page = pages[source_index]

        source_guides = self.find_vertical_guides_for_page(
            source_page,
            pages,
        )

        for target_index in target_indices:
            if target_index == source_index:
                continue

            target_page = pages[target_index]

            if self.options.remove_existing:
                self.remove_vertical_guides_from_page(
                    target_page,
                    pages,
                )

            self.copy_guides_between_pages(
                source_page,
                target_page,
                source_guides,
            )

    def get_pages(self):
        pages = self.document.xpath(
            "//inkscape:page",
            namespaces=NSMAP,
        )

        result = []

        for page in pages:
            x = float(page.get("x", "0"))
            y = float(page.get("y", "0"))
            width = float(page.get("width"))
            height = float(page.get("height"))

            result.append({
                "element": page,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            })

        return result

    def parse_page_range(self, text, max_pages):
        result = set()

        text = text.strip()

        if not text:
            return []

        for part in text.split(","):
            part = part.strip()

            if not part:
                continue

            if "-" in part:
                m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)

                if not m:
                    raise inkex.AbortExtension(
                        f'Invalid range "{part}".'
                    )

                start = int(m.group(1))
                end = int(m.group(2))

                if start > end:
                    start, end = end, start

                for i in range(start, end + 1):
                    self.validate_page_number(i, max_pages)
                    result.add(i - 1)

            else:
                page_num = int(part)
                self.validate_page_number(page_num, max_pages)
                result.add(page_num - 1)

        return sorted(result)

    def validate_page_number(self, page_num, max_pages):
        if page_num < 1 or page_num > max_pages:
            raise inkex.AbortExtension(
                f"Page {page_num} is outside the valid range 1-{max_pages}."
            )

    def find_vertical_guides_for_page(self, page, all_pages):
        namedview = self.svg.namedview

        result = []

        for guide in namedview.guides:
            orientation = guide.get("orientation", "")

            if not self.is_vertical_guide(orientation):
                continue

            guide_x = self.get_guide_x(guide)

            closest_page = self.find_closest_page_for_x(
                guide_x,
                all_pages,
            )

            if closest_page is page:
                result.append(guide)

        return result

    def remove_vertical_guides_from_page(
        self,
        page,
        all_pages,
    ):
        namedview = self.svg.namedview

        guides_to_remove = []

        for guide in namedview.guides:
            orientation = guide.get("orientation", "")

            if not self.is_vertical_guide(orientation):
                continue

            guide_x = self.get_guide_x(guide)

            closest_page = self.find_closest_page_for_x(
                guide_x,
                all_pages,
            )

            if closest_page is page:
                guides_to_remove.append(guide)

        for guide in guides_to_remove:
            parent = guide.getparent()

            if parent is not None:
                parent.remove(guide)

    def is_vertical_guide(self, orientation):
        parts = orientation.split(",")

        if len(parts) != 2:
            return False

        try:
            ox = float(parts[0])
            oy = float(parts[1])
        except ValueError:
            return False

        return abs(ox - 1.0) < 1e-6 and abs(oy) < 1e-6

    def get_guide_x(self, guide):
        pos = guide.get("position", "0,0").split(",")

        return float(pos[0])

    def find_closest_page_for_x(self, x, pages):
        best_page = None
        best_distance = None

        for page in pages:
            center_x = page["x"] + page["width"] / 2.0

            distance = abs(x - center_x)

            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_page = page

        return best_page

    def copy_guides_between_pages(
        self,
        source_page,
        target_page,
        guides,
    ):
        source_x = source_page["x"]
        target_x = target_page["x"]

        delta_x = target_x - source_x

        namedview = self.svg.namedview

        for guide in guides:
            pos = guide.get("position", "0,0").split(",")

            x = float(pos[0])
            y = float(pos[1])

            new_x = x + delta_x

            new_guide = etree.Element(
                inkex.addNS("guide", "sodipodi")
            )

            for key, value in guide.attrib.items():
                new_guide.set(key, value)

            new_guide.set(
                "position",
                f"{new_x},{y}"
            )

            namedview.append(new_guide)


if __name__ == "__main__":
    CopyVerticalGuidesBetweenPages().run()
