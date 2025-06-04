#!/usr/bin/env python
from __future__ import annotations

import os
import pathlib
import sys

exclude_programs = {
    'ansible-test',
}

bin_dir = pathlib.Path(os.environ['JUNIT_OUTPUT_DIR']).parent.parent.parent / 'bin'
programs = set(program.name for program in bin_dir.iterdir() if program.name not in exclude_programs)
docs_dir = pathlib.Path(sys.argv[1])
docs = set(path.with_suffix('').name for path in docs_dir.iterdir())

print('\n'.join(sorted(docs)))

missing = programs - docs
extra = docs - programs

if missing or extra:
    raise RuntimeError(f'{missing=} {extra=}')
