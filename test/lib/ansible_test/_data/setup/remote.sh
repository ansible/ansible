#!/bin/sh

set -eu

platform="$1"
python_version="$2"
python_interpreter="python${python_version}"

cd ~/

install_pip () {
    if ! "${python_interpreter}" -m pip.__main__ --version --disable-pip-version-check 2>/dev/null; then
        case "${python_version}" in
            *)
                pip_bootstrap_url="https://ansible-ci-files.s3.amazonaws.com/ansible-test/get-pip-20.3.4.py"
                ;;
        esac
        curl --silent --show-error "${pip_bootstrap_url}" -o /tmp/get-pip.py
        "${python_interpreter}" /tmp/get-pip.py --disable-pip-version-check --quiet
        rm /tmp/get-pip.py
    fi
}

if [ "${platform}" = "freebsd" ]; then
    py_version="$(echo "${python_version}" | tr -d '.')"

    while true; do
        env ASSUME_ALWAYS_YES=YES pkg bootstrap && \
        pkg install -q -y \
            bash \
            curl \
            gtar \
            "python${py_version}" \
            "py${py_version}-Jinja2" \
            "py${py_version}-virtualenv" \
            "py${py_version}-cryptography" \
            sudo \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done

    install_pip

    if ! grep '^PermitRootLogin yes$' /etc/ssh/sshd_config > /dev/null; then
        sed -i '' 's/^# *PermitRootLogin.*$/PermitRootLogin yes/;' /etc/ssh/sshd_config
        service sshd restart
    fi
elif [ "${platform}" = "rhel" ]; then
    if grep '8\.' /etc/redhat-release; then
        while true; do
            yum module install -q -y python36 && \
            yum install -q -y \
                gcc \
                python3-devel \
                python3-jinja2 \
                python3-virtualenv \
                python3-cryptography \
                iptables \
            && break
            echo "Failed to install packages. Sleeping before trying again..."
            sleep 10
        done
    else
        while true; do
            yum install -q -y \
                gcc \
                python-devel \
                python-virtualenv \
                python2-cryptography \
            && break
            echo "Failed to install packages. Sleeping before trying again..."
            sleep 10
        done

        install_pip
    fi

    # pin packaging and pyparsing to match the downstream vendored versions
    "${python_interpreter}" -m pip install packaging==20.4 pyparsing==2.4.7 --disable-pip-version-check
elif [ "${platform}" = "centos" ]; then
    while true; do
        yum install -q -y \
            gcc \
            python-devel \
            python-virtualenv \
            python2-cryptography \
            libffi-devel \
            openssl-devel \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done

    install_pip
elif [ "${platform}" = "osx" ]; then
    while true; do
        pip install --disable-pip-version-check --quiet \
            'virtualenv==16.7.10' \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done
elif [ "${platform}" = "aix" ]; then
    chfs -a size=1G /
    chfs -a size=4G /usr
    chfs -a size=1G /var
    chfs -a size=1G /tmp
    chfs -a size=2G /opt
    while true; do
        yum install -q -y \
            gcc \
            libffi-devel \
            python-jinja2 \
            python-cryptography \
            python-pip && \
        pip install --disable-pip-version-check --quiet virtualenv \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done
fi

# Generate our ssh key and add it to our authorized_keys file.
# We also need to add localhost's server keys to known_hosts.

if [ ! -f "${HOME}/.ssh/id_rsa.pub" ]; then
    ssh-keygen -m PEM -q -t rsa -N '' -f "${HOME}/.ssh/id_rsa"
    # newer ssh-keygen PEM output (such as on RHEL 8.1) is not recognized by paramiko
    touch "${HOME}/.ssh/id_rsa.new"
    chmod 0600 "${HOME}/.ssh/id_rsa.new"
    sed 's/\(BEGIN\|END\) PRIVATE KEY/\1 RSA PRIVATE KEY/' "${HOME}/.ssh/id_rsa" > "${HOME}/.ssh/id_rsa.new"
    mv "${HOME}/.ssh/id_rsa.new" "${HOME}/.ssh/id_rsa"
    cat "${HOME}/.ssh/id_rsa.pub" >> "${HOME}/.ssh/authorized_keys"
    chmod 0600 "${HOME}/.ssh/authorized_keys"
    for key in /etc/ssh/ssh_host_*_key.pub; do
        pk=$(cat "${key}")
        echo "localhost ${pk}" >> "${HOME}/.ssh/known_hosts"
    done
fi

# Improve prompts on remote host for interactive use.
# shellcheck disable=SC1117
cat << EOF > ~/.bashrc
if ls --color > /dev/null 2>&1; then
    alias ls='ls --color'
elif ls -G > /dev/null 2>&1; then
    alias ls='ls -G'
fi
export PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
EOF

# Make sure ~/ansible/ is the starting directory for interactive shells.
if [ "${platform}" = "osx" ]; then
    echo "cd ~/ansible/" >> ~/.bashrc
elif [ "${platform}" = "macos" ] ; then
    echo "export BASH_SILENCE_DEPRECATION_WARNING=1" >> ~/.bashrc
    echo "cd ~/ansible/" >> ~/.bashrc
fi
