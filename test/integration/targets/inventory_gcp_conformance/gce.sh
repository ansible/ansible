#!/usr/bin/env bash
# Wrapper to use the correct Python interpreter and support code coverage.

export PYTHONPATH="${PWD}/lib:$PYTHONPATH"
ABS_SCRIPT=$(python -c "import os; print(os.path.abspath('../../../../contrib/inventory/gce.py'))")
cd "${OUTPUT_DIR}"
python.py "${ABS_SCRIPT}" "$@"
