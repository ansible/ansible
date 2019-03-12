#!/usr/bin/env bash
# Wrapper to use the correct Python interpreter and support code coverage.

if [ -z "$ANSIBLE_TEST_PYTHON_INTERPRETER" ]; then
    ANSIBLE_TEST_PYTHON_INTERPRETER=$(command -v python)
fi

if [ -f ../../../../contrib/inventory/gce.py ]; then
    ABS_SCRIPT="../../../../contrib/inventory/gce.py"
    ABS_SCRIPT=$($ANSIBLE_TEST_PYTHON_INTERPRETER -c "import os; print(os.path.abspath('${ABS_SCRIPT}'))")
elif [ -f ~/ansible/contrib/inventory/gce.py ]; then
    ABS_SCRIPT=~/ansible/contrib/inventory/gce.py
else
    echo "Could not find gce.py!"
    exit 1
fi

# set the output dir
#echo "OUTPUT_DIR: $OUTPUT_DIR"
if [ -z ${OUTPUT_DIR+null} ]; then
    export OUTPUT_DIR=${PWD}
fi
pushd "${OUTPUT_DIR}" &> /dev/null || exit 1
    cp $ABS_SCRIPT .

    export PYTHONPATH=./lib
    CMD="$ANSIBLE_TEST_PYTHON_INTERPRETER gce.py ${*}"
    #echo "$CMD"
    $CMD
    RC=$?
popd &> /dev/null || exit 1
exit $RC
