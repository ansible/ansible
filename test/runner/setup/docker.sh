#!/bin/sh

set -eu

# Support images with only python3 installed.
if [ ! -f /usr/bin/python ] && [ -f /usr/bin/python3 ]; then
    ln -s /usr/bin/python3 /usr/bin/python
fi
if [ ! -f /usr/bin/pip ] && [ -f /usr/bin/pip3 ]; then
    ln -s /usr/bin/pip3 /usr/bin/pip
fi
if [ ! -f /usr/bin/virtualenv ] && [ -f /usr/bin/virtualenv-3 ]; then
    ln -s /usr/bin/virtualenv-3 /usr/bin/virtualenv
fi

# Improve prompts on remote host for interactive use.
cat << EOF > ~/.bashrc
alias ls='ls --color=auto'
export PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
cd ~/ansible/
EOF
