def add_git_host_key(module, url, accept_hostkey=True):

    """ idempotently add a git url hostkey """

    if accept_hostkey:

        fqdn = get_fqdn(module.params['repo'])

        if fqdn:
            known_host = check_hostkey(module, fqdn)
            if not known_host:
                rc, out, err = add_host_key(module, fqdn)
                if rc != 0:
                    module.fail_json(msg="failed to add %s hostkey: %s" % (fqdn, out + err))

def get_fqdn(repo_url):

    """ chop the hostname out of a giturl """

    result = None
    if "@" in repo_url:
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

    if rc == 0:
        if out != "":
            result = True

    return result

def add_host_key(module, fqdn, key_type="rsa"):

    """ use ssh-keyscan to add the hostkey """

    result = False
    keyscan_cmd = module.get_bin_path('ssh-keyscan', True)
    this_cmd = "%s -t %s %s >> ~/.ssh/known_hosts" % (keyscan_cmd, key_type, fqdn)
    rc, out, err = module.run_command(this_cmd)

    return rc, out, err

