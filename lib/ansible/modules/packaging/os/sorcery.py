#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015-2016, Vlad Glagolev <scm@vaygr.net>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sorcery
short_description: Package manager for Source Mage GNU/Linux
description:
    - Manages "spells" on Source Mage GNU/Linux using I(sorcery) toolchain
author: "Vlad Glagolev (@vaygr)"
version_added: "2.3"
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
            - special value '*' in conjunction with states C(latest) or
              C(rebuild) will update or rebuild the whole system respectively
        aliases: ["spell"]

    state:
        description:
            - Whether to cast, dispel or rebuild a package
            - state C(cast) is an equivalent of C(present), not C(latest)
            - state C(latest) always triggers C(update_cache=yes)
            - state C(rebuild) implies cast of all specified spells, not only
              those existed before
        choices: ["present", "latest", "absent", "cast", "dispelled", "rebuild"]
        default: "present"

    depends:
        description:
            - Comma-separated list of _optional_ dependencies to build a spell
              (or make sure it is built) with; use +/- in front of dependency
              to turn it on/off ('+' is optional though)
            - this option is ignored if C(name) parameter is equal to '*' or
              contains more than one spell
            - providers must be supplied in the form recognized by Sorcery, e.g.
              'openssl(SSL)'

    update:
        description:
            - Whether or not to update sorcery scripts at the very first stage
        type: bool
        default: 'no'

    update_cache:
        description:
            - Whether or not to update grimoire collection before casting spells
        type: bool
        default: 'no'
        aliases: ["update_codex"]

    cache_valid_time:
        description:
            - Time in seconds to invalidate grimoire collection on update
            - especially useful for SCM and rsync grimoires
            - makes sense only in pair with C(update_cache)
'''


EXAMPLES = '''
# Make sure spell 'foo' is installed
- sorcery:
    spell: foo
    state: present

# Make sure spells 'foo', 'bar' and 'baz' are removed
- sorcery:
    spell: foo,bar,baz
    state: absent

# Make sure spell 'foo' with dependencies 'bar' and 'baz' is installed
- sorcery:
    spell: foo
    depends: bar,baz
    state: present

# Make sure spell 'foo' with 'bar' and without 'baz' dependencies is installed
- sorcery:
    spell: foo
    depends: +bar,-baz
    state: present

# Make sure spell 'foo' with libressl (providing SSL) dependency is installed
- sorcery:
    spell: foo
    depends: libressl(SSL)
    state: present

# Playbook: make sure spells with/without required dependencies (if any) are installed
- sorcery:
    name: "{{ item.spell }}"
    depends: "{{ item.depends | default(None) }}"
    state: present
  loop:
    - { spell: 'vifm', depends: '+file,-gtk+2' }
    - { spell: 'fwknop', depends: 'gpgme' }
    - { spell: 'pv,tnftp,tor' }

# Install the latest version of spell 'foo' using regular glossary
- sorcery:
    name: foo
    state: latest

# Rebuild spell 'foo'
- sorcery:
    spell: foo
    state: rebuild

# Rebuild the whole system, but update Sorcery and Codex first
- sorcery:
    spell: '*'
    state: rebuild
    update: yes
    update_cache: yes

# Refresh the grimoire collection if it's 1 day old using native sorcerous alias
- sorcery:
    update_codex: yes
    cache_valid_time: 86400

# Update only Sorcery itself
- sorcery:
    update: yes
