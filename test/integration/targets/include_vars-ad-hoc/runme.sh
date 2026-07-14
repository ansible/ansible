#!/usr/bin/env bash

set -eux -o pipefail

echo "single file include"
ansible testhost -i ../../inventory -m include_vars -a 'dir/inc.yml' -vvv 2>&1 | grep -q 'porter.*cable'

echo "single file encrypted include"
ansible testhost -i ../../inventory -m include_vars -a 'dir/encrypted.yml' -vvv --vault-password-file vaultpass > output.txt 2>&1

echo "directory include with encrypted"
ansible testhost -i ../../inventory -m include_vars -a 'dir=dir' -vvv --vault-password-file vaultpass >> output.txt 2>&1

grep -q 'output has been hidden' output.txt

# all content should be masked if any file is encrypted
if grep -e 'i am a secret' -e 'porter.*cable' output.txt; then
  echo "FAIL: vault masking failed"
  exit 1
fi

echo PASS
