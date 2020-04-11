



def driver_options_dffs():
    for key, value in self.parameters.driver_options.items():
        if not (key in net['Options']) or value != net['Options'][key]:
            differences.add('driver_options.%s' % key,
                    parameter=value,
                    active=net['Options'].get(key))


def update_format_ipam_config(net_ipam_configs):

    config = dict()
    # Put network's IPAM config into the same format as module's IPAM config

    for k, v in net_ipam_config.items():
        config[normalize_ipam_config_key(k)] = v

    net_ipam_configs.append(config)

    return net_ipam_configs

def check_if_dicts_equal():
    net_config = dict()

    for net_ipam_config in net_ipam_configs:
        if dicts_are_essentially_equal(ipam_config, net_ipam_config):
            net_config = net_ipam_config
            break
    return net_config

def diff_ipam_config():

    for key, value in ipam_config.items():
        if value is None:
            # due to recursive argument_spec, all keys are always present
            # (but have default value None if not specified)
            continue
        if value != net_config.get(key):
            differences.add('ipam_config[%s].%s' % (idx, key),
                            parameter=value,
                            active=net_config.get(key))

def label_differences():
    for key, value in self.parameters.labels.items():
        if not (key in net['Labels']) or value != net['Labels'][key]:
            differences.add('labels.%s' % key,
                            parameter=value,
                            active=net['Labels'].get(key))
    return differences



def has_different_config(self, net):
        '''
        Evaluates an existing network and returns a tuple containing a boolean
        indicating if the configuration is different and a list of differences.
        :param net: the inspection output for an existing network
        :return: (bool, list)
        '''
        differences = DifferenceTracker()
        if self.parameters.driver and self.parameters.driver != net['Driver']:
            differences.add('driver',
                            parameter=self.parameters.driver,
                            active=net['Driver'])


        '''
        architectural strategy

            if (a && b) {
            X;
            if (c && d) {
                Y;
            }
            else {
                Z;
            }
                }

            to
            if (a && b) {
            X;
            } 
            if (a && b && c && d) {
            Y;
            } 
            if (a && b && !(c && d)) {
             Z;
             }
             https://www.drdobbs.com/architecture-and-design/refactoring-deeply-nested-code/231500074
             re desiging deeply nested code
        '''

        if self.parameters.driver_options and not net.get('Options'):
            differences.add('driver_options',
                                parameter=self.parameters.driver_options,
                                active=net.get('Options'))

        # replaces else
        if self.parameters.driver_options and net.get('Options'):
            '''
            BEFORE EXTRACT METHOD
            for key, value in self.parameters.driver_options.items():
                if not (key in net['Options']) or value != net['Options'][key]:
                    differences.add('driver_options.%s' % key,
                                    parameter=value,
                                    active=net['Options'].get(key))
            '''
            # After extract method
            differences = driver_options_dffs()

