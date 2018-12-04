# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2013, Javier Candeira <javier@candeira.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: password
    version_added: "1.1"
    author:
      - Daniel Hokka Zakrisson <daniel@hozac.com>
      - Javier Candeira <javier@candeira.com>
      - Maykel Moya <mmoya@speedyrails.com>
    short_description: retrieve or generate a random password, stored in a file
    description:
      - Generates a random plaintext password and stores it in a file at a given filepath.
      - If the file exists previously, it will retrieve its contents, behaving just like with_file.
      - 'Usage of variables like C("{{ inventory_hostname }}") in the filepath can be used to set up random passwords per host,
        which simplifies password management in C("host_vars") variables.'
      - A special case is using /dev/null as a path. The password lookup will generate a new random password each time,
        but will not write it to /dev/null. This can be used when you need a password without storing it on the controller.
    options:
      _terms:
         description:
           - path to the file that stores/will store the passwords
         required: True
      encrypt:
        description:
           - Which hash scheme to encrypt the returning password, should be one hash scheme from C(passlib.hash).
           - If not provided, the password will be returned in plain text.
           - Note that the password is always stored as plain text, only the returning password is encrypted.
           - Encrypt also forces saving the salt value for idempotence.
           - Note that before 2.6 this option was incorrectly labeled as a boolean for a long time.
        default: None
      chars:
        version_added: "1.4"
        description:
          - Define comma separated list of names that compose a custom character set in the generated passwords.
          - 'By default generated passwords contain a random mix of upper and lowercase ASCII letters, the numbers 0-9 and punctuation (". , : - _").'
          - "They can be either parts of Python's string module attributes (ascii_letters,digits, etc) or are used literally ( :, -)."
          - "To enter comma use two commas ',,' somewhere - preferably at the end. Quotes and double quotes are not supported."
        type: string
      length:
        description: The length of the generated password.
        default: 20
        type: integer
    notes:
      - A great alternative to the password lookup plugin,
        if you don't need to generate random passwords on a per-host basis,
        would be to use Vault in playbooks.
        Read the documentation there and consider using it first,
        it will be more desirable for most applications.
      - If the file already exists, no data will be written to it.
        If the file has contents, those contents will be read in as the password.
        Empty files cause the password to return as an empty string.
      - 'As all lookups, this runs on the Ansible host as the user running the playbook, and "become" does not apply,
        the target file must be readable by the playbook user, or, if it does not exist,
        the playbook user must have sufficient privileges to create it.
        (So, for example, attempts to write into areas such as /etc will fail unless the entire playbook is being run as root).'
"""

EXAMPLES = """
- name: create a mysql user with a random password
  mysql_user:
    name: "{{ client }}"
    password: "{{ lookup('password', 'credentials/' + client + '/' + tier + '/' + role + '/mysqlpassword length=15') }}"
    priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"

- name: create a mysql user with a random password using only ascii letters
  mysql_user:
    name: "{{ client }}"
    password: "{{ lookup('password', '/tmp/passwordfile chars=ascii_letters') }}"
    priv: '{{ client }}_{{ tier }}_{{ role }}.*:ALL'

- name: create a mysql user with a random password using only digits
  mysql_user:
    name: "{{ client }}"
    password: "{{ lookup('password', '/tmp/passwordfile chars=digits') }}"
    priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"

- name: create a mysql user with a random password using many different char sets
  mysql_user:
    name: "{{ client }}"
    password: "{{ lookup('password', '/tmp/passwordfile chars=ascii_letters,digits,hexdigits,punctuation') }}"
    priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"
"""

RETURN = """
_raw:
  description:
    - a password
