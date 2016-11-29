#!/bin/bash -eux
# (c) 2016, John Barker <jobarker@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

########################################################

# FIXME Describe purpose, process, directory structure, and state/variables


readonly PROG="${0##*/}"
readonly LOCKFILE_DIR=/tmp
readonly LOCK_FD=200



##
# Validate command line arguments

if [ "$#" -ne 2 ]; then
    echo "Invalid arguments provided"  >&2
    echo  >&2
    echo "USAGE: $0 platform branch" >&2
    echo  >&2
    echo "       $0 ios devel"  >&2
    echo "       $0 junos stable-2.2"  >&2
    exit 2
fi

platform=$1
branches=$2


inventory="inventory.network" # FIXME This file will updating to reference the DUT VMs once they exist

# FIXME Describe directory structure here
basedir="/tmp/run-network-test"
log_root="/var/www/html/network-tests/logs"
#DEBUG_LOGFILE="${basedir}/${PROG}-$(date '+%s').log"

main() {
    validate_tools
    setup_environment

    echo "Platform: '${platform}'"
    echo "Branches: '${branches}'"

    # Ensure we don't run more than one instance of the tests per platform.
    # As we only have one test machine per platform we can't run more than one test
    # at once

    # Use the flock method from http://www.kfirlavi.com/blog/2012/11/06/elegant-locking-of-bash-program/
    lock "${PROG}-${platform}" \
        || eexit "Only one instance of ${PROG} can run on ${platform} at one time."
    run_tests

}


setup_environment() {
    if [  -d "${basedir}" ]; then
        mkdir -p "${basedir}"
    fi

    # FIXME Create HTML template if it doesn't already exist

    if [ ! -e "${log_root}/results.html" ]; then
        # First run so write out the top of the HTML results page
        echo "One time setup: Creating '${log_root}/results.html'"



    cat << 'EOF' > "${log_root}/results.html"
<html>
    <title>Ansible Network Test Results</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/dt/jq-2.2.3/dt-1.10.12/datatables.min.css"/>
    <script type="text/javascript" src="https://cdn.datatables.net/v/dt/jq-2.2.3/dt-1.10.12/datatables.min.js"></script>
    <script>
// https://datatables.net/blog/2014-12-18 May need this
$(document).ready(function(){
    $('#results').DataTable({
        // Newest result on top
        "order": [[ 0, "desc" ]],
        // show all results
        paging: false
    });
});

    </script>
    <body>
        <table id="results" class="datatable table table-striped table-bordered display" cellspacing="0" width="100%">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Branch</th>
                    <th>sha1</th>
                    <th>Platform</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
EOF
   fi
}


# We key of platform as the Test VMs are the limiting factor, not the branches
# run-network-test/platform/devel

run_tests() {

    for branch in ${branches//,/ }
    do
        echo "Inspecting: ${branch}"
        echo "Updating git repo..."

        branch_dir="${basedir}/${platform}/${branch}"
        ansible_dir="${branch_dir}/ansible"
        if [ -d "${ansible_dir}" ]; then
            git -C "${ansible_dir}" pull
        else
            git clone "https://github.com/ansible/ansible.git" "${ansible_dir}"
        fi
        # FIXME Revert any files left over from a previous run

        # Ensure we have the correct branch and submodules checked out
        git -C "${ansible_dir}" checkout "${branch}"
        git -C "${ansible_dir}" submodule update --init

        ##
        # Have we already ran tests on this commit
        checkout_sha="$(git -C "${ansible_dir}" rev-parse HEAD )"
        echo "${checkout_sha}"

        # Check against existing sha
        if [ -e "${branch_dir}/last-tested.sha" ]; then
            if [ "x${checkout_sha}" = "x$(cat "${branch_dir}/last-tested.sha")" ]; then
                echo "SKIPPING: $branch '${checkout_sha}' Has already been tested"
                continue # to the next branch
            fi

        fi

        echo "INFO $branch which sha1 of ${checkout_sha} has not been tested yet"
        echo "${checkout_sha}" > "${branch_dir}/last-tested.sha"
        logdir_for_this_run="${log_root}/${branch}/${platform}/${checkout_sha}"
        mkdir -p "${logdir_for_this_run}"

       echo "env-setup..."
       source "${ansible_dir}/hacking/env-setup"
       ansible_exit_value=0
       cd "${ansible_dir}/test/integration"
       echo "Running Tests..."
       echo "Logs will be written to: ${log_root}/results.html"
       ansible-playbook --version > "${logdir_for_this_run}/ansible.log" 2>&1
       ANSIBLE_FORCE_COLOR=1 ANSIBLE_ROLES_PATH=targets time -p ansible-playbook \
            -vvv \
            -i ${inventory} \
            "${platform}.yaml" >> "${logdir_for_this_run}/ansible.log" 2>&1 || ansible_exit_value=$?
        echo "Ansible exited with: ${ansible_exit_value}"

        ###
        # Format logs

        # Generate HTML version
        ansi2html < "${logdir_for_this_run}/ansible.log" > "${logdir_for_this_run}/ansible.html"

        # Strip escape characters
        sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g" "${logdir_for_this_run}/ansible.log" > "${logdir_for_this_run}/ansible.txt"

        # Write row to HTML table
        # This is horrible, though it gives us a basic table of results
        # It abuses the fact that we don't *have* to have "</tbody></table></body></html>

        # Assume tests are failing unless they pass.
        # In the future we could look up the exit value to detect the difference between
        # failing test and machine not reachable
        result_cell="<td bgcolor='red'>${ansible_exit_value}</td>"
        if [ "${ansible_exit_value}" -eq "0" ]; then
            result_cell="<td bgcolor='green'>${ansible_exit_value}</td>"
        fi

        gh_link="<a href='https://github.com/ansible/ansible/commits/${checkout_sha}'>${checkout_sha}</a>"

        echo "<tr><td><a href='${branch}/${platform}/${checkout_sha}/ansible.html'>$(date -R)</a></td><td>${branch}</td><td>${gh_link}</td><td>${platform}</td>${result_cell}</tr>" >> "${log_root}/results.html"
        if [ "${ansible_exit_value}" -ne "0" ]; then
            # Display the last few lines of the log
            tail -n 20 "${logdir_for_this_run}/ansible.log"
        fi

        echo "Logs written to: ${logdir_for_this_run}"


    done
}


validate_tools() {
    # FIXME
    echo "In validate_tools"
    if ! [ -x "$(command -v git)" ]; then
        eexit "'git' is not installed." >&2
      fi
    if ! [ -x "$(command -v ansi2html)" ]; then
        eexit "'ansi2html' is not installed. Please install with 'sudo pip install ansi2html'" >&2
    fi
}


upload_to_s3() {
    # FIXME
    echo "In upload_to_s3"
}


lock() {
    local prefix=$1
    local fd=${2:-$LOCK_FD}
    local lock_file=$LOCKFILE_DIR/$prefix.lock

    # create lock file
    eval "exec $fd>$lock_file"

    # acquire the lock
    flock -n "${fd}" \
        && return 0 \
        || return 1
}

eexit() {
    echo "$1"
    exit 1
}

# Log everything of interest to syslog and to disk
# Based on https://nicolaw.uk/#BashScriptDebugSyslog

exec > >(2>&-;logger -s -t "$PROG[$$]" -p user.info 2>&1) 2> >(logger -s -t "$PROG[$$]" -p user.error)

ls
ps >&2

main "$@"
