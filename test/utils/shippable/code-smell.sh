#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

cd "${source_root}"

test/code-smell/replace-urlopen.sh .
test/code-smell/use-compat-six.sh lib
test/code-smell/boilerplate.sh
test/code-smell/required-and-default-attributes.sh
