class ModuleDocFragment(object):
    DOCUMENTATION = '''

options:
    nsip:
        description:
            - The ip address of the netscaler appliance where the nitro API calls will be made.
            - "The port can be specified with the colon (:). E.g. 192.168.1.1:555."
        required: True

    nitro_user:
        description:
            - The username with which to authenticate to the netscaler node.
        required: True

    nitro_pass:
        description:
            - The password with which to authenticate to the netscaler node.
        required: True

    nitro_protocol:
        choices: [ 'http', 'https' ]
        default: http
        description:
            - Which protocol to use when accessing the nitro API objects.

    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'

    nitro_timeout:
        description:
            - Time in seconds until a timeout error is thrown when establishing a new session with Netscaler
        default: 310

    operation:
        choices: ['present', 'absent']
        required: True
        description:
            - The operation to perform for the given netscaler module.
            - When present the resource will be created if needed and configured according to the module's parameters.
            - When absent the resource will be deleted from the netscaler node.
'''
