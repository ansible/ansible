#!/bin/bash -eux

args=('bs=1M' 'count=256')

dd "${args[@]}" if=/dev/zero    of=/tmp/zero
dd "${args[@]}" if=/dev/urandom of=/tmp/urandom

dd "${args[@]}" if=/tmp/zero    of=/tmp/copy-zero
dd "${args[@]}" if=/tmp/urandom of=/tmp/copy-urandom
