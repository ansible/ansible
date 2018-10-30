#!/usr/bin/env bash

if [[ $(python --version 2>&1) =~ 2\.6 ]]
  then
    echo "Openshift client is not supported on Python 2.6"
    exit 0
fi

set -eux

source virtualenv.sh
pip install openshift

./server.py &

# Fake auth file
mkdir -p ~/.kube/
cat <<EOF > ~/.kube/config
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: http://localhost:12345
  name: development
contexts:
- context:
    cluster: development
    user: developer
  name: dev-frontend
current-context: dev-frontend
kind: Config
preferences: {}
users:
- name: developer
  user:
    token: ZDNg7LzSlp8a0u0fht_tRnPMTOjxqgJGCyi_iy0ecUw
EOF

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=kubevirt
export ANSIBLE_INVENTORY=test.kubevirt.yml

cat << EOF > "$OUTPUT_DIR/test.kubevirt.yml"
plugin: kubevirt
connections:
  - namespaces:
      - default
EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i "$OUTPUT_DIR/test.kubevirt.yml" --list --output="$OUTPUT_DIR/plugin.out"
kill -9 "$(jobs -p)"

#################################################
#   DIFF THE RESULTS
#################################################

./inventory_diff.py "$(pwd)/test.out" "$OUTPUT_DIR/plugin.out"
