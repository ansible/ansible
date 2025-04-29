#!/bin/sh

set -eux

unset USR

ENVVAR1='var1value' USR='' ansible-playbook vars_set.yml -i ../../inventory "${@}"

ansible-playbook vars_not_set.yml -i ../../inventory "${@}"
