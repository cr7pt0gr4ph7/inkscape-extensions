#!/usr/bin/env python3

import re
import math
import inkex
from inkex import PathElement, Group


FLOAT_RE = r"[-+]?(?:\d*\.\d+|\d+\.?(?:\d*)?)(?:[eE][-+]?\d+)?"
TOKEN_RE = re.compile(rf"{FLOAT_RE}|[A-Za-z_]+")

ALL_MODE = "all"
ONLY_CLOSED_MODE = "only_closed"
ONLY_OPEN_MODE = "only_open"

class EPSPath:
    def __init__(self):
        self.commands = []
        self.closed = False

    def move_to(self, x, y):
        self.commands.append(("M", x, y))

    def line_to(self, x, y):
        self.commands.append(("L", x, y))

    def curve_to(self, x1, y1, x2, y2, x3, y3):
        self.commands.append(("C", x1, y1, x2, y2, x3, y3))

    def close(self):
        self.closed = True

    def to_svg_path(self, y_flip=False):
        parts = []

        for cmd in self.commands:
            op = cmd[0]

            if op == "M":
                _, x, y = cmd
                if y_flip:
                    y = -y
                parts.append(f"M {x} {y}")

            elif op == "L":
                _, x, y = cmd
                if y_flip:
                    y = -y
                parts.append(f"L {x} {y}")

            elif op == "C":
                _, x1, y1, x2, y2, x3, y3 = cmd

                if y_flip:
                    y1 = -y1
                    y2 = -y2
                    y3 = -y3

                parts.append(
                    f"C {x1} {y1} {x2} {y2} {x3} {y3}"
                )

        if self.closed:
            parts.append("Z")

        return " ".join(parts)


class EPSHeuristicParser:
    """
    Best-effort EPS parser.

    This parser intentionally uses heuristics rather than trying to fully
    interpret PostScript.

    Supported operators:
        mo / moveto
        li / lineto
        cv / curveto
        cp / closepath
        np / newpath
        clp

    It can recover geometry from snippets like:

        np
        55.0727 48.7511 mo
        54.8976 48.0793 54.7479 47.4011 54.6216 46.7166 cv
        ...
        clp
    """

    MOVE_OPS = {"mo", "moveto", "m"}
    LINE_OPS = {"li", "lineto", "l"}
    CURVE_OPS = {"cv", "curveto", "c"}
    CLOSE_OPS = {"cp", "closepath", "h"}
    NEWPATH_OPS = {"np", "newpath", "n"}
    CLIP_OPS = {"clp", "clip"}

    def __init__(self, text):
        self.text = text
        self.tokens = TOKEN_RE.findall(text)
        self.stack = []
        self.paths = []
        self.current_path = None

    def is_number(self, token):
        try:
            float(token)
            return True
        except ValueError:
            return False

    def pop_numbers(self, count):
        if len(self.stack) < count:
            return None

        values = self.stack[-count:]
        self.stack = self.stack[:-count]

        return [float(v) for v in values]

    def finish_current_path(self):
        if self.current_path and self.current_path.commands:
            self.paths.append(self.current_path)

        self.current_path = None

    def parse(self):
        for token in self.tokens:
            lower = token.lower()

            if self.is_number(token):
                self.stack.append(token)
                continue

            if lower in self.NEWPATH_OPS:
                self.finish_current_path()
                self.current_path = EPSPath()
                self.stack.clear()
                continue

            if lower in self.MOVE_OPS:
                vals = self.pop_numbers(2)
                if vals:
                    x, y = vals

                    if self.current_path is None:
                        self.current_path = EPSPath()

                    self.current_path.move_to(x, y)
                continue

            if lower in self.LINE_OPS:
                vals = self.pop_numbers(2)
                if vals and self.current_path:
                    x, y = vals
                    self.current_path.line_to(x, y)
                continue

            if lower in self.CURVE_OPS:
                vals = self.pop_numbers(6)
                if vals and self.current_path:
                    x1, y1, x2, y2, x3, y3 = vals
                    self.current_path.curve_to(
                        x1, y1,
                        x2, y2,
                        x3, y3
                    )
                continue

            if lower in self.CLOSE_OPS:
                if self.current_path:
                    self.current_path.close()
                continue

            if lower in self.CLIP_OPS:
                # Often indicates the end of a clipping path.
                # We preserve it as a normal path.
                self.finish_current_path()
                self.stack.clear()
                continue

            # Unknown operator:
            # heuristic recovery by clearing pathological stack growth.
            if len(self.stack) > 64:
                self.stack = self.stack[-16:]

        self.finish_current_path()
        return self.paths


class EPSPathImportExtension(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--eps_file",
            type=str,
            help="EPS file to parse"
        )

        pars.add_argument(
            "--import_mode",
            type=str,
            default="all",
            help="Import mode for EPS geometry"
        )

    def effect(self):
        eps_path = self.options.eps_file

        if not eps_path:
            raise inkex.AbortExtension("No EPS file selected")

        try:
            with open(eps_path, "r", encoding="latin-1", errors="ignore") as f:
                eps_text = f.read()

        except Exception as e:
            raise inkex.AbortExtension(f"Unable to read EPS file: {e}")

        parser = EPSHeuristicParser(eps_text)
        paths = parser.parse()

        if not paths:
            raise inkex.AbortExtension(
                "No path geometry could be extracted from the EPS file"
            )

        root = self.document.getroot()

        group = Group()
        group.label = "Imported EPS Geometry"
        root.append(group)

        imported_count = 0

        for p in paths:
            if self.options.import_mode == ONLY_CLOSED_MODE and not p.closed:
                continue

            if self.options.import_mode == ONLY_OPEN_MODE and p.closed:
                continue

            svg_d = p.to_svg_path()

            if svg_d.strip() == "":
                continue

            node = PathElement()
            node.path = svg_d

            node.style = {
                "fill": "none",
                "stroke": "#000000",
                "stroke-width": "1"
            }

            group.append(node)
            imported_count += 1

        inkex.utils.debug(
            f"Imported {imported_count} path(s) from EPS"
        )


if __name__ == "__main__":
    EPSPathImportExtension().run()
