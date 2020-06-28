# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: IpmiFunc Class
#
#   @author: zhong
#   @Date:
#=========================================================================
'''
import ctypes
import json
import sys
import re
import os
import math
import platform

from ansible.plugins.inspur_sdk.command import LoadCdll
from ansible.plugins.inspur_sdk.util import logger
# sys.path.append("..")
sys.path.append(os.path.dirname(sys.path[0]))
rootpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(rootpath, "util"))


command_path = os.path.dirname(os.path.realpath(__file__))
fruchange_path = os.path.join(command_path, "fruchange")

# ERR_CODE_SUCCESS = 0,    获取成功
# ERR_CODE_CMN_FAIL = 1,   通用异常，非认证、ip不通异常之外的，一般指数据获取异常
# ERR_CODE_PARAM_NULL = 2,    参数为空
# ERR_CODE_INPUT_ERROR = 3,    参数错误
# ERR_CODE_INTF_FAIL = 4,           建立连接异常
# ERR_CODE_INTERNAL_ERROR = 5,       内部错误
# ERR_CODE_ALLOC_MEM = 6,      分配内存异常
# ERR_CODE_NETWORK_CONNECT_FAIL = 7,   网络连接失败（任务某个ip的该端口不通）
# ERR_CODE_AUTH_NAME_OR_PWD_ERROR = 8,  （用户名或密码错误）
# ERR_CODE_USER_NOT_EXIST = 9,                   （用户不存在）


ERR_dict = {
    1: 'Ipmi information get error',
    2: 'Ipmi parameter is null',
    3: 'Ipmi parameter error',
    4: 'Cannot create ipmi link, please check host/username/pasword',
    5: 'Send ipmi raw cmd error, please check the cmd',
    6: 'Memory exception',
    7: 'Cannot connect to the server, please check host/username/pasword',
    8: 'incorrect user name or password',
    9: 'user not exist'
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

ERR = {
    1: 'ERR_CODE_CMN_FAIL',
    2: 'ERR_CODE_PARAM_NULL',
    3: 'ERR_CODE_INPUT_ERROR',
    4: 'ERR_CODE_INTF_FAIL',
    5: 'ERR_CODE_INTERNAL_ERROR',
    6: 'ERR_CODE_ALLOC_MEM',
    7: 'ERR_CODE_NETWORK_CONNECT_FAIL',
    8: 'ERR_CODE_AUTH_NAME_OR_PWD_ERROR',
    9: 'ERR_CODE_USER_NOT_EXIST'
}
DEVICE_ID = {
    0x0014: "MegaRAID Tri-Mode SAS3516",
    0x0016: "MegaRAID Tri-Mode SAS3508",
    0x005b: "MegaRAID SAS 2208",
    0x005d: "MegaRAID SAS-3 3108",
    0x005f: "MegaRAID SAS-3 3008",
    0x0097: "SAS3008 PCI-Express Fusion-MPT SAS-3",
    0x00ac: "SAS3416 Fusion-MPT Tri-Mode I/O Controller Chip (IOC)",
    0x2261: "ISP2722-based 16/32Gb Fibre Channel to PCIe Adapter",
    0xe200: "Lancer-X: LightPulse Fibre Channel Host Adapter",
    0xe300: "Lancer Gen6: LPe32000 Fibre Channel Host Adapter",
    0x5180: "9100 PRO NVMe SSD",
    0x16d7: "BCM57414 NetXtreme-E 10Gb/25Gb RDMA Ethernet Controller",
    0x1003: "MT27500 Family [ConnectX-3]",
    0x1017: "MT27800 Family [ConnectX-5]",
    0x0710: "OneConnect 10Gb NIC (be3)",
    0x1013: "MT27700 Family [ConnectX-4]",
    0x0a03: "SFC9220 10/40G Ethernet Controller",
    0xa804: "NVMe SSD Controller SM961/PM961",
    0x1007: "MT27520 Family [ConnectX-3 Pro]",
    0x1015: "MT27710 Family [ConnectX-4 Lx]",
    0x37d1: "Ethernet Connection X722 for 1GbE",
    0x37d2: "Ethernet Connection X722 for 10GBASE-T",
    0x37d3: "Ethernet Connection X722 for 10GbE SFP+",
    0x0953: "PCIe Data Center SSD",
    0x0a54: "Express Flash NVMe P4510",
    0x10c9: "82576 Gigabit Network Connection",
    0x10f8: "82599 10 Gigabit Dual Port Backplane Connection",
    0x10fb: "82599ES 10-Gigabit SFI/SFP+ Network Connection",
    0x1521: "I350 Gigabit Network Connection",
    0x1528: "Ethernet Controller 10-Gigabit X540-AT2",
    0x1529: "82599 10 Gigabit Dual Port Network Connection with FCoE",
    0x152a: "82599 10 Gigabit Dual Port Backplane Connection with FCoE",
    0x1557: "82599 10 Gigabit Network Connection",
    0x1572: "Ethernet Controller X710 for 10GbE SFP+",
    0x0540: "PBlaze4 NVMe SSD",
    0x0550: "PBlaze5 NVMe SSD",
    # 0xc4: "SAS9305",
    0x028d: "Series 8 12G SAS/PCIe 3",
    0x9361: "MegaRAID SAS 9361-8i",
    0x9371: "MegaRAID SAS 9361-16i",
    0x9364: "MegaRAID SAS 9364-8i",
    0x0017: "MegaRAID Tri-Mode SAS3408",
    0x3090: "SAS9311-8i",
    0x30a0: "SAS9300-8e",
    0x30e0: "SAS9300-8i",
    0x00af: "SAS3408 Fusion-MPT Tri-Mode I/O Controller Chip (IOC)",
    0x00ce: "MegaRAID SAS-3 3316 [Intruder]",
    0x37c8: "PF0 for Intel QuikAssist Technology",
    0x37cc: "10 Gb Ethernet",
    0x37ce: "Ethernet Connection X722 for 10GbE backplane",
    0x37d0: "Ethernet Connection X722 for 10GbE SFP+",
    0x1522: "I350 Gigabit Fiber Network Connection",
    0x1537: "I210 Gigabit Backplane Connection",
    0x1584: "Ethernet Controller XL710 for 40GbE SFP+",
    0x24f0: "Omni-Path HFI Silicon 100 Series [discrete]",
    0x028f: "Smart Storage PQI 12G SAS/PCIe 3",
    0x0100: "MLU100-C3/C4",
    0x13f2: "Tesla M60",
    0x15f8: "Tesla P100 PCIe 16GB",
    0x1b30: "Quadro P6000",
    0x1bb0: "Quadro P5000",
    0x1bb1: "Quadro P4000",
    0x1bb3: "P4 GPU",
    0x1c30: "Quadro P2000",
    0x1db1: "V100-SXM2 GPU",
    0x1db5: "V100-SXM2 GPU",
    0x1b38: "P40 GPU",
    0x1db4: "V100-PCIE GPU",
    # NF5468M5补充
    0x2031: "ISP8324-based 16Gb Fibre Channel to PCI Express Adapter",
    0x2532: "ISP2532-based 8Gb Fibre Channel to PCI Express HBA",
    0x101e: "GK110GL [Tesla K20X]",
    0x101f: "GK110GL [Tesla K20]",
    0x1020: "GK110GL [Tesla K20X]",
    0x1021: "GK110GL [Tesla K20Xm]",
    0x1022: "GK110GL [Tesla K20c]",
    0x1023: "GK110BGL [Tesla K40m]",
    0x1024: "GK110BGL [Tesla K40c]",
    0x1026: "GK110GL [Tesla K20s]",
    0x1027: "GK110BGL [Tesla K40st]",
    0x1028: "GK110GL [Tesla K20m]",
    0x1029: "GK110BGL [Tesla K40s]",
    0x102a: "GK110BGL [Tesla K40t]",
    0x102d: "GK210GL [Tesla K80]",
    0x102e: "GK110BGL [Tesla K40d]",
    0x13bc: "GM107GL [Quadro K1200]",
    0x1431: "GM206GL [Tesla M4]",
    0x13bd: "GM107GL [Tesla M10]",
    0x17fd: "GM200GL [Tesla M40]",
    0x1b06: "GTX1080TI GPU",
    0x1db6: "Tesla V100 PCIE 32G GPU",
    0x15f7: "GP100GL [Tesla P100 PCIe 32GB]",
    0x15f9: "GP100GL [Tesla P100 SXM2 16GB]",
    0xf100: "Saturn-X: LightPulse Fibre Channel Host Adapter",
    0xf180: "LLPSe12002 EmulexSecure Fibre Channel Adapter",
    0x00d1: "HBA 9405W-16i"

}
VENDOR_ID = {

    0x1000: "LSI Logic / Symbios Logic",
    0x1001: "Kolter Electronic",
    0x1002: "Advanced Micro Devices, Inc",
    0x1003: "ULSI Systems",
    0x1004: "VLSI Technology Inc",
    0x1005: "Avance Logic Inc",
    0x1006: "Reply Group",
    0x1007: "NetFrame Systems Inc",
    0x1008: "Epson",
    0x100a: "Phoenix Technologies",
    0x100b: "National Semiconductor Corporation",
    0x100c: "Tseng Labs Inc",
    0x100d: "AST Research Inc",
    0x100e: "Weitek",
    0x1010: "Video Logic, Ltd",
    0x1011: "Digital Equipment Corporation",
    0x1012: "Micronics Computers Inc",
    0x1013: "Cirrus Logic",
    0x1014: "IBM",
    0x1015: "LSI Logic Corp of Canada",
    0x1016: "ICL Personal Systems",
    0x1017: "SPEA Software AG",
    0x1018: "Unisys Systems",
    0x1019: "Elitegroup Computer Systems",
    0x101a: "AT&T GIS (NCR)",
    0x101b: "Vitesse Semiconductor",
    0x101c: "Western Digital",
    0x101d: "Maxim Integrated Products",
    0x101e: "American Megatrends Inc",
    0x101f: "PictureTel",
    0x1020: "Hitachi Computer Products",
    0x1021: "OKI Electric Industry Co. Ltd",
    0x1022: "Advanced Micro Devices, Inc",
    0x1023: "Trident Microsystems",
    0x1024: "Zenith Data Systems",
    0x1025: "Acer Incorporated",
    0x1028: "Dell",
    0x1029: "Siemens Nixdorf IS",
    0x102a: "LSI Logic",
    0x102b: "Matrox Electronics Systems Ltd",
    0x102c: "Chips and Technologies",
    0x102d: "Wyse Technology Inc",
    0x102e: "Olivetti Advanced Technology",
    0x102f: "Toshiba America",
    0x1030: "TMC Research",
    0x1031: "Miro Computer Products AG",
    0x1032: "Compaq",
    0x1033: "NEC Corporation",
    0x1034: "Framatome Connectors USA Inc",
    0x1035: "Comp. & Comm. Research Lab",
    0x1036: "Future Domain Corp",
    0x1037: "Hitachi Micro Systems",
    0x1038: "AMP, Inc",
    0x1039: "Silicon Integrated Systems",
    0x103a: "Seiko Epson Corporation",
    0x103b: "Tatung Corp. Of America",
    0x103c: "Hewlett-Packard Company",
    0x103e: "Solliday Engineering",
    0x103f: "Synopsys/Logic Modeling Group",
    0x1040: "Accelgraphics Inc",
    0x1041: "Computrend",
    0x1042: "Micron",
    0x1043: "ASUSTeK Computer Inc",
    0x1044: "Adaptec",
    0x1045: "OPTi Inc",
    0x1046: "IPC Corporation, Ltd",
    0x1047: "Genoa Systems Corp",
    0x1048: "Elsa AG",
    0x1049: "Fountain Technologies, Inc",
    0x104a: "STMicroelectronics",
    0x104b: "BusLogic",
    0x104c: "Texas Instruments",
    0x104d: "Sony Corporation",
    0x104e: "Oak Technology, Inc",
    0x104f: "Co-time Computer Ltd",
    0x1050: "Winbond Electronics Corp",
    0x1051: "Anigma, Inc",
    0x1052: "?Young Micro Systems",
    0x1053: "Young Micro Systems",
    0x1054: "Hitachi, Ltd",
    0x1055: "Microchip Technology / SMSC",
    0x1056: "ICL",
    0x1057: "Motorola",
    0x1058: "Electronics & Telecommunications RSH",
    0x1059: "Kontron",
    0x105a: "Promise Technology, Inc",
    0x105b: "Foxconn International, Inc",
    0x105c: "Wipro Infotech Limited",
    0x105d: "Number 9 Computer Company",
    0x105e: "Vtech Computers Ltd",
    0x105f: "Infotronic America Inc",
    0x1060: "United Microelectronics",
    0x1061: "I.I.T.",
    0x1062: "Maspar Computer Corp",
    0x1063: "Ocean Office Automation",
    0x1064: "Alcatel",
    0x1065: "Texas Microsystems",
    0x1066: "PicoPower Technology",
    0x1067: "Mitsubishi Electric",
    0x1068: "Diversified Technology",
    0x1069: "Mylex Corporation",
    0x106a: "Aten Research Inc",
    0x106b: "United Microelectronics",
    0x106c: "Hynix Semiconductor",
    0x106d: "Sequent Computer Systems",
    0x106e: "DFI, Inc",
    0x106f: "City Gate Development Ltd",
    0x1070: "Daewoo Telecom Ltd",
    0x1071: "Mitac",
    0x1072: "GIT Co Ltd",
    0x1073: "Yamaha Corporation",
    0x1074: "NexGen Microsystems",
    0x1075: "Advanced Integrations Research",
    0x1076: "Chaintech Computer Co. Ltd",
    0x1077: "QLogic Corp",
    0x1078: "Cyrix Corporation",
    0x1079: "I-Bus",
    0x107a: "NetWorth",
    0x107b: "Gateway, Inc",
    0x107c: "LG Electronics",
    0x107d: "LeadTek Research Inc",
    0x107e: "Interphase Corporation",
    0x107f: "Data Technology Corporation",
    0x1080: "Contaq Microsystems",
    0x1081: "Supermac Technology",
    0x1082: "EFA Corporation of America",
    0x1083: "Forex Computer Corporation",
    0x1084: "Parador",
    0x1086: "J. Bond Computer Systems",
    0x1087: "Cache Computer",
    0x1088: "Microcomputer Systems (M) Son",
    0x1089: "Data General Corporation",
    0x108a: "SBS Technologies",
    0x108c: "Oakleigh Systems Inc",
    0x108d: "Olicom",
    0x108e: "Oracle/SUN",
    0x108f: "Systemsoft",
    0x1090: "Compro Computer Services, Inc",
    0x1091: "Intergraph Corporation",
    0x1092: "Diamond Multimedia Systems",
    0x1093: "National Instruments",
    0x1094: "First International Computers",
    0x1095: "Silicon Image, Inc",
    0x1096: "Alacron",
    0x1097: "Appian Technology",
    0x1098: "Quantum Designs (H.K.) Ltd",
    0x1099: "Samsung Electronics Co., Ltd",
    0x109a: "Packard Bell",
    0x109b: "Gemlight Computer Ltd",
    0x109c: "Megachips Corporation",
    0x109d: "Zida Technologies Ltd",
    0x109e: "Brooktree Corporation",
    0x109f: "Trigem Computer Inc",
    0x123f: "LSI Logic",
    0x11ca: "LSI Systems, Inc",
    0x11c1: "LSI Corporation",
    0x10db: "Rohm LSI Systems, Inc",
    0x10df: "Emulex Corporation",
    0x1166: "Broadcom",
    0x10de: "NVIDIA Corporation",
    0x11f8: "PMC-Sierra Inc.",
    0x1344: "Micron Technology Inc.",
    0x15b3: "Mellanox Technologies",
    0x19a2: "Emulex Corporation",
    0x1c5f: "Beijing Memblaze Technology Co. Ltd.",
    0x1fc1: "QLogic, Corp.",
    0x8086: "Intel Corporation",
    0x9005: "Adaptec",
    0x9004: "Adaptec",
    0x14e4: "Brodcom Limited",
    0x144d: "Samsung Electronics Co Ltd",
    0x1924: "Solarflare Communications",
    0xcabc: "Cambricon"
}


def str2bytes(param):
    if sys.version_info < (3, 0):
        return bytes(param)
    else:
        return bytes(param, 'utf-8')


def getfruByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    # get system platform ,windows or Linux

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_fru_json = lib.get_fru_json
        get_fru_json.restype = ctypes.c_char_p
        get_fru_json.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_fru_json(str2bytes(client.host), str2bytes(client.username),
                              str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictfru = json.loads(result.decode("utf-8"))
        return dictfru


# 执行cmd命令，返回命令行获得的结果
def execSysCmd(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text


def getIpmitoolkey(result, key):
    param = key + r"[\. ]+: ([\w]+[\.]*[\w]*)"
    value = re.findall(param, result)
    return value


def getAllFruByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_all_fru_json = lib.get_all_fru_json
        get_all_fru_json.restype = ctypes.c_char_p
        get_all_fru_json.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_all_fru_json(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictfru = json.loads(result.decode('raw-unicode-escape'))
        # dictfru = json.loads(result.decode("utf-8"))
        return dictfru


def resetBMCByIpmi(client):
    '''
    reset bmc ipmi
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_mc_restart_cold = lib.set_mc_restart_cold
        set_mc_restart_cold.restype = ctypes.c_int
        set_mc_restart_cold.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int]
        result = set_mc_restart_cold(str2bytes(client.host), str2bytes(client.username),
                                     str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        return result


def getProductNameByIpmi(client):
    """
    get product Name information
    :return"""

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_fru_json = lib.get_fru_json
        get_fru_json.restype = ctypes.c_char_p
        lib.get_fru.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_fru_json(str2bytes(client.host), str2bytes(client.username),
                              str2bytes(client.passcode), str2bytes(client.lantype), client.port)

        dictfru = json.loads(result.decode('raw-unicode-escape'))
        # dictfru = json.loads(result.decode("utf-8"))
        productName = None
        if dictfru and 'code' in dictfru.keys():
            status = dictfru['code']
            if status == 0:
                productName = dictfru['data']['product_name']
            else:
                productName = ERR.get(status)

        return productName


def getMcInfoByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_mc_info_json = lib.get_mc_info_json
        get_mc_info_json.restype = ctypes.c_char_p
        lib.get_fru.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_mc_info_json(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        mcInfo = json.loads(result.decode("utf-8"))
        logger.utoolLog.info("[RAW] " + client.host + " mcinfo: [RES] " + str(mcInfo))
        return mcInfo


def getFirmwareVersoinByIpmi(client):
    '''
    get Product BMC Version By MC Info Ipmi
    :param client:
    :return product BMC Version:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_mc_info_json = lib.get_mc_info_json
        get_mc_info_json.restype = ctypes.c_char_p
        lib.get_fru.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_mc_info_json(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        mcInfo = json.loads(result.decode("utf-8"))
        bmcVersion = None
        if mcInfo and 'code' in mcInfo.keys():
            status = mcInfo['code']
            if status == 0:
                bmcVersion = mcInfo['data']['firmware_revision']
        return bmcVersion


def getSensorByIpmi(client):
    '''
    get sensor information
    :param client:
    :return product sensor  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sensor = lib.get_sensor
        get_sensor.restype = ctypes.c_char_p
        lib.get_fru.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_sensor(str2bytes(client.host), str2bytes(client.username),
                            str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        sensorList = json.loads(result.decode("utf-8"))
        return sensorList


def getSensorByNameByIpmi(client, sensorName):
    '''
    get sensor  information
    :param client:
    :return product sensor  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sensor_info_by_name = lib.get_sensor_info_by_name
        get_sensor_info_by_name.restype = ctypes.c_char_p
        get_sensor_info_by_name.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_char_p]
        result = get_sensor_info_by_name(str2bytes(client.host), str2bytes(client.username),
                                         str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(sensorName))
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def getSensorsTempByIpmi(client):
    '''
    get temp  information
    :param client:
    :return product temp  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sensors_temp = lib.get_sensors_temp
        get_sensors_temp.restype = ctypes.c_char_p
        get_sensors_temp.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_sensors_temp(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def getSensorsVoltByIpmi(client):
    '''
    get volt  information
    :param client:
    :return product volt  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sensors_volt = lib.get_sensors_volt
        get_sensors_volt.restype = ctypes.c_char_p
        get_sensors_volt.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_sensors_volt(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def getSdrElistByIpmi(client):
    '''
    get sdr elist  information
    :param client:
    :return sdr elist    information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sdrs_elist = lib.get_sdrs_elist
        get_sdrs_elist.restype = ctypes.c_char_p
        get_sdrs_elist.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_sdrs_elist(str2bytes(client.host), str2bytes(client.username),
                                str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def getSdrTypeByIpmi(client, type):
    '''
    get sensor  information
    :param client:
    :return product sensor  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_sensor_info_by_name = lib.get_sdrs_by_type
        get_sensor_info_by_name.restype = ctypes.c_char_p
        get_sensor_info_by_name.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_char_p]
        result = get_sensor_info_by_name(str2bytes(client.host), str2bytes(client.username),
                                         str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(type))
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def getEventLogByIpmi(client, filePath, startTime, endTime):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_event_log = lib.get_event_log
        get_event_log.restype = ctypes.c_int
        get_event_log.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                  ctypes.c_char_p, ctypes.c_long, ctypes.c_long, ]
        result = get_event_log(str2bytes(client.host), str2bytes(client.username),
                               str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                               str2bytes(filePath), startTime, endTime)
        return result


def getUserListByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_user_list_json = lib.get_user_list_json
        get_user_list_json.restype = ctypes.c_char_p
        get_user_list_json.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = get_user_list_json(str2bytes(client.host), str2bytes(client.username),
                                    str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def addUserByIpmi(client, bmc_user_name, bmc_password, priv_level, Enabled):
    """
    get Product FRU  information
    :param client:
    :return product FRU  information:
    """

    loadcdll = LoadCdll.LoadCdll()
    lib = loadcdll.loadCdll()
    if lib is not None:
        add_user = lib.add_user
        add_user.restype = ctypes.c_int
        add_user.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        result = add_user(str2bytes(client.host), str2bytes(client.username),
                          str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                          str2bytes(bmc_user_name), str2bytes(bmc_password), priv_level, Enabled)
        return result


def setUserPassByIpmi(client, username, userpass):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_user_password = lib.set_user_password
        set_user_password.restype = ctypes.c_int
        set_user_password.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                      ctypes.c_char_p, ctypes.c_char_p]
        result = set_user_password(str2bytes(client.host), str2bytes(client.username),
                                   str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(username),
                                   str2bytes(userpass))
        return result


def setUserPrivByIpmi(client, username, privlevel):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_user_priv = lib.set_user_priv
        set_user_priv.restype = ctypes.c_int
        set_user_priv.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                  ctypes.c_char_p, ctypes.c_int]
        result = set_user_priv(str2bytes(client.host), str2bytes(client.username),
                               str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                               str2bytes(username), privlevel)
        return result


def setUserNameByIpmi(client, oldusername, newusername):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_user_name = lib.set_user_name
        set_user_name.restype = ctypes.c_int
        set_user_name.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = set_user_name(str2bytes(client.host), str2bytes(client.username),
                               str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                               str2bytes(oldusername), str2bytes(newusername))
        return result


def setUserModByIpmi(client, username, enable):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_user_mod = lib.set_user_mod
        set_user_mod.restype = ctypes.c_int
        set_user_mod.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                 ctypes.c_char_p, ctypes.c_int]
        result = set_user_mod(str2bytes(client.host), str2bytes(client.username),
                              str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                              str2bytes(username), enable)
        return result


def getRaidTypeByIpmi(client):
    cmd = '0x3c 0x3b 0x02'
    return sendRawByIpmi(client, cmd)


def sendIPMIrawcmdByIpmi(client, netfun, command, datalist):
    '''
    send IPMI raw command
    :param client:
    :return:
    '''
    if datalist is not None:
        cmd = netfun + ' ' + command + ' ' + datalist
    else:
        cmd = netfun + ' ' + command
    return sendRawByIpmi(client, cmd)


def sendIPMIrawEXByIpmi(client, target, brige, netfun, command, datalist):
    '''
    send IPMI raw command
    ipmitool   -b 0x06 -t 0x20  raw 0x06 0x04
    55 00
    '''
    JSON = {}
    if datalist is not None:
        raw = netfun + ' ' + command + ' ' + datalist
    else:
        raw = netfun + ' ' + command
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    dictraw = {}
    res = "[Host] " + client.host + " [CMD] -b " + brige + " -t " + target + " raw " + raw + "[RES] "
    if lib is not None:
        send_raw_ex = lib.send_raw_ex
        send_raw_ex.restype = ctypes.c_char_p
        send_raw_ex.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        result = send_raw_ex(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode), str2bytes(client.lantype),
                             client.port, str2bytes(target), str2bytes(brige), str2bytes(raw))
        try:
            dictraw = json.loads(result.decode("utf-8"))
        except BaseException:
            dictraw['code'] = 102
            dictraw['data'] = res + "result is not a valid JSON format: " + str(result)
        logger.utoolLog.info(
            "[RAW] " + client.host + " -b " + brige + " -t " + target + " raw " + raw + ": [RES] " + str(dictraw))
        # print(dictraw)
        if dictraw == {}:
            dictraw['code'] = 103
            dictraw['data'] = res + ' result is none'
        else:
            if "code" in dictraw and "data" in dictraw:
                if dictraw['code'] != 0 and dictraw['data'] == "":
                    dictraw['data'] = res + ERR_dict.get(dictraw['code'])
            else:
                dictraw['code'] = 104
                dictraw['data'] = res + "result is not a valid JSON format: " + str(dictraw)
    else:
        dictraw['code'] = 101
        dictraw['data'] = 'cannot load ipmi dll.'
    return dictraw


# nouse
def getM5BmcVersionByIpmi(client, imagechoice):
    '''
    get M5 BMC Version
    :param client:
    :param imagechoice:
    :return:  BMC Version
    '''
    data = ''
    bmcVersion_all = {}
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        cmd = '0x3c 0x37 ' + str(imagechoice)
        send_raw = lib.send_raw
        send_raw.restype = ctypes.c_char_p
        send_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p]
        result = send_raw(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                          str2bytes(client.lantype), client.port, str2bytes(cmd))
        bmcInfo = json.loads(result.decode("utf-8"))
        if bmcInfo and 'code' in bmcInfo.keys():
            if bmcInfo.get('code') == 0 and bmcInfo.get('data') is not None:
                data = bmcInfo['data']
            else:
                bmcVersion_all['code'] = bmcInfo.get('code')
                bmcVersion_all['data'] = 'failed to get bmc version.'
                return bmcVersion_all
        else:
            bmcVersion_all['code'] = 103
            bmcVersion_all['data'] = 'failed to get bmc version.'
            return bmcVersion_all
    else:
        bmcVersion_all['code'] = 104
        bmcVersion_all['data'] = 'failed to get bmc version.'
        return bmcVersion_all

    bmcVersion = {}
    cmd_str = ' '.join(data).replace(' ', '').replace('\n', '')
    if len(cmd_str) < 24:
        bmcVersion_all['code'] = 1
        bmcVersion_all['data'] = "this command is incompatible with current server."
        return bmcVersion_all
    use_dict = {'00': 'no use', '01': 'in use'}
    inuseornot = cmd_str[0:2]
    bmcVersion['InUseOrNot'] = use_dict[inuseornot]
    health = cmd_str[2:4]
    bmcVersion['Health'] = health
    version = cmd_str[4:10]
    bmcVersion['Version'] = str(int(version[0:2], 16)) + '.' + str(int(version[2:4], 16)) + '.' + str(
        int(version[4:6], 16))
    datetime = cmd_str[10:24]
    year = datetime[0:4]
    pattern = re.compile('.{2}')
    time_hex = ' '.join(pattern.findall(year))
    seq = time_hex.split(' ')[::-1]
    year = ''.join(seq)
    year = int(year, 16)
    month = int(datetime[4:6], 16)
    day = int(datetime[6:8], 16)
    hour = int(datetime[8:10], 16)
    minute = int(datetime[10:12], 16)
    second = int(datetime[12:14], 16)
    bmcVersion['DateTime'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(hour) + ':' + str(
        minute) + ':' + str(second)
    bmcVersion_all['code'] = 0
    bmcVersion_all['data'] = bmcVersion

    return bmcVersion_all


# nouse
def getM5BiosVersionByIpmi(client):
    '''
    get M5 BIOS Version
    :param client:
    :return: M5 BIOS Version
    '''
    biosVersion = {}
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    biosVersion = {}
    if lib is not None:
        cmd = '0x3c 0x03 0x01 0x00'
        send_raw = lib.send_raw
        send_raw.restype = ctypes.c_char_p
        send_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p]
        result = send_raw(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                          str2bytes(client.lantype), client.port, str2bytes(cmd))
        biosInfo = json.loads(result.decode("utf-8"))
        if biosInfo and 'code' in biosInfo.keys():
            status = biosInfo['code']
            if status == 0:
                data = biosInfo['data']
                cmd_str = ' '.join(data).replace(' ', '').replace('\n', '')
                biosVersion['data'] = {}
                biosVersion['data']['Version'] = __hex2ascii(cmd_str)
                biosVersion['code'] = 0
            else:
                biosVersion['code'] = status
                biosVersion['data'] = 'failed to get bios version.'
        else:
            biosVersion['code'] = 103
            biosVersion['data'] = 'failed to get bios version.'
    else:
        biosVersion['code'] = 104
        biosVersion['data'] = 'failed to get bios version.'
    return biosVersion


# nouse
def getM5DiskcpldVersionByIpmi(client):
    '''
    get M5 Diskcpld Version
    :param client:
    :return: M5 Diskcpld Version
    '''
    data = ''
    DiskcpldVersion = {}
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        cmd = '0x3c 0x1c 0x01'
        send_raw = lib.send_raw
        send_raw.restype = ctypes.c_char_p
        send_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p]
        result = send_raw(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                          str2bytes(client.lantype), client.port, str2bytes(cmd))
        DiskcpldInfo = json.loads(result.decode("utf-8"))
        if DiskcpldInfo and 'code' in DiskcpldInfo.keys():
            status = DiskcpldInfo['code']
            if status == 0:
                data = DiskcpldInfo['data']
            else:
                DiskcpldVersion['code'] = status
                DiskcpldVersion['data'] = 'failed to get diskcpld version.'
                return DiskcpldVersion
        else:
            DiskcpldVersion['code'] = 103
            DiskcpldVersion['data'] = 'failed to get diskcpld version.'
            return DiskcpldVersion
    else:
        DiskcpldVersion['code'] = 104
        DiskcpldVersion['data'] = 'failed to get diskcpld version.'
        return DiskcpldVersion
    cmd_str = ' '.join(data).replace(' ', '').replace('\n', '')
    if len(cmd_str) < 17:
        DiskcpldVersion['code'] = 1
        DiskcpldVersion['data'] = "this command is incompatible with current server."
        return DiskcpldVersion
    present_stat = cmd_str[2:16]
    pattern = re.compile('.{2}')
    str_hex = ' '.join(pattern.findall(present_stat))
    seq = str_hex.split(' ')
    backplanes = cmd_str[16:len(cmd_str)]
    list = []
    i = 0
    for stat in seq:
        if '01' in stat:
            item_json = {}
            if len(backplanes) < (i + 1) * 2 * 28:
                DiskcpldVersion['code'] = 2
                DiskcpldVersion['data'] = "this command is incompatible with current server."
                return DiskcpldVersion
            plane = backplanes[i * 2 * 28:(i + 1) * 2 * 28]
            version = plane[0] + "." + plane[1]
            item_json['Version'] = version
            port = int(plane[2:4], 16)
            item_json['Port'] = str(port)
            hdddata = plane[4:54]
            item_json['HDDData'] = hdddata
            temp = int(plane[54:56], 16)
            item_json['Temp'] = temp
            list.append(item_json)
        i += 1
    DiskcpldVersion['code'] = 0
    DiskcpldVersion['data'] = list
    return DiskcpldVersion


# nouse
def getM5MainboardcpldVersionByIpmi(client):
    '''
    get M5 Mainboard Version
    :param client:
    :return: M5 Mainboard Version
    '''
    MainboradVersion = {}
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        cmd = '0x3c 0x03 0x05 0x00'
        send_raw = lib.send_raw
        send_raw.restype = ctypes.c_char_p
        send_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p]
        result = send_raw(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                          str2bytes(client.lantype), client.port, str2bytes(cmd))
        MainboradVersionInfo = json.loads(result.decode("utf-8"))
        if MainboradVersionInfo and 'code' in MainboradVersionInfo.keys():
            status = MainboradVersionInfo['code']
            if status == 0:
                data = MainboradVersionInfo['data']
                cmd_str = ' '.join(data).replace(' ', '').replace('\n', '')
                MainboradVersion['data'] = {}
                MainboradVersion['data']['Version'] = __hex2ascii(cmd_str)
                MainboradVersion['code'] = 0
            else:
                MainboradVersion['code'] = status
                MainboradVersion['data'] = 'failed to get mainboard version.'
        else:
            MainboradVersion['code'] = 103
            MainboradVersion['data'] = 'failed to get mainboard version.'
    else:
        MainboradVersion['code'] = 104
        MainboradVersion['data'] = 'failed to get mainboard version.'
    return MainboradVersion


def getM5PcieCountByIpmi(client):
    '''
    get pcie count
    :param client:
    :return:
    '''
    cmd_count = '0x3c 0x02 0x04 0xff 0xff'
    count_info = sendRawByIpmi(client, cmd_count)
    if count_info['code'] == 0:
        count_info['data'] = int(str(count_info['data']).strip(), 16)
    return count_info


def getM5PcieByIpmi(client, pcie_count):
    '''
    get pcie info
    :param client:
    :return:  pcie info
    '''
    pcie_data = ''
    Pcie = {}
    pcie_xcount = hex(pcie_count - 1)
    cmd_get = '0x3c 0x02 0x04 0x00 ' + str(pcie_xcount)
    pcieInfo_all = sendRawByIpmi(client, cmd_get)
    if pcieInfo_all["code"] == 0:
        pcie_data = pcieInfo_all['data']
    else:
        return pcieInfo_all

    cmd_str = ' '.join(pcie_data).replace(' ', '').replace('\n', '')
    if len(cmd_str) < 19 * 2 * pcie_count + 6:
        Pcie['code'] = 1
        Pcie['data'] = "this command is incompatible with current server."
        return Pcie
    cmd_str = cmd_str[6:]
    present_dict = {'00': 'Absent', '01': 'Present'}
    enable_dict = {'00': 'Disabled', '01': 'Enabled'}
    present_status_dict = {'00': 'onboard', '01': 'offboard'}
    width_dict = {'00': 'unknown', '01': 'X1', '02': 'X2', '04': 'X4', '08': 'X8', '10': 'X16'}
    speed_dict = {'00': 'unknown', '01': 'GEN1', '02': 'GEN2', '03': 'GEN3'}
    type_dict = {'00': 'Device was built before Class Code definitions were finalized',
                 '01': 'Mass storage controller', '02': 'Network controller',
                 '03': 'Display controller', '04': 'Multimedia device',
                 '05': 'Memory controller', '06': 'Bridge device',
                 '07': 'Simple communication controller', '08': 'Base system peripherals',
                 '09': 'input device', '0a': 'Docking stations', '0b': 'Processors',
                 '0c': 'Serial bus controller', '0d': 'Wireless controller',
                 '0e': 'intelligent I/O controller', '0f': 'Satellite communication controllers',
                 '10': 'Encryption/Decryption controllers',
                 '11': 'Data acquisition and signal processing controllers',
                 '12': 'Processing accelerators', '13': 'reserved',
                 'ff': 'Device does not fit in any defined classes', }
    riser_type_dict = {'00': 'unknown', '01': 'X8+X8+X8', '02': 'X8+X16', '03': 'X8+X8', '04': 'X16',
                       'ff': 'NO Riser'}
    location_dict = {'00': 'UP', '01': 'middle', '02': 'down', 'ff': 'NO Riser'}
    list = []
    for i in range(pcie_count):
        item_json = {}
        if len(cmd_str) < 19 * 2 * (i + 1):
            Pcie['code'] = 1
            Pcie['data'] = "this command is incompatible with current server."
            return Pcie
        pcie_str = '00010001' + cmd_str[19 * 2 * i:19 * 2 * (i + 1)]
        text = cmd_str[19 * 2 * i + 2:19 * 2 * (i + 1)]
        if max(text) == '0':
            continue
        index = pcie_str[8:10]
        item_json['Id'] = int(index, 16)
        type = pcie_str[38:40]
        item_json['Type'] = type_dict.get(type, 'null')
        busNumber = pcie_str[24:26]
        item_json['busNumber'] = '0x' + busNumber
        deviceNumber = pcie_str[26:28]
        item_json['deviceNumber'] = '0x' + deviceNumber
        functionNumber = pcie_str[28:30]
        item_json['functionNumber'] = '0x' + functionNumber
        enableStat = pcie_str[12:14]
        item_json['enableStat'] = enable_dict.get(enableStat, 'null')
        presentStat = pcie_str[10:12]
        item_json['presentStat'] = present_dict.get(presentStat, 'null')
        presentStatus = pcie_str[14:16]
        item_json['presentStatus'] = present_status_dict.get(presentStatus, 'null')
        vendorId = '0x' + str(pcie_str[18:20]) + str(pcie_str[16:18])
        item_json['vendorId'] = VENDOR_ID.get(int(vendorId, 16), 'null')
        deviceId = '0x' + str(pcie_str[22:24]) + str(pcie_str[20:22])
        item_json['deviceId'] = DEVICE_ID.get(int(deviceId, 16), 'null')
        # print(hex(int(deviceId,16)))
        # print(DEVICE_ID.get(hex(int(deviceId,16)),'null'))
        maxLinkWidth = pcie_str[30:32]
        item_json['maxLinkWidth'] = width_dict.get(maxLinkWidth, 'null')
        maxLinkSpeed = pcie_str[32:34]
        item_json['maxLinkSpeed'] = speed_dict.get(maxLinkSpeed, 'null')
        NegotiatedLinkWidth = pcie_str[34:36]
        item_json['NegotiatedLinkWidth'] = width_dict.get(NegotiatedLinkWidth, 'null')
        CurrentLinkSpeed = pcie_str[36:38]
        item_json['CurrentLinkSpeed'] = speed_dict.get(CurrentLinkSpeed, 'null')
        pcieSlot = pcie_str[40:42]
        item_json['pcieSlot'] = pcieSlot
        RiserType = pcie_str[42:44]
        item_json['RiserType'] = riser_type_dict.get(RiserType, 'null')
        pcieLocationOnRiser = pcie_str[44:46]
        item_json['pcieLocationOnRiser'] = location_dict.get(pcieLocationOnRiser, 'null')
        list.append(item_json)
    Pcie['code'] = 0
    Pcie['data'] = list
    return Pcie


# 十六进制转换Ascii
def __hex2ascii(data):
    '''
    hex to ascii
    :param data:
    :return: ascii
    '''
    list_s = []
    if data is not None and len(data) % 2 == 0:
        i = 0
        while (True):
            hex_str = data[i:i + 2]
            if '00' == hex_str:
                break
            chr_str = chr(int(hex_str, 16))
            list_s.append(chr_str)
            i += 2
            if i == len(data):
                break

    return ''.join(list_s)


# nouse
def getM5FanInfoByIpmi(client):
    '''
    get fan Info
    :param client:
    :return: fan Info
    '''
    fanInfo = {}
    cmd_mode = '0x3c 0x2e 0xff'
    fanInfo = sendRawByIpmi(client, cmd_mode)
    if fanInfo['code'] == 0:
        data = fanInfo['data'].split(' ')
    else:
        return fanInfo
    num = int(len(data) / 6)
    list = []
    present_dict = {'00': 'Absent', '01': 'Present'}
    for i in range(num):
        item_json = {}
        text = data[i * 6:(i + 1) * 6]
        item_json['id'] = i
        item_json['present'] = present_dict[text[1]]
        item_json['duty'] = int(text[3], 16)
        item_json['speed'] = int((text[5] + text[4]), 16) * 96
        list.append(item_json)
    fanInfo['data'] = list
    return fanInfo


# nouse
def getM6FanInfoByIpmi(client):
    '''
    get fan Info
    :param client:
    :return: fan Info
    '''
    cmd_mode = '0x3c 0x2e 0xff'
    fanInfo = sendRawByIpmi(client, cmd_mode)
    if fanInfo['code'] == 0:
        data = fanInfo['data'].split(' ')
    else:
        return fanInfo
    num = int(len(data) / 12)
    list = []
    present_dict = {'00': 'Absent', '01': 'Present'}
    for i in range(num):
        item_json = {}
        text = data[i * 12:(i + 1) * 12]
        item_json['id'] = i
        item_json['present'] = present_dict[text[1]]
        item_json['duty'] = int(text[3], 16)
        item_json['speed'] = int((text[5] + text[4]), 16)
        item_json['maxspeed'] = int((text[7] + text[6]), 16)
        item_json['model'] = (text[11] + text[10] + text[9] + text[8])
        list.append(item_json)
    fanInfo['data'] = list
    return fanInfo


# nouse
def getM5FanModeByIpmi(client):
    '''
    get fan mode
    :param client:
    :return: fan mode
    '''
    cmd_mode = '0x3c 0x30'
    fanModeInfo = sendRawByIpmi(client, cmd_mode)


# nouse
def setM5FanModeByIpmi(client, type):
    '''
    set fan mode
    :param client:
    :param type:
    :return: set fan mode
    '''
    cmd_mode = "0x3C 0x2F " + type
    fanModeInfo = sendRawByIpmi(client, cmd_mode)
    if fanModeInfo['code'] == 0:
        fanModeInfo['data'] = type
    return fanModeInfo


# nouse
def setM5FanSpeedByIpmi(client, id, speed_percent):
    '''
    set fan speed
    :param client:
    :param id:
    :param speed_percent:
    :return: set fan speed
    '''
    cmd_speed = "0x3C 0x2D  " + id + " " + speed_percent
    fanSpeedInfo = sendRawByIpmi(client, cmd_speed)
    if fanSpeedInfo['code'] == 0:
        fanSpeedInfo['data'] = {}
        fanSpeedInfo['data']['speed'] = speed_percent
        fanSpeedInfo['data']['id'] = id
    return fanSpeedInfo


# 获取设备信息
def getM6DeviceNumByIpmi(client, data):
    '''
    get Device Number info
    :param client:
    :return: Device Number
    '''
    cmd_get = '0x3c 0x2b ' + data
    Num_Info = sendRawByIpmi(client, cmd_get)
    Num = {}
    if Num_Info['code'] == 0:
        data_list = Num_Info['data'].split(' ')
        if len(data_list) == 2:
            Num['code'] = 0
            Num['data'] = {}
            Num['data']['DevNum'] = int(data_list[0], 16)
            if data_list[1] == 'ff':
                Num['data']['DevConfNum'] = int(data_list[0], 16)
            else:
                Num['data']['DevConfNum'] = int(data_list[1], 16)
        elif len(data_list) == 3:
            Num['code'] = 0
            Num['data'] = {}
            Num['data']['DevNum'] = int(data_list[1], 16)
            if data_list[2] == 'ff':
                Num['data']['DevConfNum'] = int(data_list[1], 16)
            else:
                Num['data']['DevConfNum'] = int(data_list[2], 16)
        else:
            Num['code'] = 1
            Num['data'] = Num_Info['data']
    else:
        return Num_Info


# nouse
def getM5WebByIpmi(client):
    '''
    get web info
    :param client:
    :return: web info
    '''
    cmd_get = '0x32 0x69 0x01 0x00 0x00 0x00 '
    web_Info = __Service(client, cmd_get, 'web')
    return web_Info


# 获取kvm配置信息nouse
def getM5KvmByIpmi(client):
    '''
    get kvm info
    :param client:
    :return: kvm info
    '''
    cmd_get = '0x32 0x69 0x02 0x00 0x00 0x00 '
    kvm_Info = __Service(client, cmd_get, 'kvm')
    return kvm_Info


# 获取cd-media配置信息nouse
def getM5CdmediaByIpmi(client):
    '''
    get cd-media info
    :param client:
    :return: cd-media info
    '''
    cmd_get = '0x32 0x69 0x04 0x00 0x00 0x00 '
    media_Info = __Service(client, cmd_get, 'cd-media')
    return media_Info


# 获取fd-media配置信息nouse
def getM5FdmediaByIpmi(client):
    '''
    get fd-media info
    :param client:
    :return: fd-media info
    '''
    cmd_get = '0x32 0x69 0x08 0x00 0x00 0x00 '
    media_Info = __Service(client, cmd_get, 'fd-media')
    return media_Info


# 获取hd-media配置信息nouse
def getM5HdmediaByIpmi(client):
    '''
    get hd-media info
    :param client:
    :return: hd-media info
    '''
    cmd_get = '0x32 0x69 0x10 0x00 0x00 0x00 '
    media_Info = __Service(client, cmd_get, 'hd-media')
    return media_Info


# 获取ssh配置信息nouse
def getM5SshByIpmi(client):
    '''
    get ssh ifo
    :param client:
    :return: ssh info
    '''
    cmd_get = '0x32 0x69 0x20 0x00 0x00 0x00 '
    ssh_Info = __Service(client, cmd_get, 'ssh')
    return ssh_Info


# 获取telnet配置信息nouse
def getM5TelnetByIpmi(client):
    '''
    get telnet info
    :param client:
    :return: telnet info
    '''
    cmd_get = '0x32 0x69 0x40 0x00 0x00 0x00 '
    telnet_Info = __Service(client, cmd_get, 'telnet')
    return telnet_Info


# 获取solssh配置信息nouse
def getM5SolsshByIpmi(client):
    '''
    get solssh info
    :param client:
    :return: solssh info
    '''
    cmd_get = '0x32 0x69 0x80 0x00 0x00 0x00 '
    solssh_Info = __Service(client, cmd_get, 'solssh')
    return solssh_Info


# 获取vnc配置信息
def getM5VncByIpmi(client):
    '''
    get vnc ifo
    :param client:
    :return: ssh info
    '''
    cmd_get = '0x32 0x69 0x00 0x01 0x00 0x00 '
    vnc_Info = __Service(client, cmd_get, 'vnc')
    return vnc_Info


# 获取NF5568vnc配置信息
def getNF5568M5VncByIpmi(client):
    '''
    get vnc ifo
    :param client:
    :return: ssh info
    '''
    cmd_get = '0x32 0x69 0x40 0x00 0x00 0x00 '
    vnc_Info = __Service(client, cmd_get, 'vnc')
    return vnc_Info


def __Service(client, cmd_get, serviceName):
    '''
    common get service info
    :param client:
    :param cmd_get:
    :param serviceName:
    :return: service info
    '''
    get_Info = sendRawByIpmi(client, cmd_get)
    if get_Info['code'] == 0:
        data = get_Info['data']
    else:
        return get_Info
    cmd_str = ' '.join(data).replace(' ', '').replace('\n', '')
    if len(cmd_str) < 88:
        get_Info['code'] = 4
        get_Info['data'] = 'this command is incompatible with current server.'
        return get_Info
    item_json = {}
    status_dict = {'00': 'Disabled', '01': 'Enabled'}
    id = cmd_str[0:8]
    if id[0:2] == "00":
        item_json['Id'] = 0
    else:
        item_json['Id'] = str(math.log(int(id[0:2], 16), 2) + 1)
    item_json['ServiceName'] = serviceName
    status = cmd_str[8:10]
    item_json['Status'] = status_dict[status]
    InterfaceName = cmd_str[10:44]
    item_json['InterfaceName'] = __hex2ascii(InterfaceName)
    if item_json['InterfaceName'] not in ["both", "eth0", "eth1", "bond1"]:
        item_json['InterfaceName'] = 'N/A'
    NonsecurePort = cmd_str[44:52]
    if "ff" in NonsecurePort:
        item_json['NonsecurePort'] = 'N/A'
    else:
        item_json['NonsecurePort'] = __hex2int(NonsecurePort)

    SecurePort = cmd_str[52:60]
    if "ff" in SecurePort:
        item_json['SecurePort'] = 'N/A'
    else:
        item_json['SecurePort'] = __hex2int(SecurePort)
    Timeout = cmd_str[60:68]
    if "ff" in Timeout:
        item_json['Timeout'] = 'N/A'
        item_json['MinimumTimeout'] = 'N/A'
        item_json['MaximumTimeout'] = 'N/A'
    else:
        item_json['Timeout'] = __hex2int(Timeout)
        MinimumTimeout = cmd_str[72:80]
        item_json['MinimumTimeout'] = __hex2int(MinimumTimeout)
        MaximumTimeout = cmd_str[80:88]
        item_json['MaximumTimeout'] = __hex2int(MaximumTimeout)

    MaximumSessions = cmd_str[68:70]
    if "ff" in MaximumSessions:
        item_json['MaximumSessions'] = 'N/A'
    else:
        binmax = '{:08b}'.format(int(MaximumSessions, 16))
        item_json['MaximumSessions'] = int(binmax[2:8], 2)
    ActiveSessions = cmd_str[70:72]
    binac = '{:08b}'.format(int(ActiveSessions, 16))
    item_json['ActiveSessions'] = int(binac[2:8], 2)
    get_Info['data'] = item_json
    return get_Info


def setM5BiosPwdByIpmi(client, type, pwd):
    '''
    :param client:
    :param pwd:
    :return:
    '''
    cmd = "0x3c 0x4a 0x0f " + type + ' ' + pwd
    return sendRawByIpmi(client, cmd)


def clearBiospwdM5ByIpmi(client, type):
    '''
    clear bios pwd
    :param client:
    :param pwd:
    :return:
    '''
    cmd = "0x3c 0x4a 0x10 " + type
    return sendRawByIpmi(client, cmd)


def restoreBiosM5ByIpmi(client):
    '''
    clear bios pwd
    :param client:
    :param pwd:
    :return:
    '''
    cmd = "0x3c 0x4a 0x0c 0x20"
    return sendRawByIpmi(client, cmd)


# nouse
def restoreBiosM6ByIpmi(client):
    '''
    clear bios pwd
    :param client:
    :param pwd:
    :return:
    '''
    cmd = "0x3c 0x31 0x10 0x00"
    return sendRawByIpmi(client, cmd)


# 十六进制字符串转int
#  先逆序 后转换
def __hex2int(data):
    '''
    hex to int
    :param data:
    :return: hex to int
    '''
    if data is not None and len(data) % 2 == 0:
        pattern = re.compile('.{2}')
        time_hex = ' '.join(pattern.findall(data))
        seq = time_hex.split(' ')[::-1]
        data = ''.join(seq)
    return int(data, 16)


def clearSelByIpmi(client):
    '''
    clear sel
    :param client:
    :return clear sel
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        clear_sel = lib.clear_sel
        clear_sel.restype = ctypes.c_int
        clear_sel.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = clear_sel(str2bytes(client.host), str2bytes(client.username),
                           str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        return result


def powerControlByIpmi(client, type):
    '''
    power control
    :param client:
    :param type:
    :return: power control
    '''
    result = {}

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        power_control = lib.power_control
        power_control.restype = ctypes.c_char_p
        power_control.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                  ctypes.c_char_p]
        result = power_control(str2bytes(client.host), str2bytes(client.username),
                               str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(type))
        dictres = json.loads(result.decode("utf-8"))
        return dictres


def getPowerStatusByIpmi(client):
    '''
    get power status
    :param client:
    :return ppower status
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        power_status = lib.power_status
        power_status.restype = ctypes.c_char_p
        power_status.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        result = power_status(str2bytes(client.host), str2bytes(client.username),
                              str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


def locateServerByIpmi(client, state):
    '''
    locate server
    :param client:
    :param state:
    :return: locate server
    '''
    locate = {}

    cmd = "0x00 0x04 0x00 " + state
    return sendRawByIpmi(client, cmd)


# nouse
def setM5WebByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_web = __setService(client, '0x01 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_web


# 设置kvm
def setM5KvmByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_kvm = __setService(client, '0x02 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_kvm


# 设置cd-media#nouse
def setM5CdmediaByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_cdmedia = __setService(client, '0x04 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_cdmedia


# 设置fd-media#nouse
def setM5FdmediaByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_fdmedia = __setService(client, '0x08 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_fdmedia


# 设置he-media#nouse
def setM5HdmediaByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_hdmedia = __setService(client, '0x10 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_hdmedia


# 设置ssh#nouse
def setM5SshByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_ssh = __setService(client, '0x20 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0xff')
    return set_ssh


# 设置telnet#nouse
def setM5TelnetByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_telnet = __setService(client, '0x40 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0xff')
    return set_telnet


# 设置solssh#nouse
def setM5SolsshByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_solssh = __setService(client, '0x80 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0xff')
    return set_solssh


# 设置service
def __setService(client, serviceid_hex, enabled, interface, nonsecure, secure, time, maximum_hex):
    cmd_set = '0x32 0x6a  ' + serviceid_hex + ' ' + enabled + ' ' + interface + ' ' + nonsecure + ' ' + secure + ' ' + time + ' ' + maximum_hex + ' 0x00'
    return sendRawByIpmi(client, cmd_set)


def setM5VncPwdByIpmi(client, pwd):
    cmd = '0x3c 0x59 ' + pwd
    return sendRawByIpmi(client, cmd)


def setM5VncByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_vnc = __setService(client, '0x00 0x01 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_vnc


def setNF5568M5VncByIpmi(client, enabled, interface, nonsecure, secure, time):
    set_vnc = __setService(client, '0x40 0x00 0x00 0x00', enabled, interface, nonsecure, secure, time, '0x00')
    return set_vnc


def getM5BiosByipmi(client, cmd, List):
    '''
    只执行单条命令
    :param client:
    :param filepath:
    :return:
    '''
    Info_data = sendRawByIpmi(client, cmd)
    if Info_data.get('code') == 0:
        cmd_result = Info_data.get('data')
    else:
        return Info_data
    bios_Info = {}
    result = M5biosResultExplanByIpmi(cmd_result, List)
    if result:
        if result.get('code') == 0:
            bios_Info['code'] = 0
            bios_Info['data'] = result.get('data')
        else:  # 解析的返回值不是9或6，暂时未解析
            bios_Info['code'] = 1
            bios_Info['data'] = 'failed to get info.'
    else:  # 解析失败
        bios_Info['code'] = 2
        bios_Info['data'] = 'failed to get info.'
    return bios_Info


def M5biosResultExplanByIpmi(cmd_result, List):
    '''
    # 根据返回结果，对应解析出它的状态
    # 返回值格式：01 00 00 C8 00 01 00 01 00
    # 从左到右返回值说明：
    # 01 00 -- 高位00 低位01 --返回值个数
    # 00 C8 -- 高位00 -- GroupIndex 低位C8--SubIndex
    # 00--标志位，是否有修改过，00 表示未被修改，01 表示被修改。
    # 01 00 -- 高位00 低位01 --Current Value  关注当前值Current Value，与set时相似
    # 01 00 -- 高位00 低位01 --Default Value
    # 将get和set的Current Value相比较，对应找到当前值并进行展示
    :param cmd_result:
    :param List:
    :return:
    '''
    result = {}
    result_split = str(cmd_result).split()
    if len(result_split) == 9:
        currentValueL = result_split[5]  # 取出低位，索引从0开始
        currentValueH = result_split[6]  # 取出高位
        Flag_set = False
        set_Attribute = List['setter']
        attribute = List['description']
        for set_cmd in set_Attribute:
            temp_set_cmd = set_cmd['cmd']
            set_split = str(temp_set_cmd).split()
            set_L = set_split[-2]
            set_H = set_split[-1]
            if currentValueL.lower() == set_L[2:].lower() and currentValueH.lower() == set_H[2:].lower():
                Flag_set = True
                key = str(attribute)
                value = set_cmd['value']
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
                break
        if Flag_set == False:
            # 出现这种现象的原因有两种
            # 一种是可能输入的BIOS项拼写错误，
            # 一种是设置项输入是数字，不能直接将get和set的直接进行对比，直接将get的值读出即可
            if List['input']:
                value_int = (str(currentValueH) + (str(currentValueL)))
                getValue = int(value_int, 16)
                key = str(attribute)
                value = getValue
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
            else:
                key = str(attribute)
                value = "Unsupport"
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
    elif len(result_split) == 6:
        # result_split = str(cmd_result).split()
        currentValueH = ''.join(result_split[2:])  # 取出选项值
        Flag_set = False
        set_Attribute = List['setter']
        attribute = List['description']
        for set_cmd in set_Attribute:
            temp_set_cmd = set_cmd['cmd']
            set_split = str(temp_set_cmd).split()
            leng = len(set_split)
            for s in range(1, leng + 1):
                set_split[s - 1] = set_split[s - 1].replace("0x", "")
            set_H = ''.join(set_split[-4:])
            if currentValueH.upper() == set_H.upper():
                Flag_set = True
                key = str(attribute)
                value = set_cmd['value']
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
                break
        if Flag_set == False:
            # 出现这种现象的原因有两种
            # 一种是可能输入的BIOS项拼写错误，
            # 一种是设置项输入是数字，不能直接将get和set的直接进行对比，直接将get的值读出即可
            if List['input']:
                s = list(reversed(result_split[2:]))
                value_int = ''.join(s)
                getValue = int(value_int, 16)
                key = str(attribute)
                value = str(getValue)
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
            else:
                key = str(attribute)
                value = 'Unsupport'
                result['code'] = 0
                result['data'] = {}
                result['data']['key'] = key
                result['data']['value'] = value
    else:
        result['code'] = 1
        result['data'] = {}

    return result


def setM5BiosByipmi(client, cmd):
    return sendRawByIpmi(client, cmd)


def setM5BiosEffectiveByipmi(client):
    cmd = '0x3c 0x4a 0x02'
    return sendRawByIpmi(client, cmd)


# nouse
def getLanByIpmi(client, channel):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        get_lan = lib.get_lan
        get_lan.restype = ctypes.c_char_p
        get_lan.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                            ctypes.c_char_p]
        result = get_lan(str2bytes(client.host), str2bytes(client.username),
                         str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(channel))
        dictsensor = json.loads(result.decode("utf-8"))
        return dictsensor


# nouse
def setIpv4ByIpmi(client, channel, ipAddress, mode, gateway, mask):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_ipv4 = lib.set_ipv4
        set_ipv4.restype = ctypes.c_int
        set_ipv4.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        result = set_ipv4(str2bytes(client.host), str2bytes(client.username),
                          str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(channel),
                          str2bytes(ipAddress), str2bytes(mode), str2bytes(gateway), str2bytes(mask))
        return result


def setIpv4ModeByIpmi(client, channel, mode):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_ipv4_mode = lib.set_ipv4_mode
        set_ipv4_mode.restype = ctypes.c_int
        set_ipv4_mode.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                  ctypes.c_char_p, ctypes.c_char_p]
        result = set_ipv4_mode(str2bytes(client.host), str2bytes(client.username),
                               str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                               str2bytes(channel), str2bytes(mode))
        return result


def setIpv4IPByIpmi(client, channel, ipAddress):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_ipv4_ip = lib.set_ipv4_ip
        set_ipv4_ip.restype = ctypes.c_int
        set_ipv4_ip.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                ctypes.c_char_p, ctypes.c_char_p]
        result = set_ipv4_ip(str2bytes(client.host), str2bytes(client.username),
                             str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                             str2bytes(channel), str2bytes(ipAddress))
        return result


def setIpv4GatewayByIpmi(client, channel, gateway):
    '''
    set ipv4 gateway
    :param client:
    :param gateway:
    :return:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_ipv4_gateway = lib.set_ipv4_gateway
        set_ipv4_gateway.restype = ctypes.c_int
        set_ipv4_gateway.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                                     ctypes.c_char_p, ctypes.c_char_p]
        result = set_ipv4_gateway(str2bytes(client.host), str2bytes(client.username),
                                  str2bytes(client.passcode), str2bytes(client.lantype), client.port,
                                  str2bytes(channel), str2bytes(gateway))
        return result


def setIpv4SubnetmaskByIpmi(client, channel, mask):
    '''
    set ipv4 subnetmask  information
    :param client:
    :return set  ipv4 subnetmask result:
    '''

    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_ipv4_subnetmask = lib.set_ipv4_subnetmask
        set_ipv4_subnetmask.restype = ctypes.c_int
        set_ipv4_subnetmask.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
        result = set_ipv4_subnetmask(str2bytes(client.host), str2bytes(client.username),
                                     str2bytes(client.passcode), str2bytes(client.lantype), client.port, str2bytes(channel),
                                     str2bytes(mask))
        return result


# nouse
def setBMCRestartColdByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_mc_restart_cold = lib.set_mc_restart_cold
        set_mc_restart_cold.restype = ctypes.c_int
        set_mc_restart_cold.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int]
        result = set_mc_restart_cold(str2bytes(client.host), str2bytes(client.username),
                                     str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        return result


# nouse
def setBMCRestartWarmByIpmi(client):
    '''
    get Product FRU  information
    :param client:
    :return product FRU  information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        set_mc_restart_warm = lib.set_mc_restart_warm
        set_mc_restart_warm.restype = ctypes.c_int
        set_mc_restart_warm.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int]
        result = set_mc_restart_warm(str2bytes(client.host), str2bytes(client.username),
                                     str2bytes(client.passcode), str2bytes(client.lantype), client.port)
        return result


# zone minutes in string
def setBMCTimezoneByIpmi(client, zoneMinutes):
    if zoneMinutes < 0:
        zoneMinutes16 = (0xffff + zoneMinutes + 0x1)
        zoneMinutes16 = hex(zoneMinutes16)
    elif zoneMinutes > 0:
        zoneMinutes16 = hex(zoneMinutes)
    else:
        zoneMinutes16 = "0x0000"
    # 执行
    cmd_time = '0x0A 0x5D 0x' + zoneMinutes16[-2:] + " " + zoneMinutes16[:-2]
    return sendRawByIpmi(client, cmd_time)


# 时间戳
def setBMCTimeByIpmi(client, stamptime):
    res = {}
    import time
    try:
        # 本地时间戳1555400100+28800
        stamptimelocal = stamptime - time.timezone
        # 本地时间戳16进制
        stampHex = hex(stamptimelocal)
        # 命令的16进制
        time16 = "0x" + stampHex[8:10] + " 0x" + stampHex[6:8] + " 0x" + stampHex[4:6] + " " + stampHex[0:4]
    except ValueError as e:
        res["code"] = 1
        return res
    # 执行
    cmd_time = '0x0A 0x49 ' + time16
    return sendRawByIpmi(client, cmd_time)


def setPsuWorkMode(client, id, cmd):
    cmdSet = '0x3c 0x28 ' + hex(id) + ' ' + hex(cmd)
    return sendRawByIpmi(client, cmdSet)


def setHDDLedPwrStatus(client, backplane_index, pid, ctr_type, state):
    cmdSet = '0x3c 0x50 ' + hex(backplane_index) + ' ' + hex(pid) + ' ' + hex(ctr_type) + ' ' + hex(state)
    return sendRawByIpmi(client, cmdSet)


def getHDDLedPwrStatus(client, backplane_index, pid, ctr_type):
    cmdSet = '0x3c 0x51 ' + hex(backplane_index) + ' ' + hex(pid) + ' ' + hex(ctr_type)
    data = sendRawByIpmi(client, cmdSet)
    if data.get('code') == 0 and data.get('data') is not None:
        tem = data.get('data').split(' ')
        data['data'] = tem[-1]
    return data


# vlan
# status 1enable 0disable
def setVlanByIpmi(client, channel, status, vlanid):
    res = {}
    if channel == 8:
        channel_raw = "0x08"
    else:
        channel_raw = "0x01"
    # vlan status
    if status == 0:
        status_raw = "0"
    elif status == 1:
        status_raw = "1"
    else:
        res["code"] = 1
        res["data"] = "status must be 1 or 0"
        return res
    # vlanid
    if int(vlanid) < 2 or int(vlanid) > 4094:
        res["code"] = 1
        res["data"] = "vlan id must be 2-4094"
        return res

    vlanid2 = bin(int(vlanid))[2:]
    zeronum = 15 - len(vlanid2)
    vlanid2 = "0" * zeronum + vlanid2
    # Byte[3:4]
    # Bit[0:14]: VLAN ID
    # 7654 3210  15141312 111098
    # Valid VLAN ID is 2~4094
    # Bit[15]: Enable Configure
    # 1=Enable, 0=Disable
    vlan316 = hex(int(vlanid2[7:15], 2))
    vlan416 = hex(int(status_raw + vlanid2[0:7], 2))
    cmd_get = '0x0C 0x01 ' + str(channel_raw) + " 0x14 " + vlan316 + " " + vlan416

    return sendRawByIpmi(client, cmd_get)


# serverty
# severity 0=information, 1=warning, 2=critical/error
# community
def setTrapByIpmi(client, key, value):
    res = {}
    if key == "community":
        if len(value) > 16:
            res["code"] = 1
            res["data"] = "Too long community(<=16)"
            return res
        op_raw = "0x01"
        value_raw = __str2ascii(value) + " 0x00"
    elif key == "severity":
        op_raw = "0x0d"
        if value == 0:
            value_raw = "0x00"
        elif value == 1:
            value_raw = "0x01"
        else:
            value_raw = "0x02"

    cmd_set = '0x3c 0x19 ' + op_raw + " " + str(value_raw)

    return sendRawByIpmi(client, cmd_set)


# Configure SNMPTrap Policy
def setSNMPTrapPolicyByIpmi(client, policyId, channel, enable):
    res = {}
    if policyId >= 1 and policyId <= 3:
        policyId_raw = "0x0" + str(policyId)
    else:
        res["code"] = 1
        return res
    if enable == 1:
        enable_raw = "0x" + str(policyId) + "8"
    elif enable == 0:
        enable_raw = "0x" + str(policyId) + "0"
    channel_raw = "0x" + str(channel) + str(policyId)

    cmd_set = '0x04 0x12 0x09 ' + policyId_raw + " " + enable_raw + " " + channel_raw + " 0x00"
    return sendRawByIpmi(client, cmd_set)


# Set alert type to SNMPTrap
def setAlertTypeByIpmi(client, policyId, channel, type):
    res = {}
    channel_raw = "0x0" + str(channel)
    if policyId >= 1 and policyId <= 3:
        policyId_raw = "0x0" + str(policyId)
    else:
        res["code"] = 1
        return res
    if type == "snmp":
        type_raw = "0x00"
    else:
        type_raw = "0x06"

    cmd_set = '0x0C 0x01 ' + channel_raw + " 0x12 " + policyId_raw + " " + type_raw + " 0x03 0x03"
    return sendRawByIpmi(client, cmd_set)


# Set destination IP
def setDestIPByIpmi(client, destinationId, channel, ip):
    res = {}
    channel_raw = "0x0" + str(channel)
    destinationId_raw = "0x0" + str(destinationId)
    ip_raw = hex(int(ip.split(".")[0])) + " " + hex(int(ip.split(".")[1])) + " " + hex(
        int(ip.split(".")[2])) + " " + hex(int(ip.split(".")[3]))
    cmd_set = '0x0C 0x01 ' + channel_raw + " 0x13 " + destinationId_raw + " 0x00 0x00 " + ip_raw + " 0x00 0x00 0x00 0x00 0x00 0x00"
    return sendRawByIpmi(client, cmd_set)


# BIOS boot options
def setBIOSBootOptionByIpmi(client, timeliness, option):
    res = {}
    if timeliness == "next":
        timeliness_raw = "0x20"
    else:
        timeliness_raw = "0x60"
    if option == "none":
        option_raw = "0x00"
    elif option == "HDD":
        option_raw = "0x02"
    elif option == "PXE":
        option_raw = "0x01"
    elif option == "CD":
        option_raw = "0x05"
    elif option == "BIOSSETUP":
        option_raw = "0x06"
    else:
        res["code"] = 1
        res["data"] = option + " is not supported"
        return res

    cmd_unlock = '0x00 0x08 0x05 '
    cmd_set = '0x00 0x08 0x05 ' + timeliness_raw + " " + option_raw + " 0x00 0x00 0x00"

    res_unlock = sendRawByIpmi(client, cmd_unlock)
    if res_unlock["code"] == 0:
        return sendRawByIpmi(client, cmd_set)
    else:
        return res_unlock


# BIOS boot mode
def setBootModeByIpmi(client, mode):
    res = {}
    if mode.upper() == "UEFI":
        mode_raw = "0x02"
    else:
        mode_raw = "0x01"
    cmd_set = '0x3c 0x48 0x00 0x2d ' + mode_raw + " 0x00 "
    return sendRawByIpmi(client, cmd_set)


# {'code': 0, 'data': '01'}
def getFirewallByIpmi(client):
    cmd_set = '0x3c 0x3b 0x15 '
    return sendRawByIpmi(client, cmd_set)


# {'data': '', 'code': 0}
def setFirewallByIpmi(client, state):
    res = {}
    if state == "close":
        state_raw = "0x00"
    elif state == "black":
        state_raw = "0x01"
    elif state == "white":
        state_raw = "0x02"
    else:
        res["code"] = 2
        res["data"] = "unsupport firewall state " + state
        return res
    cmd_set = '0x3c 0x3a 0x15 ' + state_raw
    return sendRawByIpmi(client, cmd_set)


def opWhiteListByIpmi(client, option, netfn, command):
    res = {}
    cmd = " firewall "
    if option == "add":
        op_linux = 1
        cmd = cmd + "enable channel 0x0f lun 0x00 "
    else:
        op_linux = 0
        cmd = cmd + "disable channel 0x0f lun 0x00 "

    if netfn != "":
        cmd = cmd + " netfn " + netfn
        if command != "":
            cmd = cmd + " command " + command

    # linux
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        firewall_enable_disable = lib.firewall_enable_disable
        firewall_enable_disable.restype = ctypes.c_int
        firewall_enable_disable.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_char_p]
        result = firewall_enable_disable(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                                         str2bytes(client.lantype), client.port, op_linux, str2bytes("0x0f"), str2bytes(netfn),
                                         str2bytes(command))
        return result


def opWhiteListByIpmi4(client, option, channel, lun, netfn, command):
    if option == "add":
        op_linux = 1
    else:
        op_linux = 0
    # linux
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        firewall_enable_disable = lib.firewall_enable_disable
        firewall_enable_disable.restype = ctypes.c_int
        firewall_enable_disable.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_char_p, ctypes.c_char_p]
        result = firewall_enable_disable(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode),
                                         str2bytes(client.lantype), client.port, op_linux, str2bytes(channel), str2bytes(lun),
                                         str2bytes(netfn), str2bytes(command))
        return result


# T6
def getSerialPortByIpmi(client):
    cmd_set = '0x3c 0x2c 0x00 0x00'
    return sendRawByIpmi(client, cmd_set)


def get80PortByIpmi(client):
    cmd_set = '0x32 0x73 0x00'
    return sendRawByIpmi(client, cmd_set)


# T6
def setSerialPortByIpmi(client, dest, port):
    # ['BMC','Host','PCIeNIC','MEZZNIC','SASExpander','mezzraid' ]
    res = {}
    cmd_set = '0x3c 0x2c '
    if dest == "panel":
        cmd_set = cmd_set + "0x01 "
        if port == "BMC":
            cmd_set = cmd_set + "0x01"
        elif port == "Host":
            cmd_set = cmd_set + "0x00"
        elif port == "PCIeNIC":
            cmd_set = cmd_set + "0x02"
        else:
            res = {"code": 101, "data": port + " is not supported"}
            return res
    elif dest == "sol":
        cmd_set = cmd_set + "0x02 "
        if port == "BMC":
            cmd_set = cmd_set + "0x01"
        elif port == "PCIeNIC":
            cmd_set = cmd_set + "0x02"
        elif port == "Host":
            # 00h UART1   10H  UART2
            cmd_set = cmd_set + "0x00"
        else:
            res = {"code": 101, "data": port + " is not supported"}
            return res
    else:
        res = {"code": 102, "data": "destination must be panel or sol"}
        return res
    return sendRawByIpmi(client, cmd_set)


# T6
def getTaskInfoByIpmi(client):
    cmd_set = '0x3c 0x77 0x00 0xff'
    return sendRawByIpmi(client, cmd_set)


# T6
def cancelTaskByIpmi(client, taskid):
    res = {}
    cmd_set = '0x3c 0x77 0x01 '
    if taskid < 0 or taskid > 8 or taskid == 7:
        res = {"code": 107, "data": "illegal task id(0-6, 8)"}
        return res
    else:
        cmd_set = cmd_set + "0x0" + str(taskid)
        return sendRawByIpmi(client, cmd_set)


# T6
def getTaskProgressByIpmi(client):
    cmd_set = '0x3c 0x78 0x00 '
    return sendRawByIpmi(client, cmd_set)


def sendRawByIpmi(client, raw):
    '''
    send  Raw Messaqge  information
    :param client:
    :return  result raw information:
    '''
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    dictraw = {}
    res = "[Host] " + client.host + " [CMD] " + raw + "[RES] "
    if lib is not None:
        send_raw = lib.send_raw
        send_raw.restype = ctypes.c_char_p
        send_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_char_p]
        result = send_raw(str2bytes(client.host), str2bytes(client.username), str2bytes(client.passcode), str2bytes(client.lantype),
                          client.port, str2bytes(raw))
        try:
            dictraw = json.loads(result.decode("utf-8"))
        except BaseException:
            dictraw['code'] = 102
            dictraw['data'] = res + "result is not a valid JSON format: " + str(result)
        # logger.utoolLog.info("[RAW] " + client.host + " " + raw + ": [RES] " + str(dictraw))
        if dictraw == {}:
            dictraw['code'] = 103
            dictraw['data'] = res + ' result is none'
        else:
            if "code" in dictraw and "data" in dictraw:
                if dictraw['code'] != 0 and dictraw['data'] == "":
                    dictraw['data'] = res + ERR_dict.get(dictraw['code'])
            else:
                dictraw['code'] = 104
                dictraw['data'] = res + "result is not a valid JSON format: " + str(dictraw)
    else:
        dictraw['code'] = 101
        dictraw['data'] = 'cannot load ipmi dll.'
    return dictraw


# set product serial
# nouse
def setproductserial(client, serial):
    '''
    set product serial information
    :param client:
    :return product serial result:
    '''
    # get system platform ,windows or Linux
    sysPlatform = platform.system()
    res = 0
    if sysPlatform == 'Windows':
        res = 2
    elif sysPlatform == 'Linux':
        sysArch = platform.architecture()
        if len(platform.architecture()) > 1:
            if platform.architecture()[0] == '32bit':
                fruverion = 'fru-change_x86_32'
            else:
                fruverion = 'fru-change_x86_64'
        execCmd = fruchange_path + os.sep + fruverion + " -nw -u " + client.username + " -p " + client.passcode + " -ip " + client.host + " PS " + serial
        cmdres = execSysCmd(execCmd).replace("\n", "").strip().lower()
        if serial in cmdres:
            res = 0
        else:
            res = 1
    else:
        res = 2
    return res


# set Adaptive port T6
def setAdaptiveportByIpmi(client, portlist):
    # 0dedicated 1mezz(ocpcard) 2 pcie 3lom1(onboard:magabit) 4lom2(onboard:ten magabit)
    # 0000 1111 后四位代表端口3210是否支持 1支持0不支持
    # portlist ['Dedicated:0', 'Mezz:1', 'mezz:2']
    res = {}
    portdict = {}
    for port in portlist:
        nic = port.split(":")[0].lower()
        portnumlist = port.split(":")[1]
        for i in range(len(portnumlist)):
            portnum = portnumlist[i]
            portnum = 1 << int(portnum)
            if nic not in portdict:
                portdict[nic] = portnum
            else:
                portdict[nic] = portnum | portdict[nic]
    if portdict is None or len(portdict) == 0:
        res = {"code": 105, "data": "nic list cannot be null"}
        return res
    elif len(portdict) > 2:
        res = {"code": 106, "data": "support up to 2 nics"}
        return res
    port_raw = {"dedicated": "0x00", "mezz": "0x01", "pcie": "0x02", "lom1": "0x03", "lom2": "0x04", "lom": "0x03"}
    count = len(portdict)
    cmd_set = '0x3c 0x13 '
    if count == 1:
        cmd_set = cmd_set + "0x01 "
    elif count == 2:
        cmd_set = cmd_set + "0x02 "
    for portname in portdict:
        cmd_set = cmd_set + port_raw[portname] + " " + str(hex(portdict[portname])) + " "
    # print (cmd_set)
    return sendRawByIpmi(client, cmd_set)


# set Adaptive port T6
def getAdaptiveportByIpmi(client):
    # 0dedicated 1mezz 2 pcie 3lom1 4lom2
    # 0000 1111 后四位代表端口3210是否支持 1支持0不支持
    # portlist ['Dedicated:0', 'Mezz:1', 'mezz:2']
    res = {}
    cmd_set = '0x3c 0x14 '
    return sendRawByIpmi(client, cmd_set)


def c(client, fruid, section, index, value):
    # fruid int
    # c0 Chassis Part Number
    # c1 Chassis Serial
    # c2 error
    # b0 Board Mfg
    # b1 Board Product
    # b2 Board Serial
    # b3 Board Part Number
    # p0 Product Manufacturer
    # p1 Product Name
    # p2 Product Part Number
    # p3 Product Version
    # p4 Product Serial
    # p5 Product Asset Tag
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        edit_fru = lib.fru_edit
        edit_fru.restype = ctypes.c_int
        edit_fru.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
                             ctypes.c_int, ctypes.c_char, ctypes.c_char, ctypes.c_char_p]
        result = edit_fru(
            str2bytes(client.host),
            str2bytes(client.username),
            str2bytes(client.passcode),
            str2bytes(client.lantype),
            client.port,
            fruid,
            ord(section), ord(index),
            str2bytes(value))
        return result


# bootdev
def setbootdev(client, bootdev, option):
    # bootdev
    boot_dev_list = ["none", "pxe", "disk", "safe", "diag", "cdrom", "bios", "floppy"]
    option_list = ["valid", "persistent", "efiboot"]

    InputToDev = {
        "none": 'none',
        "HDD": 'disk',
        "PXE": 'pxe',
        "CD": 'cdrom',
        "BIOSSETUP": 'bios',
    }
    InputToStyle = {
        'Once': '',
        'Continuous': 'persistent',
    }
    if bootdev not in InputToDev:
        return "-1"
    if option != "" and option not in InputToStyle:
        return "-2"
    loadCdll = LoadCdll.LoadCdll()
    lib = loadCdll.loadCdll()
    if lib is not None:
        chassis_set_bootdev = lib.chassis_set_bootdev
        chassis_set_bootdev.restype = ctypes.c_int
        chassis_set_bootdev.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
        result = chassis_set_bootdev(
            str2bytes(client.host),
            str2bytes(client.username),
            str2bytes(client.passcode),
            str2bytes(client.lantype),
            client.port,
            str2bytes(InputToDev.get(bootdev, "none")),
            # str2bytes(""))
            str2bytes(InputToStyle.get(option, "")))
        return result


# get system boot option
def getSysbootByIpmi(client):
    cmd_set = '0x00 0x09 0x05 0x00 0x00 '
    return sendRawByIpmi(client, cmd_set)


# nouse
# set system boot option
def setSysbootByIpmi(client, boottype, effective, device):
    res = {}
    InputToDev = {
        "none": '0x00',
        "HDD": '0x08',
        "PXE": '0x04',
        "CD": '0x14',
        "BIOSSETUP": '0x18',
    }
    InputToStyle = {
        'Once': '0',
        'Continuous': '1',
    }
    InputToType = {
        'Legacy': '0',
        'UEFI': '1',
    }
    cmd_sub = '0' + InputToStyle[effective] + InputToType[boottype] + '00000'
    cmd_sub_h = hex(int(cmd_sub, 2))
    cmd_set = '0x00 0x08 0x05 ' + cmd_sub_h + " " + InputToDev[device] + ' 0x00 0x00 0x00 '
    return sendRawByIpmi(client, cmd_set)


# M5 UPDATE BMC
def getMac(client):
    cmd_get = "0x3c 0x11 0x00 0x06 0x08 0x00"
    return sendRawByIpmi(client, cmd_get)


def setDedicatedMac(client, mac1):
    res = {}
    mac_cmd = ""
    mac_list = mac1.splite(" ")
    if len(mac_list) == 6:
        for m in mac_list:
            mac_cmd = mac_cmd + " 0x" + m
        cmd_set = '0x3c 0x11 0x01 0x06 0x08 0x00 ' + mac_cmd
        # print (cmd_set)
        # return {"code": 0}
        return sendRawByIpmi(client, cmd_set)
    else:
        return {"code": 1, "data": mac1 + " is not a valid MAC"}


def setHostname(client, hostname):
    res = {}
    length = len(hostname)
    hostname_cmd = " "
    for i in range(length):
        hostname_cmd = hostname_cmd + " " + str(hex(ord(hostname[i])))
    len16 = hex(length)
    if len(len16) == 3:
        len16 = "0x0" + len16[2]
    # 5-132为hostname
    cmd_set = ' 0x32 0x6c 0x01 0x00 0x00 ' + len16 + hostname_cmd + " 0x00" * (132 - 5 + 1 - length)
    # print (cmd_set)
    # return {"code": 0}
    return sendRawByIpmi(client, cmd_set)


def resetDNS(client):
    cmd_get = "0x32 0x6c 0x07 0x00"
    return sendRawByIpmi(client, cmd_get)


def getHostname(client):
    cmd_get = "0x32 0x6b 0x01 0x00"
    return sendRawByIpmi(client, cmd_get)


def getRaidStatusByIpmi(client, cid):
    cmd_get = " 0x3c 0xb9 0x05 0x00 " + hex(int(cid))
    return sendRawByIpmi(client, cmd_get)

# str转换Ascii


def __str2ascii(data):
    ascii_data = ""
    for c in data:
        ascii_data = ascii_data + " " + hex(ord(c))
    return ascii_data


if __name__ == "__main__":
    import RequestClient

    client = RequestClient.RequestClient()
    # client.setself("100.2.126.11","root","root",623,"lanplus")
    client.setself("100.2.73.41", "root", "root", 623, "lanplus")
    # client.setself("100.2.73.172","admin","admin",623,"lanplus")
    # client.setself("100.7.32.173","admin","admin",623,"lanplus")
    # client.setself("100.2.39.104","root","root",623,"lanplus")
    # client.setself("100.2.38.206","admin","admin",623,"lanplus")
    # client.setself("100.2.36.75","admin","admin",623,"lanplus")
    # client.setself("100.2.73.207","admin","admin",623,"lanplus")
    # fan = getM5FanInfoByIpmi(client)
    # fru = getRaidTypeByIpmi(client)
    target = '0x2c'
    brige = '0x06'
    netfun = '0x2e'
    command = '0xc2'
    datalist = '0x57 0x01 0x00 0x01 0x01'
    rawEx = sendIPMIrawEXByIpmi(client, target, brige, netfun, command, datalist)
    print(rawEx)
    # print(fan)
    # name = getProductNameByIpmi(client)
    # print('product Name:', name)
    # mc = getMcInfoByIpmi(client)
    # print(mc)
    # bmc = getFirmwareVersoinByIpmi(client)
    # print('bmcVersion:', bmc)
    # senorlist = getSensorByIpmi(client)
    # print('senlist:', senorlist)
    # sensor = getSensorByNameByIpmi(client,'CPU0_Temp')
    # sensor = getSdrElistByIpmi(client)
    # print('sensor:', sensor)
    # temp = getSensorByIpmi(client)
    # print(temp)
    # volt = getSensorsVoltByIpmi(client)
    # print(volt)
    # path1=os.path.dirname(os.path.abspath(__file__))
    # filePath = path1 + os.sep + client.host
    # eventlog = getEventLogByIpmi(client,filePath,1554112557,1584112557 )
    # print(eventlog)
    # user = getUserByNameIpmi(client,'admi1n')
    # print(user)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    #
    # addres = addUserByIpmi(client,"test","test",3,1)
    # print(addres)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    # pass1 = setUserPassByIpmi(client, 'test', 'test1')
    # print(pass1)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    # priv = setUserPrivByIpmi(client, 'test', 1)
    # print(priv)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    # username = setUserNameByIpmi(client, 'test', 'test1')
    # print(username)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    # mode = setUserModByIpmi(client, 'test1', 1)
    # print(mode)
    # userlist = getUserListByIpmi(client)
    # print(userlist)
    # clearSelByIpmi(client)
    # power = powerControlByIpmi(client, 'on')
    # print(power)
    # powerstatus = getPowerStatusByIpmi(client)
    # print(powerstatus)
    # lan = getLanByIpmi(client, '8')
    # print('get_lan:', lan)
    # setip = setIpv4ByIpmi(client, '8',None, 'dhcp', None, None)
    # print(setip)
    # mode = setIpv4ModeByIpmi(client, mode)
    # print(mode)
    # setIpv4IPByIpmi(client, ipAddress)
    # setIpv4GatewayByIpmi(client, gateway)
    # setIpv4SubnetmaskByIpmi(client, mask)
    # raw = sendRawByIpmi(client,"0x3c 0x42")
    # print('sendraw:', raw)

    # cold = setBMCRestartColdByIpmi(client)
    # print("setBMCRestartColdByIpmi:", cold)
    # warm = setBMCRestartWarmByIpmi(client)
    # print("warm:",warm)

    #
    # raw = getM5BmcVersionByIpmi(client, 0x02)
    # raw = getSensorByIpmi(client)
    # print('raw:', raw)
    # raw = getM5BiosVersionByIpmi(client)
    # print('raw:', raw)
    # raw = getM5DiskcpldVersionByIpmi(client)
    # print('raw:', raw)
    # raw = getM5MainboardcpldVersionByIpmi(client)
    # raw = getM5PcieCountByIpmi(client)
    # print(raw)
    # print('raw:', raw)
    # raw = clearSelByIpmi(client)
    # print('raw:', raw)
    # raw = powerControlByIpmi(client, 'on')
    # print('raw:', raw)
    # raw = getM5PcieByIpmi(client,raw.get('data'))
    # raw = getM5FanModeByIpmi(client)
    # raw = setM5FanModeByIpmi(client,'0x00')
    # raw = setM5FanSpeedByIpmi(client,'0x01',hex(20))
    # raw = getM5WebByIpmi(client)
    # raw = getM5SshByIpmi(client)
    # raw = getM6DeviceNumByIpmi(client,'0x00')
    # raw = getM6FanInfoByIpmi(client)
    # raw = getM5VncByIpmi(client)
    # raw = setM5VncByIpmi(client,'0x01','0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x00','0x0c 0x17 0x00 0x00','0x0d 0x17 0x00 0x00','0x08 0x07 0x00 0x00')
    # raw = __setService(client,'0x00 0x01 0x00 0x00','0x00','0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x00','0x0c 0x17 0x00 0x00','0x0d 0x17 0x00 0x00','0x08 0x07 0x00 0x00','0x00')
    # raw = __setService(client,'0x00 0x01 0x00 0x00','0x01','0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x00','0x0c 0x17 0x00 0x00','0x0d 0x17 0x00 0x00','0x08 0x07 0x00 0x00','0x00')
    # raw = locateServerByIpmi(client,'0x01')
    # cmd ='0x3c 0x48 0x00 0xC8 0x00 0x00'
    # raw = setM5BiosByipmi(client,cmd)
    # raw = getPowerStatusByIpmi(client)
    # print('raw:', raw)
