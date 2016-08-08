#!/bin/bash

# You will need to add these to authorize_keys for the ssh testhost and
# account. Probably shouldn't be a public machine, though these keys are
# just as random as any other key.
#
# But heads up, don't put these into authorized_keys unless you understand the
# implications.

ssh-keygen -t rsa -N '' -v -f id_rsa_testhost
ssh-keygen -t rsa -N 'password' -v -f id_rsa_testhost_password

# too readable
ssh-keygen -t rsa -N '' -v -f id_rsa_testhost_too_open
chmod 0666 id_rsa_testhost_too_open

# nothing can read it
ssh-keygen -t rsa -N '' -v -f id_rsa_testhost_can_not_read
chmod 0100 id_rsa_testhost_can_not_read
# this is meant to generate a keywith a password that is unknown, so
# we don't output it or remember it. uuid isn't a great choice, but
# pay attention to the heads up above.

UNKNOWN_PASSWORD=$(uuidgen -r)
ssh-keygen -t rsa -N "${UNKNOWN_PASSWORD}" -v -f id_rsa_testhost_password_unknown

echo "# Add the below to authorized_keys for testhost and testuser"
cat id_rsa_testhost.pub
cat id_rsa_testhost_password.pub
cat id_rsa_testhost_password_unknown.pub