"""

import os
import string
import time
import shutil
import hashlib

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.utils.encrypt import do_encrypt, random_password, random_salt
from ansible.utils.path import makedirs_safe


DEFAULT_LENGTH = 20
VALID_PARAMS = frozenset(('length', 'encrypt', 'chars'))


def _parse_parameters(term):
    """Hacky parsing of params

    See https://github.com/ansible/ansible-modules-core/issues/1968#issuecomment-136842156
    and the first_found lookup For how we want to fix this later
    """
    first_split = term.split(' ', 1)
    if len(first_split) <= 1:
        # Only a single argument given, therefore it's a path
        relpath = term
        params = dict()
    else:
        relpath = first_split[0]
        params = parse_kv(first_split[1])
        if '_raw_params' in params:
            # Spaces in the path?
            relpath = u' '.join((relpath, params['_raw_params']))
            del params['_raw_params']

            # Check that we parsed the params correctly
            if not term.startswith(relpath):
                # Likely, the user had a non parameter following a parameter.
                # Reject this as a user typo
                raise AnsibleError('Unrecognized value after key=value parameters given to password lookup')
        # No _raw_params means we already found the complete path when
        # we split it initially

    # Check for invalid parameters.  Probably a user typo
    invalid_params = frozenset(params.keys()).difference(VALID_PARAMS)
    if invalid_params:
        raise AnsibleError('Unrecognized parameter(s) given to password lookup: %s' % ', '.join(invalid_params))

    # Set defaults
    params['length'] = int(params.get('length', DEFAULT_LENGTH))
    params['encrypt'] = params.get('encrypt', None)

    params['chars'] = params.get('chars', None)
    if params['chars']:
        tmp_chars = []
        if u',,' in params['chars']:
            tmp_chars.append(u',')
        tmp_chars.extend(c for c in params['chars'].replace(u',,', u',').split(u',') if c)
        params['chars'] = tmp_chars
    else:
        # Default chars for password
        params['chars'] = [u'ascii_letters', u'digits', u".,:-_"]

    return relpath, params


def _read_password_file(b_path):
    """Read the contents of a password file and return it
    :arg b_path: A byte string containing the path to the password file
    :returns: a text string containing the contents of the password file or
        None if no password file was present.
    """
    content = None

    if os.path.exists(b_path):
        with open(b_path, 'rb') as f:
            b_content = f.read().rstrip()
        content = to_text(b_content, errors='surrogate_or_strict')

    return content


def _gen_candidate_chars(characters):
    '''Generate a string containing all valid chars as defined by ``characters``

    :arg characters: A list of character specs. The character specs are
        shorthand names for sets of characters like 'digits', 'ascii_letters',
        or 'punctuation' or a string to be included verbatim.

    The values of each char spec can be:

    * a name of an attribute in the 'strings' module ('digits' for example).
      The value of the attribute will be added to the candidate chars.
    * a string of characters. If the string isn't an attribute in 'string'
      module, the string will be directly added to the candidate chars.

    For example::

        characters=['digits', '?|']``

    will match ``string.digits`` and add all ascii digits.  ``'?|'`` will add
    the question mark and pipe characters directly. Return will be the string::

        u'0123456789?|'
    '''
    chars = []
    for chars_spec in characters:
        # getattr from string expands things like "ascii_letters" and "digits"
        # into a set of characters.
        chars.append(to_text(getattr(string, to_native(chars_spec), chars_spec),
                     errors='strict'))
    chars = u''.join(chars).replace(u'"', u'').replace(u"'", u'')
    return chars


def _parse_content(content):
    '''parse our password data format into password and salt

    :arg content: The data read from the file
    :returns: password and salt
    '''
    password = content
    salt = None

    salt_slug = u' salt='
    try:
        sep = content.rindex(salt_slug)
    except ValueError:
        # No salt
        pass
    else:
        salt = password[sep + len(salt_slug):]
        password = content[:sep]

    return password, salt


def _format_content(password, salt, encrypt=None):
    """Format the password and salt for saving
    :arg password: the plaintext password to save
    :arg salt: the salt to use when encrypting a password
    :arg encrypt: Which method the user requests that this password is encrypted.
        Note that the password is saved in clear.  Encrypt just tells us if we
        must save the salt value for idempotence.  Defaults to None.
    :returns: a text string containing the formatted information

    .. warning:: Passwords are saved in clear.  This is because the playbooks
        expect to get cleartext passwords from this lookup.
    """
    if not encrypt and not salt:
        return password

    # At this point, the calling code should have assured us that there is a salt value.
    if not salt:
        raise AnsibleAssertionError('_format_content was called with encryption requested but no salt value')

    return u'%s salt=%s' % (password, salt)


def _write_password_file(b_path, content):
    b_pathdir = os.path.dirname(b_path)
    makedirs_safe(b_pathdir, mode=0o700)

    with open(b_path, 'wb') as f:
        os.chmod(b_path, 0o600)
        b_content = to_bytes(content, errors='surrogate_or_strict') + b'\n'
        f.write(b_content)


def _get_lock(b_path):
    """Get the lock for writing password file."""
    first_process = False
    b_pathdir = os.path.dirname(b_path)
    lockfile_name = to_bytes("%s.ansible_lockfile" % hashlib.sha1(b_path).hexdigest())
    lockfile = os.path.join(b_pathdir, lockfile_name)
    if not os.path.exists(lockfile) and b_path != to_bytes('/dev/null'):
        try:
            makedirs_safe(b_pathdir, mode=0o700)
            fd = os.open(lockfile, os.O_CREAT | os.O_EXCL)
            os.close(fd)
            first_process = True
        except OSError as e:
            if e.strerror != 'File exists':
                raise

    counter = 0
    # if the lock is got by other process, wait until it's released
    while os.path.exists(lockfile) and not first_process:
        time.sleep(2 ** counter)
        if counter >= 2:
            raise AnsibleError("Password lookup cannot get the lock in 7 seconds, abort..."
                               "This may caused by un-removed lockfile"
                               "you can manually remove it from controller machine at %s and try again" % lockfile)
        counter += 1
    return first_process, lockfile


def _release_lock(lockfile):
    """Release the lock so other processes can read the password file."""
    if os.path.exists(lockfile):
        os.remove(lockfile)


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        ret = []

        for term in terms:
            relpath, params = _parse_parameters(term)
            path = self._loader.path_dwim(relpath)
            b_path = to_bytes(path, errors='surrogate_or_strict')
            chars = _gen_candidate_chars(params['chars'])

            changed = None
            # make sure only one process finishes all the job first
            first_process, lockfile = _get_lock(b_path)

            content = _read_password_file(b_path)

            if content is None or b_path == to_bytes('/dev/null'):
                plaintext_password = random_password(params['length'], chars)
                salt = None
                changed = True
            else:
                plaintext_password, salt = _parse_content(content)

            if params['encrypt'] and not salt:
                changed = True
                salt = random_salt()

            if changed and b_path != to_bytes('/dev/null'):
                content = _format_content(plaintext_password, salt, encrypt=params['encrypt'])
                _write_password_file(b_path, content)

            if first_process:
                # let other processes continue
                _release_lock(lockfile)

            if params['encrypt']:
                password = do_encrypt(plaintext_password, params['encrypt'], salt=salt)
                ret.append(password)
            else:
                ret.append(plaintext_password)

        return ret
