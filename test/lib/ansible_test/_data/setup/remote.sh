#!/bin/sh

set -eu

platform=#{platform}
platform_version=#{platform_version}
python_version=#{python_version}

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

    if [ "${py_version}" = "27" ]; then
        # on Python 2.7 our only option is to use virtualenv
        virtualenv_pkg="py27-virtualenv"
    else
        # on Python 3.x we'll use the built-in venv instead
        virtualenv_pkg=""
    fi

    # Declare platform/python version combinations which do not have supporting OS packages available.
    # For these combinations ansible-test will use pip to install the requirements instead.
    case "${platform_version}/${python_version}" in
        "11.4/3.8")
            have_os_packages=""
            ;;
        "12.2/3.8")
            have_os_packages=""
            ;;
        *)
            have_os_packages="yes"
            ;;
    esac

    # PyYAML is never installed with an OS package since it does not include libyaml support.
    # Instead, ansible-test will always install it using pip.
    if [ "${have_os_packages}" ]; then
        jinja2_pkg="py${py_version}-Jinja2"
        cryptography_pkg="py${py_version}-cryptography"
    else
        jinja2_pkg=""
        cryptography_pkg=""
    fi

    while true; do
        # shellcheck disable=SC2086
        env ASSUME_ALWAYS_YES=YES pkg bootstrap && \
        pkg install -q -y \
            bash \
            curl \
            gtar \
            libyaml \
            "python${py_version}" \
            ${jinja2_pkg} \
            ${cryptography_pkg} \
            ${virtualenv_pkg} \
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
        py_version="$(echo "${python_version}" | tr -d '.')"

        if [ "${py_version}" = "36" ]; then
            py_pkg_prefix="python3"
        else
            py_pkg_prefix="python${py_version}"
        fi

        while true; do
            yum module install -q -y "python${py_version}" && \
            yum install -q -y \
                gcc \
                "${py_pkg_prefix}-devel" \
                "${py_pkg_prefix}-jinja2" \
                "${py_pkg_prefix}-cryptography" \
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
        pip install --disable-pip-version-check --quiet \
            'virtualenv==16.7.10' \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
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
