import logging
import json
import requests
import traceback
import time

logger = logging.getLogger(__name__)

# HTTP Response handling
def convert_to_json(body):
    js = ''
    try:
        js = json.loads(body)
    except Exception as e:
        if js is None:
            pass
        else:
            logger.info('>>> Some Error occurred when converting from String to JSON.')
            logger.info('Errors : ', e.args)
    return js

class VPLEX:
    def __init__(self, ip_address, username, password):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.login_credentials = username + '@' + ip_address
        self.shell_prompt = '^.*~>'
        self.cli_prompt = '^.*:/>'
        self.model = self.set_vplex_model()

    # Common Unitilities
    def https_get(self, urlsuffix):
        url = 'https://' + str(self.ip_address) + urlsuffix
        logger.info('Connect to : ' + url)
        try:
            request_body = requests.get(url, auth=(self.username, self.password), verify=False)
        except ValueError:
            logger.error('>>> Error occurred during parsing json. VPLEX returned not a JSON value.')
            traceback.print_exc()
        except:
            logger.error('>>> URLError occurred. Please check the address or suffix you specified.')
            traceback.print_exc()
        else:
            return convert_to_json(body=request_body.text)

    def https_post(self, urlsuffix, data):
        url = 'https://' + str(self.ip_address) + urlsuffix
        logger.info('Connect to : ' + url)
        logger.info('POST Data : ' + data)
        try:
            time.sleep(3)
            request_body = requests.post(url, auth=(self.username, self.password), verify=False, data=data)
        except ValueError:
            logger.error('>>> Error occurred during parsing json. VPLEX returned not a JSON value.')
            traceback.print_exc()
        except:
            logger.error('>>> URLError occurred. Please check the address or suffix you specified.')
            traceback.print_exc()
        else:
            return convert_to_json(body=request_body.text)

    def confirm_vplex_serial_number(self, expect_serial_number):
        logger.info('Checking VPLEX S/N is same as expected or not.')
        actual_serial_number = self.https_get(urlsuffix='/vplex/clusters/cluster-1?top-level-assembly')

        if actual_serial_number['response']['context'][0]['attributes'][0]['value'] == expect_serial_number:
            return True
        else:
            return False
    
    def get_geosynchrony_version(self):
        geosync_version = self.https_post(urlsuffix='/vplex/version', data='{\"args\":\"\"}')['response']['custom-data']
        for line in geosync_version.splitlines():
            if 'Product Version' in line:
                return line.split()[2]
    
    def set_vplex_model(self):
        geosync_version = self.get_geosynchrony_version()
        if geosync_version.split('.')[0] == '6':
            model = 'VS6'
        else:
            model = 'VS2'
        return model

    def drill_down(self, object_name):
        context = self.check_vplex_context(object_name)
        if context == 'local-devices':
            data = '{\"args\":\"--device ' + object_name + '\"}'
        elif context == 'virtual-volumes':
            data = '{\"args\":\"--virtual-volume ' + object_name + '\"}'
        elif context == 'storage-views':
            data = '{\"args\":\"--storage-view ' + object_name + '\"}'
        else:
            data = ''

        uri = '/vplex/drill-down'
        response = self.https_post(urlsuffix=uri, data=data)

        return response

    def show_use_hierarchy(self, object_name):
        context = self.check_vplex_context(object_name)

        if (context == 'local-devices') or (context == 'virtual-volumes'):
            data = '{\"args\":\"--targets /clusters/cluster-1/' + context + '/' + object_name + '\"}'
        elif (context == 'storage-volumes') or (context == 'extents'):
            data = '{\"args\":\"--targets /clusters/cluster-1/storage-elements/' + context + '/' + object_name + '\"}'
        elif context == 'logical-units':
            data = '{\"args\":\"--targets /clusters/cluster-1/storage-elements/storage-arrays/*/' + context + '/' + object_name + '\"}'
        else:
            data = ''
        uri = '/vplex/show-use-hierarchy'
        response = self.https_post(urlsuffix=uri, data=data)

        return response

    # extents
    @staticmethod
    def set_extent_name(volume_name):
        return 'extent_' + volume_name + '_1'
    
    # local-devices
    @staticmethod
    def set_local_device_name(volume_name):
        return 'device_' + volume_name + '_1'

    # virtual-volumes
    @staticmethod
    def set_virtual_volume_name(volume_name):
        return 'device_' + volume_name + '_1_vol'
        
    @staticmethod
    def check_vplex_context(object_name):        
        if (object_name[:7] == 'device_') and (object_name[-6:] == '_1_vol'):
            return 'virtual-volumes'
        elif (object_name[:7] == 'device_') and (object_name[-2:] == '_1'):
            return 'local-devices'
        elif (object_name[:7] == 'extent_') and (object_name[-2:] == '_1'):
            return 'extents'
        elif object_name[:3] == 'VPD':
            return 'logical-units'
        else:
            return 'storage-volumes'

        # Exception handling
        if 'SV_' in object_name:
            return 'storage-views'
        elif '_HBA' in object_name:
            return 'initiator-ports'
        elif (object_name[:1] == 'P') and ('FC' in object_name[-4:]):
            return 'ports'
        else:
            return ''
