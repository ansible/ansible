# -*- coding: utf-8 -*-

# Copyright: (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
notes:
  - "If a new enough version of the C(cryptography) library
     is available (see Requirements for details), it will be used
     instead of the C(openssl) binary. This can be explicitly disabled
     or enabled with the C(select_crypto_backend) option. Note that using
     the C(openssl) binary will be slower and less secure, as private key
     contents always have to be stored on disk (see
     C(account_key_content))."
  - "Although the defaults are chosen so that the module can be used with
     the L(Let's Encrypt,https://letsencrypt.org/) CA, the module can in
     principle be used with any CA providing an ACME endpoint, such as
     L(Buypass Go SSL,https://www.buypass.com/ssl/products/acme)."
requirements:
  - python >= 2.6
  - either openssl or L(cryptography,https://cryptography.io/) >= 1.5
options:
  account_key_src:
    description:
      - "Path to a file containing the ACME account RSA or Elliptic Curve
         key."
      - "RSA keys can be created with C(openssl genrsa ...). Elliptic curve keys can
         be created with C(openssl ecparam -genkey ...). Any other tool creating
         private keys in PEM format can be used as well."
      - "Mutually exclusive with C(account_key_content)."
      - "Required if C(account_key_content) is not used."
    type: path
    aliases: [ account_key ]
  account_key_content:
    description:
      - "Content of the ACME account RSA or Elliptic Curve key."
      - "Mutually exclusive with C(account_key_src)."
      - "Required if C(account_key_src) is not used."
      - "I(Warning): the content will be written into a temporary file, which will
         be deleted by Ansible when the module completes. Since this is an
         important private key — it can be used to change the account key,
         or to revoke your certificates without knowing their private keys
         —, this might not be acceptable."
      - "In case C(cryptography) is used, the content is not written into a
         temporary file. It can still happen that it is written to disk by
         Ansible in the process of moving the module with its argument to
         the node where it is executed."
    type: str
    version_added: "2.5"
  account_uri:
    description:
      - "If specified, assumes that the account URI is as given. If the
         account key does not match this account, or an account with this
         URI does not exist, the module fails."
    type: str
    version_added: "2.7"
  acme_version:
    description:
      - "The ACME version of the endpoint."
      - "Must be 1 for the classic Let's Encrypt and Buypass ACME endpoints,
         or 2 for standardized ACME v2 endpoints."
    type: int
    default: 1
    choices: [ 1, 2 ]
    version_added: "2.5"
  acme_directory:
    description:
      - "The ACME directory to use. This is the entry point URL to access
         CA server API."
      - "For safety reasons the default is set to the Let's Encrypt staging
         server (for the ACME v1 protocol). This will create technically correct,
         but untrusted certificates."
      - "For Let's Encrypt, all staging endpoints can be found here:
         U(https://letsencrypt.org/docs/staging-environment/). For Buypass, all
         endpoints can be found here:
         U(https://community.buypass.com/t/63d4ay/buypass-go-ssl-endpoints)"
      - "For Let's Encrypt, the production directory URL for ACME v1 is
         U(https://acme-v01.api.letsencrypt.org/directory), and the production
         directory URL for ACME v2 is U(https://acme-v02.api.letsencrypt.org/directory)."
      - "For Buypass, the production directory URL for ACME v2 and v1 is
         U(https://api.buypass.com/acme/directory)."
      - "I(Warning): So far, the module has only been tested against Let's Encrypt
         (staging and production), Buypass (staging and production), and
         L(Pebble testing server,https://github.com/letsencrypt/Pebble)."
    type: str
    default: https://acme-staging.api.letsencrypt.org/directory
  validate_certs:
    description:
      - Whether calls to the ACME directory will validate TLS certificates.
      - "I(Warning): Should I(only ever) be set to C(no) for testing purposes,
         for example when testing against a local Pebble server."
    type: bool
    default: yes
    version_added: "2.5"
  select_crypto_backend:
    description:
      - Determines which crypto backend to use.
      - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to
        C(openssl).
      - If set to C(openssl), will try to use the C(openssl) binary.
      - If set to C(cryptography), will try to use the
        L(cryptography,https://cryptography.io/) library.
    type: str
    default: auto
    choices: [ auto, cryptography, openssl ]
    version_added: "2.7"
'''
