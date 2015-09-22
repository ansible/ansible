#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Vlad Glagolev <scm@vaygr.net>
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


DOCUMENTATION = '''
---
module: sorcery
short_description: Package manager for Source Mage GNU/Linux
description:
    - Manages "spells" on Source Mage GNU/Linux using I(sorcery) toolchain
author: Vlad Glagolev
version_added: "2.0"
notes:
    - When all three components are selected, the update goes by the sequence --
      Sorcery -> Grimoire(s) -> Spell(s); you cannot override it.
    - grimoire handling (i.e. add/remove, including SCM/rsync versions) is not
      yet supported.
requirements:
    - bash
options:
    name:
        description:
            - Name of the spell
            - multiple names can be given, separated by commas
            - special value '*' in conjunction with states 'latest' or 'rebuild'
              will update or rebuild the whole system respectively
        required: false
        aliases: ["spell"]
        default: null

    state:
        description:
            - Whether to cast, dispel or rebuild a package
            - state 'cast' is an equivalent of 'present', not 'latest'
            - state 'latest' always triggers 'update_cache=yes'
            - state 'rebuild' implies cast of all specified spells, not only
              those existed before
        required: false
        choices: ["present", "latest", "absent", "cast", "dispelled", "rebuild"]
        default: "present"

    depends:
        description:
            - Comma-separated list of _optional_ dependencies to build a spell
              (or make sure it is built) with; use +/- in front of dependency
              to turn it on/off ('+' is optional though)
            - this option is ignored if 'name' parameter is equal to '*' or
              contains more than one spell
            - providers must be supplied in the form recognized by Sorcery, i.e.
              'openssl(SSL)'
        required: false
        default: null

    update:
        description:
            - Whether or not to update sorcery scripts at the very first stage
        required: false
        choices: ["yes", "no"]
        default: "no"

    update_cache:
        description:
            - Whether or not to update grimoire collection before casting spells
        required: false
        aliases: ["update_codex"]
        choices: ["yes", "no"]
        default: "no"

    cache_valid_time:
        description:
            - Time in seconds to invalidate grimoire collection on update
            - especially useful for SCM and rsync grimoires
            - makes sense only in pair with 'update_cache'
        required: false
        default: null
'''


EXAMPLES = '''
# Make sure spell 'foo' is installed
- sorcery: spell=foo state=present

# Make sure spells 'foo', 'bar' and 'baz' are removed
- sorcery: spell=foo,bar,baz state=absent

# Make sure spell 'foo' with dependencies 'bar' and 'baz' is installed
- sorcery: spell=foo depends=bar,baz state=present

# Make sure spell 'foo' with 'bar' and without 'baz' dependencies is installed
- sorcery: spell=foo depends=+bar,-baz state=present

# Make sure spell 'foo' with libressl (providing SSL) dependency is installed
- sorcery: spell=foo depends=libressl(SSL) state=present

# Install the latest version of spell 'foo' using regular glossary
- sorcery: name=foo state=latest

# Rebuild spell 'foo'
- sorcery: spell=foo state=rebuild

# Rebuild the whole system, but update Sorcery and Codex first
- sorcery: spell=* state=rebuild update=yes update_cache=yes

# Refresh the grimoire collection if it's 1 day old using native sorcerous alias
- sorcery: update_codex=yes cache_valid_time=86400

# Update only Sorcery itself
- sorcery: update=yes
'''


import datetime
import fileinput
import os
import re
import shutil


SORCERY = {
    'sorcery': "/usr/sbin/sorcery",
    'scribe': "/usr/sbin/scribe",
    'cast': "/usr/sbin/cast",
    'dispel': "/usr/sbin/dispel",
    'gaze': "/usr/sbin/gaze"
}

SORCERY_VERSION_FILE = "/etc/sorcery/version"
SORCERY_LOG = "/var/log/sorcery"
SORCERY_STATE = "/var/state/sorcery"

CODEX = "/var/lib/sorcery/codex"


