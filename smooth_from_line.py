#!/usr/bin/env python3

import inkex
from inkex import Path


class SmoothFromLine(inkex.EffectExtension):

    def effect(self):
        num_patheffect = 0
        for element in self.svg.selection.filter(inkex.PathElement):

            if element.get("inkscape:path-effect") is None:
                element.path = self.process_path(element.path)
            else:
                num_patheffect += 1

        if num_patheffect > 0:
            inkex.errormsg(
                _(
                    f"""{num_patheffect} selected elements have an
                inkscape:path-effect applied. These elements will be
                ignored to avoid confusing results. Apply Paths->Object
                to path (Shift+Ctrl+C) and retry .""",
                )
            )

    def process_path(self, path: inkex.Path):
        path = path.to_arrays()
        new_path = []

        i = 0

        while i < len(path):

            # Need at least:
            # current cmd
            # next cmd
            if (
                i + 1 < len(path)
                and path[i][0].lower() == 'l'
                and path[i + 1][0].lower() == 'c'
            ):

                lcmd, lvals = path[i]
                ccmd, cvals = path[i + 1]

                # Handle relative commands
                if lcmd == 'l' and ccmd == 'c':
                    x1, y1 = lvals
                    dx1, dy1 = cvals[0:2]

                    # Convert:
                    # l x1,y1
                    # c dx1,dy1 ...
                    #
                    # into:
                    # s (x1-dx1),(y1-dy1) x1,y1

                    sx = x1 - dx1
                    sy = y1 - dy1

                    new_path.append([
                        's',
                        [sx, sy, x1, y1]
                    ])

                    # keep original cubic
                    new_path.append(path[i + 1])
                    i += 2
                    continue

                # Handle absolute commands
                elif lcmd == 'L' and ccmd == 'C':
                    x1, y1 = lvals
                    dx1, dy1 = cvals[0:2]

                    # Convert:
                    # L x1,y1
                    # C dx1,dy1 ...
                    #
                    # into:
                    # S (2*x1-dx1),(2*y1-dy1) x1,y1

                    sx = 2 * x1 - dx1
                    sy = 2 * y1 - dy1

                    new_path.append([
                        'S',
                        [sx, sy, x1, y1]
                    ])

                    # keep original cubic
                    new_path.append(path[i + 1])
                    i += 2
                    continue


            new_path.append(path[i])
            i += 1

        return new_path

if __name__ == '__main__':
    SmoothFromLine().run()
