#!/bin/sh
# Configure SSH keys.

ssh_public_key=#{ssh_public_key}
ssh_private_key=#{ssh_private_key}
ssh_key_type=#{ssh_key_type}

ssh_path="${HOME}/.ssh"
private_key_path="${ssh_path}/id_${ssh_key_type}"

if [ ! -f "${private_key_path}" ]; then
    # write public/private ssh key pair
    public_key_path="${private_key_path}.pub"

    # shellcheck disable=SC2174
    mkdir -m 0700 -p "${ssh_path}"
    touch "${public_key_path}" "${private_key_path}"
    chmod 0600 "${public_key_path}" "${private_key_path}"
    echo "${ssh_public_key}" > "${public_key_path}"
    echo "${ssh_private_key}" > "${private_key_path}"

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
