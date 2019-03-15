#!/usr/bin/env bash
# Wrapper to use the correct Python interpreter and support code coverage.

if [ -f ../../../../contrib/inventory/ec2.py ]; then
    ABS_SCRIPT="../../../../contrib/inventory/ec2.py"
    ABS_SCRIPT=$(python -c "import os; print(os.path.abspath('${ABS_SCRIPT}'))")
elif [ -f ~/ansible/contrib/inventory/ec2.py ]; then
    ABS_SCRIPT=~/ansible/contrib/inventory/ec2.py
else
    echo "Could not find ec2.py!"
    exit 1
fi

TARGET=$(pwd)

if [ -z "${OUTPUT_DIR+null}" ]; then
    export OUTPUT_DIR=$TARGET
fi
cd "${OUTPUT_DIR}"
cp $ABS_SCRIPT .

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i ec2.py --list --output="$OUTPUT_DIR/script.out"
