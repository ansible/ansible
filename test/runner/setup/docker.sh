#!/bin/sh

set -eu

# Required for newer mysql-server packages to install/upgrade on Ubuntu 16.04.
rm -f /usr/sbin/policy-rc.d

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

# ensure libyaml and libyaml headers are present
if [ -f /etc/fedora-release ]; then
    dnf install libyaml libyaml-devel -y
elif [ -f /etc/redhat-release ]; then
    yum install libyaml libyaml-devel -y
elif [ -f /etc/debian_version ]; then
    apt-get install libyaml-0-2 libyaml-dev -y
fi

pip install pyyaml==3.13b1 --verbose

echo "*** TESTING PYYAML LIBYAML BINDING ***"
python -c 'import yaml; print(yaml.load("[1,2,3]", Loader=yaml.CLoader))'

# Improve prompts on remote host for interactive use.
cat << EOF > ~/.bashrc
alias ls='ls --color=auto'
export PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
cd ~/ansible/
EOF
