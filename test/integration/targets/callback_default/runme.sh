#!/usr/bin/env bash

# This test compares "known good" output with various settings against output
# with the current code. It's brittle by nature, but this is probably the
# "best" approach possible.
#
# Notes:
# * options passed to this script (such as -v) are ignored, as they would change
#   the output and break the test
# * the number of asterisks after a "banner" differs depending on the number of
#   columns on the TTY, so we must adjust the columns for the current session
#   for consistency

set -eux

run_test() {
	local testname=$1
	local playbook=$2

	# output was recorded w/o cowsay, ensure we reproduce the same
	export ANSIBLE_NOCOWS=1

	# The shenanigans with redirection and 'tee' are to capture STDOUT and
	# STDERR separately while still displaying both to the console
	{ ansible-playbook -i inventory "$playbook" "${@:3}" \
		> >(set +x; tee "${OUTFILE}.${testname}.stdout"); } \
		2> >(set +x; tee "${OUTFILE}.${testname}.stderr" >&2)
	sed -i -e 's/included: .*\/test\/integration/included: ...\/test\/integration/g' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's/@@ -1,1 +1,1 @@/@@ -1 +1 @@/g' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's/: .*\/test_diff\.txt/: ...\/test_diff.txt/g' "${OUTFILE}.${testname}.stdout"
	sed -i -e "s#${ANSIBLE_PLAYBOOK_DIR}#TEST_PATH#g" "${OUTFILE}.${testname}.stdout" "${OUTFILE}.${testname}.stderr"
	sed -i -e "s#/var/root/#/root/#g" "${OUTFILE}.${testname}.stdout" "${OUTFILE}.${testname}.stderr"  # macos
	sed -i -e 's/^Using .*//g' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's/[0-9]:[0-9]\{2\}:[0-9]\{2\}\.[0-9]\{6\}/0:00:00.000000/g' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\.[0-9]\{6\}/0000-00-00 00:00:00.000000/g' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's#: .*/\.source\.txt$#: .../.source.txt#g' "${OUTFILE}.${testname}.stdout"
	sed -i -e '/secontext:/d' "${OUTFILE}.${testname}.stdout"
	sed -i -e 's/group: wheel/group: root/g' "${OUTFILE}.${testname}.stdout"

	diff -u "${ORIGFILE}.${testname}.stdout" "${OUTFILE}.${testname}.stdout" || diff_failure
	diff -u "${ORIGFILE}.${testname}.stderr" "${OUTFILE}.${testname}.stderr" || diff_failure
}

run_test_dryrun() {
	local testname=$1
	# optional, pass --check to run a dry run
	local chk=${2:-}

	# output was recorded w/o cowsay, ensure we reproduce the same
	export ANSIBLE_NOCOWS=1

	# This needed to satisfy shellcheck that can not accept unquoted variable
	cmd="ansible-playbook -i inventory ${chk} test_dryrun.yml"

	# The shenanigans with redirection and 'tee' are to capture STDOUT and
	# STDERR separately while still displaying both to the console
	{ $cmd \
		> >(set +x; tee "${OUTFILE}.${testname}.stdout"); } \
		2> >(set +x; tee "${OUTFILE}.${testname}.stderr" >&2)

	diff -u "${ORIGFILE}.${testname}.stdout" "${OUTFILE}.${testname}.stdout" || diff_failure
	diff -u "${ORIGFILE}.${testname}.stderr" "${OUTFILE}.${testname}.stderr" || diff_failure
}

diff_failure() {
	if [[ $INIT = 0 ]]; then
		echo "FAILURE...diff mismatch!"
		exit 1
	fi
}

cleanup() {
	if [[ $INIT = 0 ]]; then
		rm -rf "${OUTFILE}.*"
	fi

	if [[ -f "${BASEFILE}.unreachable.stdout" ]]; then
		rm -rf "${BASEFILE}.unreachable.stdout"
	fi

	if [[ -f "${BASEFILE}.unreachable.stderr" ]]; then
		rm -rf "${BASEFILE}.unreachable.stderr"
	fi

	# Restore TTY cols
	if [[ -n ${TTY_COLS:-} ]]; then
		stty cols "${TTY_COLS}"
	fi
}

adjust_tty_cols() {
	if [[ -t 1 ]]; then
		# Preserve existing TTY cols
		TTY_COLS=$( stty -a | grep -Eo '; columns [0-9]+;' | cut -d';' -f2 | cut -d' ' -f3 )
		# Override TTY cols to make comparing ansible-playbook output easier
		# This value matches the default in the code when there is no TTY
		stty cols 79
	fi
}

BASEFILE=callback_default.out

ORIGFILE="${BASEFILE}"
OUTFILE="${BASEFILE}.new"

trap 'cleanup' EXIT

# The --init flag will (re)generate the "good" output files used by the tests
INIT=0
if [[ ${1:-} == "--init" ]]; then
	shift
	OUTFILE=$ORIGFILE
	INIT=1
fi

adjust_tty_cols

