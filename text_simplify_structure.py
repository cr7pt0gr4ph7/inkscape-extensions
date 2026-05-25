#!/usr/bin/env python3

import copy
import inkex

from inkex import Style


SVG_TEXT_TAG = inkex.addNS("text", "svg")
SVG_TSPAN_TAG = inkex.addNS("tspan", "svg")


class TextSimplifyStructure(inkex.EffectExtension):

    def effect(self):
        for element in self.svg.selection.values():
            if element.tag == SVG_TEXT_TAG:
                self.simplify_text_tree(element)

    # -------------------------------------------------------------------------
    # Main simplification pipeline
    # -------------------------------------------------------------------------

    def simplify_text_tree(self, text_element: inkex.TextElement):
        changed = True

        # Run repeatedly because flattening may enable additional simplifications
        while changed:
            changed = False

            if self.push_common_styles_up(text_element):
                changed = True

            if self.remove_duplicate_styles(text_element):
                changed = True

            if self.flatten_nested_tspans(text_element):
                changed = True

    # -------------------------------------------------------------------------
    # Style helpers
    # -------------------------------------------------------------------------

    def parse_style(self, element: inkex.BaseElement):
        style_attr = element.get("style")
        if style_attr and style_attr.strip() != "":
            return Style(style_attr)

        return None

    def write_style(self, element: inkex.BaseElement, style_dict: dict):
        if style_dict:
            sorted_style = Style(sorted(style_dict.items(), key=lambda item: item[0]))
            element.set("style", sorted_style.to_str())
        else:
            element.set("style", None)

    def get_direct_tspan_children(self, parent):
        return [
            child for child in parent
            if child.tag == SVG_TSPAN_TAG
        ]

    # -------------------------------------------------------------------------
    # Move common styles from children to parent
    # -------------------------------------------------------------------------

    def push_common_styles_up(self, parent):
        children = self.get_direct_tspan_children(parent)

        if not children:
            return False

        child_styles = []

        for child in children:
            # Recurse into nested tspans first to ensure we are comparing
            # the final styles after pushing up from deeper levels
            self.push_common_styles_up(child)

            style = self.parse_style(child)

            # Ignore empty styles
            if not style:
                return False

            child_styles.append(style)

        common_style = dict(child_styles[0])

        for style in child_styles[1:]:
            remove_keys = []

            for key, value in common_styles.items():
                if style.get(key) != value:
                    remove_keys.append(key)

            for key in remove_keys:
                del common_styles[key]

        if not common_styles:
            return False

        parent_style = self.parse_style(parent)

        changed = False

        for key, value in common_style.items():
            if parent_style.get(key) != value:
                parent_style[key] = value
                changed = True

        if changed:
            self.write_style(parent, parent_style)

        # Remove promoted styles from children
        for child, style in zip(children, child_styles):
            modified = False

            for key, value in common_style.items():
                if style.get(key) == value:
                    del style[key]
                    modified = True

            if modified:
                self.write_style(child, style)

        return changed

    # -------------------------------------------------------------------------
    # Remove duplicated styles from descendants
    # -------------------------------------------------------------------------

    def remove_duplicate_styles(self, parent):
        changed = False

        parent_style = self.parse_style(parent)

        for child in self.get_direct_tspan_children(parent):
            child_style = self.parse_style(child)

            remove_keys = []

            for key, value in child_style.items():
                if parent_style.get(key) == value:
                    remove_keys.append(key)

            for key in remove_keys:
                del child_style[key]
                changed = True

            self.write_style(child, child_style)

            if self.remove_duplicate_styles(child):
                changed = True

        return changed

    # -------------------------------------------------------------------------
    # Flatten nested tspans where safe
    # -------------------------------------------------------------------------

    def flatten_nested_tspans(self, parent):
        changed = False

        for child in list(parent):
            if child.tag != SVG_TSPAN_TAG:
                continue

            changed |= self.flatten_nested_tspans(child)

            nested_tspans = [
                c for c in child
                if c.tag == SVG_TSPAN_TAG
            ]

            if not nested_tspans:
                continue

            # Only flatten if the parent tspan has no direct text content
            if child.text and child.text.strip():
                continue

            # Only flatten if the parent tspan has no styles (possibly because all styles have been pushed up)
            if self.parse_style(child):
                continue

            # Preserve tails carefully
            index = list(parent).index(child)

            for nested in nested_tspans:
                new_node = copy.deepcopy(nested)
                parent.insert(index, new_node)
                index += 1

            # Preserve tail text
            if child.tail:
                if nested_tspans:
                    nested_tspans[-1].tail = (
                        (nested_tspans[-1].tail or "") + child.tail
                    )

            parent.remove(child)
            changed = True

        return changed


if __name__ == "__main__":
    TextSimplifyStructure().run()
