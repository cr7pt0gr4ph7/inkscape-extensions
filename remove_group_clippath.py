#!/usr/bin/env python3

import inkex


class RemoveGroupClipPath(inkex.EffectExtension):

    def effect(self):
        count = 0

        for element in self.svg.selection.values():

            # Only process SVG group elements (<g>)
            if isinstance(element, inkex.Group):

                # Remove clip-path attribute if present
                if 'clip-path' in element.attrib:
                    del element.attrib['clip-path']
                    count += 1

        inkex.utils.debug(f"Removed clip-path from {count} group(s).")


if __name__ == '__main__':
    RemoveGroupClipPath().run()
