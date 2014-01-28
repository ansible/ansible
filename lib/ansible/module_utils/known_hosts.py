def add_git_host_key(module, url, accept_hostkey=True):

    """ idempotently add a git url hostkey """

    fqdn = get_fqdn(module.params['repo'])

    if fqdn:
        known_host = check_hostkey(module, fqdn)
        if not known_host:
            if accept_hostkey:
                rc, out, err = add_host_key(module, fqdn)
                if rc != 0:
                    module.fail_json(msg="failed to add %s hostkey: %s" % (fqdn, out + err))
            else:
                module.fail_json(msg="%s has an unknown hostkey. Set accept_hostkey to True or manually add the hostkey prior to running the git module" % fqdn)                    

def get_fqdn(repo_url):

    """ chop the hostname out of a giturl """

    result = None
    if "@" in repo_url and not repo_url.startswith("http"):
        repo_url = repo_url.split("@", 1)[1]
        if ":" in repo_url:
            repo_url = repo_url.split(":")[0]
            result = repo_url
        elif "/" in repo_url:
            repo_url = repo_url.split("/")[0]
            result = repo_url

    return result


def check_hostkey(module, fqdn):

    """ use ssh-keygen to check if key is known """

    result = False
    keygen_cmd = module.get_bin_path('ssh-keygen', True)
    this_cmd = keygen_cmd + " -H -F " + fqdn
    rc, out, err = module.run_command(this_cmd)

    if rc == 0 and out != "":
            result = True
    else:
        # Check the main system location
        this_cmd = keygen_cmd + " -H -f /etc/ssh/ssh_known_hosts -F " + fqdn
        rc, out, err = module.run_command(this_cmd)

        if rc == 0:
            if out != "":
                result = True

    return result

def add_host_key(module, fqdn, key_type="rsa"):

    """ use ssh-keyscan to add the hostkey """

    result = False
    keyscan_cmd = module.get_bin_path('ssh-keyscan', True)

    if not os.path.exists(os.path.expanduser("~/.ssh/")):
        module.fail_json(msg="%s does not exist" % os.path.expanduser("~/.ssh/"))

    this_cmd = "%s -t %s %s >> ~/.ssh/known_hosts" % (keyscan_cmd, key_type, fqdn)
    rc, out, err = module.run_command(this_cmd)

    return rc, out, err

