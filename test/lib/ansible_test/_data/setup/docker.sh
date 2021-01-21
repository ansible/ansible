#!/bin/sh

set -eu

# Required for newer mysql-server packages to install/upgrade on Ubuntu 16.04.
rm -f /usr/sbin/policy-rc.d

# Improve prompts on remote host for interactive use.
# `cat << EOF > ~/.bashrc` flakes sometimes since /tmp may not be ready yet in
# the container. So don't do that
echo "alias ls='ls --color=auto'" > ~/.bashrc
echo "export PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> ~/.bashrc
echo "cd ~/ansible/" >> ~/.bashrc
