#!/usr/bin/env python3

import re
import inkex

from inkex import PathElement, Group
from lxml import etree


FLOAT_RE = r"[-+]?(?:\d*\.\d+|\d+\.?(?:\d*)?)(?:[eE][-+]?\d+)?"
TOKEN_RE = re.compile(rf"{FLOAT_RE}|[A-Za-z_]+")


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

    def to_svg_path(self, y_flip=True):
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

    MOVE_OPS = {"mo", "moveto", "m"}
    LINE_OPS = {"li", "lineto", "l"}
    CURVE_OPS = {"cv", "curveto", "c"}
    CLOSE_OPS = {"cp", "closepath", "h"}
    NEWPATH_OPS = {"np", "newpath", "n"}
    CLIP_OPS = {"clp", "clip"}

    def __init__(self, text):
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
                    self.current_path.curve_to(*vals)

                continue

            if lower in self.CLOSE_OPS:
                if self.current_path:
                    self.current_path.close()

                continue

            if lower in self.CLIP_OPS:
                self.finish_current_path()
                self.stack.clear()
                continue

            if len(self.stack) > 64:
                self.stack = self.stack[-16:]

        self.finish_current_path()
        return self.paths


class EPSPathImport(inkex.InputExtension):
    """
    Heuristic EPS geometry importer.

    This is intentionally NOT a full PostScript interpreter.
    It scans EPS text and reconstructs SVG paths from recognizable
    geometry operators.
    """

    def load(self, stream):
        eps_text = stream.read().decode("latin-1", errors="ignore")

        parser = EPSHeuristicParser(eps_text)
        paths = parser.parse()

        if not paths:
            raise inkex.AbortExtension(
                "No path geometry could be extracted from the EPS file"
            )

        svg = etree.Element(
            inkex.addNS("svg", "svg"),
            nsmap=inkex.NSS
        )

        svg.set("width", "1000")
        svg.set("height", "1000")
        svg.set("viewBox", "0 -1000 1000 1000")

        group = Group()
        group.label = "Imported EPS Geometry"
        svg.append(group)

        imported_count = 0

        for p in paths:
            d = p.to_svg_path(y_flip=True)

            if not d.strip():
                continue

            node = PathElement()
            node.set("d", d)

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

        return etree.ElementTree(svg)


if __name__ == "__main__":
    EPSPathImport().run()
