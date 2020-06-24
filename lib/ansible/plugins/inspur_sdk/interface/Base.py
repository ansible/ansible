# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: getFruIpmi Class
#
#   @author: zhong
#   @Date:
#=========================================================================
'''
from ansible.plugins.inspur_sdk.util import RegularCheckUtil
from ansible.plugins.inspur_sdk.command import IpmiFunc
import sys
import os
import re
import time
from ansible.plugins.inspur_sdk.interface.IBase import IBase
from ansible.plugins.inspur_sdk.interface.ResEntity import *
rootpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(rootpath, "command"))
sys.path.append(os.path.join(rootpath, "util"))


class Base(IBase):

    # 100+为utool定义
    # 1-9为ipmitool工具定义

    ERR_dict = {
        1: 'Ipmi information get error',
        2: 'Ipmi parameter is null',
        3: 'Ipmi parameter error',
        4: 'Cannot create ipmi link, please check host/username/pasword',
        5: 'Cannot connect to server, please check host/username/pasword',
        6: 'Memory exception',
        7: 'Cannot connect to the server, please check host/username/pasword',
        8: 'incorrect user name or password',
        9: 'user not exist',
        101: 'Not Support',
        102: 'destination must be panel or sol',
        103: 'json loads error',
        104: 'load dll error',
        105: 'nic list cannot be null',
        106: 'support up to 2 nics',
        107: 'illegal task id(0-6, 8)'
    }
    ERR_dict_raw = {
        1: 'data acquisition exception',
        2: 'parameter is null',
        3: 'parameter error',
        4: 'create link exception',
        5: 'internal error',
        6: 'allocated memory exception',
        7: 'network connection failed',
        8: 'incorrect user name or password',
        9: 'user not exist'
    }

    def __init__(self):
        pass

    def getfru(self, client, args):
        fru = IpmiFunc.getAllFruByIpmi(client)
        res = ResultBean()
        if fru:
            if fru.get('code') == 0 and fru.get('data') is not None:
                FRUlist = []
                for product in fru.get('data'):
                    # print(product)
                    #frubean = FruBean()
                    frubean = collections.OrderedDict()
                    if product['fru_id']:
                        frubean["FRUID"] = product['fru_id']
                    else:
                        frubean["FRUID"] = None

                    if product['fru_name']:
                        frubean["FRUName"] = product['fru_name']
                    else:
                        frubean["FRUName"] = None

                    if product['chassis_type']:
                        frubean["ChassisType"] = product['chassis_type']
                    else:
                        frubean["ChassisType"] = None

                    if product['chassis_part_number']:
                        frubean["ChassisPartNumber"] = product['chassis_part_number']
                    else:
                        frubean["ChassisPartNumber"] = None

                    if product['chassis_serial']:
                        frubean["ChassisSerial"] = product['chassis_serial']
                    else:
                        frubean["ChassisSerial"] = None

                    if product['chassis_extra']:
                        if ";" not in product['chassis_extra']:
                            frubean["ChassisExtra"] = product['chassis_extra']
                        else:
                            celist = product['chassis_extra'].split(";")
                            #frubean["ChassisExtra1"] = celist[0]
                            #frubean["ChassisExtra2"] = celist[1]
                            # if len(celist) == 3:
                            #     frubean["ChassisExtra3"] = celist[2]
                            for i in range(len(celist)):
                                frubean["ChassisExtra" + str(i + 1)] = celist[i]

                    if product['board_mfg_date']:
                        frubean["BoardMfgDate"] = product['board_mfg_date']
                    else:
                        frubean["BoardMfgDate"] = None

                    if product['board_mfg']:
                        frubean["BoardMfg"] = product['board_mfg']
                    else:
                        frubean["BoardMfg"] = None

                    if product['board_product']:
                        frubean["BoardProduct"] = product['board_product']
                    else:
                        frubean["BoardProduct"] = None

                    if product['board_serial']:
                        frubean["BoardSerial"] = product['board_serial']
                    else:
                        frubean["BoardSerial"] = None
                    if product['board_part_number']:
                        frubean["BoardPartNumber"] = product['board_part_number']
                    else:
                        frubean["BoardPartNumber"] = None

                    if product['board_extra']:
                        if ";" not in product['board_extra']:
                            frubean["BoardExtra"] = product['board_extra']
                        else:
                            belist = product['board_extra'].split(";")
                            # frubean["BoardExtra1"] = belist[0]
                            # frubean["BoardExtra2"] = belist[1]
                            # if len(belist) == 3:
                            #     frubean["BoardExtra3"] = belist[2]
                            for i in range(len(belist)):
                                frubean["BoardExtra" + str(i + 1)] = belist[i]

                    if product['product_manufacturer']:
                        frubean["ProductManufacturer"] = product['product_manufacturer']
                    else:
                        frubean["ProductManufacturer"] = None

                    if product['product_name']:
                        frubean["ProductName"] = product['product_name']
                    else:
                        frubean["ProductName"] = None

                    if product['product_part_number']:
                        frubean["ProductPartNumber"] = product['product_part_number']
                    else:
                        frubean["ProductPartNumber"] = None

                    if product['product_version']:
                        frubean["ProductVersion"] = product['product_version']
                    else:
                        frubean["ProductVersion"] = None

                    if product['product_serial']:
                        frubean["ProductSerial"] = product['product_serial']
                    else:
                        frubean["ProductSerial"] = None

                    if product['product_asset_tag']:
                        frubean["ProductAssetTag"] = product['product_asset_tag']
                    else:
                        frubean["ProductAssetTag"] = None

                    if product['product_extra']:
                        if ";" not in product['product_extra']:
                            frubean["ProductExtra"] = product['product_extra']
                        else:
                            pelist = product['product_extra'].split(";")
                            # frubean["ProductExtra1"] = pelist[0]
                            # frubean["ProductExtra2"] = pelist[1]
                            for i in range(len(pelist)):
                                frubean["ProductExtra" + str(i + 1)] = pelist[i]

                    FRUlist.append(frubean)
                FRU = [{"FRU": FRUlist}]
                res.State('Success')
                res.Message(FRU)
            else:
                res.State('Failure')
                res.Message('Can not get Fru information')
        else:
            res.State('Failure')
            res.Message('Can not get Fru information')
        return res

    def getProdcut(self, client, args):
        '''
        :return:
        '''

    def getcapabilities(self, client, args):
        '''

        :return:
        '''
        res = ResultBean()
        cap = CapabilitiesBean()
        getcomand = ['get80port', 'getadaptiveport', 'getbios', 'getbiosdebug', 'getbiosresult', 'getbiossetting', 'getcapabilities', 'getcpu', 'geteventlog', 'geteventsub', 'getfan', 'getfirewall',
                     'getfru', 'getfw', 'gethealth', 'gethealthevent', 'getip', 'getldisk', 'getmemory', 'getmgmtport', 'getnic', 'getpcie', 'getpdisk', 'getpower ',
                     'getproduct', 'getpsu', 'getpwrcap', 'getraid', 'getsensor', 'getserialport', 'getservice', 'getsysboot', 'gettaskstate', 'gettemp', 'getthreshold', 'gettime', 'gettrap', 'getupdatestate', 'getuser', 'getvnc', 'getvncsession', 'getvolt']
        setcommand = ['adduser', 'addwhitelist', 'canceltask', 'clearbiospwd', 'clearsel', 'collect', 'deluser', 'delvncsession', 'delwhitelist', 'downloadsol', 'downloadtfalog', 'exportbioscfg', 'exportbmccfg', 'fancontrol',
                      'fwupdate', 'importbioscfg', 'importbmccfg', 'locatedisk', 'locateserver', 'mountvmm', 'powercontrol', 'powerctrldisk', 'recoverypsu', 'resetbmc', 'restorebios', 'restorebmc', 'sendipmirawcmd', 'settime', 'settimezone', 'settrapcom',
                      'setadaptiveport', 'setbios', 'setbiosdebug', 'setbiospwd', 'setfirewall', 'sethsc', 'setip', 'setpriv', 'setproductserial', 'setpwd', 'setserialport', 'setservice', 'setsysboot', 'setthreshold', 'settrapdest', 'setvlan', 'setvnc', 'setimageurl']
        cap.GetCommandList(getcomand)
        cap.SetCommandList(setcommand)
        res.State('Success')
        res.Message(cap.dict)
        return res

    def getcpu(self, client, args):
        '''

        :return:
        '''

    def getadaptiveport(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def getmemory(self, client, args):
        '''

        :return:
        '''

    def powercontrol(self, client, args):
        '''
        power control
        :param client:
        :param args:
        :return:power control
        '''
        choices = {'On': 'on', 'ForceOff': 'off', 'ForcePowerCycle': 'cycle', 'ForceReset': 'reset', 'GracefulShutdown': 'soft', 'Nmi': 'diag'}
        # power on, power off(immediately shutdown), power soft(orderly shutdown), power reset, power cycle. Power diag
        ctr_result = ResultBean()
        # 首先获取当前电源状态，如果是关机状态，只能开机操作
        cur_status = IpmiFunc.getPowerStatusByIpmi(client)
        if cur_status and cur_status.get('code') == 0 and cur_status.get('data') is not None and cur_status.get('data').get(
                'status') is not None:
            cur_power = cur_status.get('data').get('status')
            if cur_power == 'off' and (choices[args.state] == 'off' or choices[args.state] == 'soft'):
                ctr_result.State("Success")
                ctr_result.Message('power status is off.')
                return ctr_result
            elif cur_power == 'off' and choices[args.state] != 'on':
                ctr_result.State("Failure")
                ctr_result.Message('power status is off, please power on first.')
                return ctr_result
        elif cur_status is None:
            ctr_result.State("Failure")
            ctr_result.Message('get power status failed, load dll error')
            return ctr_result
        else:
            ctr_result.State("Failure")
            ctr_result.Message('get power status failed. ' + self.ERR_dict.get(cur_status.get('code'), ''))
            return ctr_result
        ctr_info = IpmiFunc.powerControlByIpmi(client, choices[args.state])
        if ctr_info:
            if ctr_info.get('code') == 0 and ctr_info.get('data') is not None and ctr_info.get('data').get(
                    'result') is not None:
                ctr_result.State("Success")
                ctr_result.Message('set power success,current power status is ' + ctr_info['data'].get('result') + '.')
            else:
                ctr_result.State("Failure")
                ctr_result.Message('set power failed: ' + ctr_info.get('data', ' '))
        else:
            ctr_result.State("Failure")
            ctr_result.Message('set power failed.')
        return ctr_result

    def gethealth(self, client, args):
        '''

        :return:
        '''

    def getsysboot(self, client, args):
        res = ResultBean()
        biosaAttribute = collections.OrderedDict()
        sysboot = IpmiFunc.getSysbootByIpmi(client)
        #{'data': '01 05 00 18 00 00 00', 'code': 0}
        if sysboot['code'] == 0:
            bootflags = sysboot['data'].strip().split(" ")
            data1 = bootflags[2]
            bin_1 = bin(int(data1, 16))[2:]
            if len(bin_1) < 8:
                bin_1 = "0" * (8 - len(bin_1)) + bin_1
            data2 = bootflags[3]
            #print (data2)
            bin_2 = bin(int(data2, 16))[2:]
            if len(bin_2) < 8:
                bin_2 = "0" * (8 - len(bin_2)) + bin_2
            # boot device
            boot_device = bin_2[2:6]
            boot_device_dict = {'0000': 'none',
                                '0001': 'PXE',
                                '0010': 'HDD',
                                '0011': 'HDD(SafeMode)',
                                '0100': 'Diagnostic Partition',
                                '0101': 'CD',
                                '0110': 'BIOSSETUP',
                                '1111': 'Floppy'}
            biosaAttribute['BootDevice'] = boot_device_dict.get(boot_device, 'reserved')
            # boot type
            biosaAttribute['BootMode'] = None
            # apply2
            if bin_1[1] == '0':
                biosaAttribute['Effective'] = 'Once'
            else:
                biosaAttribute['Effective'] = 'Continuous'
            # if bin_1[2]=='0':
            #     biosaAttribute['BootMode']='Legacy'
            # else:
            #     biosaAttribute['BootMode']='UEFI'

            res.State("Success")
            res.Message([biosaAttribute])
        else:
            res.State("Failure")
            res.Message(["get serial port error" + sysboot['data']])
        return res

    def geteventlog(self, client, args):
        '''

        :return:
        '''

    def downloadtfalog(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def gethealthevent(self, client, args):
        '''

        :return:
        '''

    def getraid(self, client, args):
        '''

        :return:
        '''

    def getldisk(self, client, args):
        '''

        :return:
        '''

    def clearsel(self, client, args):
        '''
        clear sel
        :param client:
        :param args:
        :return: clear sel
        '''
        clear_result = ResultBean()
        clear_code = IpmiFunc.clearSelByIpmi(client)
        if clear_code == 0:
            clear_result.State("Success")
            clear_result.Message(['Clearing SEL. Please allow a few seconds to erase.'])
        else:
            clear_result.State("Failure")
            clear_result.Message(['Clear sel failed.'])
        return clear_result

    def getnic(self, client, args):
        '''

        :return:
        '''

    def setsysboot(self, client, args):
        result = ResultBean()
        flag = True
        info = ""
        if args.mode is not None:
            mode_set = IpmiFunc.setBootModeByIpmi(client, args.mode)
            if mode_set['code'] != 0:
                flag = False
                info = "set mode error: " + mode_set['data']
        if args.effective is not None and args.device is not None:
            boot_set = IpmiFunc.setBIOSBootOptionByIpmi(client, args.effective, args.device)
            if boot_set['code'] != 0:
                flag = False
                info = info + "set boot device error: " + boot_set['data']
        if flag:
            result.State("Success")
            result.Message([])
        else:
            result.State("Failure")
            result.Message([info])
        return result

    def powerctrldisk(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def powerctrlpcie(self, client, args):
        '''

        :return:
        '''

    def getbios(self, client, args):
        '''

        :return:
        '''

    def setbios(self, client, args):
        '''

        :return:
        '''

    def setbiospwd(self, client, args):
        '''

        :return:
        '''

    def getbiossetting(self, client, args):
        '''

        :return:
        '''

    def getbiosresult(self, client, args):
        '''

        :return:
        '''

    def getbiosdebug(self, client, args):
        '''

        :return:
        '''

    def clearbiospwd(self, client, args):
        '''

        :return:
        '''

    def restorebios(self, client, args):
        '''

        :return:
        '''

    def setbiosdebug(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def mountvmm(self, client, args):
        '''

        :return:
        '''

    def setthreshold(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    # def downloadfandiag(self, client, args):

    def downloadsol(self, client, args):
        '''

        :return:
        '''

    def sethsc(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def chassis(self, client, args):
        '''

        :return:
        '''

    def getproduct(self, client, args):
        '''

        :return:
        '''

    def setproductserial(self, client, args):
        res = ResultBean()
        serial_set = IpmiFunc.editFruByIpmi(client, 0, 'p', '4', args.serial)
        if serial_set == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message([self.ERR_dict.get(serial_set, "set product serial error")])
        return res

    def getfan(self, client, args):
        '''

        :return:
        '''

    def fancontrol(self, client, args):
        '''

        :return:
        '''

    def getsensor(self, client, args):
        '''
        get sensor info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        sensors_Info = SensorBean()

        num_dict = {}
        sensors = IpmiFunc.getSensorByIpmi(client)
        sensors_num = IpmiFunc.getSdrElistByIpmi(client)
        if sensors_num and sensors_num.get('code') == 0 and sensors_num.get('data') is not None:
            num_data = sensors_num.get('data')
            # print(num_data)
            for i in range(len(num_data)):
                num_dict[num_data[i].get('name')] = int(num_data[i].get('number').split('h')[0], 16)

        if sensors:
            if sensors.get('code') == 0 and sensors.get('data') is not None:
                sensorsData = sensors.get('data')
                List = []
                size = len(sensorsData)
                sensors_Info.Maximum(size)
                num = 0
                for sensor in sensorsData:
                    sensor_single = Sensor()
                    # sensor_single.SensorNumber(num)
                    sensor_single.SensorNumber(num_dict.get(sensor.get('name', None), num))
                    sensor_single.SensorName(sensor.get('name', None))
                    if sensor.get('value', None) == '0x0':
                        sensor_single.Reading(float(0))
                    else:
                        sensor_single.Reading(None if sensor.get('value', None) == 'na' or sensor.get('value') is None else float(sensor.get('value')))
                    sensor_single.Unit(None if sensor.get('unit', None) == '' else sensor.get('unit', None))
                    sensor_single.Status(sensor.get('status', None))
                    sensor_single.unr(None if sensor.get('unr', None) == 'na' or sensor.get('unr', None) is None or sensor.get('unr', None) == '' else float(sensor.get('unr')))
                    sensor_single.uc(None if sensor.get('uc', None) == 'na' or sensor.get('uc', None) is None or sensor.get('uc', None) == '' else float(sensor.get('uc')))
                    sensor_single.unc(None if sensor.get('unc', None) == 'na' or sensor.get('unc', None) is None or sensor.get('unc', None) == '' else float(sensor.get('unc')))

                    sensor_single.lnc(None if sensor.get('lnc', None) == 'na' or sensor.get('lnc', None) is None or sensor.get('lnc', None) == '' else float(sensor.get('lnc')))
                    sensor_single.lc(None if sensor.get('lc', None) == 'na' or sensor.get('lc', None) is None or sensor.get('lc', None) == '' else float(sensor.get('lc')))
                    sensor_single.lnr(None if sensor.get('lnr', None) == 'na' or sensor.get('lnr', None) is None or sensor.get('lnr', None) == '' else float(sensor.get('lnr')))
                    num = num + 1
                    List.append(sensor_single.dict)
                sensors_Info.Sensor(List)
                result.State('Success')
                result.Message([sensors_Info.dict])

            else:
                result.State('Failure')
                result.Message(['Failed to get sensor info. ' + self.ERR_dict.get(sensors.get('code'), '')])
        else:
            result.State('Failure')
            result.Message(['Failed to get sensor info, load dll error.'])

        return result

    def getpower(self, client, args):
        Power_result = ResultBean()
        power = PowerBean()
        sensors = IpmiFunc.getSdrTypeByIpmi(client, '0x08')
        if sensors:
            if sensors.get('code') == 0 and sensors.get('data') is not None:
                sensorsData = sensors.get('data')
                List = []
                num = 0
                for sensor in sensorsData:
                    powersingle = PowerSingleBean()
                    # if 'state' in sensor and sensor.get('state').lower() == 'ok':
                    powersingle.Name(sensor.get('name', None))
                    powersingle.SensorNumber(int(sensor.get('number', num).split('h')[0], 16))
                    try:
                        if ' Watts' in sensor.get('value', 'null'):
                            powersingle.ReadingWatt(float(sensor.get('value').split(' Watts')[0]))
                        else:
                            powersingle.ReadingWatt(None)
                    except BaseException:
                        powersingle.ReadingWatt(None)
                    num = num + 1
                    List.append(powersingle.dict)
                power.Power(List)
                Power_result.State('Success')
                Power_result.Message([power.dict])

            else:
                Power_result.State('Failure')
                Power_result.Message(['Failed to get power info. ' + self.ERR_dict.get(sensors.get('code'), '')])
        else:
            Power_result.State('Failure')
            Power_result.Message(['Failed to get power info, load dll error.'])

        return Power_result

    def gettemp(self, client, args):
        '''
        get temperature info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        temp_Info = TemperatureBean()
        num_dict = {}

        sensors_temp = IpmiFunc.getSensorsTempByIpmi(client)
        sensors_num = IpmiFunc.getSdrTypeByIpmi(client, '0x01')
        if sensors_num and sensors_num.get('code') == 0 and sensors_num.get('data') is not None:
            num_data = sensors_num.get('data')
            # print(num_data)
            for i in range(len(num_data)):
                num_dict[num_data[i].get('name')] = int(num_data[i].get('number').split('h')[0], 16)

        if sensors_temp:
            if sensors_temp.get('code') == 0 and sensors_temp.get('data') is not None:
                temps = sensors_temp.get('data')
                # print(temps)
                List = []
                num = 0
                for temp in temps:
                    temp_single = Temperature()
                    if temp.get('unit') == 'degrees C':
                        temp_single.Name(temp.get('name', None))
                        temp_single.SensorNumber(num_dict.get(temp.get('name', None), num))
                        temp_single.UpperThresholdFatal(None if temp.get('unr', None) == 'na' or temp.get('unr', None) is None else float(temp.get('unr')))
                        temp_single.UpperThresholdCritical(None if temp.get('uc', None) == 'na' or temp.get('uc', None) is None else float(temp.get('uc')))
                        temp_single.UpperThresholdNonCritical(None if temp.get('unc', None) == 'na' or temp.get('unc', None) is None else float(temp.get('unc')))
                        # temp_single.ReadingCelsius(None if temp.get('value', None) == 'na' or temp.get('value',None) == '0x0' or temp.get('value') is None else float(temp.get('value')))
                        if temp.get('value', None) == '0x0':
                            temp_single.ReadingCelsius(float(0))
                        else:
                            temp_single.ReadingCelsius(None if temp.get('value', None) == 'na' or temp.get('value') is None else float(temp.get('value')))
                        temp_single.LowerThresholdNonCritical(None if temp.get('lnc', None) == 'na' or temp.get('lnc', None) is None else float(temp.get('lnc')))
                        temp_single.LowerThresholdCritical(None if temp.get('lc', None) == 'na' or temp.get('lc', None) is None else float(temp.get('lc')))
                        temp_single.LowerThresholdFatal(None if temp.get('lnr', None) == 'na' or temp.get('lnr', None) is None else float(temp.get('lnr')))
                        num = num + 1
                        List.append(temp_single.dict)
                temp_Info.Temperature(List)
                result.State('Success')
                result.Message([temp_Info.dict])

            else:
                result.State('Failure')
                result.Message(['Failed to get temp info. ' + self.ERR_dict.get(sensors_temp.get('code'), '')])
        else:
            result.State('Failure')
            result.Message(['Failed to get temp info, load dll error.'])

        return result

    def getvolt(self, client, args):
        '''
        get voltage info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        temp_Info = VoltBean()
        num_dict = {}

        sensors_temp = IpmiFunc.getSensorsVoltByIpmi(client)
        sensors_num = IpmiFunc.getSdrTypeByIpmi(client, '0x02')
        if sensors_num and sensors_num.get('code') == 0 and sensors_num.get('data') is not None:
            num_data = sensors_num.get('data')
            for i in range(len(num_data)):
                num_dict[num_data[i].get('name')] = int(num_data[i].get('number').split('h')[0], 16)

        if sensors_temp:
            if sensors_temp.get('code') == 0 and sensors_temp.get('data') is not None:
                temps = sensors_temp.get('data')
                # print(temps)
                List = []
                num = 0
                for temp in temps:
                    temp_single = Voltage()
                    if temp.get('unit') == 'Volts':
                        temp_single.Name(temp.get('name', None))
                        temp_single.SensorNumber(num_dict.get(temp.get('name', None), num))
                        temp_single.UpperThresholdFatal(
                            None if temp.get('unr', None) == 'na' or temp.get('unr', None) is None else float(
                                temp.get('unr')))
                        temp_single.UpperThresholdCritical(
                            None if temp.get('uc', None) == 'na' or temp.get('uc', None) is None else float(
                                temp.get('uc')))
                        temp_single.UpperThresholdNonCritical(
                            None if temp.get('unc', None) == 'na' or temp.get('unc', None) is None else float(
                                temp.get('unc')))
                        # temp_single.ReadingVolts(
                        #     None if temp.get('value', None) == 'na' or temp.get('value', None) == '0x0' or temp.get(
                        #         'value') is None else float(temp.get('value')))
                        if temp.get('value', None) == '0x0':
                            temp_single.ReadingVolts(float(0))
                        else:
                            temp_single.ReadingVolts(None if temp.get('value', None) == 'na'or temp.get('value') is None else float(temp.get('value')))
                        temp_single.LowerThresholdNonCritical(
                            None if temp.get('lnc', None) == 'na' or temp.get('lnc', None) is None else float(
                                temp.get('lnc')))
                        temp_single.LowerThresholdCritical(
                            None if temp.get('lc', None) == 'na' or temp.get('lc', None) is None else float(
                                temp.get('lc')))
                        temp_single.LowerThresholdFatal(
                            None if temp.get('lnr', None) == 'na' or temp.get('lnr', None) is None else float(
                                temp.get('lnr')))

                        num = num + 1
                        List.append(temp_single.dict)
                temp_Info.Voltage(List)
                result.State('Success')
                result.Message([temp_Info.dict])

            else:
                result.State('Failure')
                result.Message(['Failed to get volt info. ' + self.ERR_dict.get(sensors_temp.get('code'), '')])
        else:
            result.State('Failure')
            result.Message(['Failed to get volt info, load dll error.'])

        return result

    def getthreshold(self, client, args):
        '''

        :return:
        '''

    def getpwrcap(self, client, args):
        '''

        :return:
        '''

    def getpsu(self, client, args):
        '''

        :return:
        '''

    def recoverypsu(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getpdisk(self, client, args):
        '''

        :return:
        '''

    def getpcie(self, client, args):
        '''

        :return:
        '''

    def locateserver(self, client, args):
        '''

        :return:
        '''

    def locatedisk(self, client, args):
        '''

        :return:
        '''

    def Managers(self, client, args):
        '''

        :return:
        '''

    def getip(self, client, args):
        '''

        :return:
        '''
        # ipinfo=ResultBean()
        # netinfo=IpmiFunc.getLanByIpmi(client, args.channel)
        # if netinfo.get('code') == 0 and netinfo.get('data') is not None:
        #     lan=netinfo.get('data')
        #     lanlist=lan.split("\n")
        #     landict=collections.OrderedDict()
        #     #Auth Type Enable
        #     #Cipher Suite Priv Max
        #     ate=";"
        #     cspv=";"
        #     for laninfo in lanlist:
        #         if laninfo.strip()=="":
        #             continue
        #         key=laninfo.split(":")[0].strip()
        #         value=laninfo[(laninfo.find(":")+1):].strip()
        #         if key.strip()=="":
        #             value=value.replace(" ","")
        #             if ":" in value:
        #                 ate = ate + value + ";"
        #             elif "=" in value:
        #                 cspv = cspv + value + ";"
        #         else:
        #             landict[key]=value
        #     if "Auth Type Enable" in landict:
        #         landict["Auth Type Enable"]=landict["Auth Type Enable"] + ate
        #     if "Cipher Suite Priv Max" in landict:
        #         landict["Cipher Suite Priv Max"]=landict["Cipher Suite Priv Max"] + cspv
        #     ipinfo.State("Success")
        #     ipinfo.Message([landict])
        # else:
        #     ipinfo.State("Failure")
        #     ipinfo.Message(["get net info error"])
        #
        # return ipinfo

    def getdns(self, client, args):
        '''

        :return:
        '''

    def gettrap(self, client, args):
        '''

        :return:
        '''

    def restorebmc(self, client, args):
        '''

        :return:
        '''

    def collect(self, client, args):
        '''

        :return:
        '''

    def gettime(self, client, args):
        res = ResultBean()
        offsetres = IpmiFunc.sendRawByIpmi(client, "0x0a 0x5c")
        if offsetres.get("code", 1) == 0:
            offsetraw = offsetres.get("data", "").strip().split(" ")
            offset = int(offsetraw[1] + offsetraw[0], 16)
            we = "+"
            if offset > 32768:
                we = "-"
                offset = 65536 - offset
            hh = str(offset // 60)
            mm = str(offset % 60)
            if len(hh) == 1:
                hh = "0" + hh
            if len(mm) == 1:
                mm = "0" + mm
            timezone = we + str(hh) + ":" + str(mm)
            timeres = IpmiFunc.sendRawByIpmi(client, "0x0a 0x48")
            if timeres.get("code", 1) == 0:
                dataraw = timeres.get("data", "").strip().split(" ")
                timestamp = int(dataraw[3] + dataraw[2] + dataraw[1] + dataraw[0], 16)
                timearray = time.gmtime(timestamp)
                showtime = time.strftime("%Y-%m-%d %H:%M:%S", timearray)
                timeinfo = collections.OrderedDict()
                timeinfo['Time'] = showtime
                timeinfo['Timezone'] = timezone
                res.State("Success")
                res.Message(timeinfo)
            else:
                res.State("Success")
                res.Message("cannot get sel time. " + timeres.get("data", ""))
        else:
            res.State("Success")
            res.Message("cannot get sel time UTC offset. " + offsetres.get("data", ""))
        return res

    def settime(self, client, args):
        import time
        res = ResultBean()
        #self.newtime = "2018-05-31T10:10+08:00"
        if not RegularCheckUtil.checkBMCTime(args.newtime):
            res.State("Failure")
            #res.Message(["time param should be like YYYY-mm-ddTHH:MM±HH:MM"])
            res.Message(["time param should be like YYYY-mm-ddTHH:MM+HH:MM"])
            return res
        if "+" in args.newtime:
            newtime = args.newtime.split("+")[0]
            zone = args.newtime.split("+")[1]
            we = "+"
        else:
            zone = args.newtime.split("-")[-1]
            newtime = args.newtime.split("-" + zone)[0]
            we = "-"
        # set zone
        args.zone = "[" + we + zone + "]"
        res_zone = Base.settimezone(self, client, args)
        if res_zone.State == "Failure":
            return res_zone
        # set time
        try:
            #time.struct_time(tm_year=2019, tm_mon=4, tm_mday=16, tm_hour=15, tm_min=35, tm_sec=0, tm_wday=1, tm_yday=106, tm_isdst=-1)
            structtime = time.strptime(newtime, "%Y-%m-%dT%H:%M")
            # 时间戳1555400100
            stamptime = int(time.mktime(structtime))
        except ValueError as e:
            res.State("Failure")
            res.Message(["illage time param"])
            return res
        # 执行
        time_set = IpmiFunc.setBMCTimeByIpmi(client, stamptime)

        if time_set["code"] == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["set time error" + time_set.get('data', '')])
        return res

    def settimezone(self, client, args):
        import time
        res = ResultBean()
        if RegularCheckUtil.checkBMCZone(args.zone) == 1:
            res.State("Failure")
            #res.Message(["timezone should be like [±HH:MM]"])
            res.Message(["timezone should be like [+HH:MM]"])
            return res
        elif RegularCheckUtil.checkBMCZone(args.zone) == 2:
            res.State("Failure")
            res.Message(["timezone should be -12:00 to +14:00"])
            return res
        ew = args.zone[1]
        hh = int(args.zone[2:4])
        mm = int(args.zone[5:7])
        zoneMinutes = int(ew + str(hh * 60 + mm))
        if mm != 0 and mm != 30:
            res.State("Not Support")
            res.Message(["minutes can only be 0 or 30 now"])
            return res

        time_set = IpmiFunc.setBMCTimezoneByIpmi(client, zoneMinutes)
        if time_set["code"] == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["set time zone error" + time_set.get('data', '')])
        return res

    def resetbmc(self, client, args):
        '''

        :return:
        '''
        res = ResultBean()
        reset = IpmiFunc.resetBMCByIpmi(client)
        if reset == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["reset bmc failure"])
        return res

    def setip(self, client, args):
        res = ResultBean()
        if args.version is None:
            res.State("Failure")
            res.Message(["ip version(4/6) must be input"])
        elif args.version == "6":
            res.State("Not Support")
            res.Message([])
        elif args.version == "4":
            '''
            if args.channel is None:
                res.State("Failure")
                res.Message(["lan channel(1/8) must be input"])
            elif args.channel != "1" and args.channel != "8":
                res.State("Failure")
                res.Message(["lan channel must be 1 or 8"])
            else:
            '''
            # channel 1专口ip
            args.channel = "1"
            # 调用父类方法
            ipinfo = Base.getip(self, client, args)
            if ipinfo.State == "Failure":
                res.State("Failure")
                res.Message(["set vlan error"])
                return res
            ipm = ipinfo.Message[0]
            if ipm["IP Address"] == client.host:
                args.channel = "1"
            else:
                args.channel = "8"
            state = "Success"
            message = ""
            if args.mode.lower() == "dhcp":
                if args.addr is not None or args.gateway is not None or args.sub is not None:
                    res.State("Failure")
                    res.Message(["ip address, gateway, subnet cannot be setted when mode is DHCP"])
                else:
                    modeSet = IpmiFunc.setIpv4ModeByIpmi(client, args.channel, args.mode.lower())
                    if modeSet == 0:
                        message = "Set mode to " + args.mode + ". "
                    else:
                        state = "Failure"
            elif args.mode.lower() == "static":
                if args.mode is not None:
                    modeSet = IpmiFunc.setIpv4ModeByIpmi(client, args.channel, args.mode.lower())
                    if modeSet == 0:
                        message = "Set mode to " + args.mode + ". "
                    else:
                        state = "Failure"
                if args.gateway is not None:
                    if RegularCheckUtil.checkIP(args.gateway):
                        gatewaySet = IpmiFunc.setIpv4GatewayByIpmi(client, args.channel, args.gateway)
                        if gatewaySet == 0:
                            message = message + "Set gateway " + args.gateway + ". "
                        else:
                            state = "Failure"
                    else:
                        state = "Failure"
                        message = message + "Illegal gateway ip. "
                if args.sub is not None:
                    if RegularCheckUtil.checkSubnetMask(args.sub):
                        subSet = IpmiFunc.setIpv4SubnetmaskByIpmi(client, args.channel, args.sub)
                        if subSet == 0:
                            message = message + "Set subnet " + args.sub + ". "
                        else:
                            state = "Failure"
                    else:
                        state = "Failure"
                        message = message + "Illegal subnet. "
                # 最后修改ip
                if args.addr is not None:
                    if RegularCheckUtil.checkIP(args.addr):
                        addrSet = IpmiFunc.setIpv4IPByIpmi(client, args.channel, args.addr)
                        if addrSet == 0:
                            message = message + "Set ip " + args.addr + ". "
                        else:
                            state = "Failure"
                    else:
                        state = "Failure"
                        message = message + "Illegal ip. "
                res.State(state)
                res.Message([message])
            else:
                res.State("Failure")
                res.Message(["ip mode must be dhcp or static"])
        else:
            res.State("Failure")
            res.Message(["ip version must be 4 or 6"])

        return res

    def setvlan(self, client, args):
        res = ResultBean()
        if args.vlan_status is None and args.vlan_id is None:
            res.State("Success")
            res.Message(["nothing to set"])
            return res
        # channel
        args.channel = "1"
        # 调用父类方法
        ipinfo = Base.getip(self, client, args)
        if ipinfo.State == "Failure":
            res.State("Failure")
            res.Message(["set vlan error"])
            return res
        ipm = ipinfo.Message[0]
        if ipm["IP Address"] == client.host:
            channel = 1
        else:
            channel = 8
            args.channel = "8"
            ipinfo = Base.getip(self, client, args)
            ipm = ipinfo.Message[0]
        if ipm["802.1q VLAN ID"] == "Disabled":
            if args.vlan_status == "Disabled":
                res.State("Success")
                res.Message(["vlan is already disabled"])
                return res
            elif args.vlan_status is None:
                res.State("Failure")
                res.Message(["vlan is disabled, enable it first"])
                return res
            elif args.vlan_id is None:
                res.State("Failure")
                res.Message(["vlan id is needed"])
                return res
        else:
            if args.vlan_status == "Enabled" and args.vlan_id is None:
                res.State("Failure")
                res.Message(["vlan id is already enabled"])
                return res

        # vlan status
        if args.vlan_status == "Disabled":
            status = 0
        elif args.vlan_status == "Enabled":
            if args.vlan_id is None:
                res.State("Failure")
                res.Message(["vlan is disabled, enable it first"])
                return res
            status = 1
        else:
            res.State("Failure")
            res.Message(["vlan status must be enabled or disabled"])
            return res
        # vlanid
        if args.vlan_id is None:
            args.vlan_id = 2
        if args.vlan_id < 2 or args.vlan_id > 4094:
            res.State("Failure")
            res.Message(["vlan id must be 2-4094"])
            return res

        vlan_set = IpmiFunc.setVlanByIpmi(client, channel, status, args.vlan_id)
        if vlan_set["code"] == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["set vlan error"])
        return res

    def getvnc(self, client, args):
        '''

        :return:
        '''

    def setvnc(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getservice(self, client, args):
        '''
        get service info
        :param client:
        :param args:
        :return: service info
        '''
        Enabled = {'Enable': 'Enabled', 'Disable': 'Disabled'}
        service = ResultBean()
        service_all = ServiceBean()
        list = []
        # 获取服务列表全部信息
        Name = ["Web", "Kvm", "Cdmedia", "Fdmedia", "Hdmedia", "Ssh", "Telnet", "Solssh"]
        serviceFormat = {"kvm": 'KVM',
                         "cd-media": 'CDMedia',
                         "fd-media": 'FDMedia',
                         "hd-media": 'HDMedia',
                         "cd_media": 'CDMedia',
                         "fd_media": 'FDMedia',
                         "hd_media": 'HDMedia',
                         "vnc": 'VNC',
                         "ssh": 'SSH'}
        for service_name in Name:
            service_item = ServiceSingleBean()
            try:
                item_Info = getattr(IpmiFunc, "getM5" + service_name + 'ByIpmi')(client)
            except BaseException:
                service.State('Failure')
                service.Message(['this command is incompatible with current server.'])
                return service
            if item_Info:
                if item_Info.get('code') == 0 and item_Info.get('data') is not None:
                    sname = item_Info.get('data').get('ServiceName')
                    fname = serviceFormat.get(sname, '')
                    if fname == '':
                        fname = sname.upper()
                    service_item.Name(fname)
                    service_item.Enable(Enabled.get(item_Info.get('data').get('Status'), item_Info.get('data').get('Status')))
                    service_item.Port(None if item_Info.get('data').get('SecurePort') == 'N/A' else item_Info.get('data').get('SecurePort'))
                    service_item.Port2(None if item_Info.get('data').get('NonsecurePort') == 'N/A' else item_Info.get('data').get('NonsecurePort'))
                    service_item.SSLEnable('Enabled')
                else:
                    continue
            else:
                continue
            list.append(service_item.dict)
        if len(list) != 0:
            service_all.Service(list)
            service.State('Success')
            service.Message([service_all.dict])
        else:
            service.State('Failure')
            service.Message(['failed to get service info.'])
        return service

    def setservice(self, client, args):
        '''
        set service
        :param client:
        :param args:
        :return:
        '''
        set_result = ResultBean()
        if args.sslenable is not None:
            set_result.State("Not Support")
            set_result.Message(["currently not support set -t"])
            return set_result
        if args.secureport is None and args.nonsecureport is None and args.enabled is None and args.sslenable is None:
            set_result.State("Failure")
            set_result.Message(["please input a subcommand"])
            return set_result
        if args.service == 'ssh':
            if args.nonsecureport is not None:
                set_result.State("Failure")
                set_result.Message(["ssh not support nonsecure port."])
                return set_result
        elif args.service == 'telnet':
            if args.secureport is not None:
                set_result.State("Failure")
                set_result.Message(["telnet not support secure port."])
                return set_result
        elif args.service == 'solssh':
            if args.secureport is not None:
                set_result.State("Failure")
                set_result.Message(["solssh not support secure port."])
                return set_result
        if args.enabled is not None and args.enabled == 'Disabled' and (
                args.secureport is not None or args.nonsecureport is not None):
            set_result.State("Failure")
            set_result.Message(["Settings are not supported when -e is set to Disabled."])
            return set_result
        if args.enabled is not None:
            if 'Enabled' in args.enabled:
                enabled = ' 0x01'
            else:
                enabled = ' 0x00'
        if args.secureport is not None:
            if args.secureport < 1 or args.secureport > 65535:
                set_result.State("Failure")
                set_result.Message(["secureport is in 1-65535."])
                return set_result
            else:
                sp = '{:08x}'.format(args.secureport)
                sp_hex = hexReverse(sp)

        if args.nonsecureport is not None:
            if args.nonsecureport < 1 or args.nonsecureport > 65535:
                set_result.State("Failure")
                set_result.Message(["nonsecureport is in 1-65535."])
                return set_result
            else:
                nsp = '{:08x}'.format(args.nonsecureport)
                nsp_hex = hexReverse(nsp)

        # 获取信息
        service_name = args.service.replace('-', '').title()
        try:
            Info_all = getattr(IpmiFunc, "getM5" + service_name + 'ByIpmi')(client)
        except BaseException:
            set_result.State('Failure')
            set_result.Message(['this command is incompatible with current server.'])
            return set_result
        if Info_all:
            if Info_all.get('code') == 0 and Info_all.get('data') is not None:
                Info = Info_all.get('data')
                if args.enabled is None:
                    status_dict = {'Disabled': '00', 'Enabled': '01'}
                    if Info['Status'] == 'Disabled':
                        set_result.State("Failure")
                        set_result.Message(["please set status to Enabled firstly."])
                        return set_result
                    enabled = hex(int(status_dict[Info['Status']]))

                if args.nonsecureport is None:
                    if Info['NonsecurePort'] == 'N/A':
                        nsp_hex = "0xff " * 4
                    else:
                        nsp = '{:08x}'.format(Info['NonsecurePort'])
                        nsp_hex = hexReverse(nsp)
                if args.secureport is None:
                    if Info['SecurePort'] == 'N/A':
                        sp_hex = "0xff " * 4
                    else:
                        sp = '{:08x}'.format(Info['SecurePort'])
                        sp_hex = hexReverse(sp)

                if Info['InterfaceName'] == 'N/A':
                    interface_temp = "F" * 16
                    interface = ascii2hex(interface_temp, 17)
                else:
                    interface = ascii2hex(Info['InterfaceName'], 17)

                if Info['Timeout'] == "N/A":
                    t_hex = "0xff " * 4
                else:
                    t = '{:08x}'.format(Info['Timeout'])
                    t_hex = hexReverse(t)

                set_Info = getattr(IpmiFunc, "setM5" + service_name + 'ByIpmi')(client, enabled, interface, nsp_hex,
                                                                                sp_hex, t_hex)
                if set_Info:
                    if set_Info.get('code') == 0:
                        set_result.State("Success")
                        set_result.Message(["set service success."])
                        return set_result
                    else:
                        set_result.State("Failure")
                        set_result.Message(["failed to set service: " + set_Info.get('data', '')])
                        return set_result
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set service, return None."])
                    return set_result
            else:
                set_result.State("Failure")
                set_result.Message(["failed to set service info: " + Info_all.get('data', '')])
                return set_result
        else:
            set_result.State("Failure")
            set_result.Message(["failed to set service info"])
            return set_result

    def getmgmtport(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def getserialport(self, client, args):
        '''

        :return:
        '''

    def setserialport(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def setadaptiveport(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def settrapcom(self, client, args):
        res = ResultBean()
        flag = True
        info = ""
        if args.severity is None and args.community is None and args.enabled is None:
            res.State("Failure")
            res.Message(["nothing to set, input severity/community/enable"])
            return res
        # enable
        if args.enabled is not None and args.enabled == "Disabled":
            res.State("Not Support")
            res.Message([["cannot disable trap"]])
            return res
        # community
        if args.community is not None:
            community_set = IpmiFunc.setTrapByIpmi(client, "community", args.community)
            if community_set["code"] != 0:
                flag = False
                info = info + " set community failed: " + community_set.get('data', '')
        # severity
        if args.severity is not None:
            s_dict = {'All': 0, 'WarningAndCritical': 1, 'Critical': 2}
            community_set = IpmiFunc.setTrapByIpmi(client, "severity", s_dict[args.severity])
            if community_set["code"] != 0:
                flag = False
                info = info + " set severity failed: " + community_set.get('data', '')
        if flag:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message([info])
        return res

    def settrapdest(self, client, args):
        res = ResultBean()
        if args.destination == 0:
            res.State("Not Support")
            res.Message(["id 0 is not supported on the M5 platform"])
            return res
        if args.enabled == "Enabled":
            enable = 1
        else:
            enable = 0
        # channel
        args.channel = "1"
        # 调用父类方法
        ipinfo = Base.getip(self, client, args)
        if ipinfo.State == "Failure":
            res.State("Failure")
            res.Message(["set trap dest error"])
            return res
        ipm = ipinfo.Message[0]
        if ipm["IP Address"] == client.host:
            channel = 1
        else:
            channel = 8

        trap_set = IpmiFunc.setSNMPTrapPolicyByIpmi(client, args.destination, channel, enable)
        if trap_set["code"] != 0:
            res.State("Failure")
            res.Message(["Set SNMP Trap policy error:" + trap_set["data"]])
            return res
        tpye_set = IpmiFunc.setAlertTypeByIpmi(client, args.destination, channel, "snmp")
        if tpye_set["code"] != 0:
            res.State("Failure")
            res.Message(["Set Alert Type error:" + tpye_set["data"]])
            return res
        if RegularCheckUtil.checkIP(args.address):
            d_set = IpmiFunc.setDestIPByIpmi(client, args.destination, channel, args.address)
            if d_set["code"] != 0:
                res.State("Failure")
                res.Message(["Set destination address error:" + d_set["data"]])
                return res
        else:
            res.State("Failure")
            res.Message(["illegal ip"])
            return res
        res.State("Success")
        res.Message([])
        return res

    # def triggernmi(self, client, args):
    #
    #     ctr_result = ResultBean()
    #     ctr_info = IpmiFunc.powerControlByIpmi(client, 'diag')
    #     if ctr_info:
    #         if ctr_info.get('code') == 0 and ctr_info.get('data') is not None and ctr_info.get('data').get(
    #                 'result') is not None:
    #             ctr_result.State("Success")
    #             ctr_result.Message('trigger a nmi to host.')
    #         else:
    #             ctr_result.State("Failure")
    #             ctr_result.Message('failed to trigger nmi. '+self.ERR_dict.get(ctr_info.get('code') == 0))
    #     else:
    #         ctr_result.State("Failure")
    #         ctr_result.Message('failed to trigger nmi.')
    #     return ctr_result

    def exportbmccfg(self, client, args):
        '''

        :return:
        '''

    def importbmccfg(self, client, args):
        '''

        :return:
        '''

    def exportbioscfg(self, client, args):
        '''
        export bios setup configuration
        :param client:
        :param args:
        :return:
        '''
        bios = ResultBean()
        bios.State('Not Support')
        bios.Message([])
        return bios

    def importbioscfg(self, client, args):
        '''
        import bios cfg
        :param client:
        :param args:
        :return:
        '''
        bios = ResultBean()
        bios.State('Not Support')
        bios.Message([])
        return bios

    def delvncsession(self, client, args):
        '''

        :return:
        '''

    def sendipmirawcmd(self, client, args):

        def checkcmd(cmd):
            if cmd is None:
                return ""
            if not cmd.startswith("0x") and not cmd.startswith("0X"):
                try:
                    cmd = int(cmd)
                    cmd = hex(cmd)
                except BaseException:
                    return 1
            if len(cmd) > 4 or len(cmd) < 3:
                return 2
            p = '^0[xX][0-9a-fA-F]{1,2}$'
            if re.search(p, cmd, re.I):
                if len(cmd) == 3:
                    cmd = "0x0" + cmd[2]
                return cmd
            else:
                return 3

        check_error = {
            0: " cannot be None",
            1: " should be number",
            2: " should be between 0-255 or 0x00-0xff",
            3: " should be illegal hex",
        }
        res = ResultBean()
        netfun = checkcmd(args.netfun)
        if isinstance(netfun, int):
            res.State("Failure")
            res.Message([{"ipmirsp": "netfun" + check_error.get(netfun)}])
            return res

        command = checkcmd(args.command)
        if isinstance(command, int):
            res.State("Failure")
            res.Message([{"ipmirsp": "command" + check_error.get(command)}])
            return res

        # if args.bridge is not None:
        bridge = checkcmd(args.bridge)
        if isinstance(bridge, int):
            res.State("Failure")
            res.Message([{"ipmirsp": "command" + check_error.get(bridge)}])
            return res

        # if args.target is not None:
        target = checkcmd(args.target)
        if isinstance(target, int):
            res.State("Failure")
            res.Message([{"ipmirsp": "command" + check_error.get(target)}])
            return res

        datalist = None
        if args.datalist is not None:
            dp = '^[0-9a-fA-FxX ]+$'
            if not re.search(dp, args.datalist, re.I):
                res.State("Failure")
                res.Message([{"ipmirsp": "Bad character in datalist."}])
                return res

            datalistraw = args.datalist.strip().split(" ")
            datalist = ""
            for data in datalistraw:
                data = checkcmd(data)
                if isinstance(data, int):
                    res.State("Failure")
                    res.Message([{"ipmirsp": "param in datalist" + check_error.get(data)}])
                    return res
                else:
                    datalist = datalist + " " + data

        if args.target is not None or args.bridge is not None:
            result = IpmiFunc.sendIPMIrawEXByIpmi(client, target, bridge, netfun, command, datalist)
        else:
            result = IpmiFunc.sendIPMIrawcmdByIpmi(client, netfun, command, datalist)
        if result is None or result == {}:
            res.State("Failure")
            res.Message([{"ipmirsp": "failed to send raw command."}])
        elif result.get("code") == 0:
            res.State("Success")
            res.Message([{"ipmirsp": result["data"]}])
        else:
            res.State("Failure")
            res.Message([{"ipmirsp": result.get("data", "")}])
        return res

    def AccountService(self, client, args):
        '''

        :return:
        '''

    def getuser(self, client, args):
        '''

        :return:
        '''
        # res = ResultBean()
        # userlist = IpmiFunc.getUserListByIpmi(client)
        # if userlist["code"] == 0:
        #     res.State("Success")
        #     res.Message([userlist])
        # else:
        #     res.State("Failure")
        #     res.Message(["get user list error"])
        # return res

    def adduser(self, client, args):
        priv_dict = {"administrator": 4, "operator": 3, "user": 2, "commonuser": 2, "noaccess": 2}
        if args.roleid.lower() == "noaccess":
            args.access = 0
        else:
            args.access = 1
        res = ResultBean()
        userlist = IpmiFunc.addUserByIpmi(client, args.uname, args.upass, priv_dict.get(args.roleid.lower()), args.access)
        # print ("userlist")
        # print (userlist)
        if userlist == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["add user error"])
        return res

    def deluser(self, client, args):
        res = ResultBean()
        userRes = IpmiFunc.getUserListByIpmi(client)
        if userRes.get("code") == 0:
            userInfo = userRes.get("data")
            userid = ""
            for user in userInfo:
                if user.get("user_name") == args.uname:
                    userid = user.get("user_id", "")
            if userid == "":
                res.State("Failure")
                res.Message(["user '" + args.uname + "' not exist"])
                return res
        else:
            res.State("Failure")
            res.Message(["cannot get user list" + str(userRes)])
            return res
        userid = "0x0" + hex(userid)[2]
        del_raw = "0x06 0x45 " + userid + " 0xff 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 "
        del_res = IpmiFunc.sendRawByIpmi(client, del_raw)
        if del_res.get("code") == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["del user error" + str(del_res)])
        return res

    def setpwd(self, client, args):
        res = ResultBean()
        userRes = IpmiFunc.setUserPassByIpmi(client, args.uname, args.upass)
        if userRes == 0:
            res.State("Success")
            res.Message([])
        else:
            res.State("Failure")
            res.Message(["user not exits"])
        return res

    def setpriv(self, client, args):
        priv_dict = {"administrator": 4, "operator": 3, "commonuser": 2, "noaccess": 15}
        res = ResultBean()
        if args.roleid.lower() == "noaccess":
            userRes1 = IpmiFunc.setUserModByIpmi(client, args.uname, 0)
            userRes2 = IpmiFunc.setUserPrivByIpmi(client, args.uname, 15)
            if userRes1 == 0 and userRes2 == 0:
                res.State("Success")
                res.Message([])
            else:
                res.State("Failure")
                res.Message([])
            return res
        else:
            userRes1 = IpmiFunc.setUserModByIpmi(client, args.uname, 1)
            userRes2 = IpmiFunc.setUserPrivByIpmi(client, args.uname, priv_dict.get(args.roleid.lower()))
            if userRes1 == 0 and userRes2 == 0:
                res.State("Success")
                res.Message([])
            else:
                res.State("Failure")
                res.Message([])
            return res

    def updateservice(self, client, args):
        '''

        :return:
        '''

    def getfw(self, client, args):
        '''

        :return:
        '''

    def getupdatestate(self, client, args):
        '''

        :return:
        '''

    def fwupdate(self, client, args):
        '''

        :return:
        '''

    def getvncsession(self, client, args):
        '''

        :return:
        '''

    def EventServices(self, client, args):
        '''

        :return:'''

    def geteventsub(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def addeventsub(self, client, args):
        '''

        :return:
        '''

    def deleventsub(self, client, args):
        '''

        :return:
        '''

    def TaskService(self, client, args):
        '''

        :return:
        '''

    def gettaskstate(self, client, args):
        '''

        :return:
        '''

    def cancletask(self, client, args):
        '''

        :return:
        '''

    def get80port(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getfirewall(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def setfirewall(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def Opwhitelist(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def addwhitelist(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def delwhitelist(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def setimageurl(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getimageurl(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def methods(self, client, args):
        return(list(filter(lambda m: not m.startswith("__") and not m.endswith("__") and callable(getattr(self, client, args, m)), dir(self, client, args))))

# Ascii转十六进制


def ascii2hex(data, length):
    count = length - len(data)
    list_h = []
    for c in data:
        list_h.append(str(hex(ord(c))))
    data = ' '.join(list_h) + ' 0x00' * count
    return data

# 十六进制字符串逆序


def hexReverse(data):
    pattern = re.compile('.{2}')
    time_hex = ' '.join(pattern.findall(data))
    seq = time_hex.split(' ')[::-1]
    data = '0x' + ' 0x'.join(seq)
    return data


if __name__ == "__main__":
    class aaa():
        def __init__(self):
            self.newtime = "2018-05-31T10:10+08:00"
            #self.newtime = "20180531101010"
            self.vlan_status = "enable"
            self.channel = "8"
            self.vlan_id = "666"
            self.zone = "+09:00"
            self.uname = "yuwenjie"
            self.upass = "555555"
            self.group = "user"
            self.access = 1
    import RequestClient
    client = RequestClient.RequestClient()
    # client.setself("100.2.73.207","root","root",623,"lanplus")
    client.setself("100.2.73.169", "admin", "admin", 623, "lanplus")
    base = Base()
    args = aaa()
    # message = base.getfru(client,None)
    # message = base.clearsel(client, None)
    #message = base.settimezone(client, args)
    #message = base.settime(client, args)
    #message = base.setvlan(client, args)
    #message = base.getuser(client, None)
    #message = base.adduser(client, args)
    #message = base.deluser(client, args)
    #message = base.setpwd(client, args)
    message = base.setpriv(client, args)
    '''
        class tex():
        def state(self, value):
            tex.state = value
    client = RequestClient.RequestClient()
    client.setself("100.2.73.207","root","root",623,"lanplus")
    base = Base()
    args = tex()
    args.state('On')
    # message = base.getfru(client,None)
    # message = base.clearsel(client, None)
    '''
    print (message)
    print (message.State)
    print (message.Message)
    print(json.dumps(message, default=lambda o: o.__dict__, sort_keys=True, indent=4))
