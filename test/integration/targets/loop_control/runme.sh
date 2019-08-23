#!/usr/bin/env bash

set -eux

# user output has:
#ok: [localhost] => (item=looped_var foo_label) => {
#ok: [localhost] => (item=looped_var bar_label) => {
MATCH='foo_label
bar_label'
[ "$(ansible-playbook label.yml "$@" |grep 'item='|sed -e 's/^.*(item=looped_var \(.*\)).*$/\1/')" == "${MATCH}" ]

# user output has:
#ok: [localhost] => {
#    "msg": "1 0 3 2 True False 3 first,second,third"
#ok: [localhost] => {
#    "msg": "2 1 2 1 False False 3 first,second,third"
#ok: [localhost] => {
#    "msg": "3 2 1 0 False True 3 first,second,third"
MATCH='"1 0 3 2 True False 3 first,second,third"
"2 1 2 1 False False 3 first,second,third"
"3 2 1 0 False True 3 first,second,third"'
[ "$(ansible-playbook extended.yml "$@" |grep '"msg":'|sed -e 's/^.*"msg": \(.*\)$/\1/')" == "${MATCH}" ]