def exec_command(command, module):
    """ Run sorcery commands without asking questions.

    This prevents commands from stuck due to queries and forces to use default
    answers. It also leverages output if a user has the VOYEUR option turned on
    in Sorcery.

    """

    prompt_env = "env PROMPT_DELAY=0 VOYEUR=0"

    return module.run_command("%s %s" % (prompt_env, command))


def codex_cksum(module):
    """ Get SHA1 hashes for grimoire versions. """

    checksums = {}

    for grimoire in os.listdir(CODEX):
        grimoire_version_path = os.path.join(CODEX, grimoire, "VERSION")

        checksums[grimoire] = module.sha1(grimoire_version_path)

    return checksums


def codex_fresh(module):
    """ Check if grimoire collection is fresh enough. """

    if not module.params['cache_valid_time']:
        return False

    timedelta = datetime.timedelta(seconds=module.params['cache_valid_time'])

    # we have to make sure listing doesn't include files (i.e. archives)
    for grimoire in os.listdir(CODEX):
        lastupdate_path = os.path.join(SORCERY_STATE, grimoire + ".lastupdate")

        try:
            mtime = os.stat(lastupdate_path).st_mtime
        except:
            return False

        lastupdate_ts = datetime.datetime.fromtimestamp(mtime)

        # if any grimoire is not fresh, we invalidate the Codex
        if lastupdate_ts + timedelta < datetime.datetime.now():
            return False

    return True


def update_sorcery(module):
    """ Update sorcery scripts.

    This runs 'sorcery update' ('sorcery -u'). Check mode always returns a
    positive change value.

    """

    checksum_before = None
    checksum_after = None
    changed = False

    if module.check_mode:
        if not module.params['name'] and not module.params['update_cache']:
            module.exit_json(changed=True, msg="would have updated Sorcery")
    else:
        cmd_sorcery = "%s update" % SORCERY['sorcery']

        cksum_before = module.sha1(SORCERY_VERSION_FILE)

        rc, stdout, stderr = exec_command(cmd_sorcery, module)

        if rc != 0:
            module.fail_json(msg="unable to update Sorcery: " + stdout)

        cksum_after = module.sha1(SORCERY_VERSION_FILE)

        if cksum_before != cksum_after:
            changed = True

        if not module.params['name'] and not module.params['update_cache']:
            module.exit_json(changed=changed,
                             msg="successfully updated Sorcery")


def update_codex(module):
    """ Update grimoire collections.

    This runs 'scribe update'. Check mode always returns a positive change
    value.

    """

    params = module.params

    cksums_before = {}
    cksums_after = {}
    changed = False
    fresh = codex_fresh(module)

    if module.check_mode:
        if not params['name']:
            if fresh:
                module.exit_json(changed=False, msg="Codex is already fresh")
            else:
                module.exit_json(changed=True, msg="would have updated Codex")
    elif not fresh or params['name'] and params['state'] == 'latest':
        # SILENT is required as a workaround for query() in libgpg
        cmd_scribe = "SILENT=1 %s update" % SORCERY['scribe']

        cksums_before = codex_cksum(module)

        rc, stdout, stderr = exec_command(cmd_scribe, module)

        if rc != 0:
            module.fail_json(msg="unable to update Codex: " + stdout)

        cksums_after = codex_cksum(module)

        if cksums_before != cksums_after:
            changed = True

        if not params['name']:
            module.exit_json(changed=changed,
                             msg="successfully updated Codex")


