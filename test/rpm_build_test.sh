#!/bin/bash

######################################################################
# RPM building tests
#
# This runs the 'make (s)rpm' commands and checks that the expected
# files were created. The build logs are saved for each test.
######################################################################

info_msg() {
    cat <<EOF
#############################################
${1}
#############################################

EOF
}

build() {
    # Expecting to receive 'rpm' or 'srpm'
    local TARGET=${1}
    TEST_NUM=$(( ${TEST_NUM} + 1 ))
    local build_log=`mktemp`

    # Update global log index
    BUILD_LOGS[${TEST_NUM}]=${build_log}

    info_msg "Running ${TARGET} building test"
    make ${TARGET} > ${build_log} 2>&1
}

check_result() {
    local TEST_NAME=${1}
    local TARGET_FILE=${2}

    if [ -f "${TARGET_FILE}" ]; then
	RESULTS[${TEST_NUM}]="[${TEST_NAME}] Success!"
    else
	RESULTS[${TEST_NUM}]="[${TEST_NAME}] Failure!"
    fi
}

print_results() {
    echo "
#############################################
RPM BUILD TEST RESULTS:"
    for i in `seq ${TEST_NUM}`; do
	echo
	echo "${RESULTS[${i}]}"
	echo "Build log: ${BUILD_LOGS[${i}]}"
    done
    echo "#############################################"
}

##############################
# VARS
##############################

TEST_NUM=0
HERE=`basename $(pwd)`
RESULTS=
BUILD_LOGS=

##############################
# Makefile is in the root of the checkout, we must go to there.
##############################

if [ ! -f 'Makefile' ]; then
    # We are most likely in the 'test' directory
    if [ "${HERE}" = "test" ]; then
	pushd ..
	make clean > /dev/null 2>&1
    else
	# Give up, it could be anywhere.
	echo "[Error] Unable to locate Makefile."
	echo "[Error] Must be ran from test directory or the root checkout"
	exit 1
    fi
fi

RPMNAME=`make rpmname`
SRPMNAME=`make srpmname`

##############################
# Exec RPM Building Testing
##############################

build "rpm"

check_result "Build RPM" "${RPMNAME}"

##############################
# Exec SRPM Building Testing
##############################

build "srpm"

check_result "Build SRPM" "${SRPMNAME}"

##############################
# Summarize test results
##############################

print_results
