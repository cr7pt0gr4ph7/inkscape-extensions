#!/usr/bin/env python3

import re
import inkex
from inkex import Guide, Vector2d
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
            type=str,
            default="1",
            help="Source page index or ID",
        )

        pars.add_argument(
            "--target_pages",
            type=str,
            default="2",
            help='Target page list/ranges like "1,2-4,page5"',
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
            raise inkex.AbortExtension(
                "Document contains no pages."
            )

        source_page = self.resolve_page_reference(
            self.options.source_page,
            pages,
        )

        target_pages = self.parse_target_pages(
            self.options.target_pages,
            pages,
        )

        source_guides = self.find_vertical_guides_for_page(
            source_page,
            pages,
        )

        for target_page in target_pages:
            if target_page is source_page:
                continue

            if self.options.remove_existing:
                self.remove_vertical_guides_from_page(target_page, pages)

            self.copy_guides_between_pages(
                source_page,
                target_page,
                source_guides,
            )

    def get_pages(self):
        return self.svg.namedview.get_pages()

    def resolve_page_reference(
        self,
        text,
        pages,
    ):
        text = text.strip()

        if re.fullmatch(r"\d+", text):
            page_index = int(text)

            page = self.find_page_by_index(pages, page_index)

            if page is None:
                raise inkex.AbortExtension(
                    f"Page index {page_index} does not exist."
                )

            return page

        page = self.find_page_by_id(pages, text)

        if page is None:
            raise inkex.AbortExtension(
                f'Page ID "{text}" does not exist.'
            )

        return page

    def parse_target_pages(
        self,
        text,
        pages,
    ):
        result = []
        seen = set()

        text = text.strip()

        if not text:
            return []

        for part in text.split(","):
            part = part.strip()

            if not part:
                continue

            range_match = re.fullmatch(
                r"(\d+)\s*-\s*(\d+)",
                part,
            )

            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))

                if start > end:
                    start, end = end, start

                for page_index in range(start, end + 1):
                    page = self.find_page_by_index(pages, page_index)

                    if page is None:
                        raise inkex.AbortExtension(
                            f"Page index {page_index} does not exist."
                        )

                    if page.eid not in seen:
                        result.append(page)
                        seen.add(page.eid)

                continue

            page = self.resolve_page_reference(part, pages)

            if page.eid not in seen:
                result.append(page)
                seen.add(page.eid)

        return result

    def find_page_by_index(
        self,
        pages,
        page_index,
    ):
        if page_index >= 1 and page_index <= len(pages):
            return pages[page_index - 1]

        return None

    def find_page_by_id(
        self,
        pages,
        page_id,
    ):
        for page in pages:
            if page.eid == page_id:
                return page

        return None

    def find_vertical_guides_for_page(
        self,
        page,
        all_pages,
    ):
        namedview = self.svg.namedview

        result = []

        for guide in namedview.get_guides():
            if not guide.is_vertical:
                continue

            guide_x = guide.position.x

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

        for guide in namedview.get_guides():
            if not guide.is_vertical:
                continue

            guide_x = guide.position.x

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

    def find_closest_page_for_x(
        self,
        x,
        pages,
    ):
        best_page = None
        best_distance = None

        for page in pages:
            center_x = (
                page.x
                + page.width / 2.0
            )

            distance = abs(x - center_x)

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance
                best_page = page

        return best_page

    def copy_guides_between_pages(
        self,
        source_page,
        target_page,
        guides,
    ):
        source_x = source_page.x
        target_x = target_page.x

        delta_x = target_x - source_x

        namedview = self.svg.namedview

        for guide in guides:
            pos = guide.position

            x = pos.x
            y = pos.y

            new_x = x + delta_x

            new_guide = guide.copy()
            new_guide.set_id(None)
            namedview.append(new_guide)
            new_guide.set_position(new_x, y)


if __name__ == "__main__":
    CopyVerticalGuidesBetweenPages().run()