# Force the 'default' callback plugin, since that's what we're testing
export ANSIBLE_STDOUT_CALLBACK=default
# Disable color in output for consistency
export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_NOCOLOR=1

# Default settings
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=1
export ANSIBLE_DISPLAY_OK_HOSTS=1
export ANSIBLE_DISPLAY_FAILED_STDERR=0
export ANSIBLE_CHECK_MODE_MARKERS=0

run_test default test.yml

set +e
ANSIBLE_CALLBACKS_ENABLED=default run_test include_role_fails test_include_role_fails.yml
set -e

# Check for async output
# NOTE: regex to match 1 or more digits works for both BSD and GNU grep
ansible-playbook -i inventory test_async.yml 2>&1 | tee async_test.out
grep "ASYNC OK .* jid=j[0-9]\{1,\}" async_test.out
grep "ASYNC FAILED .* jid=j[0-9]\{1,\}" async_test.out
rm -f async_test.out

# Hide skipped
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=0

run_test hide_skipped test.yml

# Hide skipped/ok
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=0
export ANSIBLE_DISPLAY_OK_HOSTS=0

run_test hide_skipped_ok test.yml

# Hide ok
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=1
export ANSIBLE_DISPLAY_OK_HOSTS=0

run_test hide_ok test.yml

# Failed to stderr
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=1
export ANSIBLE_DISPLAY_OK_HOSTS=1
export ANSIBLE_DISPLAY_FAILED_STDERR=1

run_test failed_to_stderr test.yml
export ANSIBLE_DISPLAY_FAILED_STDERR=0


# Test displaying task path on failure
export ANSIBLE_SHOW_TASK_PATH_ON_FAILURE=1
run_test display_path_on_failure test.yml
export ANSIBLE_SHOW_TASK_PATH_ON_FAILURE=0


# Default settings with unreachable tasks
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=1
export ANSIBLE_DISPLAY_OK_HOSTS=1
export ANSIBLE_DISPLAY_FAILED_STDERR=1
export ANSIBLE_TIMEOUT=1

# Check if UNREACHABLE is available in stderr
set +e
ansible-playbook -i inventory test_2.yml > >(set +x; tee "${BASEFILE}.unreachable.stdout";) 2> >(set +x; tee "${BASEFILE}.unreachable.stderr" >&2) || true
set -e
if test "$(grep -c 'UNREACHABLE' "${BASEFILE}.unreachable.stderr")" -ne 1; then
	echo "Test failed"
	exit 1
fi
export ANSIBLE_DISPLAY_FAILED_STDERR=0

export ANSIBLE_CALLBACK_RESULT_FORMAT=yaml
run_test result_format_yaml test.yml
export ANSIBLE_CALLBACK_RESULT_FORMAT=json

export ANSIBLE_CALLBACK_RESULT_FORMAT=yaml
export ANSIBLE_CALLBACK_FORMAT_PRETTY=1
run_test result_format_yaml_lossy_verbose test.yml -v
run_test yaml_result_format_yaml_verbose test_yaml.yml -v
export ANSIBLE_CALLBACK_RESULT_FORMAT=json
unset ANSIBLE_CALLBACK_FORMAT_PRETTY

export ANSIBLE_CALLBACK_RESULT_FORMAT=yaml
export ANSIBLE_CALLBACK_FORMAT_PRETTY=0
run_test result_format_yaml_verbose test.yml -v
export ANSIBLE_CALLBACK_RESULT_FORMAT=json
unset ANSIBLE_CALLBACK_FORMAT_PRETTY


## DRY RUN tests
#
# Default settings with dry run tasks
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=1
export ANSIBLE_DISPLAY_OK_HOSTS=1
export ANSIBLE_DISPLAY_FAILED_STDERR=1
# Enable Check mode markers
export ANSIBLE_CHECK_MODE_MARKERS=1

# Test the wet run with check markers
run_test_dryrun check_markers_wet

# Test the dry run with check markers
run_test_dryrun check_markers_dry --check

# Disable Check mode markers
export ANSIBLE_CHECK_MODE_MARKERS=0

# Test the wet run without check markers
run_test_dryrun check_nomarkers_wet

# Test the dry run without check markers
run_test_dryrun check_nomarkers_dry --check

# Make sure implicit meta tasks are not printed
ansible-playbook -i host1,host2 no_implicit_meta_banners.yml > meta_test.out
cat meta_test.out
[ "$(grep -c 'TASK \[meta\]' meta_test.out)" -eq 0 ]
rm -f meta_test.out

# Ensure free/host_pinned non-lockstep strategies display correctly
diff -u callback_default.out.free.stdout <(ANSIBLE_STRATEGY=free ansible-playbook -i inventory test_non_lockstep.yml 2>/dev/null)
diff -u callback_default.out.fqcn_free.stdout <(ANSIBLE_STRATEGY=ansible.builtin.free ansible-playbook -i inventory test_non_lockstep.yml 2>/dev/null)
diff -u callback_default.out.host_pinned.stdout <(ANSIBLE_STRATEGY=host_pinned ansible-playbook -i inventory test_non_lockstep.yml 2>/dev/null)
