# shellcheck shell=sh

set -eu

remove_externally_managed_marker()
{
    "${python_interpreter}" -c '
import pathlib
import sysconfig
path = pathlib.Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED"
path.unlink(missing_ok=True)
'
}

install_ssh_keys()
{
    if [ ! -f "${ssh_private_key_path}" ]; then
        # write public/private ssh key pair
        public_key_path="${ssh_private_key_path}.pub"

        # shellcheck disable=SC2174
        mkdir -m 0700 -p "${ssh_path}"
        touch "${public_key_path}" "${ssh_private_key_path}"
        chmod 0600 "${public_key_path}" "${ssh_private_key_path}"
        echo "${ssh_public_key}" > "${public_key_path}"
        echo "${ssh_private_key}" > "${ssh_private_key_path}"

        # add public key to authorized_keys
        authoried_keys_path="${HOME}/.ssh/authorized_keys"

        # the existing file is overwritten to avoid conflicts (ex: RHEL on EC2 blocks root login)
        cat "${public_key_path}" > "${authoried_keys_path}"
        chmod 0600 "${authoried_keys_path}"

        # add localhost's server keys to known_hosts
        known_hosts_path="${HOME}/.ssh/known_hosts"

        for key in /etc/ssh/ssh_host_*_key.pub; do
            echo "localhost $(cat "${key}")" >> "${known_hosts_path}"
        done
    fi
}

customize_bashrc()
{
    true > ~/.bashrc

    # Show color `ls` results when available.
    if ls --color > /dev/null 2>&1; then
        echo "alias ls='ls --color'" >> ~/.bashrc
    elif ls -G > /dev/null 2>&1; then
        echo "alias ls='ls -G'" >> ~/.bashrc
    fi

    # Improve shell prompts for interactive use.
    echo "export PS1='"'\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '"'" >> ~/.bashrc
}

install_pip() {
    if ! "${python_interpreter}" -m pip.__main__ --version --disable-pip-version-check 2>/dev/null; then
        case "${python_version}" in
            *)
                pip_bootstrap_url="https://ci-files.testing.ansible.com/ansible-test/get-pip-24.0.py"
                ;;
        esac

        while true; do
            curl --silent --show-error "${pip_bootstrap_url}" -o /tmp/get-pip.py && \
            "${python_interpreter}" /tmp/get-pip.py --disable-pip-version-check --quiet && \
            rm /tmp/get-pip.py \
            && break
            echo "Failed to install packages. Sleeping before trying again..."
            sleep 10
        done
    fi
}

bootstrap_remote_alpine()
{
    py_pkg_prefix="py3"

    packages="
        acl
        bash
        gcc
        python3-dev
        ${py_pkg_prefix}-pip
        sudo
        "

    if [ "${controller}" ]; then
        packages="
            ${packages}
            ${py_pkg_prefix}-cryptography
            ${py_pkg_prefix}-packaging
            ${py_pkg_prefix}-yaml
            ${py_pkg_prefix}-jinja2
            ${py_pkg_prefix}-resolvelib
            "
    fi

    while true; do
        # shellcheck disable=SC2086
        apk add -q ${packages} \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done

    # Upgrade the `libexpat` package to ensure that an upgraded Python (`pyexpat`) continues to work.
    while true; do
        # shellcheck disable=SC2086
        apk upgrade -q libexpat \
        && break
        echo "Failed to upgrade libexpat. Sleeping before trying again..."
        sleep 10
    done
}

bootstrap_remote_fedora()
{
    py_pkg_prefix="python3"

    packages="
        acl
        gcc
        ${py_pkg_prefix}-devel
        "

    if [ "${controller}" ]; then
        packages="
            ${packages}
            ${py_pkg_prefix}-cryptography
            ${py_pkg_prefix}-jinja2
            ${py_pkg_prefix}-packaging
            ${py_pkg_prefix}-pyyaml
            ${py_pkg_prefix}-resolvelib
            "
    fi

    while true; do
        # shellcheck disable=SC2086
        dnf install -q -y ${packages} \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done
}

