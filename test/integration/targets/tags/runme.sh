#!/usr/bin/env bash

set -eux -o pipefail

# Run these using en_US.UTF-8 because list-tasks is a user output function and so it tailors its output to the
# user's locale.  For unicode tags, this means replacing non-ascii chars with "?"

COMMAND=(ansible-playbook -i ../../inventory test_tags.yml -v --list-tasks)

export LC_ALL=en_US.UTF-8

# Run everything by default
[ "$("${COMMAND[@]}" | grep -F Task_with | xargs)" = \
"Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always] Task_with_unicode_tag TAGS: [くらとみ] Task_with_list_of_tags TAGS: [café, press] Task_without_tag TAGS: [] Task_with_csv_tags TAGS: [tag1, tag2] Task_with_templated_tags TAGS: [tag3] Task_with_meta_tags TAGS: [meta_tag]" ]

# Run the exact tags, and always
[ "$("${COMMAND[@]}" --tags tag | grep -F Task_with | xargs)" = \
"Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always]" ]

# Skip one tag
[ "$("${COMMAND[@]}" --skip-tags tag | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_unicode_tag TAGS: [くらとみ] Task_with_list_of_tags TAGS: [café, press] Task_without_tag TAGS: [] Task_with_csv_tags TAGS: [tag1, tag2] Task_with_templated_tags TAGS: [tag3] Task_with_meta_tags TAGS: [meta_tag]" ]

# Skip a unicode tag
[ "$("${COMMAND[@]}" --skip-tags 'くらとみ' | grep -F Task_with | xargs)" = \
"Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always] Task_with_list_of_tags TAGS: [café, press] Task_without_tag TAGS: [] Task_with_csv_tags TAGS: [tag1, tag2] Task_with_templated_tags TAGS: [tag3] Task_with_meta_tags TAGS: [meta_tag]" ]

# Skip a meta task tag
[ "$("${COMMAND[@]}" --skip-tags meta_tag | grep -F Task_with | xargs)" = \
"Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always] Task_with_unicode_tag TAGS: [くらとみ] Task_with_list_of_tags TAGS: [café, press] Task_without_tag TAGS: [] Task_with_csv_tags TAGS: [tag1, tag2] Task_with_templated_tags TAGS: [tag3]" ]

# Run just a unicode tag and always
[ "$("${COMMAND[@]}" --tags 'くらとみ' | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_unicode_tag TAGS: [くらとみ]" ]

# Run a tag from a list of tags and always
[ "$("${COMMAND[@]}" --tags café | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_list_of_tags TAGS: [café, press]" ]

# Run tag with never
[ "$("${COMMAND[@]}" --tags donever | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_never_tag TAGS: [donever, never]" ]

# Run csv tags
[ "$("${COMMAND[@]}" --tags tag1 | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_csv_tags TAGS: [tag1, tag2]" ]

# Run templated tags
[ "$("${COMMAND[@]}" --tags tag3 | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_templated_tags TAGS: [tag3]" ]

# Run meta tags
[ "$("${COMMAND[@]}" --tags meta_tag | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_with_meta_tags TAGS: [meta_tag]" ]

# Run tagged
[ "$("${COMMAND[@]}" --tags tagged | grep -F Task_with | xargs)" = \
"Task_with_tag TAGS: [tag] Task_with_always_tag TAGS: [always] Task_with_unicode_tag TAGS: [くらとみ] Task_with_list_of_tags TAGS: [café, press] Task_with_csv_tags TAGS: [tag1, tag2] Task_with_templated_tags TAGS: [tag3] Task_with_meta_tags TAGS: [meta_tag]" ]

# Run untagged
[ "$("${COMMAND[@]}" --tags untagged | grep -F Task_with | xargs)" = \
"Task_with_always_tag TAGS: [always] Task_without_tag TAGS: []" ]

# Skip 'always'
[ "$("${COMMAND[@]}" --tags untagged --skip-tags always | grep -F Task_with | xargs)" = \
"Task_without_tag TAGS: []" ]

# Test ansible_run_tags
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=all "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=all --tags all "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=list --tags tag1,tag3 "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=list --tags tag1 --tags tag3 "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=untagged --tags untagged "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=untagged_list --tags untagged,tag3 "$@"
ansible-playbook -i ../../inventory ansible_run_tags.yml -e expect=tagged --tags tagged "$@"

ansible-playbook test_template_parent_tags.yml "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'Tagged_task')" = "1" ]; rm out.txt

ansible-playbook test_template_parent_tags.yml --tags tag1 "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'Tagged_task')" = "1" ]; rm out.txt

ansible-playbook test_template_parent_tags.yml --skip-tags tag1 "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'Tagged_task')" = "0" ]; rm out.txt
