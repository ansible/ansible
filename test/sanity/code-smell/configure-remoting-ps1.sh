#!/bin/sh

FILE='examples/scripts/ConfigureRemotingForAnsible.ps1'

if [ ! -f "${FILE}" ] || [ -h "${FILE}" ]; then
    echo 'The file "ConfigureRemotingForAnsible.ps1" is missing or is not a regular file.'
    echo 'It is required by external automated processes and should not be moved or renamed.'
    exit 1
fi