bootstrap_remote_freebsd()
{
    packages="
        python${python_package_version}
        py${python_package_version}-sqlite3
        py${python_package_version}-setuptools
        bash
        curl
        gtar
        sudo
        "

    if [ "${controller}" ]; then
        jinja2_pkg="py${python_package_version}-jinja2"
        cryptography_pkg="py${python_package_version}-cryptography"
        pyyaml_pkg="py${python_package_version}-yaml"
        packaging_pkg="py${python_package_version}-packaging"

        # Declare platform/python version combinations which do not have supporting OS packages available.
        # For these combinations ansible-test will use pip to install the requirements instead.
        case "${platform_version}/${python_version}" in
            13.3/3.9)
                # defaults above 'just work'TM
                ;;
            13.3/3.11)
                jinja2_pkg=""  # not available
                cryptography_pkg=""  # not available
                pyyaml_pkg=""  # not available
                ;;
            14.1/3.9)
                # defaults above 'just work'TM
                ;;
            14.1/3.11)
                cryptography_pkg=""  # not available
                jinja2_pkg=""  # not available
                pyyaml_pkg=""  # not available
                ;;
            *)
                # just assume nothing is available
                jinja2_pkg=""  # not available
                cryptography_pkg=""  # not available
                pyyaml_pkg=""  # not available
                packaging_pkg="" # not available
                ;;
        esac

        packages="
            ${packages}
            ${packaging_pkg}
            libyaml
            ${pyyaml_pkg}
            ${jinja2_pkg}
            ${cryptography_pkg}
            "
    fi

    while true; do
        # shellcheck disable=SC2086
        env ASSUME_ALWAYS_YES=YES pkg bootstrap && \
        pkg install -q -y ${packages} \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done

    install_pip

    if ! grep '^PermitRootLogin yes$' /etc/ssh/sshd_config > /dev/null; then
        sed -i '' 's/^# *PermitRootLogin.*$/PermitRootLogin yes/;' /etc/ssh/sshd_config
        service sshd restart
    fi

    # make additional wheels available for packages which lack them for this platform
    echo "# generated by ansible-test
[global]
extra-index-url = https://spare-tire.testing.ansible.com/simple/
prefer-binary = yes
" > /etc/pip.conf

    # enable ACL support on the root filesystem (required for become between unprivileged users)
    fs_path="/"
    fs_device="$(mount -v "${fs_path}" | cut -w -f 1)"
    # shellcheck disable=SC2001
    fs_device_escaped=$(echo "${fs_device}" | sed 's|/|\\/|g')

    mount -o acls "${fs_device}" "${fs_path}"
    awk 'BEGIN{FS=" "}; /'"${fs_device_escaped}"'/ {gsub(/^rw$/,"rw,acls", $4); print; next} // {print}' /etc/fstab > /etc/fstab.new
    mv /etc/fstab.new /etc/fstab

    # enable sudo without a password for the wheel group, allowing ansible to use the sudo become plugin
    echo '%wheel ALL=(ALL:ALL) NOPASSWD: ALL' > /usr/local/etc/sudoers.d/ansible-test
}

bootstrap_remote_macos()
{
    # Silence macOS deprecation warning for bash.
    echo "export BASH_SILENCE_DEPRECATION_WARNING=1" >> ~/.bashrc

    # Make sure ~/ansible/ is the starting directory for interactive shells on the control node.
    # The root home directory is under a symlink. Without this the real path will be displayed instead.
    if [ "${controller}" ]; then
        echo "cd ~/ansible/" >> ~/.bashrc
    fi

    # Make sure commands like 'brew' can be found.
    # This affects users with the 'zsh' shell, as well as 'root' accessed using 'sudo' from a user with 'zsh' for a shell.
    # shellcheck disable=SC2016
    echo 'PATH="/usr/local/bin:$PATH"' > /etc/zshenv
}