def manage_depends(module):
    """ Check for matching dependencies.

    This inspects spell's dependencies with the desired states and returns
    'True' if a recast is needed to match them.

    """

    params = module.params

    if module.check_mode:
        sorcery_depends_orig = os.path.join(SORCERY_STATE, "depends")
        sorcery_depends = os.path.join(SORCERY_STATE, "depends.check")

        try:
            shutil.copy2(sorcery_depends_orig, sorcery_depends)
        except IOError:
            module.fail_json(msg="failed to copy depends.check file")
    else:
        sorcery_depends = os.path.join(SORCERY_STATE, "depends")

    spell = params['name']
    depends = {}
    needs_recast = False

    rex = re.compile(r"^(?P<status>\+?|\-){1}(?P<depend>[a-z0-9]+[a-z0-9_\-\+\.]*(\([A-Z0-9_\-\+\.]+\))*)$")

    for d in params['depends'].split(','):
        match = rex.match(d)

        if not match:
            module.fail_json(msg="wrong depends line for spell '%s'" % spell)

        # normalize status
        status = 'on' if not match.group('status') or match.group('status') \
                 == '+' else 'off'

        depends[match.group('depend')] = status

    # drop providers spec
    depends_list = [s.split('(')[0] for s in depends.keys()]

    cmd_gaze = "%s -q version %s" % (SORCERY['gaze'], ' '.join(depends_list))

    rc, stdout, stderr = exec_command(cmd_gaze, module)

    if rc != 0:
        module.fail_json(msg="wrong dependencies for spell '%s'" % spell)

    rex_spell = re.compile("^%s:" % spell)

    fi = fileinput.input(sorcery_depends, inplace=True)

    try:
        for line in fi:
            if rex_spell.match(line):
                for d in depends:
                    # when local status is 'off' and dependency is provider, use
                    # only provider value
                    d_offset = d.find('(')

                    if d_offset != -1:
                        d_p = re.escape(d[d_offset:])
                    else:
                        d_p = ''

                    # .escape() is needed mostly for the spells like 'libsigc++'
                    rex = re.compile("%s:(?:%s|%s):(?P<lstatus>on|off):optional:" %
                                     (re.escape(spell), re.escape(d), d_p))

                    match = rex.match(line)

                    if match:
                        if match.group('lstatus') == depends[d]:
                            depends[d] = None

                        break
                    else:
                        print line,
            else:
                print line,
    except IOError:
        module.fail_json(msg="I/O error on the depends file")
    finally:
        fi.close()

    depends_new = [v for v in depends.keys() if depends[v]]

    if depends_new:
        try:
            with open(sorcery_depends, 'a') as fl:
                for k in depends_new:
                    fl.write("%s:%s:%s:optional::\n" % (spell, k, depends[k]))
        except IOError:
            module.fail_json(msg="I/O error on the depends file")

        needs_recast = True

    if module.check_mode:
        try:
            os.remove(sorcery_depends)
        except IOError:
            module.fail_json(msg="failed to clean up depends.backup file")

    return needs_recast


