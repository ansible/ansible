# shellcheck shell=sh

set -eu

>&2 echo "@MARKER@"

cgroup_path="$(awk -F: '$2 ~ /^name=systemd$/ { print "/sys/fs/cgroup/systemd"$3 }' /proc/1/cgroup)"

if [ "${cgroup_path}" ] && [ -d "${cgroup_path}" ]; then
    probe_path="${cgroup_path%/}/ansible-test-probe-@LABEL@"
    mkdir "${probe_path}"
    rmdir "${probe_path}"
    exit 0
fi

>&2 echo "No systemd cgroup v1 hierarchy found"
exit 1