'''


RETURN = '''
'''


import datetime
import fileinput
import os
import re
import shutil
import sys


# auto-filled at module init
SORCERY = {
    'sorcery': None,
    'scribe': None,
    'cast': None,
    'dispel': None,
    'gaze': None
}

SORCERY_LOG_DIR = "/var/log/sorcery"
SORCERY_STATE_DIR = "/var/state/sorcery"


def get_sorcery_ver(module):
    """ Get Sorcery version. """

    cmd_sorcery = "%s --version" % SORCERY['sorcery']

    rc, stdout, stderr = module.run_command(cmd_sorcery)

    if rc != 0 or not stdout:
        module.fail_json(msg="unable to get Sorcery version")

    return stdout.strip()


def codex_fresh(codex, module):
    """ Check if grimoire collection is fresh enough. """

    if not module.params['cache_valid_time']:
        return False

    timedelta = datetime.timedelta(seconds=module.params['cache_valid_time'])

    for grimoire in codex:
        lastupdate_path = os.path.join(SORCERY_STATE_DIR,
                                       grimoire + ".lastupdate")

        try:
            mtime = os.stat(lastupdate_path).st_mtime
        except Exception:
            return False

        lastupdate_ts = datetime.datetime.fromtimestamp(mtime)

        # if any grimoire is not fresh, we invalidate the Codex
        if lastupdate_ts + timedelta < datetime.datetime.now():
            return False

    return True


def codex_list(module):
    """ List valid grimoire collection. """

    codex = {}

    cmd_scribe = "%s index" % SORCERY['scribe']

    rc, stdout, stderr = module.run_command(cmd_scribe)

    if rc != 0:
        module.fail_json(msg="unable to list grimoire collection, fix your Codex")

    rex = re.compile(r"^\s*\[\d+\] : (?P<grim>[\w\-+.]+) : [\w\-+./]+(?: : (?P<ver>[\w\-+.]+))?\s*$")

    # drop 4-line header and empty trailing line
    for line in stdout.splitlines()[4:-1]:
        match = rex.match(line)

        if match:
            codex[match.group('grim')] = match.group('ver')

    if not codex:
        module.fail_json(msg="no grimoires to operate on; add at least one")

    return codex


def update_sorcery(module):
    """ Update sorcery scripts.

    This runs 'sorcery update' ('sorcery -u'). Check mode always returns a
    positive change value.

    """

    changed = False

    if module.check_mode:
        if not module.params['name'] and not module.params['update_cache']:
            module.exit_json(changed=True, msg="would have updated Sorcery")
    else:
        sorcery_ver = get_sorcery_ver(module)

        cmd_sorcery = "%s update" % SORCERY['sorcery']

        rc, stdout, stderr = module.run_command(cmd_sorcery)

        if rc != 0:
            module.fail_json(msg="unable to update Sorcery: " + stdout)

        if sorcery_ver != get_sorcery_ver(module):
            changed = True

        if not module.params['name'] and not module.params['update_cache']:
            module.exit_json(changed=changed,
                             msg="successfully updated Sorcery")


def update_codex(module):
    """ Update grimoire collections.

    This runs 'scribe update'. Check mode always returns a positive change
    value when 'cache_valid_time' is used.

    """

    params = module.params

    changed = False

    codex = codex_list(module)
    fresh = codex_fresh(codex, module)

    if module.check_mode:
        if not params['name']:
            if not fresh:
                changed = True

            module.exit_json(changed=changed, msg="would have updated Codex")
    elif not fresh or params['name'] and params['state'] == 'latest':
        # SILENT is required as a workaround for query() in libgpg
        module.run_command_environ_update.update(dict(SILENT='1'))

        cmd_scribe = "%s update" % SORCERY['scribe']

        rc, stdout, stderr = module.run_command(cmd_scribe)

        if rc != 0:
            module.fail_json(msg="unable to update Codex: " + stdout)

        if codex != codex_list(module):
            changed = True

        if not params['name']:
            module.exit_json(changed=changed,
                             msg="successfully updated Codex")


def match_depends(module):
    """ Check for matching dependencies.

    This inspects spell's dependencies with the desired states and returns
    'False' if a recast is needed to match them. It also adds required lines
    to the system-wide depends file for proper recast procedure.

    """

    params = module.params
    spells = params['name']

    depends = {}

    depends_ok = True

    if len(spells) > 1 or not params['depends']:
        return depends_ok

    spell = spells[0]

    if module.check_mode:
        sorcery_depends_orig = os.path.join(SORCERY_STATE_DIR, "depends")
        sorcery_depends = os.path.join(SORCERY_STATE_DIR, "depends.check")

        try:
            shutil.copy2(sorcery_depends_orig, sorcery_depends)
        except IOError:
            module.fail_json(msg="failed to copy depends.check file")
    else:
        sorcery_depends = os.path.join(SORCERY_STATE_DIR, "depends")

    rex = re.compile(r"^(?P<status>\+?|\-){1}(?P<depend>[a-z0-9]+[a-z0-9_\-\+\.]*(\([A-Z0-9_\-\+\.]+\))*)$")

    for d in params['depends'].split(','):
        match = rex.match(d)

        if not match:
            module.fail_json(msg="wrong depends line for spell '%s'" % spell)

        # normalize status
        if not match.group('status') or match.group('status') == '+':
            status = 'on'
        else:
            status = 'off'

        depends[match.group('depend')] = status

    # drop providers spec
    depends_list = [s.split('(')[0] for s in depends]

    cmd_gaze = "%s -q version %s" % (SORCERY['gaze'], ' '.join(depends_list))

    rc, stdout, stderr = module.run_command(cmd_gaze)

    if rc != 0:
        module.fail_json(msg="wrong dependencies for spell '%s'" % spell)

    fi = fileinput.input(sorcery_depends, inplace=True)

    try:
        try:
            for line in fi:
                if line.startswith(spell + ':'):
                    match = None

                    for d in depends:
                        # when local status is 'off' and dependency is provider,
                        # use only provider value
                        d_offset = d.find('(')

                        if d_offset == -1:
                            d_p = ''
                        else:
                            d_p = re.escape(d[d_offset:])

                        # .escape() is needed mostly for the spells like 'libsigc++'
                        rex = re.compile("%s:(?:%s|%s):(?P<lstatus>on|off):optional:" %
                                         (re.escape(spell), re.escape(d), d_p))

                        match = rex.match(line)

                        # we matched the line "spell:dependency:on|off:optional:"
                        if match:
                            # if we also matched the local status, mark dependency
                            # as empty and put it back into depends file
                            if match.group('lstatus') == depends[d]:
                                depends[d] = None

                                sys.stdout.write(line)

                            # status is not that we need, so keep this dependency
                            # in the list for further reverse switching;
                            # stop and process the next line in both cases
                            break

                    if not match:
                        sys.stdout.write(line)
                else:
                    sys.stdout.write(line)
        except IOError:
            module.fail_json(msg="I/O error on the depends file")
    finally:
        fi.close()

    depends_new = [v for v in depends if depends[v]]

    if depends_new:
        try:
            try:
                fl = open(sorcery_depends, 'a')

                for k in depends_new:
                    fl.write("%s:%s:%s:optional::\n" % (spell, k, depends[k]))
            except IOError:
                module.fail_json(msg="I/O error on the depends file")
        finally:
            fl.close()

        depends_ok = False

    if module.check_mode:
        try:
            os.remove(sorcery_depends)
        except IOError:
            module.fail_json(msg="failed to clean up depends.backup file")

    return depends_ok


def manage_spells(module):
    """ Cast or dispel spells.

    This manages the whole system ('*'), list or a single spell. Command 'cast'
    is used to install or rebuild spells, while 'dispel' takes care of theirs
    removal from the system.

    """

    params = module.params
    spells = params['name']

    sorcery_queue = os.path.join(SORCERY_LOG_DIR, "queue/install")

    if spells == '*':
        if params['state'] == 'latest':
            # back up original queue
            try:
                os.rename(sorcery_queue, sorcery_queue + ".backup")
            except IOError:
                module.fail_json(msg="failed to backup the update queue")

            # see update_codex()
            module.run_command_environ_update.update(dict(SILENT='1'))

            cmd_sorcery = "%s queue"

            rc, stdout, stderr = module.run_command(cmd_sorcery)

            if rc != 0:
                module.fail_json(msg="failed to generate the update queue")

            try:
                queue_size = os.stat(sorcery_queue).st_size
            except Exception:
                module.fail_json(msg="failed to read the update queue")

            if queue_size != 0:
                if module.check_mode:
                    try:
                        os.rename(sorcery_queue + ".backup", sorcery_queue)
                    except IOError:
                        module.fail_json(msg="failed to restore the update queue")

                    module.exit_json(changed=True, msg="would have updated the system")

                cmd_cast = "%s --queue" % SORCERY['cast']

                rc, stdout, stderr = module.run_command(cmd_cast)

                if rc != 0:
                    module.fail_json(msg="failed to update the system")

                module.exit_json(changed=True, msg="successfully updated the system")
            else:
                module.exit_json(changed=False, msg="the system is already up to date")
        elif params['state'] == 'rebuild':
            if module.check_mode:
                module.exit_json(changed=True, msg="would have rebuilt the system")

            cmd_sorcery = "%s rebuild" % SORCERY['sorcery']

            rc, stdout, stderr = module.run_command(cmd_sorcery)

            if rc != 0:
                module.fail_json(msg="failed to rebuild the system: " + stdout)

            module.exit_json(changed=True, msg="successfully rebuilt the system")
        else:
            module.fail_json(msg="unsupported operation on '*' name value")
    else:
        if params['state'] in ('present', 'latest', 'rebuild', 'absent'):
            # extract versions from the 'gaze' command
            cmd_gaze = "%s -q version %s" % (SORCERY['gaze'], ' '.join(spells))

            rc, stdout, stderr = module.run_command(cmd_gaze)

            # fail if any of spells cannot be found
            if rc != 0:
                module.fail_json(msg="failed to locate spell(s) in the list (%s)" %
                                 ', '.join(spells))

            cast_queue = []
            dispel_queue = []

            rex = re.compile(r"[^|]+\|[^|]+\|(?P<spell>[^|]+)\|(?P<grim_ver>[^|]+)\|(?P<inst_ver>[^$]+)")

            # drop 2-line header and empty trailing line
            for line in stdout.splitlines()[2:-1]:
                match = rex.match(line)

                cast = False

                if params['state'] == 'present':
                    # spell is not installed..
                    if match.group('inst_ver') == '-':
                        # ..so set up depends reqs for it
                        match_depends(module)

                        cast = True
                    # spell is installed..
                    else:
                        # ..but does not conform depends reqs
                        if not match_depends(module):
                            cast = True
                elif params['state'] == 'latest':
                    # grimoire and installed versions do not match..
                    if match.group('grim_ver') != match.group('inst_ver'):
                        # ..so check for depends reqs first and set them up
                        match_depends(module)

                        cast = True
                    # grimoire and installed versions match..
                    else:
                        # ..but the spell does not conform depends reqs
                        if not match_depends(module):
                            cast = True
                elif params['state'] == 'rebuild':
                    cast = True
                # 'absent'
                else:
                    if match.group('inst_ver') != '-':
                        dispel_queue.append(match.group('spell'))

                if cast:
                    cast_queue.append(match.group('spell'))

            if cast_queue:
                if module.check_mode:
                    module.exit_json(changed=True, msg="would have cast spell(s)")

                cmd_cast = "%s -c %s" % (SORCERY['cast'], ' '.join(cast_queue))

                rc, stdout, stderr = module.run_command(cmd_cast)

                if rc != 0:
                    module.fail_json(msg="failed to cast spell(s): %s" + stdout)

                module.exit_json(changed=True, msg="successfully cast spell(s)")
            elif params['state'] != 'absent':
                module.exit_json(changed=False, msg="spell(s) are already cast")

            if dispel_queue:
                if module.check_mode:
                    module.exit_json(changed=True, msg="would have dispelled spell(s)")

                cmd_dispel = "%s %s" % (SORCERY['dispel'], ' '.join(dispel_queue))

                rc, stdout, stderr = module.run_command(cmd_dispel)

                if rc != 0:
                    module.fail_json(msg="failed to dispel spell(s): %s" + stdout)

                module.exit_json(changed=True, msg="successfully dispelled spell(s)")
            else:
                module.exit_json(changed=False, msg="spell(s) are already dispelled")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, aliases=['spell'], type='list'),
            state=dict(default='present', choices=['present', 'latest',
                                                   'absent', 'cast', 'dispelled', 'rebuild']),
            depends=dict(default=None),
            update=dict(default=False, type='bool'),
            update_cache=dict(default=False, aliases=['update_codex'], type='bool'),
            cache_valid_time=dict(default=0, type='int')
        ),
        required_one_of=[['name', 'update', 'update_cache']],
        supports_check_mode=True
    )

    if os.geteuid() != 0:
        module.fail_json(msg="root privileges are required for this operation")

    for c in SORCERY:
        SORCERY[c] = module.get_bin_path(c, True)

    # prepare environment: run sorcery commands without asking questions
    module.run_command_environ_update = dict(PROMPT_DELAY='0', VOYEUR='0')

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
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
