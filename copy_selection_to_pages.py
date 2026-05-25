#!/usr/bin/env python3

import copy
import re

import inkex


class CopySelectionToPages(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--target_pages",
            type=str,
            default="2",
            help='Target page list/ranges like "1,2-4,page5"',
        )

        pars.add_argument(
            "--exclude_source_page",
            type=inkex.Boolean,
            default=True,
            help="Do not copy back onto the source page",
        )

    def effect(self):
        pages = self.get_pages()

        if not pages:
            raise inkex.AbortExtension(
                "Document contains no pages."
            )

        if not self.svg.selection:
            raise inkex.AbortExtension(
                "No objects selected."
            )

        selected_elements = list(self.svg.selection.values())

        source_page = self.find_source_page_for_selection(
            selected_elements,
            pages,
        )

        if source_page is None:
            raise inkex.AbortExtension(
                "Could not determine the source page from the selection."
            )

        target_pages = self.parse_target_pages(
            self.options.target_pages,
            pages,
        )

        for target_page in target_pages:
            if (
                self.options.exclude_source_page
                and target_page is source_page
            ):
                continue

            self.copy_selection_between_pages(
                source_page,
                target_page,
                selected_elements,
            )

    def get_pages(self):
        return self.svg.namedview.get_pages()

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
                    page = self.find_page_by_index(
                        pages,
                        page_index,
                    )

                    if page is None:
                        raise inkex.AbortExtension(
                            f"Page index {page_index} does not exist."
                        )

                    if page.eid not in seen:
                        result.append(page)
                        seen.add(page.eid)

                continue

            page = self.resolve_page_reference(
                part,
                pages,
            )

            if page.eid not in seen:
                result.append(page)
                seen.add(page.eid)

        return result

    def resolve_page_reference(
        self,
        text,
        pages,
    ):
        text = text.strip()

        if re.fullmatch(r"\d+", text):
            page_index = int(text)

            page = self.find_page_by_index(
                pages,
                page_index,
            )

            if page is None:
                raise inkex.AbortExtension(
                    f"Page index {page_index} does not exist."
                )

            return page

        page = self.find_page_by_id(
            pages,
            text,
        )

        if page is None:
            raise inkex.AbortExtension(
                f'Page ID "{text}" does not exist.'
            )

        return page

    def find_page_by_index(
        self,
        pages,
        page_index,
    ):
        if (
            page_index >= 1
            and page_index <= len(pages)
        ):
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

    def find_source_page_for_selection(
        self,
        elements,
        pages,
    ):
        counts = {}

        for element in elements:
            bbox = element.bounding_box()

            if bbox is None:
                continue

            center_x = bbox.center_x
            center_y = bbox.center_y

            page = self.find_page_containing_point(
                center_x,
                center_y,
                pages,
            )

            if page is None:
                continue

            counts[page] = counts.get(page, 0) + 1

        if not counts:
            return None

        return max(
            counts.items(),
            key=lambda item: item[1],
        )[0]

    def find_page_containing_point(
        self,
        x,
        y,
        pages,
    ):
        for page in pages:
            if (
                x >= page.x
                and x <= page.x + page.width
                and y >= page.y
                and y <= page.y + page.height
            ):
                return page

        return None

    def copy_selection_between_pages(
        self,
        source_page,
        target_page,
        elements,
    ):
        delta_x = target_page.x - source_page.x
        delta_y = target_page.y - source_page.y

        layer = self.svg.get_current_layer()

        for element in elements:
            new_element = copy.deepcopy(element)

            new_element.set_id(None)

            transform = new_element.transform

            transform.add_translate(
                delta_x,
                delta_y,
            )

            new_element.transform = transform

            layer.append(new_element)


if __name__ == "__main__":
    CopySelectionToPages().run()
