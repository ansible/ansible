#!/usr/bin/env bash

set -eux

# fun multilevel finds
for seed in play_adj play_adj_subdir somepath/play_adj_subsubdir in_role otherpath/in_role_subdir
do
	ansible-playbook find_levels/play.yml -e "seed='${seed}'" "$@"
done
