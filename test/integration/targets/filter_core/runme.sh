#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml "$@"
ANSIBLE_ROLES_PATH=../ ansible-playbook handle_undefined_type_errors.yml "$@"

# Remove passlib installed by setup_passlib_controller
source virtualenv.sh
SITE_PACKAGES=$(python -c "import sysconfig; print(sysconfig.get_path('purelib'))")
echo "raise ImportError('passlib')" > "${SITE_PACKAGES}/passlib.py"

# Test with libc (without libxcrypt)
ANSIBLE_ROLES_PATH=../ ansible-playbook password_hash.yml "$@"

# Install libxcrypt and capture output
INSTALL_OUTPUT=$(ANSIBLE_ROLES_PATH=../ ansible localhost -m include_role -a name=setup_libxcrypt 2>&1)
echo "$INSTALL_OUTPUT"

# Check if libxcrypt was installed by looking for the handler output
if echo "$INSTALL_OUTPUT" | grep -q 'LIBXCRYPT_WAS_INSTALLED'; then
    # Setup cleanup trap
    cleanup_libxcrypt() {
        echo "Cleaning up libxcrypt..."
        ANSIBLE_ROLES_PATH=../ ansible localhost -m include_role -a 'name=setup_libxcrypt tasks_from=uninstall' || true
    }
    trap cleanup_libxcrypt EXIT
fi

# Test with libxcrypt (new ansible-playbook process will discover it)
if echo "$INSTALL_OUTPUT" | grep -q 'LIBXCRYPT_WAS_INSTALLED'; then
    ANSIBLE_ROLES_PATH=../ ansible-playbook password_hash.yml -e '{expect_libxcrypt: true}' "$@"
else
    ANSIBLE_ROLES_PATH=../ ansible-playbook password_hash.yml "$@"
fi