'''
architectural strategy

    If (a && b) {
      If (c && d)  {
         Y;
      }

      to
      if(a and b and (c and d)):
          y;
'''
        '''
        BEFORE
        if self.parameters.ipam_driver:
            if not net.get('IPAM') or net['IPAM']['Driver'] != self.parameters.ipam_driver:
                differences.add('ipam_driver',
                                parameter=self.parameters.ipam_driver,
                                active=net.get('IPAM'))

        '''

        # AFTER

        if self.parameters.ipam_driver and (not net.get('IPAM') or net['IPAM']['Driver'] != self.parameters.ipam_driver):
            differences.add('ipam_driver',
                            parameter=self.parameters.ipam_driver,
                            active=net.get('IPAM'))


                '''
                architectural strategy

                    If (a && b) {
                        X;
                      If (c && d)  {
                         Y;
                      }
                     Z;
                        }
                    to
                    if (a && b) {
                          X;
                        }
                        if (a && b && c && d) {
                          Y;
                        }
                        if (a && b) {
                          Z;
                        }
                     https://www.drdobbs.com/architecture-and-design/refactoring-deeply-nested-code/231500074
                     re desiging deeply nested code
                '''

        if self.parameters.ipam_driver_options is not None:
            ipam_driver_options = net['IPAM'].get('Options') or {}

        if self.parameters.ipam_driver_options is not None and ipam_driver_options != self.parameters.ipam_driver_options:
            differences.add('ipam_driver_options',
                                parameter=self.parameters.ipam_driver_options,
                                active=ipam_driver_options)

        if self.parameters.ipam_config is not None and self.parameters.ipam_config and (not net.get('IPAM') or not net['IPAM']['Config']) :
            differences.add('ipam_config',
                            parameter=self.parameters.ipam_config,
                            active=net.get('IPAM', {}).get('Config'))



        if self.parameters.ipam_config is not None and self.parameters.ipam_config and not (not net.get('IPAM') or not net['IPAM']['Config']) :
            # Put network's IPAM config into the same format as module's IPAM config
            net_ipam_configs = []

            '''
            BEFORE extract method
            for net_ipam_config in net['IPAM']['Config']:
                config = dict()
                for k, v in net_ipam_config.items():
                    config[normalize_ipam_config_key(k)] = v
                net_ipam_configs.append(config)
            '''
            # AFTER EXTRACT METHOD

            for net_ipam_config in net['IPAM']['Config']:
                net_ipam_configs = update_format_ipam_config(net_ipam_configs):


            # Compare lists of dicts as sets of dicts
            for idx, ipam_config in enumerate(self.parameters.ipam_config):
                '''
                net_config = dict()

                for net_ipam_config in net_ipam_configs:
                    if dicts_are_essentially_equal(ipam_config, net_ipam_config):
                        net_config = net_ipam_config
                        break
                '''

                net_config = check_if_dicts_equal()

    '''
    BEFORE EXTRACT METHOD
                for key, value in ipam_config.items():
                    if value is None:
                        # due to recursive argument_spec, all keys are always present
                        # (but have default value None if not specified)
                        continue
                    if value != net_config.get(key):
                        differences.add('ipam_config[%s].%s' % (idx, key),
                                        parameter=value,
                                        active=net_config.get(key))
    '''

    # after extract method

                differences = diff_ipam_config()


        if self.parameters.enable_ipv6 is not None and self.parameters.enable_ipv6 != net.get('EnableIPv6', False):
            differences.add('enable_ipv6',
                            parameter=self.parameters.enable_ipv6,
                            active=net.get('EnableIPv6', False))

        if self.parameters.internal is not None and self.parameters.internal != net.get('Internal', False):
            differences.add('internal',
                            parameter=self.parameters.internal,
                            active=net.get('Internal'))

        if self.parameters.scope is not None and self.parameters.scope != net.get('Scope'):
            differences.add('scope',
                            parameter=self.parameters.scope,
                            active=net.get('Scope'))

        if self.parameters.attachable is not None and self.parameters.attachable != net.get('Attachable', False):
            differences.add('attachable',
                            parameter=self.parameters.attachable,
                            active=net.get('Attachable'))

        '''
                     if (a && b) {
                X;
                if (c && d) {
                    Y;
                }
                else {
                    Z;
                }
            }

            if (a && b) {
                X;
            } 
            if (a && b && c && d) {
                Y;
            } 
            if (a && b && !(c && d)) {
                 Z;
            }
        '''
        if self.parameters.labels and not net.get('Labels') :
            differences.add('labels',
                            parameter=self.parameters.labels,
                            active=net.get('Labels'))

        if self.parameters.labels and net.get('Labels') :
        '''
         BEFORE EXTRACT METHOD

            for key, value in self.parameters.labels.items():
                if not (key in net['Labels']) or value != net['Labels'][key]:
                    differences.add('labels.%s' % key,
                                    parameter=value,
                                    active=net['Labels'].get(key))
        '''
        # AFTER EXTRACT METHOD

            differences = label_differences()


        return not differences.empty, differences