def manage_spells(module):
    """ Cast or dispel spells.

    This manages the whole system ('*'), list or a single spell. Command 'cast'
    is used to install or rebuild spells, while 'dispel' takes care of theirs
    removal from the system.

    """

    params = module.params
    sorcery_queue = os.path.join(SORCERY_LOG, "queue/install")

    if params['name'] == '*':
        if params['state'] == 'latest':
            changed = False

            # back up original queue
            try:
                os.rename(sorcery_queue, sorcery_queue + ".backup")
            except IOError:
                module.fail_json(msg="failed to backup the update queue")

            cmd_sorcery = "SILENT=1 %s queue"

            rc, stdout, stderr = exec_command(cmd_sorcery, module)

            if rc != 0:
                module.fail_json(msg="failed to generate the update queue")

            try:
                queue_size = os.stat(sorcery_queue).st_size
            except:
                module.fail_json(msg="failed to read the update queue")

            if queue_size != 0:
                if module.check_mode:
                    try:
                        os.rename(sorcery_queue + ".backup", sorcery_queue)
                    except IOError:
                        module.fail_json(msg="failed to restore the update queue")

                    module.exit_json(changed=True, msg="would have updated the system")

                cmd_cast = "%s --queue" % SORCERY['cast']

                rc, stdout, stderr = exec_command(cmd_cast, module)

                if rc != 0:
                    module.fail_json(msg="failed to update the system")

                changed = True

            if changed:
                module.exit_json(changed=changed, msg="successfully updated the system")
            else:
                module.exit_json(changed=changed, msg="the system is already up to date")
        elif params['state'] == 'rebuild':
            if module.check_mode:
                module.exit_json(changed=True, msg="would have rebuilt the system")

            cmd = "%s rebuild" % SORCERY['sorcery']

            rc, stdout, stderr = exec_command(cmd_gaze, module)

            if rc != 0:
                module.fail_json(msg="failed to rebuild the system: " + stdout)

            module.exit_json(changed=True, msg="successfully rebuilt the system")
        else:
            module.fail_json(msg="unsupported operation on '*' name value")
    else:
        if params['state'] in ('present', 'latest', 'rebuild', 'absent'):
            spells = [s for s in module.params['name'].split(',')]
            # extract versions from the 'gaze' command
            cmd_gaze = "%s -q version %s" % (SORCERY['gaze'], ' '.join(spells))

            rc, stdout, stderr = exec_command(cmd_gaze, module)

            # fail if any of spells cannot be found
            if rc != 0:
                module.fail_json(msg="failed to locate spell(s) in the list (%s)" % \
                                 ', '.join(spells))

            tocast = []
            todispel = []

            rex = re.compile(r"[^|]+\|[^|]+\|(?P<spell>[^|]+)\|(?P<grim_ver>[^|]+)\|(?P<inst_ver>[^$]+)")

            # drop 2-line header and empty trailing line
            for line in stdout.splitlines()[2:-1]:
                match = rex.match(line)

                cast = False

                if params['state'] == 'present':
                    if match.group('inst_ver') == '-':
                        if len(spells) > 1 or manage_depends(module):
                            cast = True
                    elif len(spells) == 1 and manage_depends(module):
                        cast = True
                elif params['state'] == 'latest':
                    if match.group('grim_ver') != match.group('inst_ver'):
                        cast = True
                    elif len(spells) == 1 and manage_depends(module):
                        cast = True
                elif params['state'] == 'rebuild':
                    cast = True
                else:
                    # 'absent'
                    if match.group('inst_ver') != '-':
                        todispel.append(match.group('spell'))

                if cast:
                    tocast.append(match.group('spell'))

            if tocast:
                if module.check_mode:
                    module.exit_json(changed=True, msg="would have cast spell(s)")

                cmd_cast = "%s -c %s" % (SORCERY['cast'], ' '.join(tocast))

                rc, stdout, stderr = exec_command(cmd_cast, module)

                if rc != 0:
                    module.fail_json(msg="failed to cast spell(s): %s" + stdout)

                module.exit_json(changed=True, msg="successfully cast spell(s)")
            elif params['state'] != 'absent':
                module.exit_json(changed=False, msg="spell(s) are already cast")

            if todispel:
                if module.check_mode:
                    module.exit_json(changed=True, msg="would have dispelled spell(s)")

                cmd_dispel = "%s %s" % (SORCERY['dispel'], ' '.join(todispel))

                rc, stdout, stderr = exec_command(cmd_dispel, module)

                if rc != 0:
                    module.fail_json(msg="failed to dispel spell(s): %s" + stdout)

                module.exit_json(changed=True, msg="successfully dispelled spell(s)")
            else:
                module.exit_json(changed=False, msg="spell(s) are already dispelled")


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(default=None, aliases=['spell']),
            state = dict(default='present', choices=['present', 'latest',
                         'absent', 'cast', 'dispelled', 'rebuild']),
            depends = dict(default=None),
            update = dict(default=False, choices=BOOLEANS, type='bool'),
            update_cache = dict(default=False, aliases=['update_codex'],
                                choices=BOOLEANS, type='bool'),
            cache_valid_time = dict(default=0, type='int')
        ),
        required_one_of = [['name', 'update', 'update_cache']],
        supports_check_mode = True
    )

    if os.geteuid() != 0:
        module.fail_json(msg="sudo/become is required for this operation")

    for c, p in SORCERY.iteritems():
        if not os.path.exists(p):
            module.fail_json(msg="cannot find %s executable at %s" % (c, p))

    params = module.params

    # normalize 'state' parameter
    if params['state'] in ('present', 'cast'):
        params['state'] = 'present'
    elif params['state'] in ('absent', 'dispelled'):
        params['state'] = 'absent'

    if params['update']:
        update_sorcery(module)

    if params['update_cache'] or params['state'] == 'latest':
        update_codex(module)

    if params['name']:
        manage_spells(module)


# import module snippets
from ansible.module_utils.basic import *

main()
