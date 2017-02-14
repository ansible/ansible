#!/bin/sh

cd test/runner/

pylint --max-line-length=160 --reports=n ./*.py ./*/*.py \
    --jobs 2 \
    --rcfile /dev/null \
    --function-rgx '[a-z_][a-z0-9_]{2,40}$' \
    -d unused-import \
    -d too-few-public-methods \
    -d too-many-arguments \
    -d too-many-branches \
    -d too-many-locals \
    -d too-many-statements \
    -d too-many-nested-blocks \
    -d too-many-instance-attributes \
    -d too-many-lines \
    -d too-many-return-statements
