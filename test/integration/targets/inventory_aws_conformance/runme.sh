#!/usr/bin/env bash

set -eux

# set the output dir
if [ -z ${OUTPUT_DIR+null} ]; then
    export OUTPUT_DIR=$(pwd)
fi

#################################################
#   RUN THE SCRIPT
#################################################

# run the script first
cat << EOF > $OUTPUT_DIR/ec2.ini
[ec2]
regions = us-east-1
cache_path = $(pwd)/.cache
cache_max_age = 0

[credentials]
aws_access_key_id = FOO
aws_secret_acccess_key = BAR
EOF

rm -f script.out
./ec2.sh | tee -a $OUTPUT_DIR/script.out
#./ec2.sh 
RC=$?
if [[ $RC != 0 ]]; then
    exit $RC
fi
#rm -f $OUTPUT_DIR/ec2.ini
#rm -f $OUTPUT_DIR/ec2.py
#rm -rf .cache

#exit 0

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=aws_ec2
export ANSIBLE_INVENTORY=test.aws_ec2.yml
export AWS_ACCESS_KEY_ID=FOO
export AWS_SECRET_ACCESS_KEY=BAR

cat << EOF > $OUTPUT_DIR/test.aws_ec2.yml
plugin: aws_ec2
regions:
    - us-east-1
EOF

# override boto's import path(s)
echo "PWD: $(pwd)"
export PYTHONPATH=$(pwd)/lib:$PYTHONPATH

rm -f $OUTPUT_DIR/plugin.out
ansible-inventory -i $OUTPUT_DIR/test.aws_ec2.yml --list | tee -a $OUTPUT_DIR/plugin.out
rm -f $OUTPUT_DIR/aws_ec2.yml

#################################################
#   DIFF THE RESULTS
#################################################

diff -y $OUTPUT_DIR/script.out $OUTPUT_DIR/plugin.out
