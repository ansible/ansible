from __future__ import annotations

import ast
import pathlib
import sys


class CallVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id.endswith("FieldAttribute"):
            if len([kw for kw in node.keywords if kw.arg in ("default", "required")]) > 1:
                print(f"{self.path}:{node.lineno}:{node.col_offset}: use only one of `default` or `required` with `{node.func.id}`")


def main() -> None:
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        tree = ast.parse(pathlib.Path(path).read_text(), path)
        CallVisitor(path).visit(tree)


if __name__ == "__main__":
    main()
