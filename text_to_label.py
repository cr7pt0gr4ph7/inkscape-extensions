#!/usr/bin/env python3

import inkex
from inkex import TextElement


class TextToLabelExtension(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--keep_existing",
            type=inkex.Boolean,
            default=True,
            help="Keep existing labels"
        )

        pars.add_argument(
            "--recursive",
            type=inkex.Boolean,
            default=True,
            help="Recurse into child elements"
        )

    def process_element(self, element, keep_existing, recursive):

        # Process text elements
        if isinstance(element, TextElement):
            current_label = element.label

            # Skip if preserving existing labels
            if keep_existing and current_label:
                return

            text_content = element.get_text()

            if text_content:
                element.label = text_content.strip()

        # Recurse into children
        if recursive:
            for child in element:
                self.process_element(child, keep_existing, recursive)

    def effect(self):
        keep_existing = self.options.keep_existing
        recursive = self.options.recursive

        for element in self.svg.selection.values():
            self.process_element(element, keep_existing, recursive)


if __name__ == "__main__":
    TextToLabelExtension().run()
