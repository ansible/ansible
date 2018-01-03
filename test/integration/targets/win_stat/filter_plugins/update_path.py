class FilterModule(object):
    def filters(self):
        return {
            'update_stat': self.update_stat
        }

    def update_stat(self, dict_value, repl_dict):
        new_dict = dict_value.copy()
        for key, value in repl_dict.items():
            new_dict['stat'][key] = value
        return new_dict
