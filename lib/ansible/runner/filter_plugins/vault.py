# (c) 2013, Jan-Piet Mens <jpmens()gmail.com>
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

import os.path
from ansible import errors
from ansible import constants
import base64
HAVE_VAULT=1
try:
    import keyczar.readers
    import keyczar.keys
except ImportError:
    HAVE_VAULT=None

def vault(*a, **kw):
    ''' Decrypt the base64-encded value in `a' using the vault
        Supported keywords:
        keystore=       path to key store
        outfile=        path into which to write output (e.g. binary data)
                        in this case, the template returns an empty string ""
                        unless return= is set
        return=         String which is to be printed instead-of default
    '''

    if HAVE_VAULT is None:
        raise errors.AnsibleError("|Vault not available: Keyczar not installed")
    if len(a) < 1:
        raise errors.AnsibleError("|Vault filter expects base64 string and key name")

    instr = str(a[0])        # base64-encoded ciphertext

    keyname = constants.ANSIBLE_VAULT_DEFAULTKEY
    if len(a) == 2:
        keyname = a[1]

    if type(instr) != str or len(instr) < 1:
        raise errors.AnsibleError("|Vault input must be string")
    if type(keyname) != str:
        raise errors.AnsibleError("|Vault keyname must be string")

    keystore = constants.ANSIBLE_VAULT_KEYSTORE
    if 'keystore' in kw:
        keystore = kw['keystore']

    outfile = None
    if 'outfile' in kw:
        outfile = kw['outfile']

    returnval = None
    if 'return' in kw:
        returnval = kw['return']

    keydir = "%s/%s" % (keystore, keyname)

    try:
        filereader = keyczar.readers.FileReader(keydir)
        key = filereader.GetKey(1)
    except keyczar.errors.KeyczarError:
        raise errors.AnsibleError("Vault cannot access keydir %s" % keydir)

    try:
        aeskey = keyczar.keys.AesKey.Read(key)
        ciphertext = base64.b64decode(instr)
        cleartext = aeskey.Decrypt(ciphertext)
    except TypeError:
        raise errors.AnsibleError("Vault cannot decrypt input. Is it base64?")
    except keyczar.errors.InvalidSignatureError:
        raise errors.AnsibleError("Vault cannot decrypt input. Wrong key used?")
    except:
        raise errors.AnsibleError("Vault cannot decrypt input.")

    if outfile is not None:
        try:
            f = open(outfile, 'wb')
        except:
            raise errors.AnsibleError("Vault cannot open output file %s" % outfile)

        f.write(cleartext)
        if returnval is not None:
            return returnval
        return ""

    return cleartext

class FilterModule(object):
    ''' More Ansible core jinja2 filters '''

    def filters(self):
        return {
            # decrypt
            'vault': vault,
        }
