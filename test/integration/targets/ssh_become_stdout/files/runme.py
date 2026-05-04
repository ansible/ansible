import subprocess

def cleanup():
    run(["docker", "stop", "host1"])
    run(["docker", "rm", "host1"])

def run(args_list):
    return subprocess.run(args=args_list, capture_output=True, text=True)

def setup_container():

    run(["docker", "run", "-d", "--name", "host1", "ubuntu:24.04", "sleep", "infinity"])

    run(["docker",
                            "exec",
                            "host1",
                            "apt-get",
                            "update"])

    run(["docker", "exec", "host1", "apt-get", "install", "sudo", "-y"])

    run(["docker", "exec", "host1", "useradd", "-m", "john"])

    p = subprocess.Popen(
        ["docker", "exec", "-i", "host1", "/usr/sbin/chpasswd"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        out, errs = p.communicate("john:12345".encode())
    except subprocess.TimeoutExpired:
        p.kill()
        out, errs = p.communicate()

    run(["docker", "exec", "host1", "usr/sbin/usermod", "-aG", "sudo", "john"])

    run(["docker", "exec", "host1", "apt-get", "update"])

    run(["docker", "exec", "host1", "apt-get", "install", "openssh-server", "python3", "-y"])

    run(["docker", "exec", "host1", "mkdir", "-p", "/var/run/sshd"])

    run(["docker", "exec", "host1", "apt-get", "update"])

    run(["docker", "exec", "host1", "apt-get", "install", "-y", "locales"])

    run(["docker", "exec", "host1", "locale-gen", "en_US.UTF-8"])

    p = subprocess.Popen(
        ["docker", "exec", "host1", "cat", ">", "/etc/default/locale"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        out, errs = p.communicate("LANG=en_US.UTF-8".encode())
    except subprocess.TimeoutExpired:
        p.kill()
        out, errs = p.communicate()

    run(["docker", "exec", "host1", "/usr/sbin/sshd"])

if __name__ == "__main__":
    cleanup()
    setup_container()
