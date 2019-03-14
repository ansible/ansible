#!/usr/bin/env bash
# Wrapper to use the correct Python interpreter and support code coverage.

if [ -z "$ANSIBLE_TEST_PYTHON_INTERPRETER" ]; then
    ANSIBLE_TEST_PYTHON_INTERPRETER=$(which python)
fi

#REL_SCRIPT="../../../../contrib/inventory/ec2.py"
#ABS_SCRIPT="$("${ANSIBLE_TEST_PYTHON_INTERPRETER}" -c "import os; print(os.path.abspath('${REL_SCRIPT}'))")"
#ABS_SCRIPT=/root/ansible/contrib/inventory/ec2.py

if [ -f ../../../../contrib/inventory/ec2.py ]; then
    ABS_SCRIPT="../../../../contrib/inventory/ec2.py"
    ABS_SCRIPT=$($ANSIBLE_TEST_PYTHON_INTERPRETER -c "import os; print(os.path.abspath('${ABS_SCRIPT}'))")
elif [ -f ~/ansible/contrib/inventory/ec2.py ]; then
    ABS_SCRIPT=~/ansible/contrib/inventory/ec2.py
else
    echo "Could not find ec2.py!"
    exit 1
fi
#ls -al $ABS_SCRIPT

TARGET=$(pwd)
# set the output dir
#echo "OUTPUT_DIR: $OUTPUT_DIR"

if [ -z "${OUTPUT_DIR+null}" ]; then
    export OUTPUT_DIR=$TARGET
fi
cd "${OUTPUT_DIR}"
cp $ABS_SCRIPT .

#ls -al $TARGET/boto
#ls -al /root/ansible/lib
#ls -al .
#pwd
#echo "TARGET $TARGET"
#echo "PPATH $PYTHONPATH"
export PYTHONPATH=$TARGET/lib:$PYTHONPATH
exec "$ANSIBLE_TEST_PYTHON_INTERPRETER" ec2.py
