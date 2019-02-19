#!/usr/bin/env bash
# Wrapper to use the correct Python interpreter and support code coverage.

REL_SCRIPT="../../../../contrib/inventory/foreman.py"
ABS_SCRIPT="$("python.py" -c "import os; print(os.path.abspath('${REL_SCRIPT}'))")"

# Make sure output written to current directory ends up in the temp dir.
cd "${OUTPUT_DIR}"

python.py "${ABS_SCRIPT}" "$@"
