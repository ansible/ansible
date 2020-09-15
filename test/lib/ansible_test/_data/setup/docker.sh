#!/bin/sh

set -eu

# Required for newer mysql-server packages to install/upgrade on Ubuntu 16.04.
rm -f /usr/sbin/policy-rc.d

# Improve prompts on remote host for interactive use.
# shellcheck disable=SC1117
cat << EOF > ~/.bashrc
alias ls='ls --color=auto'
export PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
cd ~/ansible/
EOF