bootstrap_remote_rhel_9()
{
    if [ "${python_version}" = "3.9" ]; then
        py_pkg_prefix="python3"
    else
        py_pkg_prefix="python${python_version}"
    fi

    packages="
        gcc
        ${py_pkg_prefix}-devel
        ${py_pkg_prefix}-pip
        "

    # Jinja2 is not installed with an OS package since the provided version is too old.
    # Instead, ansible-test will install it using pip.
    # packaging and resolvelib are missing for controller supported Python versions, so we just
    # skip them and let ansible-test install them from PyPI.
    if [ "${controller}" ]; then
        packages="
            ${packages}
            ${py_pkg_prefix}-cryptography
            ${py_pkg_prefix}-pyyaml
            "
    fi

    while true; do
        # shellcheck disable=SC2086
        dnf install -q -y ${packages} \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done
}

bootstrap_remote_rhel()
{
    case "${platform_version}" in
        9.*) bootstrap_remote_rhel_9 ;;
    esac
}

bootstrap_remote_ubuntu()
{
    py_pkg_prefix="python3"

    packages="
        acl
        gcc
        python${python_version}-dev
        python3-pip
        python${python_version}-venv
        "

    if [ "${controller}" ]; then
        cryptography_pkg="${py_pkg_prefix}-cryptography"
        jinja2_pkg="${py_pkg_prefix}-jinja2"
        packaging_pkg="${py_pkg_prefix}-packaging"
        pyyaml_pkg="${py_pkg_prefix}-yaml"
        resolvelib_pkg="${py_pkg_prefix}-resolvelib"

        # Declare platforms which do not have supporting OS packages available.
        # For these ansible-test will use pip to install the requirements instead.
        # Only the platform is checked since Ubuntu shares Python packages across Python versions.
        case "${platform_version}" in
        esac

        packages="
            ${packages}
            ${cryptography_pkg}
            ${jinja2_pkg}
            ${packaging_pkg}
            ${pyyaml_pkg}
            ${resolvelib_pkg}
            "
    fi

    while true; do
        # shellcheck disable=SC2086
        apt-get update -qq -y && \
        DEBIAN_FRONTEND=noninteractive apt-get install -qq -y --no-install-recommends ${packages} \
        && break
        echo "Failed to install packages. Sleeping before trying again..."
        sleep 10
    done
}

bootstrap_docker()
{
    # Required for newer mysql-server packages to install/upgrade on Ubuntu 16.04.
    rm -f /usr/sbin/policy-rc.d

    for key_value in ${python_interpreters}; do
        IFS=':' read -r python_version python_interpreter << EOF
${key_value}
EOF

        echo "Bootstrapping Python ${python_version} at: ${python_interpreter}"

        remove_externally_managed_marker
    done
}

bootstrap_remote()
{
    for key_value in ${python_interpreters}; do
        IFS=':' read -r python_version python_interpreter << EOF
${key_value}
EOF

        echo "Bootstrapping Python ${python_version} at: ${python_interpreter}"

        python_package_version="$(echo "${python_version}" | tr -d '.')"

        case "${platform}" in
            "alpine") bootstrap_remote_alpine ;;
            "fedora") bootstrap_remote_fedora ;;
            "freebsd") bootstrap_remote_freebsd ;;
            "macos") bootstrap_remote_macos ;;
            "rhel") bootstrap_remote_rhel ;;
            "ubuntu") bootstrap_remote_ubuntu ;;
        esac

        remove_externally_managed_marker
    done
}

bootstrap()
{
    ssh_path="${HOME}/.ssh"
    ssh_private_key_path="${ssh_path}/id_${ssh_key_type}"

    install_ssh_keys
    customize_bashrc

    # allow tests to detect ansible-test bootstrapped instances, as well as the bootstrap type
    echo "${bootstrap_type}" > /etc/ansible-test.bootstrap

    case "${bootstrap_type}" in
        "docker") bootstrap_docker ;;
        "remote") bootstrap_remote ;;
    esac
}

# These variables will be templated before sending the script to the host.
# They are at the end of the script to maintain line numbers for debugging purposes.
bootstrap_type=#{bootstrap_type}
controller=#{controller}
platform=#{platform}
platform_version=#{platform_version}
python_interpreters=#{python_interpreters}
ssh_key_type=#{ssh_key_type}
ssh_private_key=#{ssh_private_key}
ssh_public_key=#{ssh_public_key}

bootstrap
