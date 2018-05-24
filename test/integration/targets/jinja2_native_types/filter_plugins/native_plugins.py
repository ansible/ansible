from ansible.module_utils._text import to_text


class FilterModule(object):
    def filters(self):
        return {
            'to_text': to_text,
        }
