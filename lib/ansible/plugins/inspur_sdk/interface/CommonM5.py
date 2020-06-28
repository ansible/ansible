# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: base Class
#
#   @author: zhong
#   @Date:
#=========================================================================
'''
from ansible.plugins.inspur_sdk.util import HostTypeJudge
import threading
from ansible.plugins.inspur_sdk.util import RegularCheckUtil
from ansible.plugins.inspur_sdk.util import RequestClient
from ansible.plugins.inspur_sdk.command import backup, restore
from ansible.plugins.inspur_sdk.command import RestFunc
from ansible.plugins.inspur_sdk.command import IpmiFunc
import sys
import os
import json
import time
import re
from ansible.plugins.inspur_sdk.interface.Base import ascii2hex
from ansible.plugins.inspur_sdk.interface.Base import hexReverse
from ansible.plugins.inspur_sdk.interface.Base import Base
from ansible.plugins.inspur_sdk.interface.ResEntity import *
from ansible.plugins.inspur_sdk.util import configUtil
import collections
# sys.path.append(os.path.abspath("../command"))

rootpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(rootpath, "command"))
sys.path.append(os.path.join(rootpath, "util"))

MR_LD_CACHE_WRITE_BACK = 0x01
MR_LD_CACHE_WRITE_ADAPTIVE = 0x02
MR_LD_CACHE_READ_AHEAD = 0x04
MR_LD_CACHE_READ_ADAPTIVE = 0x08
MR_LD_CACHE_WRITE_CACHE_BAD_BBU = 0x10
MR_LD_CACHE_ALLOW_WRITE_CACHE = 0x20
MR_LD_CACHE_ALLOW_READ_CACHE = 0x40

# fwupdate 重试次数
retry_count = 3

STR_LD_CACHE_LIST = {
    0x01: 'Write Back',
    0x02: 'Adaptive Write',
    0x04: 'Read Ahead',
    0x08: 'Adaptive Read ahead',
    0x10: 'Write Caching OK If Bad BBU',
    0x20: 'Write Caching Allowed',
    0x40: 'Read Caching Allowed',
    0xfc: "Direct IO",
    0xfd: "Cached IO",
    0xfe: "Write through",
    0xff: "No Read Ahead"
}
STR_LD_ACCESS = {
    0: 'Unchanged'
}
STR_PD_INTERFACE_TYPE = {
    0x01: 'Parallel SCSI',
    0x02: 'SAS',
    0x03: 'SATA',
    0x04: 'FC',
    0xff: 'Unknown'
}

STR_MEDIA_TYPE = {
    0: 'HDD',
    1: 'SSD'
}
Enabled = {'Enable': 'Enabled', 'Disable': 'Disabled'}
PCI_IDS_LIST = {
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
PCI_IDS_DEVICE_LIST = {

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
CTRLMFC_maintainPdFailHistory = {0: False, 1: True}
CTRLPROP_enableJBOD = {0: False, 1: True}
CTRLPROP_Health = {0: 'OK', 1: 'Warning'}  # 未使用
# STR_PD_FW_STATE = {
#     0x00: 'Offline',
#     0x01: 'Online',
#     0x02: 'Open'
# }
STR_PD_FW_STATE = {
    0x00: 'Unconfigured Good',
    0x01: 'Unconfigured Bad',
    0x02: 'Hot Spare',
    0x10: 'Offline',
    0x11: 'Failed',
    0x14: 'Rebuild',
    0x18: 'Online',
    0x20: 'Copyback',
    0x40: 'JBOD',
    0x80: 'Sheld Unconfigured',
    0x82: 'Sheld Hot Spare',
    0x90: 'Sheld Configured'
}

raidlevels = {
    0: 'RAID0',
    1: 'RAID1',
    5: 'RAID5',
    6: 'RAID6',
    17: 'RAID10'
}


class CommonM5(Base):

    def getcapabilities(self, client, args):
        res = ResultBean()
        cap = CapabilitiesBean()
        getcomand = ['getadaptiveport', 'getbios', 'getcapabilities', 'getcpu', 'geteventlog', 'getfan', 'getfru', 'getfw', 'gethealth', 'getip', 'getnic', 'getpcie', 'getpdisk', 'getpower', 'getproduct', 'getpsu', 'getsensor', 'getservice', 'getsysboot', 'gettemp', 'gettime', 'gettrap', 'getuser', 'getvolt', 'getraid', 'getmemory', 'getldisk', 'getfirewall', 'gethealthevent']
        getcomand_not_support = ['getbiossetting', 'getbiosresult', 'geteventsub', 'getpwrcap', 'getmgmtport', 'getupdatestate', 'getserialport', 'getvnc', 'getvncsession', 'gettaskstate', 'getbiosdebug', 'getthreshold', 'get80port']
        setcommand = ['adduser', 'clearsel', 'collect', 'deluser', 'fancontrol', 'fwupdate', 'locatedisk', 'locateserver', 'mountvmm', 'powercontrol', 'resetbmc', 'restorebmc', 'sendipmirawcmd', 'settimezone', 'settrapcom', 'setbios', 'setip', 'setpriv', 'setpwd', 'setservice', 'setsysboot', 'settrapdest', 'setvlan', 'settime', 'setproductserial']
        setcommand_ns = ['setbiospwd', 'sethsc', 'clearbiospwd', 'restorebios', 'setfirewall', 'setimageurl', 'setadaptiveport', 'setserialport', 'powerctrldisk', 'recoverypsu', 'setvnc', 'downloadtfalog', 'setthreshold', 'addwhitelist', 'delwhitelist', 'delvncsession', 'downloadsol', 'exportbmccfg', 'exportbioscfg', 'importbioscfg', 'importbmccfg', 'canceltask', 'setbiosdebug']
        cap.GetCommandList(getcomand)
        cap.SetCommandList(setcommand)
        res.State('Success')
        res.Message(cap)
        return res

    def getcpu(self, client, args):
        '''
        get CPUs info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        cpu_Info = CPUBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getCpuInfoByRest(client)
        if res == {}:
            result.State('Failure')
            result.Message(['get cpu info failed'])
        elif res.get('code') == 0 and res.get('data') is not None:
            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get(
                    'data') is not None and 'cpu_status' in overalhealth.get('data'):
                cpu_Info.OverallHealth(
                    'OK' if overalhealth.get('data').get('cpu_status') == 'OK' else overalhealth.get('data').get(
                        'cpu_status').capitalize())
            else:
                cpu_Info.OverallHealth(None)

            cpus = res.get('data').get('processors', [])
            size = len(cpus)
            cpu_Info.Maximum(size)
            cpu_Info.TotalPowerWatts(None)
            list = []

            for cpu in cpus:
                cpu_singe = Cpu()
                if cpu.get('proc_status') == 1:
                    # 在位
                    name = 'CPU' + str(cpu.get('proc_id', 0))
                    cpu_singe.CommonName(name)
                    cpu_singe.Location('mainboard')
                    if 'proc_name' in cpu:
                        cpu_singe.Model(cpu.get('proc_name'))
                        if 'Intel' in cpu.get('proc_name'):
                            cpu_singe.Manufacturer('Intel')
                        else:
                            cpu_singe.Manufacturer(None)
                    else:
                        cpu_singe.Model(cpu.get(None))
                        cpu_singe.Manufacturer(None)
                    cpu_singe.L1CacheKiB(cpu.get('proc_l1cache_size', None))
                    cpu_singe.L2CacheKiB(cpu.get('proc_l2cache_size', None))
                    cpu_singe.L3CacheKiB(cpu.get('proc_l3cache_size', None))
                    # 获取温度
                    sensor = IpmiFunc.getSensorByNameByIpmi(client, name + '_Temp')
                    if sensor and sensor.get('code') == 0:
                        temp = sensor.get('data').get('value')
                        cpu_singe.Temperature(float(temp) if (temp is not None and temp.lower() != 'na') else None)
                    else:
                        cpu_singe.Temperature(None)
                    cpu_singe.EnabledSetting(None)
                    cpu_singe.ProcessorType('CPU')
                    cpu_singe.ProcessorArchitecture(None)
                    cpu_singe.InstructionSet(None)
                    cpu_singe.MaxSpeedMHz(cpu.get('proc_speed', None))
                    cpu_singe.TotalCores(cpu.get('proc_used_core_count', None))
                    cpu_singe.TotalThreads(cpu.get('proc_thread_count', None))
                    cpu_singe.Socket(None)
                    cpu_singe.PPIN(None)
                    cpu_singe.State('Enabled')
                    if 'status' in cpu:
                        cpu_singe.Health('OK' if cpu.get('status') == 'OK' else cpu.get('status').capitalize())
                    else:
                        cpu_singe.Health(None)
                else:
                    cpu_singe.CommonName('CPU' + str(cpu.get('proc_id')))
                    cpu_singe.Location('mainboard')
                    cpu_singe.State('Absent')

                list.append(cpu_singe.dict)
            cpu_Info.CPU(list)

            result.State('Success')
            result.Message([cpu_Info.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message(["get cpu information error, " + res.get('data')])
        else:
            result.State("Failure")
            result.Message(["get cpu information error, error code " + str(res.get('code'))])

        # logout
        RestFunc.logout(client)

        return result

    def getmemory(self, client, args):
        '''
        get DIMMs info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        memory_Info = MemoryBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getMemoryInfoByRest(client)
        if res == {}:
            result.State('Failure')
            result.Message(['get memory info failed'])
        elif res.get('code') == 0 and res.get('data') is not None:
            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get(
                    'data') is not None and 'mem_status' in overalhealth.get('data'):
                memory_Info.OverallHealth(
                    'OK' if overalhealth.get('data').get('mem_status') == 'OK' else overalhealth.get('data').get(
                        'mem_status').capitalize())
            else:
                memory_Info.OverallHealth(None)

            memorys = res.get('data').get('mem_modules', [])
            size = len(memorys)
            memory_Info.Maximum(res.get('data').get('total_memory_count', size))

            list = []
            memoryGiB = 0
            for memory in memorys:
                memory_singe = Memory()
                if memory.get('mem_mod_status') == 1:
                    # 在位
                    if 'mem_mod_cpu_num' in memory and 'mem_riser_num' in memory and 'mem_mod_socket_num' in memory:
                        name = 'DIMM' + '{0}{1}{2}'.format(memory.get('mem_mod_cpu_num', 0),
                                                           memory.get('mem_riser_num', 0),
                                                           memory.get('mem_mod_socket_num', 0))
                    else:
                        name = 'DIMM' + '{:03}'.format(memory.get('mem_mod_id', 0))

                    # if memory.get('mem_mod_slot') is None and 'mem_mod_cpu_num' in memory and 'mem_riser_num' in memory and 'mem_mod_socket_num' in memory:
                    #     location = 'CPU' + str(memory.get('mem_mod_cpu_num', 0)) + '_C' + str(memory.get('mem_riser_num',0)) + 'D' + str(memory.get('mem_mod_socket_num', 0))
                    # else:
                    location = 'mainboard'
                    memory_singe.CommonName(name)
                    memory_singe.Location(location)
                    memory_singe.Manufacturer(memory.get('mem_mod_vendor', None))
                    memory_singe.CapacityMiB(memory.get('mem_mod_size') * 1024 if 'mem_mod_size' in memory else None)
                    memory_singe.OperatingSpeedMhz(memory.get('mem_mod_frequency', None))
                    memory_singe.SerialNumber(memory.get('mem_mod_serial_num', None))
                    # memory_singe.MemoryDeviceType(memory.get('mem_mod_type', None))
                    memory_singe.MemoryDeviceType(typeconvert(memory.get('mem_mod_type', None)))
                    memory_singe.DataWidthBits(memory.get('mem_mod_data_width', None))
                    memory_singe.RankCount(memory.get('mem_mod_ranks', None))
                    if 'mem_mod_part_num' in memory:
                        memory_singe.PartNumber(memory.get('mem_mod_part_num').strip())
                    else:
                        memory_singe.PartNumber(None)
                    # memory_singe.Technology(memory.get('mem_mod_technology',None))
                    memory_singe.Technology(None)
                    memory_singe.MinVoltageMillivolt(memory.get('mem_mod_min_volt', None))
                    if 'mem_mod_size' in memory:
                        memoryGiB = memoryGiB + memory.get('mem_mod_size')
                    else:
                        memoryGiB = memoryGiB + 0
                    memory_singe.State('Enabled')
                    if 'status' in memory:
                        memory_singe.Health('OK' if memory.get('status') == 'OK' else memory.get('status').capitalize())
                    elif 'mem_mod_status' in memory:
                        memory_singe.Health('OK' if int(memory.get('mem_mod_status')) == 1 else None)
                    else:
                        memory_singe.Health(None)
                else:
                    if 'mem_mod_cpu_num' in memory and 'mem_riser_num' in memory and 'mem_mod_socket_num' in memory:
                        name = 'DIMM' + '{0}{1}{2}'.format(memory.get('mem_mod_cpu_num', 0),
                                                           memory.get('mem_riser_num', 0),
                                                           memory.get('mem_mod_socket_num', 0))
                    else:
                        name = 'DIMM' + '{:03}'.format(memory.get('mem_mod_id', 0))

                    # if memory.get('mem_mod_slot') is None and 'mem_mod_cpu_num' in memory and 'mem_riser_num' in memory and 'mem_mod_socket_num' in memory:
                    #     location = 'CPU' + str(memory.get('mem_mod_cpu_num', 0)) + '_C' + str(memory.get('mem_riser_num',0)) + 'D' + str(memory.get('mem_mod_socket_num', 0))
                    # else:
                    location = 'mainboard'
                    memory_singe.CommonName(name)
                    memory_singe.Location(location)
                    memory_singe.State('Absent')

                list.append(memory_singe.dict)
            memory_Info.TotalSystemMemoryGiB(memoryGiB)
            memory_Info.TotalPowerWatts(None)
            memory_Info.Memory(list)

            result.State('Success')
            result.Message([memory_Info.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message(["get memory information error, " + res.get('data')])
        else:
            result.State("Failure")
            result.Message(["get memory information error, error code " + str(res.get('code'))])

        # logout
        RestFunc.logout(client)
        return result

    def gethealth(self, client, args):
        '''
        get server overall health and component health
        :param client:
        :param args:
        :return:
        '''
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        Health_Info = HealthBean()
        Health = RestFunc.getHealthSummaryByRest(client)
        # 状态 ok present absent normal warning critical
        Health_dict = {'ok': 0, 'present': 1, 'absent': 2, 'normal': 3, 'warning': 4, 'critical': 5}
        Dist = {'OK': 'OK', 'None': None}
        if Health.get('code') == 0 and Health.get('data') is not None:
            info = Health.get('data')
            if 'Health_Status' in info:
                # Health_Info.System(info.get('Health_Status', None).capitalize())
                Health_Info.System(Dist.get(info.get('Health_Status'), info.get('Health_Status').capitalize()))
            else:
                health_list = [0]
                if 'cpu_status' in info and Health_dict.get(info['cpu_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['cpu_status'].lower()))
                if 'fans_status' in info and Health_dict.get(info['fans_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_status'].lower()))
                if 'fans_redundancy' in info and Health_dict.get(info['fans_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_redundancy'].lower()))
                if 'mem_status' in info and Health_dict.get(info['mem_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['mem_status'].lower()))
                if 'me_hlth_status' in info and Health_dict.get(info['me_hlth_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['me_hlth_status'].lower()))
                if 'nic_status' in info and Health_dict.get(info['nic_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['nic_status'].lower()))
                if 'power_supplies_status' in info and Health_dict.get(
                        info['power_supplies_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_status'].lower()))
                if 'power_supplies_redundancy' in info and Health_dict.get(
                        info['power_supplies_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_redundancy'].lower()))
                if 'storage_status' in info and Health_dict.get(info['storage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['storage_status'].lower()))
                if 'temperature_status' in info and Health_dict.get(info['temperature_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['temperature_status'].lower()))
                if 'voltage_status' in info and Health_dict.get(info['voltage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['voltage_status'].lower()))
                hel = list(Health_dict.keys())[list(Health_dict.values()).index(max(health_list))]
                Health_Info.System(Dist.get(hel.upper(), hel.capitalize()))
            Health_Info.CPU(Dist.get(info.get('cpu_status', 'None'), info.get('cpu_status').capitalize()))
            Health_Info.Memory(Dist.get(info.get('mem_status', 'None'), info.get('mem_status').capitalize()))
            Health_Info.Storage(Dist.get(info.get('storage_status', 'None'), info.get('storage_status').capitalize()))
            Health_Info.Network(Dist.get(info.get('nic_status', 'None'), info.get('nic_status').capitalize()))
            Health_Info.PSU(
                Dist.get(info.get('power_supplies_status', 'None'), info.get('power_supplies_status').capitalize()))
            Health_Info.Fan(Dist.get(info.get('fans_status', 'None'), info.get('fans_status').capitalize()))
            result.State('Success')
            result.Message([Health_Info.dict])
        elif Health == {}:
            result.State('Failure')
            result.Message(['get health info failed'])
        elif Health.get('code') != 0 and Health.get('data') is not None:
            result.State("Failure")
            result.Message(["get health information error, " + Health.get('data')])
        else:
            result.State("Failure")
            result.Message(["get health information error, error code " + str(Health.get('code'))])

        # logout
        RestFunc.logout(client)
        return result

    def getserver(self, client, args):
        '''
        get server overall health and component health
        :param client:
        :param args:
        :return:
        '''
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        Health_Info = HealthBean()
        Health = RestFunc.getHealthSummaryByRest(client)
        Power = RestFunc.getChassisStatusByRest(client)
        # 状态 ok present absent normal warning critical
        Health_dict = {'ok': 0, 'present': 1, 'absent': 2, 'normal': 3, 'warning': 4, 'critical': 5}
        Dist = {'OK': 'OK', 'None': None}
        led_dict = {0: 'On', 1: 'Off'}
        if Health.get('code') == 0 and Health.get('data') is not None and Power.get('code') == 0 and Power.get('data') is not None:
            info = Power.get('data')
            Health_Info.PowerStatus(info.get('power_status', 'None'))
            Health_Info.UIDLed(info.get('led_status', 'None'))
            info = Health.get('data')
            if 'Health_Status' in info:
                # Health_Info.System(info.get('Health_Status', None).capitalize())
                Health_Info.System(Dist.get(info.get('Health_Status'), info.get('Health_Status').capitalize()))
            else:
                health_list = [0]
                if 'cpu_status' in info and Health_dict.get(info['cpu_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['cpu_status'].lower()))
                if 'fans_status' in info and Health_dict.get(info['fans_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_status'].lower()))
                if 'fans_redundancy' in info and Health_dict.get(info['fans_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_redundancy'].lower()))
                if 'mem_status' in info and Health_dict.get(info['mem_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['mem_status'].lower()))
                if 'me_hlth_status' in info and Health_dict.get(info['me_hlth_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['me_hlth_status'].lower()))
                if 'nic_status' in info and Health_dict.get(info['nic_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['nic_status'].lower()))
                if 'power_supplies_status' in info and Health_dict.get(
                        info['power_supplies_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_status'].lower()))
                if 'power_supplies_redundancy' in info and Health_dict.get(
                        info['power_supplies_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_redundancy'].lower()))
                if 'storage_status' in info and Health_dict.get(info['storage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['storage_status'].lower()))
                if 'temperature_status' in info and Health_dict.get(info['temperature_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['temperature_status'].lower()))
                if 'voltage_status' in info and Health_dict.get(info['voltage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['voltage_status'].lower()))
                hel = list(Health_dict.keys())[list(Health_dict.values()).index(max(health_list))]
                Health_Info.System(Dist.get(hel.upper(), hel.capitalize()))
            Health_Info.CPU(Dist.get(info.get('cpu_status', 'None'), info.get('cpu_status').capitalize()))
            Health_Info.Memory(Dist.get(info.get('mem_status', 'None'), info.get('mem_status').capitalize()))
            Health_Info.Storage(Dist.get(info.get('storage_status', 'None'), info.get('storage_status').capitalize()))
            Health_Info.Network(Dist.get(info.get('nic_status', 'None'), info.get('nic_status').capitalize()))
            Health_Info.PSU(
                Dist.get(info.get('power_supplies_status', 'None'), info.get('power_supplies_status').capitalize()))
            Health_Info.Fan(Dist.get(info.get('fans_status', 'None'), info.get('fans_status').capitalize()))
            Health_Info.Voltage(Dist.get(info.get('voltage_status', 'None'), info.get('voltage_status').capitalize()))
            Health_Info.Temperature(Dist.get(info.get('temperature_status', 'None'), info.get('temperature_status').capitalize()))
            Health_Info.ME(Dist.get(info.get('me_hlth_status', 'None'), info.get('me_hlth_status').capitalize()))
            result.State('Success')
            result.Message([Health_Info.dict])
        elif Health == {}:
            result.State('Failure')
            result.Message(['get health info failed'])
        elif Health.get('code') != 0 and Health.get('data') is not None:
            result.State("Failure")
            result.Message(["get health information error, " + Health.get('data')])
        elif Power == {}:
            result.State('Failure')
            result.Message(['get chassis info failed'])
        elif Power.get('code') != 0 and Power.get('data') is not None:
            result.State("Failure")
            result.Message(["get chassis information error, " + Power.get('data')])
        else:
            result.State("Failure")
            result.Message(["get health information error, error code " + str(Health.get('code'))])

        # logout
        RestFunc.logout(client)
        return result

    def getsysboot(self, client, args):
        res = Base.getsysboot(self, client, args)
        if res.State == "Success":
            biosaAttribute = res.Message[0]
            args.bootmodeflag = True
            result = self.getbios(client, args)
            if result.State == "Success" and len(result.Message) > 0:
                bootmodedict = result.Message[0]
                for key in bootmodedict:
                    if "LEGACY" in bootmodedict.get(key).upper():
                        biosaAttribute['BootMode'] = "Legacy"
                    elif "UEFI" in bootmodedict.get(key).upper():
                        biosaAttribute['BootMode'] = "UEFI"
        return res

    def setsysboot(self, client, args):
        if args.effective is None and args.device is None and args.mode is None:
            res = {}
            res['State'] = "Success"
            res['Message'] = ["nothing to change"]
            return res
        if args.mode is not None:
            biosinfo = ""
            Bios_result = ResultBean()
            xml_path = os.path.join(IpmiFunc.command_path, "bios")
            # 不再多调用HostTypeJudge，直接调用IpmiFunc
            # 根据productname获取xml文件
            #hostTypeClient = HostTypeJudge.HostTypeClient()
            # get productName,BMC Version
            #productName, firmwareVersion = hostTypeClient.getProductNameByIPMI(args)

            productName = IpmiFunc.getProductNameByIpmi(client)
            firmwareVersion = IpmiFunc.getFirmwareVersoinByIpmi(client)
            if productName is None:
                res = {}
                res['State'] = "Not Support"
                res['Message'] = ["cannot get productName"]
                return res
            elif productName == 'NF5288M5' or productName == "NF8480M5":
                biosVersion = getbiosVersion(client)
                # print(biosVersion)
                if biosVersion is None:
                    Bios_result.State("Failure")
                    Bios_result.Message(["get bios version failed,please check the power status."])
                    return Bios_result
                elif productName == 'NF5288M5':
                    biosver = biosVersion.replace(".", "_")
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + biosver + ".xml"
                elif productName == 'NF8480M5':
                    biosVersion_split = biosVersion.split('.')
                    if len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 0 and int(
                            biosVersion_split[2]) >= 4:
                        xmlfilepath = xml_path + os.path.sep + productName + ".xml"
                    elif len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 1 and int(
                            biosVersion_split[2]) >= 0 and int(biosVersion_split[2]) <= 6:
                        xmlfilepath = xml_path + os.path.sep + productName + "_" + "411" + ".xml"
                    elif biosVersion in ["4.1.07"]:
                        xmlfilepath = xml_path + os.path.sep + productName + "_" + "417" + ".xml"
                    else:
                        xmlfilepath = xml_path + os.path.sep + productName + "_" + biosVersion + ".xml"
            else:
                xmlfilepath = xml_path + os.path.sep + productName + ".xml"
            # print(xmlfilepath)
            # print(os.path.exists(xmlfilepath))
            if os.path.exists(xmlfilepath) is False:
                if productName == "NF5288M5" or productName == "NF8480M5":
                    Bios_result.Message(["Not Supported current bios version: {0}.".format(biosVersion)])
                else:
                    Bios_result.Message(["Not Supported ProductName " + productName])
                Bios_result.State('Failure')
                return Bios_result

            # 根据路径读取xml文件，得到全部的信息字典列表infoList
            biosconfutil = configUtil.configUtil()  # 实例化类对象
            blongtoSet, descriptionList, infoList = biosconfutil.getSetOption(xmlfilepath)  # 读取xml文件，返回信息

            for info in infoList:
                info_str = str(info)
                if "Legacy" in info_str and "UEFI" in info_str:
                    setlist = info.get("setter")
                    for setcmd in setlist:
                        if args.mode in setcmd.get("value"):
                            bios_Info = IpmiFunc.setM5BiosByipmi(client, setcmd.get("cmd"))
                            if bios_Info and bios_Info.get('code') == 0:
                                break
                            else:
                                Bios_result.State('Failure')
                                Bios_result.Message(["set boot mode failed, please check the power and bios status."])
                                return Bios_result
            # 全部执行完成之后，执行生效的命令
            bios_effective = IpmiFunc.setM5BiosEffectiveByipmi(client)
            if bios_effective and bios_effective.get('code') == 0:
                biosinfo = "set boot mode success"
            else:
                Bios_result.State('Failure')
                Bios_result.Message(["failed to execute an order to make boot mode effective."])
                return Bios_result

        # 只输入一个则补全另一个
        if args.device is None and args.effective is not None:
            result = ResultBean()
            result.State("Failure")
            result.Message(["Boot device and effective should be set together."])
            return result
        if args.device is not None and args.effective is None:
            result = ResultBean()
            result.State("Failure")
            result.Message(["Boot device and effective should be set together."])
            return result
        if args.effective is not None and args.device is not None:
            result = ResultBean()
            # login
            headers = RestFunc.login(client)
            if headers == {}:
                login_res = ResultBean()
                login_res.State("Failure")
                login_res.Message(["login error, please check username/password/host/port"])
                return login_res
            client.setHearder(headers)
            # set
            boot_set = RestFunc.setSysBootByRest(client, args.mode, args.effective, args.device)
            if boot_set["code"] == 0:
                result.State("Success")
                result.Message(["the command will be invalid if the server is not rebooted within 60-second timeout"])
            else:
                result.State("Failure")
                result.Message([boot_set.get('data')])
            # logout
            RestFunc.logout(client)
            return result
        elif args.effective is None and args.device is None:
            result = ResultBean()
            result.State("Success")
            result.Message([biosinfo])
            return result

    def geteventlog(self, client, args):
        nicRes = ResultBean()
        if args.eventfile is not None:
            file_name = os.path.basename(args.eventfile)
            file_path = os.path.dirname(args.eventfile)
            # 用户输入路径，则默认文件名eventlog_psn_time
            if file_name == "":
                psn = "UNKNOWN"
                res = Base.getfru(self, client, args)
                if res.State == "Success":
                    frulist = res.Message[0].get("FRU", [])
                    if frulist != []:
                        psn = frulist[0].get('ProductSerial', 'UNKNOWN')
                else:
                    return res
                import time
                struct_time = time.localtime()
                logtime = time.strftime("%Y%m%d-%H%M", struct_time)
                file_name = "eventlog_" + psn + "_" + logtime
                args.eventfile = os.path.join(file_path, file_name)
            if not os.path.exists(file_path):
                try:
                    os.makedirs(file_path)
                except BaseException:
                    nicRes.State("Failure")
                    nicRes.Message(["cannot build path " + file_path])
                    return nicRes
            else:
                if os.path.exists(args.eventfile):
                    name_id = 1
                    path_new = os.path.splitext(args.eventfile)[0] + "(1)" + os.path.splitext(args.eventfile)[1]
                    while os.path.exists(path_new):
                        name_id = name_id + 1
                        path_new = os.path.splitext(args.eventfile)[0] + "(" + str(name_id) + ")" + \
                            os.path.splitext(args.eventfile)[1]
                    args.eventfile = path_new
        # check param
        if args.logtime is not None and args.count is not None:
            nicRes.State("Failure")
            nicRes.Message(["param date and count cannot be set together at one query"])
            return nicRes
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        # bmc zone in minutes
        date_res = RestFunc.getDatetimeByRest(client)
        if date_res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get bmc time"])
            RestFunc.logout(client)
            return nicRes
        elif date_res.get('code') == 0 and date_res.get('data') is not None:
            bmczone = date_res.get('data')['utc_minutes']
        elif date_res.get('code') != 0 and date_res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([date_res.get('data')])
            RestFunc.logout(client)
            return nicRes
        else:
            nicRes.State("Failure")
            nicRes.Message(["get bmc time error"])
            RestFunc.logout(client)
            return nicRes

        if args.logtime is not None:
            import time
            # self.newtime = "2018-05-31T10:10+08:00"
            if not RegularCheckUtil.checkBMCTime(args.logtime):
                nicRes.State("Failure")
                # nicRes.Message(["time param should be like YYYY-mm-ddTHH:MM±HH:MM"])
                nicRes.Message(["time param should be like YYYY-mm-ddTHH:MM+HH:MM"])
                RestFunc.logout(client)
                return nicRes
            if "+" in args.logtime:
                newtime = args.logtime.split("+")[0]
                zone = args.logtime.split("+")[1]
                we = "+"
            else:
                zone = args.logtime.split("-")[-1]
                newtime = args.logtime.split("-" + zone)[0]
                we = "-"
            hh = int(zone[0:2])
            mm = int(zone[3:5])
            # output zone in minutes
            showzone = int(we + str(hh * 60 + mm))
            # bmc zone in minutes

            try:
                # time.struct_time(tm_year=2019, tm_mon=4, tm_mday=16, tm_hour=15, tm_min=35, tm_sec=0, tm_wday=1, tm_yday=106, tm_isdst=-1)
                structtime = time.strptime(newtime, "%Y-%m-%dT%H:%M")
                # 时间戳1555400100
                stamptime = int(time.mktime(structtime))
                # 时间戳还差了 showzone - localzone的秒数
                stamptime = stamptime - (showzone * 60 - abs(int(time.timezone)))
            except ValueError as e:
                # print (str(e))
                nicRes.State("Failure")
                nicRes.Message(["illage time"])
                RestFunc.logout(client)
                return nicRes
        else:
            stamptime = ""
            showzone = bmczone

        if args.count is not None:
            if args.count <= 0:
                nicRes.State("Failure")
                nicRes.Message(["count param should be positive"])
                RestFunc.logout(client)
                return nicRes
        else:
            args.count = -1

        # check over
        res = RestFunc.getEventLog(client, args.count, stamptime, bmczone, showzone, False)
        # res = {"code":0,"data":"xxxxx"}
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get event log"])
        elif res.get('code') == 0 and res.get('data') is not None:
            json_res = {"EventLog": res.get('data')[::-1]}
            if args.eventfile is not None:
                try:
                    logfile = open(args.eventfile, "w")
                    # logfile.write(str(json))
                    logfile.write(
                        json.dumps(json_res, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=True))
                    logfile.close()
                except Exception as e:
                    # print  (str(e))
                    nicRes.State("Failure")
                    nicRes.Message(["cannot write log in " + args.eventfile])
                    RestFunc.logout(client)
                    return nicRes
                nicRes.State("Success")
                nicRes.Message(["Event logs is stored in : " + args.eventfile])
            else:
                nicRes.State("Success")
                nicRes.Message([json_res])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get eventlog error"])
        # logout
        RestFunc.logout(client)
        return nicRes

    def cleareventlog(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.deleteEventLog(client)
        result = ResultBean()
        if res == {}:
            result.State("Failure")
            result.Message(["clear event log error"])
        elif res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            result.Message(['clear event log success.'])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message([res.get('data')])
        else:
            result.State("Failure")
            result.Message(["clear event log error"])
        # logout
        RestFunc.logout(client)
        return result

    def clearauditlog(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.deleteAuditLog(client)
        result = ResultBean()
        if res == {}:
            result.State("Failure")
            result.Message(["clear audit log error"])
        elif res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            result.Message(['clear audit log success.'])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message([res.get('data')])
        else:
            result.State("Failure")
            result.Message(["clear audit log error"])
        # logout
        RestFunc.logout(client)
        return result

    def clearsystemlog(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        level_dict = {"alert": 1, "critical": 2, "error": 3, "notice": 4, "warning": 5, "debug": 6, "emergency": 7,
                      "info": 8, "all": 0}
        if args.level in level_dict:
            level = level_dict[args.level]
        else:
            level = 1
        result = ResultBean()
        if level > 0:
            res = RestFunc.deleteSystemLog(client, level)
            if res == {}:
                result.State("Failure")
                result.Message(["clear system log error"])
            elif res.get('code') == 0 and res.get('data') is not None:
                result.State("Success")
                result.Message(['clear system log success.'])
            elif res.get('code') != 0 and res.get('data') is not None:
                result.State("Failure")
                result.Message([res.get('data')])
            else:
                result.State("Failure")
                result.Message(["clear system log error"])
        else:
            Success_list = []
            Failure_list = []
            for i in range(1, 9):
                res = RestFunc.deleteSystemLog(client, i)
                if res.get('code') == 0 and res.get('data') is not None:
                    Success_list.append(level_dict[i])
                else:
                    Failure_list.append(level_dict[i])
            if Failure_list == []:
                result.State("Success")
                result.Message(['clear BMC system log success.'])
            elif Success_list == []:
                result.State("Failure")
                result.Message(['clear BMC system log error.'])
            else:
                result.State("Failure")
                result.Message(["the following level(s) failed: " + str(Failure_list)])

        # logout
        RestFunc.logout(client)
        return result

    def gettime(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getDatetimeByRest(client)
        timeinfo = ResultBean()
        if res == {}:
            timeinfo.State("Failure")
            timeinfo.Message(["cannot get bmc time"])
        elif res.get('code') == 0 and res.get('data') is not None:
            timeinfo.State("Success")
            data = res.get('data')
            zone_min = int(data.get('utc_minutes'))
            if zone_min >= 0:
                zone_EW = "+"
            else:
                zone_EW = "-"
            zone_HH = abs(zone_min) // 60
            if zone_HH < 10:
                zone_HH = "0" + str(zone_HH)
            else:
                zone_HH = str(zone_HH)

            zone_MM = zone_min % 60
            if zone_MM < 10:
                zone_MM = "0" + str(zone_MM)
            else:
                zone_MM = str(zone_MM)

            zone_HM = zone_EW + zone_HH + ":" + zone_MM
            import time
            time_stamp = data.get('localized_timestamp')
            struct_time = time.gmtime(time_stamp)
            format_time = time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
            res = collections.OrderedDict()
            if (str(data['auto_date']) == "0"):
                statustemp = "disabled"
            else:
                statustemp = "enabled"
            res['DateAutoSyn'] = statustemp
            res['Time'] = format_time
            res['Timezone'] = zone_HM
            if (str(data['auto_date']) != "0"):
                res['1stNTP'] = data.get('primary_ntp', 'N/A')
                res['2ndNTP'] = data.get('secondary_ntp', 'N/A')
                res['3ndNTP'] = data.get('third_ntp', 'N/A')
                if 'date_cycle' in data:
                    res['NTPSYNCycle'] = str(data.get('date_cycle')) + ' min'
            timeinfo.Message(res)
        elif res.get('code') != 0 and res.get('data') is not None:
            timeinfo.State("Failure")
            timeinfo.Message([res.get('data')])
        else:
            timeinfo.State("Failure")
            timeinfo.Message(["get bmc time error"])
        # logout
        RestFunc.logout(client)
        return timeinfo

    def settime(self, client, args):
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        timeinfo = setNTP(client, args)
        # logout
        RestFunc.logout(client)
        return timeinfo

    def downloadtfalog(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def gethealthevent(self, client, args):
        nicRes = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        # bmc zone in minutes
        date_res = RestFunc.getDatetimeByRest(client)
        if date_res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get bmc time"])
            return nicRes
        elif date_res.get('code') == 0 and date_res.get('data') is not None:
            bmczone = date_res.get('data')['utc_minutes']
        elif date_res.get('code') != 0 and date_res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([date_res.get('data')])
            return nicRes
        else:
            nicRes.State("Failure")
            nicRes.Message(["get bmc time error"])
            return nicRes

        showzone = bmczone

        # check over
        res = RestFunc.getEventLog(client, -1, "", bmczone, showzone, True)
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get event log"])
        elif res.get('code') == 0 and res.get('data') is not None:
            nicRes.State("Success")
            json = {"HealthEvents": res.get('data')[::-1]}
            nicRes.Message([json])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get event log error"])
        # logout
        RestFunc.logout(client)
        return nicRes

    def getraid(self, client, args):
        '''
        get raid information
        :param client:
        :param args:
        :return:
        '''
        raid_return = ResultBean()
        # 获取raid类型 raw命令
        raid_type = IpmiFunc.getRaidTypeByIpmi(client)
        if raid_type:
            if raid_type.get('code') == 0 and raid_type.get('data') is not None:
                raidtype = raid_type.get('data')
            else:
                raidtype = 'ff'
        else:
            raidtype = 'ff'
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        if raidtype == '01':
            raid_return = getCtrlInfo_PMC(client)
        elif raidtype == 'fe':
            raid_return.State('Failure')
            raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return raid_return
        elif raidtype == '00' or raidtype == '02' or raidtype == '03':
            raid_return = getCtrlInfo_LSI(client)
        elif raidtype == 'ff':
            raid_return = getCtrlInfo(client)
        else:
            raid_return = getCtrlInfo_LSI(client)
        # raid_bean = getCtrlInfo_PMC(client)
        # logout
        RestFunc.logout(client)
        return raid_return

    def getldisk(self, client, args):
        '''
        get logical disk info
        :param client:
        :param args:
        :return:
        '''
        ldisk_return = ResultBean()
        # 获取raid类型 raw命令
        raid_type = IpmiFunc.getRaidTypeByIpmi(client)
        if raid_type:
            if raid_type.get('code') == 0 and raid_type.get('data') is not None:
                raidtype = raid_type.get('data')
            else:
                raidtype = 'ff'
        else:
            raidtype = 'ff'
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        if raidtype == '01':
            ldisk_return = getLdInfo_PMC(client)
        elif raidtype == 'fe':
            ldisk_return.State('Failure')
            ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return ldisk_return
        elif raidtype == '00' or raidtype == '02' or raidtype == '03':
            ldisk_return = getLdInfo_LSI(client)
        elif raidtype == 'ff':
            ldisk_return = getLdInfo(client)
        else:
            ldisk_return = getLdInfo_LSI(client)
        # ldisk_return = getLdInfo(client)
        # logout
        RestFunc.logout(client)
        return ldisk_return

    def getnic(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getAdapterByRest(client)
        nicRes = ResultBean()
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get nic info"])
        elif res.get('code') == 0 and res.get('data') is not None:
            port_status_dict = {0: "Not Linked", 1: "Linked", 2: "NA", "Unknown": "NA"}
            nicRes.State("Success")
            nicinfo = NicAllBean()
            nicinfo.OverallHealth("OK")
            nicinfo.Maximum(1)
            PCIEinfo = NICBean()
            PCIEinfo.CommonName("PCIE")
            PCIEinfo.Location(None)
            PCIEinfo.Manufacturer(None)
            PCIEinfo.Model(None)
            PCIEinfo.Serialnumber(None)
            PCIEinfo.State(None)
            PCIEinfo.Health(None)
            i = 0
            data = res.get('data')['sys_adapters']
            controllerList = []
            for ada in data:
                adapterinfo = NICController()
                adapterinfo.Id(i)
                i = i + 1
                if ada['vendor'] == "":
                    adapterinfo.Manufacturer(None)
                else:
                    if "0x" in ada['vendor']:
                        maf = PCI_IDS_LIST.get(int(ada['vendor'], 16), ada['vendor'])
                        adapterinfo.Manufacturer(maf)
                    else:
                        adapterinfo.Manufacturer(ada['vendor'])
                if ada['model'] == "":
                    adapterinfo.Model(None)
                else:
                    if "0x" in ada['model']:
                        mod = PCI_IDS_DEVICE_LIST.get(int(ada['model'], 16), ada['model'])
                        adapterinfo.Model(mod)
                    else:
                        adapterinfo.Model(ada['model'])
                adapterinfo.Serialnumber(None)
                adapterinfo.FirmwareVersion(None)
                ports = ada['ports']
                adapterinfo.PortCount(len(ports))
                portlist = []
                for port in ports:
                    portBean = NicPort()
                    portBean.Id(port['id'])
                    portBean.MACAddress(port['mac_addr'])
                    portBean.LinkStatus(port_status_dict[port['status']])
                    portBean.MediaType(None)
                    portlist.append(portBean.dict)
                adapterinfo.Port(portlist)
                controllerList.append(adapterinfo.dict)
            PCIEinfo.Controller(controllerList)
            nicinfo.NIC([PCIEinfo.dict])
            nicRes.Message([nicinfo.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get nic info error"])
        # logout
        RestFunc.logout(client)
        return nicRes

    def getbios(self, client, args):
        '''
        get bios
        :param client:
        :param args:
        :return:
        '''
        Bios_result = ResultBean()
        xml_path = os.path.join(IpmiFunc.command_path, "bios")
        # 不再多调用HostTypeJudge，直接调用IpmiFunc
        # 根据productname获取xml文件
        #hostTypeClient = HostTypeJudge.HostTypeClient()
        # get productName,BMC Version
        #productName, firmwareVersion = hostTypeClient.getProductNameByIPMI(args)

        productName = IpmiFunc.getProductNameByIpmi(client)
        firmwareVersion = IpmiFunc.getFirmwareVersoinByIpmi(client)
        # print(productName)
        # print(firmwareVersion)
        if productName is None:
            res = {}
            res['State'] = "Not Support"
            res['Message'] = ["cannot get productName"]
            # print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False))
            return res
        elif productName == 'NF5288M5' or productName == "NF8480M5":
            biosVersion = getbiosVersion(client)
            # print(biosVersion)
            if biosVersion is None:
                Bios_result.State("Failure")
                Bios_result.Message(["get bios version failed,please check the power status."])
                return Bios_result
            elif productName == 'NF5288M5':
                biosver = biosVersion.replace(".", "_")
                xmlfilepath = xml_path + os.path.sep + productName + "_" + biosver + ".xml"
            elif productName == 'NF8480M5':
                biosVersion_split = biosVersion.split('.')
                if len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 0 and int(biosVersion_split[2]) >= 4:
                    xmlfilepath = xml_path + os.path.sep + productName + ".xml"
                elif len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 1 and int(
                        biosVersion_split[2]) >= 0 and int(biosVersion_split[2]) <= 6:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + "411" + ".xml"
                elif biosVersion in ["4.1.07"]:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + "417" + ".xml"
                else:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + biosVersion + ".xml"
        else:
            xmlfilepath = xml_path + os.path.sep + productName + ".xml"
        # print(xmlfilepath)
        # print(os.path.exists(xmlfilepath))
        if os.path.exists(xmlfilepath) is False:
            if productName == "NF5288M5" or productName == "NF8480M5":
                Bios_result.Message(["Not Supported current bios version: {0}.".format(biosVersion)])
            else:
                Bios_result.Message(["Not Supported ProductName " + productName])
            Bios_result.State('Failure')
            return Bios_result

        # 根据路径读取xml文件，得到全部的信息字典列表infoList
        biosconfutil = configUtil.configUtil()  # 实例化类对象
        blongtoSet, descriptionList, infoList = biosconfutil.getSetOption(xmlfilepath)  # 读取xml文件，返回信息
        # for bootmode only
        if "bootmodeflag" in vars(args):
            infoList2 = []
            for info in infoList:
                if info.get("description") == "BootMode":
                    infoList2.append(info)
                    break
                if info.get("description") == "BootType":
                    infoList2.append(info)
                    break
            infoList = infoList2

        class MyThread(threading.Thread):

            def __init__(self, func, args):
                super(MyThread, self).__init__()
                self.func = func
                self.args = args

            def run(self):
                self.result = self.func(*self.args)

            def get_result(self):
                try:
                    return self.result
                except Exception:
                    return {}

        # starttime = datetime.datetime.now()
        biosaAttribute = {}

        threads = []
        # thread_max = threading.BoundedSemaphore(5)
        # for i in range(len(infoList)):
        #     thread_max.acquire()
        #     # t = MyThread(getBiosAll, args=(client, [infoList[i]]))
        #     t = threading.Thread(target=getBiosAll, args=(client, [infoList[i]]))
        #     t.start()
        #     threads.append(t)
        # for t in threads:
        #     t.join()
        # dict.update(t.get_result())
        num = 20
        num_loc = int(len(infoList) / num)
        for i in range(num):
            t1 = i * num_loc
            t2 = (i + 1) * num_loc
            t1_infolist = infoList[t1:t2]
            t_bios = MyThread(getBiosAll, args=(client, t1_infolist))
            threads.append(t_bios)
        if (num * num_loc) < len(infoList):
            t_bios = MyThread(getBiosAll, args=(client, infoList[num * num_loc:]))
            threads.append(t_bios)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            biosaAttribute.update(t.get_result())

        # endtime = datetime.datetime.now()
        # during = endtime-starttime
        # print(during)
        Bios_result.Message([biosaAttribute])
        Bios_result.State('Success')
        return Bios_result

    def setbios(self, client, args):
        '''
        set bios
        :param client:
        :param args:
        :return:
        '''
        Bios_result = ResultBean()
        # 不再多调用HostTypeJudge，直接调用IpmiFunc
        # 根据productname获取xml文件
        #hostTypeClient = HostTypeJudge.HostTypeClient()
        # get productName,BMC Version
        #productName, firmwareVersion = hostTypeClient.getProductNameByIPMI(args)

        productName = IpmiFunc.getProductNameByIpmi(client)
        firmwareVersion = IpmiFunc.getFirmwareVersoinByIpmi(client)
        xml_path = os.path.join(IpmiFunc.command_path, "bios")
        if productName is None:
            res = {}
            res['State'] = "Not Support"
            res['Message'] = ["cannot get productName"]
            # print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False))
            return res
        elif productName == 'NF5288M5' or productName == "NF8480M5":
            biosVersion = getbiosVersion(client)
            # print(biosVersion)
            if biosVersion is None:
                Bios_result.State("Failure")
                Bios_result.Message(["get bios version failed, please check the power status."])
                return Bios_result
            elif productName == 'NF5288M5':
                biosver = biosVersion.replace(".", "_")
                xmlfilepath = xml_path + os.path.sep + productName + "_" + biosver + ".xml"
            elif productName == 'NF8480M5':
                biosVersion_split = biosVersion.split('.')
                if len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 0 and int(biosVersion_split[2]) >= 4:
                    xmlfilepath = xml_path + os.path.sep + productName + ".xml"
                elif len(biosVersion_split) == 3 and int(biosVersion_split[1]) == 1 and int(
                        biosVersion_split[2]) >= 0 and int(biosVersion_split[2]) <= 6:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + "411" + ".xml"
                elif biosVersion in ["4.1.07"]:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + "417" + ".xml"
                else:
                    xmlfilepath = xml_path + os.path.sep + productName + "_" + biosVersion + ".xml"
        else:
            xmlfilepath = xml_path + os.path.sep + productName + ".xml"
            # print(xmlfilepath)
            # print(os.path.exists(xmlfilepath))
        if os.path.exists(xmlfilepath) is False:
            if productName == "NF5288M5" or productName == "NF8480M5":
                Bios_result.Message(["Not Supported current bios version: {0}.".format(biosVersion)])
            else:
                Bios_result.Message(["Not Supported ProductName " + productName])
            Bios_result.State('Failure')
            return Bios_result

        if args.attribute is None and args.value is None and args.fileurl is None:
            Bios_result.Message(['please input a command at least.'])
            Bios_result.State('Failure')
        elif args.attribute is None and args.value is None and args.fileurl is not None:
            if os.path.exists(args.fileurl) and os.path.isfile(args.fileurl):
                path_service = args.fileurl
                try:
                    biosJson = restore_bios(client, path_service)
                    if len(biosJson) == 0:
                        Bios_result.Message(['file is empty.'])
                        Bios_result.State('Failure')
                        return Bios_result
                    # 执行单个设置 先读取文件，判断-a -v是否在列表中
                    # 根据路径读取xml文件，得到全部的信息字典列表infoList
                    biosconfutil = configUtil.configUtil()  # 实例化类对象
                    blongtoSet, descriptionList, infoList = biosconfutil.getSetOption(xmlfilepath)  # 读取xml文件，返回信息
                    for key, value in biosJson.items():
                        # 判断-a是否在列表中
                        if judgeAttInList(key.replace(" ", ''), descriptionList) is False:
                            Bios_result.State('Failure')
                            Bios_result.Message(["'{0}' is not in set options.".format(key)])
                            return Bios_result
                        Flag, cmd, infomation = judgeValueInList(key.replace(" ", ''), value, infoList)
                        if Flag:
                            # 执行子命令
                            bios_Info = IpmiFunc.setM5BiosByipmi(client, cmd)
                            if bios_Info and bios_Info.get('code') == 0:
                                continue
                            else:
                                Bios_result.State('Failure')
                                Bios_result.Message(
                                    ["bios cmd execution failed, please check the power and bios status."])
                                return Bios_result
                        else:
                            value_list = []
                            for values in infomation.get('setter', ''):
                                value_list.append(values.get('value'))
                            if value_list:
                                Bios_result.State('Failure')
                                Bios_result.Message(["'{0}' is not in '{1}' value options".format(
                                    value, key) + "," + "available -v: " + ','.join(value_list)])
                            else:
                                Bios_result.State('Failure')
                                Bios_result.Message(["{0} is not in '{1}' value options.".format(value, key)])
                            return Bios_result
                    # 全部执行完成之后，执行生效的命令
                    bios_effective = IpmiFunc.setM5BiosEffectiveByipmi(client)
                    if bios_effective and bios_effective.get('code') == 0:
                        Bios_result.State('Success')
                        Bios_result.Message(['bios attribute set successfully.'])
                        return Bios_result
                    else:
                        Bios_result.State('Failure')
                        Bios_result.Message(["failed to execute an order to make it effective."])
                        return Bios_result
                except BaseException:
                    Bios_result.Message(['file format error.'])
                    Bios_result.State('Failure')
            else:
                Bios_result.Message(['file path error.'])
                Bios_result.State('Failure')
        elif args.attribute is not None and args.value is not None and args.fileurl is None:
            # 执行单个设置 先读取文件，判断-a -v是否在列表中
            # args.attribute = args.attribute.replace(" ",'')
            # 根据路径读取xml文件，得到全部的信息字典列表infoList
            biosconfutil = configUtil.configUtil()  # 实例化类对象
            blongtoSet, descriptionList, infoList = biosconfutil.getSetOption(xmlfilepath)  # 读取xml文件，返回信息
            # 判断-a是否在列表中
            if judgeAttInList(args.attribute.replace(" ", ''), descriptionList) is False:
                Bios_result.State('Failure')
                Bios_result.Message(["'{0}' is not in set options.".format(args.attribute)])
                return Bios_result
            Flag, cmd, infomation = judgeValueInList(args.attribute.replace(" ", ''), args.value, infoList)
            if Flag:
                # 执行子命令
                bios_Info = IpmiFunc.setM5BiosByipmi(client, cmd)
                if bios_Info and bios_Info.get('code') == 0:
                    bios_effective = IpmiFunc.setM5BiosEffectiveByipmi(client)
                    if bios_effective and bios_effective.get('code') == 0:
                        Bios_result.State('Success')
                        Bios_result.Message(['bios attribute set successfully.'])
                        return Bios_result
                    else:
                        Bios_result.State('Failure')
                        Bios_result.Message(["failed to execute an order to make it effective."])
                        return Bios_result
                else:
                    Bios_result.State('Failure')
                    Bios_result.Message(["bios cmd execution failed, please check the power and bios status."])
                    return Bios_result
            else:
                value_list = []
                for value in infomation.get('setter', ''):
                    value_list.append(value.get('value'))
                if value_list:
                    Bios_result.State('Failure')
                    Bios_result.Message(["'{0}' is not in '{1}' value options".format(args.value,
                                                                                      args.attribute) + "," + "available -v: " + ','.join(
                        value_list)])
                else:
                    Bios_result.State('Failure')
                    Bios_result.Message(["'{0}' is not in '{1}' value options.".format(args.value, args.attribute)])
                return Bios_result
        else:
            Bios_result.Message(['-a must be used with -v,mutually exclusive with -f.'])
            Bios_result.State('Failure')
        return Bios_result

    def setbiospwd(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getbiossetting(self, client, args):
        '''
        get the BIOS debug enabled status
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def getbiosresult(self, client, args):
        '''
        get bios config result
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def getbiosdebug(self, client, args):
        '''
        get the bios debug enabled status
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def clearbiospwd(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def restorebios(self, client, args):
        '''
        restore BIOS setup factory configuration
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def restorebmc(self, client, args):
        '''
        restore BMC factory configuration
        :param client:        :param args:
        :return:
        '''
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # restoreBMCByRest
        res = RestFunc.restoreBMCByRest(client)
        if res.get('code') == 0:
            result.State('Success')
            result.Message(['restore BMC Success,please wait for a few minutes'])
        else:
            result.State('Failure')
            result.Message(['please input image path'])
        return result

    def mountvmm(self, client, args):
        '''
        mount or unmount virtual media
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()

        # 首先判断路径下文件在不在(paramiko)
        # if os.path.isfile(args.image) is False:
        #     result.State('Failure')
        #     result.Message(['file is not exist,please check the path.'])
        #     return result

        if args.operatortype == 'Mount' and args.image is None:
            result.State('Failure')
            result.Message(['please input image path'])
            return result
        elif args.operatortype == 'Unmount' and args.image is not None:
            result.State('Failure')
            result.Message(['Currently image(-i) is not needed'])
            return result
        elif args.operatortype == 'Mount' and args.image is not None:
            # 挂载
            # 判断文件是否是iso格式
            if args.image[-4:] != '.iso':
                result.State('Failure')
                result.Message(['The file format should be iso.'])
                return result
            # 将image拆成 host path filename,原格式protocol://[username:password@]IP[:port]/directory/filename。
            if '://' not in args.image or '/' not in args.image:
                result.State('Failure')
                result.Message(['image(-i) format error'])
                return result
            try:
                [protocol, data] = args.image.split('://')
                List = data.split('/')
                if len(List) == 1:
                    result.State('Failure')
                    result.Message(['image(-i) format error'])
                    return result
                host = List[0]
                path_list = List[1:-1]
                filename = List[-1]
                if '@' in host and ':' in host:
                    [username_password, ip_port] = host.split('@')
                    if ':' in username_password:
                        [user, passwd] = username_password.split(':')
                    else:
                        [user, passwd] = '', ''
                    if ':' in ip_port:
                        [ip, port] = ip_port.split(':')
                    else:
                        ip = ip_port
                elif '@' in host and ':' not in host:
                    result.State('Failure')
                    result.Message(['image(-i) format error'])
                    return result
                elif '@' not in host and ':' in host:
                    [ip, port] = host.split(':')
                    [user, passwd] = '', ''
                else:
                    ip = host
                    [user, passwd] = '', ''
                path = '/' + '/'.join(path_list)
            except BaseException:
                result.State('Failure')
                result.Message(['image(-i) format error'])
                return result
            #  判断protocol与IP格式
            if RegularCheckUtil.checkIP(ip) is False:
                result.State('Failure')
                result.Message(['ip format error'])
                return result
            if protocol == 'nfs':
                # login
                headers = RestFunc.login(client)
                if headers == {}:
                    login_res = ResultBean()
                    login_res.State("Failure")
                    login_res.Message(["login error, please check username/password/host/port"])
                    return login_res
                client.setHearder(headers)
                mount = RestFunc.mountnfsByRest(client, ip, path)
                flag_index = 0
                index = None
                if mount and mount.get('code') == 0:
                    mountImage = RestFunc.imageByRest(client)  # 如果挂载文件路径出错，此时会检查出来
                    if mountImage and mountImage.get('code') == 0:
                        image_list = mountImage.get('data')
                        size = len(image_list)
                        for i in range(size):
                            if filename == image_list[i].get('image_name'):
                                index = image_list[i].get('image_index')
                                flag_index = 1
                        if flag_index == 0:
                            result.State('Failure')
                            result.Message(['file is not exist,please check the path.'])
                            # logout
                            RestFunc.logout(client)
                            return result
                        elif flag_index == 1 and index is None:
                            result.State('Failure')
                            result.Message(['request image_index is None.'])
                            # logout
                            RestFunc.logout(client)
                            return result
                        # 挂载具体文件
                        mountStart = RestFunc.mountStartByRest(client, index, filename)
                        if mountStart and mountStart.get('code') == 0:
                            result.State('Success')
                            result.Message(['mount success.'])
                        else:
                            result.State('Failure')
                            result.Message(['mount start failed, ' + mountStart.get('data')])
                    else:
                        result.State('Failure')
                        result.Message(['Could not mount the remote path'])
                else:
                    result.State('Failure')
                    result.Message([mount.get('data')])
            elif protocol == 'cifs':
                if user == "" or passwd == "":
                    result.State('Failure')
                    result.Message(['please input username and password.'])
                    return result
                # login
                headers = RestFunc.login(client)
                if headers == {}:
                    login_res = ResultBean()
                    login_res.State("Failure")
                    login_res.Message(["login error, please check username/password/host/port"])
                    return login_res
                client.setHearder(headers)
                mount = RestFunc.mountcifsByRest(client, ip, path, user, passwd)
                flag_index = 0
                index = None
                if mount and mount.get('code') == 0:
                    mountImage = RestFunc.imageByRest(client)  # 如果挂载文件路径出错，此时会检查出来
                    if mountImage and mountImage.get('code') == 0:
                        image_list = mountImage.get('data')
                        size = len(image_list)
                        for i in range(size):
                            if filename == image_list[i].get('image_name'):
                                index = image_list[i].get('image_index')
                                flag_index = 1
                        if flag_index == 0:
                            result.State('Failure')
                            result.Message(['file is not exist,please check the path.'])
                            # logout
                            RestFunc.logout(client)
                            return result
                        elif flag_index == 1 and index is None:
                            result.State('Failure')
                            result.Message(['request image_index is None.'])
                            # logout
                            RestFunc.logout(client)
                            return result
                        # 挂载具体文件
                        mountStart = RestFunc.mountStartByRest(client, index, filename)
                        if mountStart and mountStart.get('code') == 0:
                            result.State('Success')
                            result.Message(['mount success.'])
                        else:
                            result.State('Failure')
                            result.Message(['mount start failed, ' + mountStart.get('data')])
                    else:
                        result.State('Failure')
                        result.Message(['Could not mount the remote path'])
                else:
                    result.State('Failure')
                    result.Message([mount.get('data')])

            else:
                result.State('Failure')
                result.Message(['this protocol is not supported.'])
                return result
        else:
            # 卸载
            # login
            headers = RestFunc.login(client)
            if headers == {}:
                login_res = ResultBean()
                login_res.State("Failure")
                login_res.Message(["login error, please check username/password/host/port"])
                return login_res
            client.setHearder(headers)
            unmount = RestFunc.mountStopByRest(client)
            if unmount and unmount.get('code') == 0:
                result.State('Success')
                result.Message(['unmount success.'])
            else:
                result.State('Failure')
                result.Message(['mount stop failed, ' + str(unmount.get('data'))])
        # logout
        RestFunc.logout(client)
        return result

    def downloadfandiag(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def downloadsol(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getproduct(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        product_Result = ResultBean()
        product_Info = ProductBean()
        deviceOwnerID = None
        fru = IpmiFunc.getAllFruByIpmi(client)
        if fru:
            if fru.get('code') == 0 and fru.get('data') is not None and fru.get('data')[0].get(
                    'board_serial') is not None:
                deviceOwnerID = fru.get('data')[0].get('board_serial')
            else:
                deviceOwnerID = None
        else:
            deviceOwnerID = None

        res_2 = RestFunc.getFruByRest(client)
        flag = 1
        if res_2.get('code') == 0 and res_2.get('data') is not None:
            info = res_2.get('data')
            for i in range(len(info)):
                if info[i].get('device') is not None and info[i].get('device').get('name') is not None and info[i].get(
                        'device').get('name') == "BMC_FRU":
                    flag = 0
                    if info[i].get('product') is not None:
                        product_Info.ProductName(info[i].get('product').get('product_name', None))
                        product_Info.Manufacturer(info[i].get('product').get('manufacturer', None))
                        product_Info.SerialNumber(info[i].get('product').get('serial_number', None))
                    else:
                        product_Info.ProductName(None)
                        product_Info.Manufacturer(None)
                        product_Info.SerialNumber(None)
                    product_Info.UUID(info[i].get('device').get('uuid', None))
        if flag == 1:
            product_Info.ProductName(None)
            product_Info.Manufacturer(None)
            product_Info.SerialNumber(None)
            product_Info.UUID(None)
        product_Info.DeviceOwnerID(deviceOwnerID)
        product_Info.DeviceSlotID("0")

        res_1 = RestFunc.getChassisStatusByRest(client)
        if res_1.get('code') == 0 and res_1.get('data') is not None:
            product_Info.PowerState(res_1.get('data').get('power_status', None))
        else:
            product_Info.PowerState(None)
        # TotalPowerWatts
        res_4 = RestFunc.getPsuInfoByRest(client)
        if res_4.get('code') == 0 and res_4.get('data') is not None:
            info = res_4.get('data')
            if 'present_power_reading' in info:
                product_Info.TotalPowerWatts(int(info['present_power_reading']))
            else:
                product_Info.TotalPowerWatts(-1)
        else:
            product_Info.TotalPowerWatts(-1)
        # Health: Health_Status
        res_3 = RestFunc.getHealthSummaryByRest(client)
        # 状态 ok present absent normal warning critical
        Health_dict = {'ok': 0, 'present': 1, 'absent': 2, 'normal': 3, 'warning': 4, 'critical': 5}
        if res_3.get('code') == 0 and res_3.get('data') is not None:
            info = res_3.get('data')
            if 'Health_Status' in info:
                product_Info.Health(
                    'OK' if res_3.get('data').get('Health_Status').lower() == 'ok' else res_3.get('data').get(
                        'Health_Status').capitalize())
            else:
                health_list = [0]
                if 'cpu_status' in info and Health_dict.get(info['cpu_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['cpu_status'].lower()))
                if 'fans_status' in info and Health_dict.get(info['fans_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_status'].lower()))
                if 'fans_redundancy' in info and Health_dict.get(info['fans_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fans_redundancy'].lower()))
                if 'mem_status' in info and Health_dict.get(info['mem_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['mem_status'].lower()))
                if 'me_hlth_status' in info and Health_dict.get(info['me_hlth_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['me_hlth_status'].lower()))
                if 'nic_status' in info and Health_dict.get(info['nic_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['nic_status'].lower()))
                if 'power_supplies_status' in info and Health_dict.get(
                        info['power_supplies_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_status'].lower()))
                if 'power_supplies_redundancy' in info and Health_dict.get(
                        info['power_supplies_redundancy'].lower()) is not None:
                    health_list.append(Health_dict.get(info['power_supplies_redundancy'].lower()))
                if 'storage_status' in info and Health_dict.get(info['storage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['storage_status'].lower()))
                if 'temperature_status' in info and Health_dict.get(info['temperature_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['temperature_status'].lower()))
                if 'voltage_status' in info and Health_dict.get(info['voltage_status'].lower()) is not None:
                    health_list.append(Health_dict.get(info['voltage_status'].lower()))
                # print(health_list)
                hel = list(Health_dict.keys())[list(Health_dict.values()).index(max(health_list))]
                product_Info.Health('OK' if hel.lower() == 'ok' else hel.capitalize())
        else:
            product_Info.Health(None)
        if res_1.get('code') != 0 and res_2.get('code') != 0 and res_3.get('code') != 0 and res_4.get('code') != 0:
            product_Result.State('Failure')
            product_Result.Message(['get product information error'])
        else:
            product_Result.State('Success')
            product_Result.Message([product_Info.dict])

        # logout
        RestFunc.logout(client)
        return product_Result

    def getfan(self, client, args):
        '''
        get system fans info
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        fan_Info = FanBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getFanInfoByRest(client)
        if res == {}:
            result.State('Failure')
            result.Message(['get fan info failed'])
        elif res.get('code') == 0 and res.get('data') is not None:

            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get(
                    'data') is not None and 'fans_status' in overalhealth.get('data'):
                fan_Info.OverallHealth(
                    'OK' if overalhealth.get('data').get('fans_status') == 'OK' else overalhealth.get('data').get(
                        'fans_status').capitalize())
            else:
                fan_Info.OverallHealth(None)
            fans = res.get('data').get('fans', [])
            size = len(fans)
            fan_Info.Maximum(size)

            list = []
            module_dict = {'1': 'Front', '2': 'Rear'}
            status_dict = {0: 'OK', 1: 'Warning', 2: 'Critical'}
            i = 0
            model_list = []
            persent_list = []
            for fan in fans:
                fan_singe = Fan()
                fan_singe.Id(i)
                try:
                    if 'fan_name' in fan:
                        fan_singe.CommonName(fan.get('fan_name'))
                    else:
                        if 'index' in fan:
                            index = '{:02x}'.format(fan['index'])
                            if len(index) != 2:
                                fan_singe.CommonName('Fan' + str(i))
                            else:
                                fan_singe.CommonName('Fan Module' + index[0:1] + ' ' + module_dict.get(index[1:2], ''))
                        else:
                            fan_singe.CommonName('Fan' + str(i))
                except BaseException:
                    fan_singe.CommonName('Fan' + str(i))
                fan_singe.Location('Chassis')
                if fan.get('present') == 1:
                    # 在位
                    # fan_singe.Id(fan.get('id',None))
                    fan_singe.Model(fan.get('model', None))
                    fan_singe.RatedSpeedRPM(None)
                    model_list.append(fan.get('model', None))
                    persent_list.append(fan.get('speed_percent', None))
                    fan_singe.SpeedRPM(fan.get('speed_rpm', None))
                    fan_singe.LowerThresholdRPM(None)
                    fan_singe.State('Enabled')
                    if 'status_str' in fan:
                        fan_singe.Health('OK' if fan.get('status_str') == 'OK' else fan.get('status_str').capitalize())
                    else:
                        fan_singe.Health(status_dict.get(fan.get('status', None), None))
                else:
                    fan_singe.State('Absent')

                list.append(fan_singe.dict)
                i += 1
            if len(set(model_list)) == 1:
                fan_Info.Model(model_list[0])
            else:
                fan_Info.Model(None)
            if len(set(persent_list)) == 1:
                fan_Info.FanSpeedLevelPercents(persent_list[0])
            else:
                fan_Info.FanSpeedLevelPercents(None)
            if 'control_mode' in res.get('data'):
                fan_Info.FanSpeedAdjustmentMode(
                    'Automatic' if res.get('data').get('control_mode') == 'auto' else 'Manual')
            else:
                fan_Info.FanSpeedAdjustmentMode(None)
            if 'fans_power' in res.get('data'):
                fan_Info.FanTotalPowerWatts(res.get('data').get('fans_power'))
            else:
                fan_Info.FanTotalPowerWatts(None)
            fan_Info.FanManualModeTimeoutSeconds(None)
            fan_Info.Fan(list)
            result.State('Success')
            result.Message([fan_Info.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message(["get fan information error, " + res.get('data')])
        else:
            result.State("Failure")
            result.Message(["get fan information error, error code " + str(res.get('code'))])
        # logout
        RestFunc.logout(client)
        return result

    # def fancontrol(self, client, args):
    #     '''
    #     set fan mode or speed
    #     :param client:
    #     :param args:
    #     :return: set result
    #     '''
    #     result = ResultBean()
    #     # 获取风扇id
    #     if args.id != 255:
    #         try:
    #             fanAllInfo = IpmiFunc.getM5FanInfoByIpmi(client)
    #             if fanAllInfo['code'] == 0:
    #                 num = len(fanAllInfo['data'])
    #                 if args.id < 0 or args.id > num-1:
    #                     result.State("Failure")
    #                     result.Message(["fan id error,range 0-{0} or 255".format(num-1)])
    #                     return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(["get fan id failed"])
    #                 return result
    #         except:
    #             result.State("Failure")
    #             result.Message(["this command is incompatible with current server."])
    #             return result
    #
    #     if args.fanspeedlevel is not None and args.mode is not None:
    #         if args.mode == 'Automatic':
    #             result.State("Failure")
    #             result.Message(["Set fan speed need in Manual mode"])
    #             return result
    #         else:
    #             if args.fanspeedlevel <= 0 or args.fanspeedlevel > 100:
    #                 result.State("Failure")
    #                 result.Message(["fanspeedlevel in range of 1-100"])
    #                 return result
    #             flag_mode = 1
    #             flag_speed = 1
    #             # 先设置模式
    #             Mode = {"Automatic": "0x00", "Manual": "0x01"}
    #             setMode = IpmiFunc.setM5FanModeByIpmi(client, Mode[args.mode])
    #             if setMode:
    #                 if setMode.get('code') == 0 and setMode.get('data') is not None:
    #                     flag_mode = 0
    #                 else:
    #                     result.State("Failure")
    #                     result.Message(['failed to set mode'])
    #                     return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(['failed to set mode'])
    #                 return result
    #             # 再设置速度
    #             setSpeed_Info = IpmiFunc.setM5FanSpeedByIpmi(client, hex(args.id), hex(args.fanspeedlevel))
    #             if setSpeed_Info:
    #                 if setSpeed_Info.get('code') == 0 and setSpeed_Info.get('data') is not None:
    #                     flag_speed = 0
    #                 else:
    #                     result.State("Failure")
    #                     result.Message(['failed to set speed'])
    #                     return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(['failed to set speed'])
    #                 return result
    #             if flag_mode == 0 and flag_speed == 0:
    #                 result.State("Success")
    #                 result.Message(["set mode and speed success"])
    #                 return result
    #     elif args.fanspeedlevel is None and args.mode is None:
    #         result.State("Failure")
    #         result.Message(["Please input a command."])
    #         return result
    #     elif args.fanspeedlevel is not None and args.mode is None:
    #         # set fan speed manually 必须是手动模式下（如果要设置，直接获取当前模式，判断是否是手动）
    #         curMode = ''
    #         curMode_Info = IpmiFunc.getM5FanModeByIpmi(client)
    #         if curMode_Info:
    #             if curMode_Info.get('code') == 0 and curMode_Info.get('data') is not None:
    #                 curMode_data = curMode_Info.get('data')
    #                 if curMode_data == '00':
    #                     curMode = "Automatic"
    #                 elif curMode_data == '01':
    #                     curMode = "Manual"
    #                 else:
    #                     result.State("Failure")
    #                     result.Message(["failed to get mode."])
    #                     return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(["failed to get mode."])
    #                 return result
    #
    #         else:
    #             result.State("Failure")
    #             result.Message(["failed to get mode."])
    #             return result
    #         if curMode and curMode == 'Automatic':
    #             result.State("Failure")
    #             result.Message(["Automatic mode not support set speed."])
    #             return result
    #         else:
    #             setSpeed_Info = IpmiFunc.setM5FanSpeedByIpmi(client,hex(args.id),hex(args.fanspeedlevel))
    #             if setSpeed_Info:
    #                 if setSpeed_Info.get('code') == 0 and setSpeed_Info.get('data') is not None:
    #                     result.State("Success")
    #                     result.Message(["set speed success"])
    #                     return result
    #                 else:
    #                     result.State("Failure")
    #                     result.Message(['ipmi command execute failed'])
    #                     return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(['ipmi command execute exception'])
    #                 return result
    #     elif args.fanspeedlevel is None and args.mode is not None:
    #         if args.mode == 'Manual':
    #             result.State("Failure")
    #             result.Message(['Manual must be used with fanspeedlevel '])
    #             return result
    #         Mode = {"Automatic":"0x00","Manual":"0x01"}
    #         setMode = IpmiFunc.setM5FanModeByIpmi(client,Mode[args.mode])
    #         if setMode:
    #             if setMode.get('code') == 0 and setMode.get('data') is not None:
    #                 result.State("Success")
    #                 result.Message(["set mode success"])
    #                 return result
    #             else:
    #                 result.State("Failure")
    #                 result.Message(['ipmi command execute failed'])
    #                 return result
    #         else:
    #             result.State("Failure")
    #             result.Message(['ipmi command execute exception'])
    #             return result
    def fancontrol(self, client, args):
        '''
        set fan mode or speed
        :param client:
        :param args:
        :return: set result
        '''
        result = ResultBean()
        if args.fanspeedlevel is None and args.mode is None:
            result.State("Failure")
            result.Message(["Please input a command."])
            return result
        if args.fanspeedlevel is not None and args.mode is not None:
            if args.mode == 'Automatic':
                result.State("Failure")
                result.Message(["Set fan speed need with Manual mode"])
                return result
            elif args.fanspeedlevel <= 0 or args.fanspeedlevel > 100:
                result.State("Failure")
                result.Message(["fanspeedlevel in range of 1-100"])
                return result
        if args.fanspeedlevel is None and args.mode is not None:
            if args.mode == 'Manual':
                result.State("Failure")
                result.Message(['Manual must be used with fanspeedlevel '])
                return result
        # login
        headers = RestFunc.login(client)
        client.setHearder(headers)
        res = RestFunc.getFanInfoByRest(client)
        if res.get('code') == 0 and res.get('data') is not None:
            fans = res.get('data').get('fans')
            if fans is None:
                result.State("Failure")
                result.Message(['failed to parse fans id information.'])
                # logout
                RestFunc.logout(client)
                return result
            fanNum = len(fans)
            # 获取风扇id
            if args.id != 255:
                if args.id < 0 or args.id > fanNum - 1:
                    result.State("Failure")
                    result.Message(["fan id error,range 0-{0} or 255".format(fanNum - 1)])
                    # logout
                    RestFunc.logout(client)
                    return result
            if args.fanspeedlevel is not None and args.mode is not None:
                flag_mode = 1
                flag_speed = 1
                # 先设置模式
                if args.mode == 'Manual':
                    mode = 'manual'
                else:
                    mode = 'auto'
                setMode = RestFunc.setM5FanModeByRest(client, mode)
                if setMode.get('code') == 0 and setMode.get('data') is not None:
                    flag_mode = 0
                else:
                    result.State("Failure")
                    result.Message(['failed to set mode, ' + str(setMode.get('data'))])
                    # logout
                    RestFunc.logout(client)
                    return result
                # 再设置速度
                if args.id != 255:
                    setSpeed_Info = RestFunc.setM5FanSpeedByRest(client, args.id + 1, args.fanspeedlevel)
                    if setSpeed_Info.get('code') == 0 and setSpeed_Info.get('data') is not None:
                        flag_speed = 0
                    else:
                        result.State("Failure")
                        result.Message(['failed to set speed, ' + str(setSpeed_Info.get('data'))])
                        # logout
                        RestFunc.logout(client)
                        return result
                else:
                    setSpeed_Res = []
                    for i in range(fanNum):
                        setSpeed_Info = RestFunc.setM5FanSpeedByRest(client, i + 1, args.fanspeedlevel)
                        setSpeed_Res.append(setSpeed_Info.get('code'))
                    if max(setSpeed_Res) != 0:
                        result.State("Failure")
                        result.Message(['failed to set speed.'])
                        # logout
                        RestFunc.logout(client)
                        return result
                    else:
                        flag_speed = 0

                if flag_mode == 0 and flag_speed == 0:
                    result.State("Success")
                    result.Message(["set mode and speed success"])
                    # logout
                    RestFunc.logout(client)
                    return result
            elif args.fanspeedlevel is not None and args.mode is None:
                # set fan speed manually 必须是手动模式下（如果要设置，直接获取当前模式，判断是否是手动）
                curMode = ''
                curMode_Info = RestFunc.getM5FanModeByRest(client)
                # print(curMode_Info)
                if curMode_Info.get('code') == 0 and curMode_Info.get('data') is not None:
                    curMode_data = curMode_Info.get('data').get('control_mode')
                    if curMode_data == 'auto':
                        curMode = "Automatic"
                    elif curMode_data == 'manual':
                        curMode = "Manual"
                    else:
                        result.State("Failure")
                        result.Message(["fan mode information parsing failed."])
                        # logout
                        RestFunc.logout(client)
                        return result
                else:
                    result.State("Failure")
                    result.Message(["failed to get fan mode, " + str(curMode_Info.get('data'))])
                    # logout
                    RestFunc.logout(client)
                    return result

                if curMode and curMode == 'Automatic':
                    result.State("Failure")
                    result.Message(["not support set speed in Automatic mode."])
                    # logout
                    RestFunc.logout(client)
                    return result
                else:
                    if args.id != 255:
                        setSpeed_Info = RestFunc.setM5FanSpeedByRest(client, args.id + 1, args.fanspeedlevel)
                        if setSpeed_Info.get('code') == 0 and setSpeed_Info.get('data') is not None:
                            result.State("Success")
                            result.Message(["set speed success"])
                        else:
                            result.State("Failure")
                            result.Message(['failed to set fan speed, ' + str(setSpeed_Info.get('data'))])
                    else:
                        setSpeed_Res = []
                        for i in range(fanNum):
                            setSpeed_Info = RestFunc.setM5FanSpeedByRest(client, i + 1, args.fanspeedlevel)
                            setSpeed_Res.append(setSpeed_Info.get('code'))
                        if max(setSpeed_Res) != 0:
                            result.State("Failure")
                            result.Message(['failed to set speed'])
                        else:
                            result.State("Success")
                            result.Message(["set speed success"])
                    # logout
                    RestFunc.logout(client)
                    return result
            elif args.fanspeedlevel is None and args.mode is not None:
                if args.mode == 'Manual':
                    mode = 'manual'
                else:
                    mode = 'auto'
                setMode = RestFunc.setM5FanModeByRest(client, mode)
                # print(setMode)
                if setMode.get('code') == 0 and setMode.get('data') is not None:
                    result.State("Success")
                    result.Message(["set mode success"])
                    # logout
                    RestFunc.logout(client)
                    return result
                else:
                    result.State("Failure")
                    result.Message(['failed to set fan mode, ' + str(setMode.get('data'))])
                    # logout
                    RestFunc.logout(client)
                    return result
        else:
            result.State('Failure')
            result.Message(['get fans info failed, ' + str(res.get('data'))])
            # logout
            RestFunc.logout(client)
            return result

    def getthreshold(self, client, args):
        '''
        get predictive failure threshold
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        result.State("Not Support")
        result.Message([])
        return result

    def getpwrcap(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getpsu(self, client, args):
        '''
        get system psus info
        :param client:
        :param args:
        :return:
        '''
        psu_return = ResultBean()
        psu_Info = PSUBean()
        List = []
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getPsuInfoByRest(client)
        if res == {}:
            psu_return.State('Failure')
            psu_return.Message('get psu info failed')
        elif res.get('code') == 0 and res.get('data') is not None:
            psu_allInfo = res.get('data')
            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get(
                    'data') is not None and 'power_supplies_status' in overalhealth.get('data'):
                psu_Info.OverallHealth(
                    'OK' if overalhealth.get('data').get('power_supplies_status') == 'OK' else overalhealth.get(
                        'data').get('power_supplies_status').capitalize())
            else:
                psu_Info.OverallHealth(None)
            temp = psu_allInfo.get('power_supplies', [])
            size = len(temp)
            psu_Info.Maximum(size)

            for i in range(size):
                psu = PSUSingleBean()
                if temp[i].get('present') == 1:
                    # 在位
                    psu.Id(temp[i].get('id', None))
                    psu.CommonName('PSU' + str(temp[i].get('id')))
                    psu.Location('Chassis')
                    psu.Model(temp[i].get('model', None))
                    psu.Manufacturer(temp[i].get('vendor_id', None))
                    psu.Protocol(None)
                    psu.PowerOutputWatts(int(temp[i].get('ps_out_power')) if 'ps_out_power' in temp[i] else None)
                    psu.InputAmperage(
                        int(temp[i].get('ps_in_current')) * 1.0 / 100 if 'ps_in_current' in temp[i] else None)
                    res1 = RestFunc.getPsuInfo1ByRest(client)
                    if res1.get('code') == 0 and res1.get('data') is not None and 'mode' in res1.get('data')[i]:
                        if res1.get('data')[i].get('mode') == 14:
                            psu.ActiveStandby('Standby')
                        elif res1.get('data')[i].get('mode') == 85:
                            psu.ActiveStandby('Active')
                        elif res1.get('data')[i].get('mode') == 0:
                            psu.ActiveStandby('Normal')
                        else:
                            psu.ActiveStandby(None)
                    else:
                        psu.ActiveStandby(None)
                    psu.OutputVoltage(int(temp[i].get('ps_out_volt')) * 1.0 / 100 if 'ps_out_volt' in temp[i] else None)
                    psu.PowerInputWatts(int(temp[i].get('ps_in_power')) if 'ps_in_power' in temp[i] else None)
                    psu.OutputAmperage(
                        int(temp[i].get('ps_out_current')) * 1.0 / 100 if 'ps_out_current' in temp[i] else None)
                    psu.PartNumber(None if temp[i].get('part_num', None) == '' else temp[i].get('part_num', None))
                    psu.PowerSupplyType(temp[i].get('input_type', 'AC'))
                    psu.LineInputVoltage(int(temp[i].get('ps_in_volt')) if 'ps_in_volt' in temp[i] else None)
                    psu.PowerCapacityWatts(int(temp[i].get('ps_out_power_max', None)))
                    psu.FirmwareVersion(temp[i].get('fw_ver', None))
                    psu.SerialNumber(temp[i].get('serial_num', None))
                    if 'status' in temp[i]:
                        psu.Health('OK' if temp[i].get('status') == 'OK' else temp[i].get('status').capitalize())
                    else:
                        if 'power_status' in temp[i]:
                            psu.Health('OK' if temp[i].get('power_status') == 0 else 'Critical')
                        else:
                            flag = 0
                            psu.Health(None)
                    psu.State('Enabled')
                else:
                    psu.Id(temp[i].get('id', 0))
                    psu.CommonName('PSU' + str(temp[i].get('id')))
                    psu.Location('Chassis')
                    psu.State('Absent')
                List.append(psu.dict)

            psu_Info.PSU(List)
            psu_return.State('Success')
            psu_return.Message([psu_Info.dict])
        else:
            psu_return.State('Failure')
            psu_return.Message('get psu info failed, ' + str(res.get('data')))
        # logout
        RestFunc.logout(client)
        return psu_return

    def getpdisk(self, client, args):
        '''
        get physical drive info
        :param client:
        :param args:
        :return:
        '''
        disk_return = ResultBean()
        # 获取raid类型 raw命令
        raid_type = IpmiFunc.getRaidTypeByIpmi(client)
        if raid_type:
            if raid_type.get('code') == 0 and raid_type.get('data') is not None:
                raidtype = raid_type.get('data')
            else:
                raidtype = 'ff'
        else:
            raidtype = 'ff'
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        if raidtype == '01':
            disk_return = getPdInfo_PMC(client)
        elif raidtype == 'fe':
            disk_return.State('Failure')
            disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return disk_return
        elif raidtype == '00' or raidtype == '02' or raidtype == '03':
            disk_return = getPdInfo_LSI(client)
        elif raidtype == 'ff':
            disk_return = getPdInfo(client)
        else:
            disk_return = getPdInfo_LSI(client)
        # disk_return = getPdInfo_PMC(client)
        # logout
        RestFunc.logout(client)
        return disk_return

    def getpcie(self, client, args):
        pcie_result = ResultBean()
        pcie_bean = PcieBean()
        pcie_count = IpmiFunc.getM5PcieCountByIpmi(client)
        if pcie_count.get('code') != 0:
            pcie_result.State('Failure')
            pcie_result.Message(['get pcie count failed. ' + pcie_count.get('data')])
            return pcie_result
        try:
            pcie_info = IpmiFunc.getM5PcieByIpmi(client, pcie_count.get('data'))
        except BaseException:
            pcie_result.State('Failure')
            pcie_result.Message(['get pcie info failed, parsing failed.'])
            return pcie_result

        List = []

        if pcie_info.get('code') == 0:
            data = pcie_info['data']
            # print(data)
            size = len(data)
            for i in range(size):
                pcie = Pcie()
                pcie.Id(i)
                pcie.CommonName('PCIe' + str(i))
                pcie.Location('mainboard')
                if data[i].get('presentStat', None) == "Present":
                    pcie.Type(data[i].get('Type', None))
                    pcie.SlotBus(data[i].get('busNumber', None))
                    pcie.SlotDevice(data[i].get('deviceNumber', None))
                    pcie.SlotFunction(data[i].get('functionNumber', None))
                    pcie.State("Enabled")
                else:
                    pcie.State("Absent")
                # pcie.Health(None)
                List.append(pcie.dict)
            pcie_bean.OverallHealth(None)
            pcie_bean.Maximum(pcie_count.get('data'))
            pcie_bean.PCIeDevice(List)
            pcie_result.State('Success')
            pcie_result.Message([pcie_bean.dict])
        else:
            pcie_result.State('Failure')
            pcie_result.Message(['get pcie info failed. ' + pcie_info.get('data')])

        return pcie_result

    def locateserver(self, client, args):
        '''
        locate server
        :param client:
        :param args:
        :return: locate server
        '''
        locate_result = ResultBean()
        if args.state == 'on':
            state = str(hex(1))
        elif args.state == 'off':
            state = str(hex(0))
        else:
            locate_result.State('Not Support')
            locate_result.Message([])
            return locate_result
        if args.state is not None and args.frequency is not None:
            if args.state != 'blink':
                locate_result.State('Failure')
                locate_result.Message(['set frequency need state is blink.'])
                return locate_result
        locate_info = IpmiFunc.locateServerByIpmi(client, state)
        if locate_info:
            if locate_info.get('code') == 0:
                locate_result.State('Success')
                locate_result.Message(['operation is successful.'])
            else:
                locate_result.State('Failure')
                locate_result.Message(['failed to operate server. ' + locate_info.get('data', '')])
        else:
            locate_result.State('Failure')
            locate_result.Message(['failed to operate server.'])
        return locate_result

    def locatedisk(self, client, args):
        '''
        locate disk
        :param client:
        :param args:
        :return:
        '''
        locate_Info = ResultBean()
        if args.cid is None:
            locate_Info.State('Failure')
            locate_Info.Message(['cid is needed.'])
            return locate_Info
        state = {'on': 0, 'off': 1}
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # 获取当前的cid,pd,检查输入是否在范围内(PMC不支持设置，只获取LSI的即可)
        cid_countInfo = RestFunc.getLSICtrlCountByRest(client)
        if cid_countInfo == {}:
            locate_Info.State("Failure")
            locate_Info.Message(["get controller id failed"])
            # logout
            RestFunc.logout(client)
            return locate_Info
        elif cid_countInfo.get('code') == 0 and cid_countInfo.get('data') is not None and cid_countInfo.get('data').get(
                'ctrlCount') is not None:
            cid_count = cid_countInfo.get('data').get('ctrlCount')
            cid = list(range(cid_count))
            # print(cid)
            pid = {}
            for i in cid:
                pid[i] = []
                pid_countInfo = RestFunc.getLSICtrlpdInfoByRest(client, i)
                if pid_countInfo == {}:
                    locate_Info.State("Failure")
                    locate_Info.Message(["get physical disk id failed"])
                    # logout
                    RestFunc.logout(client)
                    return locate_Info
                elif pid_countInfo.get('code') == 0 and pid_countInfo.get('data') is not None:
                    pid_info = pid_countInfo.get('data')
                    for j in range(len(pid_info)):
                        pid[i].append(pid_info[j].get('devId'))
                else:
                    locate_Info.State("Failure")
                    locate_Info.Message(['failed to get disk information,' + str(pid_countInfo.get('data'))])
                    # logout
                    RestFunc.logout(client)
                    return locate_Info
            # print(pid)
        else:
            locate_Info.State("Failure")
            locate_Info.Message(["failed to get disk count information, " + str(cid_countInfo.get('data'))])
            # logout
            RestFunc.logout(client)
            return locate_Info
        # 检查cid pid
        if args.cid not in cid:
            locate_Info.State("Failure")
            if len(cid) == 0:
                locate_Info.Message(["no controller is detected currently."])
            else:
                locate_Info.Message(["please input -cid from {0}.".format(cid)])
            # logout
            RestFunc.logout(client)
            return locate_Info
        if args.pid not in pid[args.cid]:
            locate_Info.State("Failure")
            if len(pid[args.cid]) == 0:
                locate_Info.Message(["no physical disk is detected currently."])
            else:
                locate_Info.Message(["please input -i from {0}.".format(pid[args.cid])])
            # logout
            RestFunc.logout(client)
            return locate_Info
        res = RestFunc.locateDiskByRest(client, args.cid, args.pid, state[args.state])
        if res == {}:
            locate_Info.State("Failure")
            locate_Info.Message(["disk operation failed"])
        elif res.get('code') == 0 and res.get('data') is not None:
            locate_Info.State('Success')
            locate_Info.Message(['operation is successful,please wait a few seconds.'])
        else:
            locate_Info.State("Failure")
            locate_Info.Message(['locate disk failed, ' + str(res.get('data'))])
        # logout
        RestFunc.logout(client)
        return locate_Info

    def getip(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getLanByRest(client)
        ipinfo = ResultBean()
        if res == {}:
            ipinfo.State("Failure")
            ipinfo.Message(["cannot get lan info"])
        elif res.get('code') == 0 and res.get('data') is not None:
            ipinfo.State("Success")
            data = res.get('data')
            for lan in data:
                if lan['ipv4_address'] != client.host and lan['ipv6_address'] != client.host:
                    continue
                ipbean = NetBean()

                if lan['lan_enable'] == "Disabled":
                    ipbean.IPVersion('Disabled')
                    ipbean.PermanentMACAddress(lan['mac_address'])
                    ipv4 = IPv4Bean()
                    ipv6 = IPv6Bean()
                    ipbean.IPv4(ipv4.dict)
                    ipbean.IPv6(ipv6.dict)
                else:
                    if lan['ipv4_enable'] == "Enabled" and lan['ipv6_enable'] == "Enabled":
                        ipbean.IPVersion('IPv4andIPv6')
                    elif lan['ipv4_enable'] == "Enabled":
                        ipbean.IPVersion('IPv4')
                    elif lan['ipv6_enable'] == "Enabled":
                        ipbean.IPVersion('IPv6')
                    ipbean.PermanentMACAddress(lan['mac_address'])
                    if lan['ipv4_enable'] == "Enabled":
                        ipv4 = IPv4Bean()
                        ipv4.AddressOrigin(lan['ipv4_dhcp_enable'])
                        ipv4.Address(lan['ipv4_address'])
                        ipv4.SubnetMask(lan['ipv4_subnet'])
                        ipv4.Gateway(lan['ipv4_gateway'])
                        ipbean.IPv4(ipv4.dict)
                    if lan['ipv6_enable'] == "Enabled":
                        ipv6 = IPv6Bean()
                        ipv6.AddressOrigin(lan['ipv6_dhcp_enable'])
                        ipv6.Address(lan['ipv6_address'])
                        ipv6.PrefixLength(lan['ipv6_prefix'])
                        ipv6.Gateway(lan['ipv6_gateway'])
                        ipbean.IPv6([ipv6.dict])
                    vlanbean = vlanBean()
                    vlanbean.State(lan['vlan_enable'])
                    vlanbean.VLANId(lan['vlan_id'])
                    ipbean.VLANInfo(vlanbean.dict)
                ipinfo.Message([ipbean.dict])
                break
        elif res.get('code') != 0 and res.get('data') is not None:
            ipinfo.State("Failure")
            ipinfo.Message([res.get('data')])
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get lan info error"])
        # logout
        RestFunc.logout(client)
        return ipinfo

    def getdns(self, client, args):
        '''

        :return:
        '''

    def gettrap(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getSnmpInfoByRest(client)
        snmpinfo = ResultBean()
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get snmp information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            snmpinfo.State("Success")
            version_dict = {1: "V1", 2: "V2C", 3: "V3", "-": "-"}
            severity_dict = {0: "All", 1: "WarningAndCritical", 2: "Critical", "-": "-"}
            item = res.get('data')
            snmpbean = SnmpBean()
            snmpbean.Enable('Enabled')
            snmpbean.TrapVersion(version_dict[item.get('trap_version', "-")])
            if "community" in item:
                snmpbean.Community(item.get('community', "-"))
            snmpbean.Severity(severity_dict[item.get('event_level', "-")])
            destinationlRes = CommonM5.getDestination(self, client, None)
            if destinationlRes.State == "Success":
                snmpbean.Destination(destinationlRes.Message[0])
            else:
                snmpbean.Destination(None)
            snmpinfo.Message([snmpbean.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get snmp information error"])
        # logout
        RestFunc.logout(client)
        return snmpinfo

    def getsnmp(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        dict_snmp = {
            'SNMP_VERSION_ALL': 1,
            'SNMP_VERSION_DETAIL_BIT': 128,
            'SNMP_VERSION_V1_READ_BIT': 1,
            'SNMP_VERSION_V1_WRITE_BIT': 16,
            'SNMP_VERSION_V2C_READ_BIT': 2,
            'SNMP_VERSION_V2C_WRITE_BIT': 32,
            'SNMP_VERSION_V3_ONLY': 0,
            'SNMP_VERSION_V3_READ_BIT': 4,
            'SNMP_VERSION_V3_WRITE_BIT': 64,
        }
        authentication_dict = {0: "NONE", 1: "SHA", 2: "MD5"}
        privacy_dict = {0: "NONE", 1: "DES", 2: "AES"}
        res = RestFunc.getSnmpM5ByRest(client)
        snmpinfo = ResultBean()
        if res.get('code') == 0 and res.get('data') is not None:
            result = res['data']
            version_dict = {0: 'v1', 1: 'v2c', 2: 'v3', 3: 'all', 4: 'customize', }
            print("-" * 50)
            if 'version' in result:
                version = result.get('version')
                snmpv1writeenable = False
                snmpv1readenable = False
                snmpv2cwriteenable = False
                snmpv2creadenable = False
                snmpv3writeenable = False
                snmpv3readenable = False
                if version == dict_snmp['SNMP_VERSION_V3_ONLY'] or version == (
                        dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V3_READ_BIT'] | dict_snmp[
                            'SNMP_VERSION_V3_WRITE_BIT']):
                    versiondisp = 2
                    snmpv3writeenable = True
                    snmpv3readenable = True
                elif version == (
                        dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V2C_READ_BIT'] | dict_snmp[
                            'SNMP_VERSION_V2C_WRITE_BIT']):
                    versiondisp = 1
                    snmpv2cwriteenable = True
                    snmpv2creadenable = True
                elif version == (
                        dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V1_READ_BIT'] | dict_snmp[
                            'SNMP_VERSION_V1_WRITE_BIT']):
                    versiondisp = 0
                    snmpv1writeenable = True
                    snmpv1readenable = True
                elif version == dict_snmp['SNMP_VERSION_V3_ONLY'] or version == (dict_snmp['SNMP_VERSION_DETAIL_BIT']
                                                                                 | dict_snmp['SNMP_VERSION_V3_READ_BIT']
                                                                                 | dict_snmp[
                                                                                     'SNMP_VERSION_V3_WRITE_BIT']
                                                                                 | dict_snmp[
                                                                                     'SNMP_VERSION_V2C_READ_BIT']
                                                                                 | dict_snmp[
                                                                                     'SNMP_VERSION_V2C_WRITE_BIT']
                                                                                 | dict_snmp[
                                                                                     'SNMP_VERSION_V2C_READ_BIT']
                                                                                 | dict_snmp[
                                                                                     'SNMP_VERSION_V2C_WRITE_BIT']):
                    versiondisp = 3
                    snmpv1writeenable = True
                    snmpv1readenable = True
                    snmpv2cwriteenable = True
                    snmpv2creadenable = True
                    snmpv3writeenable = True
                    snmpv3readenable = True
                else:
                    versiondisp = 4
                    if (version & dict_snmp['SNMP_VERSION_V1_READ_BIT'] != 0):
                        snmpv1readenable = True
                    if (version & dict_snmp['SNMP_VERSION_V2C_READ_BIT'] != 0):
                        snmpv2creadenable = True
                    if (version & dict_snmp['SNMP_VERSION_V3_READ_BIT'] != 0):
                        snmpv3readenable = True
                    if (version & dict_snmp['SNMP_VERSION_V1_WRITE_BIT'] != 0):
                        snmpv1writeenable = True
                    if (version & dict_snmp['SNMP_VERSION_V2C_WRITE_BIT'] != 0):
                        snmpv2cwriteenable = True
                    if (version & dict_snmp['SNMP_VERSION_V3_WRITE_BIT'] != 0):
                        snmpv3writeenable = True
            if result.get('auth_protocol') == 0:
                auth_passwd = 'N/A'
            else:
                auth_passwd = result.get('auth_passwd')
            if result.get('priv_protocol') == 0:
                priv_passwd = 'N/A'
            else:
                priv_passwd = result.get('priv_passwd')
            snmp = SnmpGetSetM5Bean()
            if 'version' in result:
                snmp.GETSETVersion(str(version_dict.get(versiondisp, 'N/A')))
                snmp.snmpv1readenable(snmpv1readenable)
                snmp.snmpv1writeenable(snmpv1writeenable)
                snmp.snmpv2creadenable(snmpv2creadenable)
                snmp.snmpv2cwriteenable(snmpv2cwriteenable)
                snmp.snmpv3readenable(snmpv3readenable)
                snmp.snmpv3writeenable(snmpv3writeenable)
                if versiondisp == 1 or versiondisp == 0:
                    snmp.Community(str(result.get('community', 'N/A')))
                elif versiondisp == 2:
                    snmp.Username(str(result.get('username', 'N/A')))
                    snmp.AuthProtocol(authentication_dict.get(result.get('auth_protocol'), 'N/A'))
                    snmp.AuthPasswd(auth_passwd)
                    snmp.PrivProtocol(privacy_dict.get(result.get('priv_protocol'), 'N/A'))
                    snmp.PrivPasswd(priv_passwd)
                else:
                    snmp.Community(str(result.get('community', 'N/A')))
                    snmp.Username(str(result.get('username', 'N/A')))
                    snmp.AuthProtocol(authentication_dict.get(result.get('auth_protocol'), 'N/A'))
                    snmp.AuthPasswd(auth_passwd)
                    snmp.PrivProtocol(privacy_dict.get(result.get('priv_protocol'), 'N/A'))
                    snmp.PrivPasswd(priv_passwd)
            else:
                snmp.Community(str(result.get('community', 'N/A')))
                snmp.Username(str(result.get('username', 'N/A')))
                snmp.AuthProtocol(authentication_dict.get(result.get('auth_protocol'), 'N/A'))
                snmp.AuthPasswd(auth_passwd)
                snmp.PrivProtocol(privacy_dict.get(result.get('priv_protocol'), 'N/A'))
                snmp.PrivPasswd(priv_passwd)
            snmpinfo.State("Success")
            snmpinfo.Message([snmp.dict])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["can not get SNMP GET/SET configure"])

        RestFunc.logout(client)
        return snmpinfo

    def setsnmp(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        snmpinfo = setSNMP(client, args)
        # logout
        RestFunc.logout(client)
        return snmpinfo

    def getsnmptrap(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getSnmpInfoByRest(client)
        snmpinfo = ResultBean()
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get snmp information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            snmpinfo.State("Success")
            version_dict = {1: "V1", 2: "V2C", 3: "V3", "V2": "V2C"}
            severity_dict = {0: "All", 1: "WarningAndCritical", 2: "Critical", "info": "All",
                             "warning": "WarningAndCritical", "critical": "Critical"}
            authentication_dict = {0: "NONE", 1: "SHA", 2: "MD5"}
            privacy_dict = {0: "NONE", 1: "DES", 2: "AES"}
            item = res.get('data')
            snmpbean = SnmpBean()
            snmpbean.TrapVersion(version_dict.get(item.get('trap_version'), item.get('trap_version')))
            snmpbean.Severity(severity_dict.get(item.get('event_level'), item.get('event_level')))
            if item.get('trap_version') == 3:
                snmpbean.UserName(item.get('username', 'N/A'))
                snmpbean.EngineID(item.get('engine_id', 'N/A'))
                snmpbean.AUTHProtocol(authentication_dict.get(item.get('auth_protocol'), item.get('auth_protocol')))
                if 'auth_protocol' in item and (item['auth_protocol'] == 1 or item['auth_protocol'] == 2):
                    mm = str(item.get('auth_passwd'))
                    snmpbean.AUTHPwd(mm)
                else:
                    snmpbean.AUTHPwd('-')
                snmpbean.PRIVProtocol(privacy_dict.get(item.get('priv_protocol'), item.get('priv_protocol')))
                if 'priv_protocol' in item and (item['priv_protocol'] == 1 or item['priv_protocol'] == 2):
                    nn = str(item.get('priv_passwd'))
                    snmpbean.PRIVPwd(nn)
                else:
                    snmpbean.PRIVPwd('-')
            else:
                snmpbean.Community(item.get('community', 'N/A'))
            snmpbean.Community(item.get('community', 'N/A'))
            snmpbean.SystemName(item.get('system_name', 'N/A'))
            snmpbean.SystemId(item.get('system_id', 'N/A'))
            snmpbean.Location(item.get('location', 'N/A'))
            snmpbean.ContactName(item.get('contact_name', 'N/A'))
            snmpbean.HostOS(item.get('host_os', 'N/A'))
            if 'trap_port' in item:
                snmpbean.Port(item.get('trap_port', 'N/A'))
            else:
                snmpbean.Port(item.get('port', 'N/A'))
            snmpinfo.Message([snmpbean.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get snmp information error, error code " + str(res.get('code'))])
        RestFunc.logout(client)
        return snmpinfo

    def getalertpolicy(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        snmpinfo = getAlertPolicy(client, args)
        # logout
        RestFunc.logout(client)
        return snmpinfo

    def setsnmptrap(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        snmpinfo = setSNMPtrap(client, args)
        # logout
        RestFunc.logout(client)
        return snmpinfo

    def setalertpolicy(self, client, args):
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        snmpinfo = setAlertPolicy(client, args)
        # logout
        RestFunc.logout(client)
        return snmpinfo

    # not interface sub function

    def getDestination(self, client, args):
        # login
        '''
        headers=RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        '''
        # get
        res = RestFunc.getLanDestinationsByRest(client)
        snmpinfo = ResultBean()
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get lan destination information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            data = res.get('data')
            dlist = []
            for aitem in data:
                destinationbean = DestinationBean()
                destinationbean.Id(aitem['id'])
                destinationbean.ChannelId(aitem['channel_id'])
                destinationbean.LanChannel(aitem['lan_channel'])
                destinationbean.Address(aitem['destination_address'])
                destinationbean.Name(aitem['name'])
                # 5180m5没有此字段
                # destinationbean.Domain(aitem['destination_domain'])
                destinationbean.Domain(aitem.get('destination_domain', ""))
                destinationbean.Type(aitem['destination_type'])
                destinationbean.Subject(aitem['subject'])
                destinationbean.Message(aitem['message'])
                dlist.append(destinationbean)

            ares = RestFunc.getAlertPoliciesByRest(client)
            if ares == {}:
                snmpinfo.State("Failure")
                snmpinfo.Message(["cannot get alert policy information"])
            elif ares.get('code') == 0 and ares.get('data') is not None:
                adata = ares.get('data')
                alist = []
                for i in range(3):
                    dt = DestinationTXBean()
                    dt.Id(adata[i]['id'])
                    if adata[i]['enable_policy'] == 1:
                        dt.Enable("Enabled")
                    else:
                        dt.Enable("Disabled")
                    if adata[i]['channel_number'] == 8:
                        if dlist[i].Type == "email":
                            dt.Address(dlist[i].Name)
                        elif dlist[i].Type == "snmp":
                            dt.Address(dlist[i].Address)
                        elif dlist[i].Type == "snmpdomain":
                            dt.Address(dlist[i].Domain)
                        else:
                            dt.Address("")
                    else:
                        if dlist[i + 15].Type == "email":
                            dt.Address(dlist[i + 15].Name)
                        elif dlist[i + 15].Type == "snmp":
                            dt.Address(dlist[i + 15].Address)
                        elif dlist[i + 15].Type == "snmpdomain":
                            dt.Address(dlist[i + 15].Domain)
                        else:
                            dt.Address("")
                    if dt.Address == "":
                        dt.Address = None
                    dt.Port("162")
                    alist.append(dt.dict)
                snmpinfo.State("Success")
                snmpinfo.Message([alist])
            elif res.get('code') != 0 and res.get('data') is not None:
                snmpinfo.State("Failure")
                snmpinfo.Message([res.get('data')])
            else:
                snmpinfo.State("Failure")
                snmpinfo.Message(["get alert policy information error"])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get lan destination information error"])
        # logout
        # RestFunc.logout(client)
        return snmpinfo

    def settrapcom(self, client, args):
        snmpinfo = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        getres = RestFunc.getSnmpInfoByRest(client)
        trapinfo = {}
        if getres == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get information"])
        elif getres.get('code') == 0 and getres.get('data') is not None:
            trapinfo = getres.get('data')
        elif getres.get('code') != 0 and getres.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([getres.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get information error, error code " + str(getres.get('code'))])
        if trapinfo == {}:
            return snmpinfo
        # set
        changeflag = False
        enableflag = False
        # enable
        # disable
        if args.enabled == "Disabled":
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot set M5 snmp trap disable"])
            return snmpinfo

        # severity
        if args.severity is not None:
            # s_dict = {'All': 'info', 'WarningAndCritical': "warning", 'Critical': "critical"}
            s_dict = {'All': 0, 'WarningAndCritical': 1, 'Critical': 2}
            if "event_level" in trapinfo:
                if trapinfo.get("event_level") != s_dict.get(args.severity, "0"):
                    trapinfo["event_level"] = s_dict.get(args.severity, "0")
                    changeflag = True
        # version
        if args.version is not None:
            if "trap_version" in trapinfo:
                if trapinfo["trap_version"] != args.version:
                    trapinfo["trap_version"] = args.version
                    changeflag = True
        # community
        if args.community is not None:
            if "community" in trapinfo:
                if trapinfo["community"] != args.community:
                    trapinfo["community"] = args.community
                    changeflag = True
            else:
                # in laster bmc, 3 password key
                trapinfo["community"] = args.community
                changeflag = True

        else:
            if "community" not in trapinfo:
                snmpinfo.State("Failure")
                snmpinfo.Message(["community cannot null"])
                return snmpinfo

        # if not change
        if not changeflag:
            snmpinfo.State("Success")
            snmpinfo.Message(["nothing to change."])
            return snmpinfo

        trapinfo["auth_passwd"] = ""
        trapinfo["priv_passwd"] = ""
        trapinfo["encrypt_flag"] = 0

        res = RestFunc.setTrapComByRest(client, trapinfo)
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            snmpinfo.State("Success")
            snmpinfo.Message([])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get information error, error code " + str(res.get('code'))])
        # logout
        RestFunc.logout(client)
        return snmpinfo

    def settrapdest(self, client, args):
        res = ResultBean()
        if args.port is None and args.address is None and args.enabled is None:
            res.State("Failure")
            res.Message(["nothing to set, input port/address/enable"])
            return res
        if args.destinationid == 4:
            res.State("Not Support")
            res.Message(["id 4 is not supported on the M5 platform"])
            return res
        if args.port is not None:
            res.State("Not Support")
            res.Message(["dest port cannot be set on the M5 platform, default 162"])
            return res

       # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        if args.enabled == "Disabled":
            enable = 0
        elif args.enabled == "Enabled":
            enable = 1
        else:
            destinationlRes = CommonM5.getDestination(self, client, None)
            # logout
            # RestFunc.logout(client)
            if destinationlRes.State == "Success":
                alist = destinationlRes.Message[0]
                for a in alist:
                    if a['Id'] == args.destinationid:
                        if a['Enable'] == "Enable":
                            enable = 1
                        else:
                            enable = 0
                        break
            else:
                res.State("Failure")
                res.Message(["get trap dest current info error"])
                RestFunc.logout(client)
                return res
        # channel
        args.channel = "8"
        # 默认shared 除非share没有地址
        ipinfo = RestFunc.getLanByRest(client)
        res = ResultBean()
        if ipinfo == {}:
            res.State("Failure")
            res.Message(["cannot get lan info"])
        elif ipinfo.get('code') == 0 and ipinfo.get('data') is not None:
            data = ipinfo.get('data')
            for lan in data:
                if lan['interface_name'] != "eth0":
                    continue
                if lan['lan_enable'] == "Disabled":
                    ipv4 = ""
                    ipv6 = ""
                else:
                    ipv4 = lan['ipv4_address']
                    ipv6 = lan['ipv6_address']
                break
            if ipv4 == client.host or ipv6 == client.host:
                channel = 8
            else:
                channel = 1
        elif ipinfo.get('code') != 0 and ipinfo.get('data') is not None:
            res.State("Failure")
            res.Message([ipinfo.get('data')])
        else:
            res.State("Failure")
            res.Message(["get lan info error"])
        # logout
        RestFunc.logout(client)
        if res.State == "Failure":
            return res

        trap_set = IpmiFunc.setSNMPTrapPolicyByIpmi(client, args.destinationid, channel, enable)
        if trap_set["code"] != 0:
            res.State("Failure")
            res.Message(["Set SNMP Trap policy error:" + trap_set["data"]])
            return res
        tpye_set = IpmiFunc.setAlertTypeByIpmi(client, args.destinationid, channel, "snmp")
        if tpye_set["code"] != 0:
            res.State("Failure")
            res.Message(["Set Alert Type error:" + tpye_set["data"]])
            return res
        if args.address is not None:
            if RegularCheckUtil.checkIP(args.address):
                d_set = IpmiFunc.setDestIPByIpmi(client, args.destinationid, channel, args.address)
                if d_set["code"] != 0:
                    res.State("Failure")
                    res.Message(["Set destination address error:" + d_set["data"]])
                    return res
            else:
                res.State("Failure")
                res.Message(["illegal ip address(-a)"])
                return res
        res.State("Success")
        res.Message([])
        return res

    def setip(self, client, args):
        checkparam_res = ResultBean()
        # check param
        if args.version is None:
            checkparam_res.State("Failure")
            checkparam_res.Message(["ip version(4/6) must be input"])
        elif args.version == "6":
            checkparam_res.State("Not Support")
            checkparam_res.Message([])
        elif args.version == "4":
            # dhcp
            if args.mode is not None and args.mode.lower() == "dhcp":
                if args.addr is not None or args.gateway is not None or args.sub is not None:
                    checkparam_res.State("Failure")
                    checkparam_res.Message(["ip address, gateway, subnet cannot be setted when mode is DHCP"])
            elif args.mode is not None and args.mode.lower() == "static":
                if args.gateway is not None:
                    if not RegularCheckUtil.checkIP(args.gateway):
                        checkparam_res.State("Failure")
                        checkparam_res.Message(["Illegal gateway ip."])
                elif args.sub is not None:
                    if not RegularCheckUtil.checkSubnetMask(args.sub):
                        checkparam_res.State("Failure")
                        checkparam_res.Message(["Illegal subnet."])
                elif args.addr is not None:
                    if not RegularCheckUtil.checkIP(args.addr):
                        checkparam_res.State("Failure")
                        checkparam_res.Message(["Illegal ip."])
        else:
            checkparam_res.State("Failure")
            checkparam_res.Message(["ip version must be 4 or 6"])
        if checkparam_res.State == "Failure" or checkparam_res.State == "Not Support":
            return checkparam_res
        # check param end
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getLanByRest(client)
        ipinfo = ResultBean()
        if res == {}:
            ipinfo.State("Failure")
            ipinfo.Message(["cannot get lan information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            data = res.get('data')
            for lan in data:
                if lan['ipv4_address'] != client.host and lan['ipv6_address'] != client.host:
                    continue

                # dhcp_dict = {'static':0, 'disable':-1, 'dhcp':1}
                dhcp_dict = {'Static': 0, 'Disabled': -1, 'DHCP': 1, 'static': 0, 'disable': -1, 'dhcp': 1}
                status_dict = {'Disabled': 0, 'Enabled': 1}
                lan['lan_enable'] = status_dict[lan['lan_enable']]
                lan['ipv4_enable'] = status_dict[lan['ipv4_enable']]
                lan['ipv6_enable'] = status_dict[lan['ipv6_enable']]
                lan['vlan_enable'] = status_dict[lan['vlan_enable']]
                lan['ipv4_dhcp_enable'] = dhcp_dict[lan['ipv4_dhcp_enable']]
                lan['ipv6_dhcp_enable'] = dhcp_dict[lan['ipv6_dhcp_enable']]

                if args.mode is not None:
                    lan['ipv4_dhcp_enable'] = dhcp_dict[args.mode]

                if lan['ipv4_dhcp_enable'] == 1:
                    if args.addr is not None or args.gateway is not None or args.sub is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["ip address, gateway, subnet cannot be setted when mode is DHCP"])
                else:
                    if args.gateway is not None:
                        if not RegularCheckUtil.checkIP(args.gateway):
                            ipinfo.State("Failure")
                            ipinfo.Message(["Illegal gateway ip."])
                        else:
                            lan['ipv4_gateway'] = args.gateway

                    if args.sub is not None:
                        if not RegularCheckUtil.checkSubnetMask(args.sub):
                            ipinfo.State("Failure")
                            ipinfo.Message(["Illegal subnet."])
                        else:
                            lan['ipv4_subnet'] = args.sub
                    if args.addr is not None:
                        if not RegularCheckUtil.checkIP(args.addr):
                            ipinfo.State("Failure")
                            ipinfo.Message(["Illegal ip."])
                        else:
                            lan['ipv4_address'] = args.addr
                if ipinfo.State == "Failure":
                    RestFunc.logout(client)
                    return ipinfo
                # ipinfo.State("Failure")
                # ipinfo.Message(lan)
                # return ipinfo
                setres = RestFunc.setLanByRest(client, lan)
                if setres["code"] == 0:
                    ipinfo.State("Success")
                    ipinfo.Message(['set ip complete'])
                else:
                    ipinfo.State("Failure")
                    ipinfo.Message([setres['data']])
                RestFunc.logout(client)
                return ipinfo
        elif res.get('code') != 0 and res.get('data') is not None:
            ipinfo.State("Failure")
            ipinfo.Message([res.get('data')])
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get lan information error"])
        # logout
        RestFunc.logout(client)
        return ipinfo

    # def setvlan(self, client, args):
    #     checkparam_res = ResultBean()
    #     # check param
    #     # vlanid
    #     if args.vlan_id is not None:
    #         if args.vlan_id < 2 or args.vlan_id > 4094:
    #             checkparam_res.State("Failure")
    #             checkparam_res.Message(["vlan id must be 2-4094"])
    #     if checkparam_res.State == "Failure" or checkparam_res.State == "Not Support":
    #         return checkparam_res
    #     # check param end
    #     # login
    #     headers = RestFunc.login(client)
    #     if headers == {}:
    #         login_res = ResultBean()
    #         login_res.State("Failure")
    #         login_res.Message(["login error, please check username/password/host/port"])
    #         return login_res
    #     client.setHearder(headers)
    #     # get
    #     res = RestFunc.getLanByRest(client)
    #     ipinfo = ResultBean()
    #     if res == {}:
    #         ipinfo.State("Failure")
    #         ipinfo.Message(["cannot get lan information"])
    #     elif res.get('code') == 0 and res.get('data') is not None:
    #         data = res.get('data')
    #         for lan in data:
    #             if lan['ipv4_address'] != client.host and lan['ipv6_address']!= client.host:
    #                 continue
    #
    #             # dhcp_dict = {'static':0, 'disable':-1, 'dhcp':1}
    #             dhcp_dict = {'Static': 0, 'Disabled': -1, 'DHCP': 1, 'static': 0, 'disable': -1, 'dhcp': 1}
    #             status_dict = {'Disabled': 0, 'Enabled': 1}
    #             lan['lan_enable'] = status_dict[lan['lan_enable']]
    #             lan['ipv4_enable'] = status_dict[lan['ipv4_enable']]
    #             lan['ipv6_enable'] = status_dict[lan['ipv6_enable']]
    #             lan['vlan_enable'] = status_dict[lan['vlan_enable']]
    #             lan['ipv4_dhcp_enable'] = dhcp_dict[lan['ipv4_dhcp_enable']]
    #             lan['ipv6_dhcp_enable'] = dhcp_dict[lan['ipv6_dhcp_enable']]
    #
    #             if args.vlan_status == "Disabled":
    #                 lan['vlan_enable'] = 0
    #             elif args.vlan_status == "Enabled":
    #                 lan['vlan_enable'] = 1
    #
    #             if lan['vlan_enable'] == 0:
    #                 if args.vlan_id is not None:
    #                     ipinfo.State("Failure")
    #                     ipinfo.Message(["Set vlan enable first to set vlan id"])
    #             else:
    #                 if args.vlan_id is not None:
    #                     lan['vlan_id'] = args.vlan_id
    #                 if lan['vlan_id'] == 0:
    #                     ipinfo.State("Failure")
    #                     ipinfo.Message(["Input vlan id."])
    #
    #             if ipinfo.State == "Failure":
    #                 RestFunc.logout(client)
    #                 return ipinfo
    #             setres = RestFunc.setLanByRest(client, lan)
    #             if setres["code"] == 0:
    #                 ipinfo.State("Success")
    #                 ipinfo.Message(['set vlan complete'])
    #             else:
    #                 ipinfo.State("Failure")
    #                 ipinfo.Message([setres['data']])
    #             RestFunc.logout(client)
    #             return ipinfo
    #     elif res.get('code') != 0 and res.get('data') is not None:
    #         ipinfo.State("Failure")
    #         ipinfo.Message([res.get('data')])
    #     else:
    #         ipinfo.State("Failure")
    #         ipinfo.Message(["get lan information error"])
    #     # logout
    #     RestFunc.logout(client)
    #     return ipinfo

    def getvnc(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def setvnc(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getvncsession(self, client, args):

        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getmgmtport(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getserialport(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def exportbmccfg(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def importbmccfg(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    # def exportbioscfg(self, client, args):
    #     '''
    #     export bios setup configuration
    #     :param client:
    #     :param args:
    #     :return:
    #     '''
    #     export = ResultBean()
    #     file_path = os.path.dirname(args.fileurl)
    #     if not os.path.exists(file_path):
    #         try:
    #             os.makedirs(file_path)
    #         except:
    #             export.State("Failure")
    #             export.Message(["cannot build path."])
    #             return export
    #     # login
    #     headers = RestFunc.login(client)
    #     if headers == {}:
    #         login_res=ResultBean()
    #         login_res.State("Failure")
    #         login_res.Message(["login error, please check username/password/host/port"])
    #         return login_res
    #     client.setHearder(headers)
    #     # get
    #     res = RestFunc.exportBiosCfgByRest(client, args.fileurl)
    #
    #     if res == {}:
    #         export.State("Failure")
    #         export.Message(["export bios setup configuration file failed."])
    #     elif res.get('code') == 0:
    #         export.State('Success')
    #         export.Message([res.get('data')])
    #     elif res.get('code') == 4:
    #         export.State('Failure')
    #         export.Message([res.get('data')])
    #     else:
    #         export.State("Failure")
    #         export.Message(["export bios setup configuration file error, "+res.get('data')])
    #     # logout
    #     RestFunc.logout(client)
    #     return export
    #
    # def importbioscfg(self, client, args):
    #     '''
    #     import bios cfg
    #     :param client:
    #     :param args:
    #     :return:
    #     '''
    #     # login
    #     headers = RestFunc.login(client)
    #     if headers == {}:
    #         login_res=ResultBean()
    #         login_res.State("Failure")
    #         login_res.Message(["login error, please check username/password/host/port"])
    #         return login_res
    #     client.setHearder(headers)
    #     # get
    #     res = RestFunc.importBiosCfgByRest(client, args.fileurl)
    #     import_Info = ResultBean()
    #     if res == {}:
    #         import_Info.State("Failure")
    #         import_Info.Message(["import bios setup configuration file failed."])
    #     elif res.get('code') == 0:
    #         import_Info.State('Success')
    #         import_Info.Message(['import bios setup configuration file success.'])
    #     else:
    #         import_Info.State("Failure")
    #         import_Info.Message(["import bios setup configuration file error, "+str(res.get('data'))])
    #     # logout
    #     RestFunc.logout(client)
    #     return import_Info

    def delvncsession(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def getuser(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getUserByRest(client)
        userRoleIdDict = {"none": "NoAccess",
                          "administrator": "Administrator",
                          "user": "Commonuser",
                          "oem": "OEM",
                          "operator": "Operator"}
        userinfo = ResultBean()
        if res == {}:
            userinfo.State("Failure")
            userinfo.Message(["cannot get user information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            userinfo.State("Success")
            data = res.get('data')
            userlist = []
            for userdata in data:
                if userdata['name'] == "":
                    continue
                user = UserBean()
                user.UserId(userdata['id'])
                user.UserName(userdata['name'])
                # user.RoleId(userdata['network_privilege'])
                user.RoleId(userRoleIdDict.get(userdata['network_privilege'], userdata['network_privilege']))
                prilist = []
                if userdata['kvm'] == 1:
                    prilist.append("KVM")
                if userdata['vmedia'] == 1:
                    prilist.append("VMM")
                user.Privilege(prilist)
                if userdata['access'] == 1:
                    user.Locked(False)
                    user.Enable(True)
                else:
                    user.Locked(True)
                    user.Enable(False)
                userlist.append(user.dict)
            userinfo.Message([{"User": userlist}])
        elif res.get('code') != 0 and res.get('data') is not None:
            userinfo.State("Failure")
            userinfo.Message([res.get('data')])
        else:
            userinfo.State("Failure")
            userinfo.Message(["get user information error"])
        # logout
        RestFunc.logout(client)
        return userinfo

    def adduser(self, client, args):
        userinfo = ResultBean()
        # 校验
        if not RegularCheckUtil.checkUsername(args.uname):
            userinfo.State('Failure')
            userinfo.Message(['Illegal username.'])
            return userinfo
        if not RegularCheckUtil.checkPassword(args.upass):
            userinfo.State('Failure')
            userinfo.Message(['Illegal password.'])
            return userinfo
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getUserByRest(client)
        if res == {}:
            userinfo.State("Failure")
            userinfo.Message(["cannot get user information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            space_flag = False
            duplication_flag = False
            data = res.get('data')
            for userdata in data:
                if userdata['name'] == "":
                    if not space_flag:
                        space_flag = True
                        args.userID = userdata['id']
                elif userdata['name'] == args.uname:
                    duplication_flag = True
            # 有重名
            if duplication_flag:
                userinfo.State('Failure')
                userinfo.Message(['username already exist.'])
            elif space_flag:
                # add
                if "kvm" in args.priv.lower():
                    args.kvm = 1
                else:
                    args.kvm = 0
                if "vmm" in args.priv.lower():
                    args.vmm = 1
                else:
                    args.vmm = 0
                if "sol" in args.priv.lower():
                    args.sol = 1
                else:
                    args.sol = 0
                if "none" in args.priv.lower():
                    args.sol = 0
                    args.vmm = 0
                    args.kvm = 0
                if args.roleid == "NoAccess":
                    # 权限为无权限 则无法登陆以及默认为用户
                    args.access = 0
                    args.group = "User"
                elif args.roleid == "Commonuser":
                    args.roleid = "User"
                    args.group = args.roleid
                    args.access = 1
                elif args.roleid == "OEM":
                    args.group = "Administrator"
                    args.access = 1
                else:
                    args.group = args.roleid
                    args.access = 1
                res_add = RestFunc.addUserByRest(client, args)
                # print (res_add.get('code'))
                if res_add.get('code') == 0:
                    # 设置权限none
                    if args.roleid == "NoAccess":
                        userRes = IpmiFunc.setUserPrivByIpmi(client, args.uname, 15)
                        if userRes == 0:
                            userinfo.State("Success")
                            userinfo.Message(['add user success.'])
                        else:
                            userinfo.State("Failure")
                            userinfo.Message(['set user priv noaccess error.'])
                    elif args.roleid == "OEM":
                        userRes = IpmiFunc.setUserPrivByIpmi(client, args.uname, 5)
                        if userRes == 0:
                            userinfo.State("Success")
                            userinfo.Message(['add user success.'])
                        else:
                            userinfo.State("Failure")
                            userinfo.Message(['set user priv oem error.'])
                    else:
                        userinfo.State("Success")
                        userinfo.Message(['add user success.'])
                else:
                    userinfo.State('Failure')
                    # userinfo.Message(["add user failed."])
                    userinfo.Message([res_add.get('data')])
            else:
                userinfo.State('Failure')
                userinfo.Message(['no space for new user, add user failed.'])
        elif res.get('code') != 0 and res.get('data') is not None:
            userinfo.State("Failure")
            userinfo.Message([res.get('data')])
        else:
            userinfo.State("Failure")
            userinfo.Message(["get user information error"])
        # logout
        RestFunc.logout(client)
        return userinfo

    def setpriv(self, client, args):
        userinfo = ResultBean()
        # 校验
        if not RegularCheckUtil.checkUsername(args.uname):
            userinfo.State('Failure')
            userinfo.Message(['Illegal username.'])
            return userinfo
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getUserByRest(client)
        if res == {}:
            userinfo.State("Failure")
            userinfo.Message(["cannot get user information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            # if user exist
            user_flag = False
            user_old = {}
            data = res.get('data')
            for userdata in data:
                if userdata['name'] == args.uname:
                    user_flag = True
                    args.userID = userdata['id']
                    user_old = userdata
                    break
            # 有该用户
            if user_flag:
                # set
                if args.priv is not None:
                    if "kvm" in args.priv.lower():
                        args.kvm = 1
                    else:
                        args.kvm = 0
                    if "vmm" in args.priv.lower():
                        args.vmm = 1
                    else:
                        args.vmm = 0
                    if "sol" in args.priv.lower():
                        args.sol = 1
                    else:
                        args.sol = 0
                    if "none" in args.priv.lower():
                        args.sol = 0
                        args.vmm = 0
                        args.kvm = 0
                if args.roleid is not None:
                    if args.roleid == "NoAccess":
                        if args.uname == client.username:
                            userinfo.State("Failure")
                            userinfo.Message(["cannot disable yourself"])
                            RestFunc.logout(client)
                            return userinfo
                        # 权限为无权限 则无法登陆以及默认为用户
                        args.access = 0
                        args.group = user_old["group_name"]
                    elif args.roleid == "OEM":
                        args.access = 1
                        args.group = user_old["group_name"]
                    elif args.roleid == "Commonuser":
                        args.roleid = "User"
                        args.group = args.roleid
                        args.access = 1
                    else:
                        args.group = args.roleid
                        args.access = 1
                res_set = RestFunc.setUserByRest(client, args)
                if res_set.get('code') == 0:
                    # 设置权限none
                    if args.roleid == "NoAccess":
                        userRes = IpmiFunc.setUserPrivByIpmi(client, args.uname, 15)
                        if userRes == 0:
                            userinfo.State("Success")
                            userinfo.Message(['set user success.'])
                        else:
                            userinfo.State("Failure")
                            userinfo.Message(['set user priv noaccess error.'])
                    elif args.roleid == "OEM":
                        userRes = IpmiFunc.setUserPrivByIpmi(client, args.uname, 5)
                        if userRes == 0:
                            userinfo.State("Success")
                            userinfo.Message(['set user success.'])
                        else:
                            userinfo.State("Failure")
                            userinfo.Message(['set user priv oem error.'])
                    else:
                        userinfo.State("Success")
                        userinfo.Message(['set user priv success.'])
                else:
                    userinfo.State('Failure')
                    userinfo.Message([res_set.get('data')])
            else:
                userinfo.State('Failure')
                userinfo.Message(['no user named ' + args.uname])
        elif res.get('code') != 0 and res.get('data') is not None:
            userinfo.State("Failure")
            userinfo.Message([res.get('data')])
        else:
            userinfo.State("Failure")
            userinfo.Message(["get user information error"])
        # logout
        RestFunc.logout(client)
        return userinfo

    def deluser(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getUserByRest(client)
        userinfo = ResultBean()
        if res == {}:
            userinfo.State("Failure")
            userinfo.Message(["cannot get user information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            id_flag = False
            data = res.get('data')
            for userdata in data:
                if userdata['name'] == args.uname:
                    args.userID = userdata['id']
                    id_flag = True
                    break
            # 有该条目
            if id_flag:
                # del
                res_del = RestFunc.delUserByRest(client, args.userID, args.uname)
                if res_del.get('code') == 0:
                    userinfo.State("Success")
                    userinfo.Message(['del user success.'])
                else:
                    userinfo.State('Failure')
                    # userinfo.Message(["add user failed."])
                    userinfo.Message([res_del.get('data')])
            else:
                userinfo.State('Failure')
                userinfo.Message([str(args.uname) + ' does not exits.'])
        elif res.get('code') != 0 and res.get('data') is not None:
            userinfo.State("Failure")
            userinfo.Message([res.get('data')])
        else:
            userinfo.State("Failure")
            userinfo.Message(["get uswer information error"])
        # logout
        RestFunc.logout(client)
        return userinfo

    # rest需要密码，因此使用ipmitool
    def setpwdDrop(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getUserByRest(client)
        userinfo = ResultBean()
        if res == {}:
            userinfo.State("Failure")
            userinfo.Message(["cannot get information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            id_flag = False
            data = res.get('data')
            for userdata in data:
                if userdata['name'] == args.uname:
                    args.userID = userdata['id']
                    args.access = userdata['access']
                    args.group = userdata['group_name']
                    id_flag = True
                    break
            # 有该条目
            if id_flag:
                # del
                res_del = RestFunc.setpwdByRest(client, args)
                if res_del.get('code') == 0:
                    userinfo.State("Success")
                    userinfo.Message(['set pwd success.'])
                else:
                    userinfo.State('Failure')
                    # userinfo.Message(["add user failed."])
                    userinfo.Message([res_del.get('data')])
            else:
                userinfo.State('Failure')
                userinfo.Message([str(args.uname) + ' does not exits.'])
        elif res.get('code') != 0 and res.get('data') is not None:
            userinfo.State("Failure")
            userinfo.Message([res.get('data')])
        else:
            userinfo.State("Failure")
            userinfo.Message(["get information error, error code " + str(res.get('code'))])
        # logout
        RestFunc.logout(client)
        return userinfo

    def getfw(self, client, args):
        '''
        get fw version
        :param client:
        :param args:
        :return:fw version
        '''
        result = ResultBean()
        fw = fwBean()
        fwlist = []
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.getFwVersion(client)
        if res == {}:
            result.State("Failure")
            result.Message(["cannot get firmware version"])
        elif res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            data = res.get('data')
            size = len(data)
            Type = {'BMC': 'BMC', 'BIOS': 'BIOS', 'ME': 'ME', 'PSU': 'PSU', 'TPM': 'TPM', 'CPU': 'CPU', 'CPLD': 'CPLD',
                    'LED': 'LED'}
            SupportActivateType = {'BMC': ['resetbmc'], 'BIOS': ['resethost', 'poweroff', 'dcpowercycle'],
                                   'CPLD': ['poweroff', 'dcpowercycle'], 'ME':
                                       ['resethost', 'poweroff', 'dcpowercycle']}
            Update = {'BMC': True, 'BIOS': True, 'ME': True, 'PSU': False, 'TPM': False, 'CPU': False, 'CPLD': True,
                      'LED': False}
            # SupportActivateMode = {'BMC':'Manual','BIOS':'Manual','ME':'Manual','PSU':None,'TPM':None,'CPU':None,'CPLD':'Manual'}
            for i in range(size):
                fwsingle = fwSingleBean()
                fwversion = None
                flag = 0
                fwsingle.Name(data[i].get('dev_name'))
                index_version = data[i].get('dev_version').find('(')
                if index_version == -1:
                    #fwsingle.Version(None if data[i].get('dev_version') == '' else data[i].get('dev_version'))
                    fwversion = None if data[i].get('dev_version') == '' else data[i].get('dev_version')
                else:
                    #fwsingle.Version(None if data[i].get('dev_version') == '' else data[i].get('dev_version')[:index_version].strip())
                    fwversion = None if data[i].get('dev_version') == '' else data[i].get('dev_version')[:index_version].strip()
                for key in Type.keys():
                    if key in data[i].get('dev_name'):
                        fwsingle.Type(Type[key])
                        fwsingle.Version(fwversion)
                        fwsingle.Updateable(Update[key])
                        fwsingle.SupportActivateType(SupportActivateType.get(key, ['none']))
                        # fwsingle.SupportActivateMode(SupportActivateMode.get(key,None))
                        flag = 1
                        break
                if flag == 0:
                    fwsingle.Type(None)
                    fwsingle.Version(fwversion)
                    fwsingle.Updateable(None)
                    fwsingle.SupportActivateType(['none'])
                fwlist.append(fwsingle.dict)
            fw.Firmware(fwlist)
            result.Message([fw.dict])
        else:
            result.State("Failure")
            result.Message(["get firmware version error, error info:  " + str(res.get('data'))])
        # logout
        RestFunc.logout(client)
        return result

    def getupdatestate(self, client, args):
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

    def fwupdate(self, client, args):
        def ftime(ff="%Y-%m-%d %H:%M:%S "):
            try:
                import time
                localtime = time.localtime()
                f_localtime = time.strftime(ff, localtime)
                return f_localtime
            except BaseException:
                return ""

        def wirte_log(log_path, stage="", state="", note=""):
            try:
                log_list = []
                with open(log_path, 'r') as logfile_last:
                    log_cur = logfile_last.read()
                    if log_cur != "":
                        log_cur_dict = eval(log_cur)
                        log_list = log_cur_dict.get("log")

                with open(log_path, 'w') as logfile:
                    # {
                    #     "Time":"2018-11-20T10:20:12+08:00",
                    #     "Stage":"Upload File",
                    #     "State":"Invalid URI",
                    #     "Note":"Not support the protocol 'CIFS'."
                    #  }
                    # 升级阶段：上传文件(Upload File)、文件校验(File Verify)、应用（刷写目标FLASH）(Apply)、生效(Activate)。
                    # 错误状态：网络不通(Network Ping NOK)、无效URI(Invalid URI)、连接失败(Connect Failed)、文件不存在(File Not Exist)、空间不足(Insufficient Space)、格式错误(Format Error)、非法镜像(Illegal Image)、机型不支持(Unsupported Machine)、镜像与升级目标部件不匹配(Image and Target Component Mismatch)、BMC重启失败(BMC Reboot Failed)、版本校验失败(Version Verify Failed)、FLASH空间不足(Insufficient Flash)、FLASH写保护(FLASH Write Protection)、数据校验失败(Data Verify Failed)。
                    # 正常进展：开始（Start）、进行中（In Progress）、完成（Finish）、成功（Success）、网络能ping通（Network Ping OK）、BMC重启成功（BMC Reboot Success）、升级完删除缓存的镜像成功(Delete Image Success)、升级重试第N次(Upgrade Retry N Times)、刷到暂存FLASH成功(Write to Temporary FLASH Success)、版本校验成功(Version Verify OK)、同步刷新另一片镜像成功(Sync Flash The Other Image Success)……
                    log_time = ftime("%Y-%m-%dT%H:%M:%S")
                    import time
                    tz = time.timezone
                    if tz < 0:
                        we = "+"
                        tz = abs(tz)
                    hh = tz // 3600
                    if hh < 10:
                        hh = "0" + str(hh)
                    else:
                        hh = str(hh)
                    mm = tz % 3600
                    if mm < 10:
                        mm = "0" + str(mm)
                    else:
                        mm = str(mm)
                    tz_format = we + hh + ":" + mm
                    log_time_format = log_time + tz_format

                    log = {}
                    log["Time"] = log_time_format
                    log["Stage"] = stage
                    log["State"] = state
                    log["Note"] = str(note)
                    log_list.append(log)
                    log_dict = {"log": log_list}
                    logfile.write(json.dumps(log_dict, default=lambda o: o.__dict__, sort_keys=True, indent=4,
                                             ensure_ascii=False))
                return True
            except Exception as e:
                return (str(e))

        result = ResultBean()

        # 创建目录
        # getpsn
        psn = "UNKNOWN"
        res_syn = Base.getfru(self, client, args)
        if res_syn.State == "Success":
            frulist = res_syn.Message[0].get("FRU", [])
            if frulist != []:
                psn = frulist[0].get('ProductSerial', 'UNKNOWN')
        else:
            return res_syn
        logtime = ftime("%Y%m%d%H%M%S")
        dir_name = logtime + "_" + psn
        # 创建目录
        T6_path = os.path.abspath(__file__)
        interface_path = os.path.split(T6_path)[0]
        root_path = os.path.dirname(interface_path)
        update_path = os.path.join(root_path, "update")
        if not os.path.exists(update_path):
            os.makedirs(update_path)
        update_plog_path = os.path.join(update_path, dir_name)
        if not os.path.exists(update_plog_path):
            os.makedirs(update_plog_path)

        log_path = os.path.join(update_plog_path, "updatelog")
        if not os.path.exists(log_path):
            with open(log_path, 'w') as newlog:
                log_dict = {"log": []}
                newlog.write(str(log_dict))

        # 能ping通
        print(ftime() + "Ping https successfully")
        wirte_log(log_path, "Upload File", "Network Ping OK", "")

        # file check
        updatefile = args.url
        if not os.path.exists(updatefile):
            result.State("Failure")
            result.Message(["Image is not exists"])
            wirte_log(log_path, "Upload File", "File Not Exist", result.Message[0])
            RestFunc.logout(client)
            return result
        if not os.path.isfile(updatefile):
            result.State("Failure")
            result.Message(["Image is not file"])
            wirte_log(log_path, "Upload File", "File Not Exist", result.Message[0])
            RestFunc.logout(client)
            return result
        # session文件
        session_path = os.path.join(update_plog_path, "session")

        # 循环
        upgrade_count = 0
        while True:
            # 判断session是否存在，存在则logout&del
            if os.path.exists(session_path):
                os.remove(session_path)
            # 删除
            if result.State == "Success":
                if args.type == "BMC" or args.type == "bmc":
                    psn = ""
                    hostname = ""
                    # 设置hostname
                    # get Product Serial Number
                    res = Base.getfru(self, client, args)
                    if res.State == "Success":
                        frulist = res.Message[0].get("FRU", [])
                        if frulist != []:
                            psn = frulist[0].get('ProductSerial', 'UNKNOWN')
                            print(ftime() + "Product serial is " + str(psn))
                        else:
                            print(ftime() + "Can not get product serial")
                            # 删除session
                            RestFunc.logout(client)
                            return result
                    else:
                        print(ftime() + "Cannot get product serial")
                        # 删除session
                        RestFunc.logout(client)
                        return result
                    # gethostname
                    time.sleep(30)
                    hostnameRes = IpmiFunc.getHostname(client)
                    if hostnameRes.get("code", "1") == 0:
                        hostname_str = hostnameRes.get("data", "")
                        hostname_list = hostname_str.split(" ")
                        for i in range(2, len(hostname_list)):
                            if hostname_list[i] != "00":
                                hostname = hostname + chr(int(hostname_list[i], 16))
                        print(ftime() + "Hostname is " + hostname)
                    else:
                        print(ftime() + "Can not get hostname: " + hostnameRes.get("data", "0"))
                        # 删除session
                        RestFunc.logout(client)
                        return result

                    # sethostname
                    if psn != "" and hostname != "" and hostname != psn:
                        sethostnameRes = IpmiFunc.setHostname(client, psn)
                        if sethostnameRes.get("code", "1") == 0:
                            resetDNSRes = IpmiFunc.resetDNS(client)
                            time.sleep(60)
                            print(ftime() + "set hostname success")
                            # if resetDNSRes.get("code", "1") == 0:
                            #resetBMC = IpmiFunc.resetBMCByIpmi(client)
                        else:
                            print(ftime() + "set hostname failed: " + sethostnameRes.get("data", ""))
                            # 删除session
                            RestFunc.logout(client)
                            return result
                # 删除session
                RestFunc.logout(client)
                return result
            elif result.State == "Failure":
                upgrade_count = upgrade_count + 1
                if upgrade_count > retry_count:
                    RestFunc.logout(client)
                    return result
                else:
                    if isinstance(result.Message, list) and result.Message:
                        print(ftime() + result.Message[0])
                    print(ftime() + "Upgrade Retry " + str(upgrade_count) + " Times")
                    # 重新升级 初始化result
                    wirte_log(log_path, "Upload File", "Upgrade Retry " + str(upgrade_count) + " Times", "")
                    result = ResultBean()
                    if args.type == "BMC" or args.type == "bmc":
                        print(ftime() + "Reset bmc")
                        RestFunc.resetBmcByRest(client)
                        time.sleep(60)
                    else:
                        RestFunc.logout(client)

            # login
            headers = {}
            logcount = 0
            while True:
                # 等6分钟后尝试使用root登陆
                if logcount == 15:
                    print(ftime() + "Check BMC with init user: root")
                    client.username = "root"
                    client.password = "root"
                elif logcount > 18:
                    # 7分钟后超时退出
                    break
                else:
                    logcount = logcount + 1
                    import time
                    time.sleep(20)
                # login
                headers = RestFunc.login(client)
                if headers != {}:
                    # 记录session
                    with open(session_path, 'w') as new_session:
                        new_session.write(str(headers))
                    client.setHearder(headers)
                    print(ftime() + "Create session successfully")
                    client.setHearder(headers)
                    break
                else:
                    print(ftime() + "Create session failed")
                    wirte_log(log_path, "Upload File", "Connect Failed", "Connect number:" + str(logcount))
            # 10次无法登陆 不再重试
            if headers == {}:
                result.State("Failure")
                result.Message(["Create session failed."])
                return result

            # update
            if args.type == "BMC" or args.type == "bmc":
                # 改写mac 若使用共享口调用utool ，且共享口专口MAC不一样，则修改专口Mac
                res = RestFunc.getLanByRest(client)
                if res == {}:
                    print(ftime() + "cannot get lan info")
                elif res.get('code') == 0 and res.get('data') is not None:
                    data = res.get('data')
                    ip1 = ""
                    ip8 = ""
                    mac1 = ""
                    mac8 = ""
                    for lan in data:
                        if lan.get('channel_number', '') == 8:
                            ip8 = lan.get('ipv4_address', '')
                            ip68 = lan.get('ipv6_address', '')
                            mac8 = lan.get('mac_address', '')
                        elif lan.get('channel_number', '') == 1:
                            ip1 = lan.get('ipv4_address', '')
                            ip61 = lan.get('ipv6_address', '')
                            mac1 = lan.get('mac_address', '')
                        else:
                            continue

                    print(ftime() + "Dedicated MAC is " + mac1)
                    print(ftime() + "Sharelink MAC is " + mac8)
                    macRes = IpmiFunc.getMac(client)
                    #{'code': 0, 'data': '06 6c 92 bf f8 cb 99'}
                    if macRes.get("code", 1) == 0:
                        mac_raw = macRes.get("data", "err")[3:].strip().upper()
                        mac = ":".join(mac_raw.split(" "))
                        print(ftime() + "Real Dedicated MAC is " + mac)
                        if mac != "00:00:00:00:00:00":
                            # 1 dedicated       8 sharelink
                            mac_flag = False
                            if RegularCheckUtil.checkIP(client.host):
                                if client.host == ip8 and ip1 != client.host:
                                    mac_flag = True
                            else:
                                if client.host == ip68 and ip61 != client.host:
                                    mac_flag = True
                            if mac_flag:
                                if mac != mac1:
                                    print(ftime() + "set Real Dedicated MAC to dedicate MAC.")
                                    macset = IpmiFunc.setDedicatedMac(client, mac)
                                    if macset["code"] != 0:
                                        print(ftime() + "Set dedicated MAC error: " + str(macset["data"]))
                    else:
                        print(ftime() + "Cannot get Real Dedicated MAC: " + macRes.get("data", ""))
                else:
                    print(ftime() + "cannot get lan info " + str(res))
                # 打印当前版本及升级文件
                fw1 = ""
                fw2 = ""
                cfw = ""
                res = RestFunc.getBMCImageByRest(client)
                if res == {}:
                    wirte_log(log_path, "Upload File", "Version Verify Failed", 'get bmc version info failed')
                    print(ftime() + 'get bmc version info failed')
                elif res.get('code') == 0 and res.get('data') is not None:
                    # fw_version_1 2
                    bmc_dict = res.get('data')
                    image_dict = {"dual": "both", "single": "active"}
                    fw1 = bmc_dict.get("fw_version_1")
                    fw2 = bmc_dict.get("fw_version_2")
                    cfw = bmc_dict.get("current_active_image")
                    if cfw == fw1:
                        print(ftime() + "Image1(Activate) current version:" + fw1)
                        print(ftime() + "Image2(Inactivate) current version:" + fw2)
                    else:
                        print(ftime() + "Image1(Inactivate) current version:" + fw1)
                        print(ftime() + "Image2(Activate) current version:" + fw2)
                else:
                    print(ftime() + "get bmc version information error, " + res.get('data'))
                    wirte_log(log_path, "Upload File", "Version Verify Failed", res.get('data'))

                # 设置改写配置
                override_res = RestFunc.preserveBMCConfigM5(client, args.override)
                if override_res == {}:
                    result.State("Failure")
                    result.Message(["Cannot set bmc preserve config " + str(override_res.get('data'))])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    continue
                elif override_res.get('code') != 0:
                    result.State("Failure")
                    result.Message([override_res.get('data')])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    continue
                '''
                if args.override == 1:
                    override_res = RestFunc.setOverrideBMCConfigM5(client)
                    if override_res == {}:
                        result.State("Failure")
                        result.Message(["Cannot override config"])
                        continue
                    elif override_res.get('code') != 0:
                        result.State("Failure")
                        result.Message(
                            ["set override config error, " + str(override_res.get('data'))])
                        continue
                elif args.override == 2:
                    #保存所有配置，除了sdr
                    override_res = RestFunc.peserveBMCCfgExceptSDRM5(client)
                    if override_res == {}:
                        result.State("Failure")
                        result.Message(["Cannot preserve config"])
                        continue
                    elif override_res.get('code') != 0:
                        result.State("Failure")
                        result.Message(
                            ["set override config error, " + str(override_res.get('data'))])
                        continue
                '''
                # choose bmc update mode active standby both
                # Tencent only dual and single
                image_dict = {"dual": "both", "single": "active"}
                if args.dualimage not in image_dict:
                    flashImageConfig = {"code": "1", "data": "dualimage should be dual or single"}
                else:
                    flashImageConfig = RestFunc.setFlashImageConfig(client, image_dict.get(args.dualimage, ""))
                if flashImageConfig == {}:
                    result.State("Failure")
                    result.Message(['Failed to call BMC interface api/maintenance/flash_image_config, response is none'])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                elif flashImageConfig.get('code') == 0 and flashImageConfig.get('data') is not None:
                    # print('flashImageConfig:',flashImageConfig.get('data'))
                    # enter update mode
                    flashMode = RestFunc.bmcFlashMode(client)
                    if flashMode == {}:
                        result.State("Failure")
                        result.Message(['Failed to call BMC interface api/maintenance/flash, response is none'])
                        wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    elif flashMode.get('code') == 0 and flashMode.get('data') is not None:
                        # print('flashMode',flashMode.get('data'))
                        # upload bmc file
                        print(ftime() + "Upload file start")
                        wirte_log(log_path, "Upload File", "Start", "")
                        print(ftime() + "Firmware image is " + os.path.abspath(args.url))
                        uploadfile = RestFunc.uploadBMCImageFile(client, args.url)
                        if uploadfile == {}:
                            result.State("Failure")
                            result.Message(["cannot upload file"])
                            wirte_log(log_path, "Upload File", "Connect Failed",
                                      "Exceptions occurred while calling interface")
                        elif uploadfile.get('code') == 0 and uploadfile.get('data') is not None:
                            print(ftime() + "Upload file successfully")
                            wirte_log(log_path, "Upload File", "Success", "")
                            # print('uploadfile', uploadfile)
                            # verification
                            wirte_log(log_path, "File Verify", "Start", "")
                            verification = RestFunc.verifyUpdateImageByRest(client)
                            # print('verification', verification)
                            if verification == {}:
                                result.State("Failure")
                                result.Message(['Failed to call BMC interface api/maintenance/firmware/verification, response is none'])
                                wirte_log(log_path, "File Verify", "Connect Failed",
                                          "Exceptions occurred while calling interface")
                            elif verification.get('code') == 0 and verification.get('data') is not None:
                                print(ftime() + "File verify successfully")
                                wirte_log(log_path, "File Verify", "Success", "")
                                # update
                                if args.override == 0:
                                    preserve = 1
                                elif args.override == 1:
                                    preserve = 0
                                else:
                                    preserve = 0
                                # preserve 锁定为0 通过preserveBMCConfigM5进行配置改写
                                preserve = 0
                                print(ftime() + "Apply(Flash) start")
                                wirte_log(log_path, "Apply", "Start", "")
                                flash = RestFunc.updateBMCByRest(client, preserve, 1)
                                if flash == {}:
                                    result.State("Failure")
                                    result.Message(['Failed to call BMC interface api/maintenance/firmware/upgrade, response is none'])
                                    wirte_log(log_path, "Apply", "Connect Failed",
                                              "Exceptions occurred while calling interface")
                                elif flash.get('code') == 0 and flash.get('data') is not None:
                                    error_count = 0
                                    # max progress number
                                    count = 0
                                    # 100num  若进度10次都是100 则主动reset
                                    count_100 = 0
                                    error_info = ""
                                    while True:
                                        if count > 120:
                                            result.State("Failure")
                                            result.Message(
                                                ["Apply cost too much time, please check if upgrade is ok or not. Last response is " + error_info])
                                            wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                                            break
                                        if error_count > 10:
                                            result.State("Failure")
                                            result.Message(["Get apply progress error, please check is upgraded or not. Last response is " + error_info])
                                            wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                                            # TODO
                                            # check是否升级成功
                                            break
                                        if count_100 > 3:
                                            # result.State("Success")
                                            # result.Message(
                                            #     ["Apply progress is 100% but it does not complete, check if upgrade is ok or not"])
                                            # wirte_log(log_path, "Apply", "In Progress", result.Message)
                                            break
                                        count = count + 1
                                        import time
                                        time.sleep(10)
                                        progress = RestFunc.getBMCUpgradeProgessByRest(client)
                                        # print('progress', progress)
                                        if progress == {}:
                                            error_count = error_count + 1
                                            error_info = 'Failed to call BMC interface api/maintenance/firmware/flash-progress, response is none'
                                        elif progress.get('code') == 0 and progress.get('data') is not None:
                                            # { "id": 1, "action": "Flashing...", "progress": "0% done         ", "state": 0 }
                                            error_info = str(progress.get('data'))
                                            if progress.get('data')['state'] == 2:
                                                print(ftime() + "Apply(Flash) inprogress, progress: 100%")
                                                # print('upgrade complete, BMC will reset, please wait for a minute')
                                                print(ftime() + "Apply(Flash) successfully")
                                                wirte_log(log_path, "Apply", "Success", "")
                                                # result.State("Success")
                                                # result.Message(["upgrade complete, BMC will reset, please wait for a minute"])
                                                break
                                            elif "%" in progress.get('data')['progress']:
                                                pro = progress.get('data')['progress'].split("%")[0]
                                                process = ftime() + "Apply(Flash) inprogress, progress: " + str(pro) + "%  "
                                                b_num = len(process)
                                                # print(process + "\b" * b_num, end="", flush=True)
                                                wirte_log(log_path, "Apply", "In Progress",
                                                          "progress:" + str(pro) + "%")
                                                if pro == '100':
                                                    count_100 = count_100 + 1
                                        else:
                                            # 有可能还没检查到进度完成，就完成并且重启了
                                            if progress.get('code') == 1500 and "Read timed out" in progress.get('error'):
                                                if args.type == "BMC" and args.mode == "Auto":
                                                    print(ftime() + "Apply(Flash) inprogress, progress: 100%")
                                                    print(ftime() + "Apply(Flash) successfully")
                                                    wirte_log(log_path, "Apply", "Success", "")
                                                    break
                                            error_count = error_count + 1
                                            error_info = str(progress.get('data'))
                                    if result.State != "Failure":
                                        print(ftime() + "Activate inprogress")
                                        print(ftime() + "BMC reboot start(about 4 minutes)")
                                        wirte_log(log_path, "Activate", "Start", "BMC will reboot")
                                        time.sleep(60)
                                        print(ftime() + "BMC reboot inprogress.")
                                        time.sleep(60)
                                        print(ftime() + "BMC reboot inprogress..")
                                        time.sleep(60)

                                        uname = client.username
                                        pword = client.password
                                        # web service 是否启动
                                        reset_try_count = 0
                                        headers = {}
                                        while True:
                                            print(ftime() + "BMC reboot inprogress...")
                                            time.sleep(20)
                                            reset_try_count = reset_try_count + 1
                                            # 7分钟未启动 尝试使用root登陆
                                            if reset_try_count == 12:
                                                print(ftime() + "Check BMC with init user: root")
                                                client.username = "root"
                                                client.password = "root"
                                            # 20分钟未启动 说明BMC启动失败
                                            if reset_try_count > 50:
                                                result.State('Failure')
                                                result.Message(
                                                    ["BMC reset timeout, please manually check if upgrade is ok."])
                                                print(ftime() + "BMC reboot failed")
                                                wirte_log(log_path, "Activate", "BMC Reboot Failed", result.Message)
                                                break
                                            try:
                                                headers = RestFunc.login(client)
                                                if headers != {}:
                                                    with open(session_path, 'w') as new_session:
                                                        new_session.write(str(headers))
                                                    break
                                            except Exception as e:
                                                # print(str(e))
                                                continue

                                        if result.State != 'Failure':
                                            client.setHearder(headers)
                                            print(ftime() + "BMC reboot complete...")
                                            # get
                                            res = RestFunc.getBMCImageByRest(client)
                                            if res == {}:
                                                result.State('Failure')
                                                result.Message(['get bmc version info failed'])
                                                print(ftime() + "Version verify failed")
                                                wirte_log(log_path, "Activate", "Version Verify Failed", result.Message)
                                            elif res.get('code') == 0 and res.get('data') is not None:
                                                # fw_version_1 2
                                                bmc_dict = res.get('data')
                                                image_dict = {"dual": "both", "single": "active"}
                                                if args.dualimage == "dual":
                                                    image1_update_info = " BMC update successfully, Version: image1 change from " + fw1 + " to " + bmc_dict.get(
                                                        "fw_version_1")
                                                    image2_update_info = " BMC update successfully, Version: image2 change from " + fw2 + " to " + bmc_dict.get(
                                                        "fw_version_2")
                                                    image_info = [image1_update_info, image2_update_info]
                                                else:
                                                    image1_update_info = " BMC update successfully, Version: image1 change from " + fw1 + " to " + bmc_dict.get(
                                                        "fw_version_1")
                                                    image2_update_info = ""
                                                    image_info = [image1_update_info]
                                                    '''
                                                    if cfw == "Image-1":
                                                        image1_update_info = " BMC update successfully, Version: image1 change from " + fw1 + " to " + bmc_dict.get("fw_version_1")
                                                        image2_update_info = ""
                                                        image_info=[image1_update_info]
                                                    else:
                                                        image1_update_info = ""
                                                        image2_update_info = " BMC update successfully, Version: image2 change from " + fw2 + " to " + bmc_dict.get("fw_version_2")
                                                        image_info=[image2_update_info]
                                                    '''

                                                print(ftime() + "Version verify ok")
                                                print(ftime() + image1_update_info + image2_update_info)
                                                wirte_log(log_path, "Activate", "Version Verify OK",
                                                          image1_update_info + image2_update_info)
                                                result.State("Success")
                                                result.Message([image_info])
                                            elif res.get('code') != 0 and res.get('data') is not None:
                                                result.State("Failure")
                                                result.Message(["get bmc version information error, " + res.get('data')])
                                                print(ftime() + "Version verify failed")
                                                wirte_log(log_path, "Activate", "Version Verify Failed", res.get('data'))
                                            else:
                                                result.State("Failure")
                                                result.Message(
                                                    ["get bmc version information error, error code " + str(
                                                        res.get('code'))])
                                                print(ftime() + "Version verify failed")
                                                wirte_log(log_path, "Activate", "Version Verify Failed",
                                                          "error code " + str(res.get('code')))
                                        else:
                                            client.username = uname
                                            client.password = pword
                                else:
                                    result.State("Failure")
                                    result.Message(["Flash BMC error, error code " + str(verification.get('code'))])
                                    wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                            else:
                                result.State("Failure")
                                result.Message([verification.get('data')])
                                wirte_log(log_path, "File Verify", "Data Verify Failed", str(verification.get('data')))
                        else:
                            result.State("Failure")
                            result.Message([uploadfile.get('data')])
                            wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    else:
                        result.State("Failure")
                        result.Message([flashMode.get('data')])
                        wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                else:
                    result.State("Failure")
                    result.Message([flashImageConfig.get('data')])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue
            elif args.type == "BIOS" or args.type == "bios":
                biosmode = RestFunc.getBiosFlashModeByRest(client)
                if biosmode == {}:
                    result.State("Failure")
                    result.Message(["can not get bios mode, interface api/maintenance/firmware/flash-mode returns nothing"])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                elif biosmode.get('code') == 0 and biosmode.get('data') is not None:
                    if args.override == 0:
                        reserve = 1
                    else:
                        reserve = 0
                    biosFlash = RestFunc.setBiosFlashOptionByRest(client, reserve)
                    if biosFlash == {}:
                        result.State("Failure")
                        result.Message(["can not set bios option, api/maintenance/bios_flash returns nothing"])
                        wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    elif biosFlash.get('code') == 0 and biosFlash.get('data') is not None:
                        print(ftime() + "Upload file start")
                        wirte_log(log_path, "Upload File", "Start", "")
                        upload = RestFunc.uploadBiosImageFile(client, args.url)
                        if upload == {}:
                            result.State("Failure")
                            result.Message(["can not upload file, api/maintenance/firmware returns nothing"])
                            wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                        elif upload.get('code') == 0 and upload.get('data') is not None:
                            print(ftime() + "Upload file successfully")
                            wirte_log(log_path, "Upload File", "Success", "")
                            wirte_log(log_path, "File Verify", "Start", "")
                            vert = RestFunc.verifyBiosUpdateImageByRest(client)
                            if vert == {}:
                                result.State("Failure")
                                result.Message(["can not get bios mode, interface api/maintenance/firmware/bios_verification returns nothing"])
                                wirte_log(log_path, "File Verify", "Connect Failed", result.Message)
                            elif vert.get('code') == 0 and vert.get('data') is not None:
                                print(ftime() + "File verify successfully")
                                print(ftime() + "Apply(Flash) start")
                                wirte_log(log_path, "Apply", "Start", "")
                                flash = RestFunc.updateBiosByRest(client, args.hasme)
                                if flash == {}:
                                    result.State("Failure")
                                    result.Message(["can not flash bios " + 'Failed to call BMC interface api/maintenance/firmware/biosupgrade, response is none'])
                                    wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                                elif flash.get('code') == 0 and flash.get('data') is not None:

                                    # progress
                                    # max error number
                                    error_count = 0
                                    # max progress number
                                    count = 0
                                    # 100num  若进度10次都是100 则主动reset
                                    count_100 = 0
                                    error_info = ""
                                    while True:
                                        if count > 120:
                                            result.State("Failure")
                                            result.Message(
                                                ["Apply cost too much time, please check if upgrade is ok or not. Last response is " + error_info])
                                            wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                                            break
                                        if error_count > 10:
                                            result.State("Failure")
                                            result.Message(
                                                ["Get apply progress error, please check is upgraded or not. Last response is " + error_info])
                                            wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                                            # TODO
                                            # check是否升级成功
                                            break
                                        if count_100 > 3:
                                            result.State('Success')
                                            result.Message([
                                                "Activate pending, set BIOS setup options will activate later, trigger: systemreboot."])
                                            print(ftime() + "Activate pending")
                                            wirte_log(log_path, "Apply", "Write to Temporary FLASH Success",
                                                      result.Message)
                                            break
                                        count = count + 1
                                        import time
                                        time.sleep(5)
                                        progress = RestFunc.getBiosUpgradeProgessByRest(client)
                                        # print("progress",progress)
                                        if progress == {}:
                                            error_count = error_count + 1
                                            error_info = 'Failed to call BMC interface api/maintenance/firmware/flash-progress, response is none'
                                        elif progress.get('code') == 0 and progress.get('data') is not None:
                                            # { "id": 1, "action": "Flashing...", "progress": "0% done         ", "state": 0 }
                                            error_info = str(progress.get('data'))
                                            if progress.get('data')['state'] == 2:
                                                print(ftime() + "Apply(Flash) inprogress, progress: 100%")
                                                # print('upgrade complete, BMC will reset, please wait for a minute')
                                                result.State('Success')
                                                result.Message([
                                                    "Activate pending, set BIOS setup options will activate later, trigger: systemreboot."])
                                                print(ftime() + "Activate pending")
                                                wirte_log(log_path, "Apply", "Write to Temporary FLASH Success",
                                                          result.Message)
                                                break
                                            elif "%" in progress.get('data')['progress']:
                                                pro = progress.get('data')['progress'].split("%")[0]
                                                if pro == '100':
                                                    count_100 = count_100 + 1
                                                process = ftime() + "Apply(Flash) inprogress, progress: " + str(
                                                    pro) + "%"
                                                b_num = len(process)
                                                # print(process + "\b" * b_num, end="", flush=True)
                                                wirte_log(log_path, "Apply", "In Progress",
                                                          "progress:" + str(pro) + "%")
                                        else:
                                            error_count = error_count + 1
                                            error_info = progress.get("data")
                                else:
                                    result.State("Failure")
                                    result.Message(["can not flash bios: " + flash.get("data")])
                                    wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                            else:
                                result.State("Failure")
                                result.Message(["Vertification File failed: " + vert.get("data")])
                                wirte_log(log_path, "File Verify", "Connect Failed", result.Message)
                        else:
                            result.State("Failure")
                            result.Message(["can not upload File, " + upload.get("data")])
                            wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    else:
                        result.State("Failure")
                        result.Message(["can not get bios mode: " + biosFlash.get("data")])
                        wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                else:
                    result.State("Failure")
                    result.Message(["can not set bios option: " + biosmode.get("data")])
                    wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue
            else:
                result.State("Failure")
                result.Message(["please input -t type: BMC or BIOS"])
                # logout
                RestFunc.logout(client)
                return result

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

    def geteventsub(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def gettaskstate(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def canceltask(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([])
        return res

    def collect(self, client, args):
        if args.component is not None:
            res = ResultBean()
            res.State("Not Support")
            res.Message(["param(-t) component is not support"])
            return res
        checkparam_res = ResultBean()
        if args.fileurl == ".":
            file_name = ""
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)
        elif args.fileurl == "..":
            file_name = ""
            file_path = os.path.abspath("..")
            args.fileurl = os.path.join(file_path, file_name)
        elif re.search(r"^[C-Zc-z]\:$", args.fileurl, re.I):
            file_name = ""
            file_path = os.path.abspath(args.fileurl + "\\")
            args.fileurl = os.path.join(file_path, file_name)
        else:
            file_name = os.path.basename(args.fileurl)
            file_path = os.path.dirname(args.fileurl)
        # 只输入文件名字，则默认为当前路径
        if file_path == "":
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)

        # 用户输入路径，则默认文件名dump_psn_time.tar
        if file_name == "":
            psn = "UNKNOWN"
            res = Base.getfru(self, client, args)
            if res.State == "Success":
                frulist = res.Message[0].get("FRU", [])
                if frulist != []:
                    psn = frulist[0].get('ProductSerial', 'UNKNOWN')
            else:
                return res
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = "dump_" + psn + "_" + logtime + ".tar"
            args.fileurl = os.path.join(file_path, file_name)
        else:
            p = r'\.tar$'
            if not re.search(p, file_name, re.I):
                checkparam_res.State("Failure")
                checkparam_res.Message(["Filename should be xxx.tar"])
                return checkparam_res
            file_name = file_name[0:-4] + ".tar"
        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except BaseException:
                checkparam_res.State("Failure")
                checkparam_res.Message(["can not create path."])
                return checkparam_res
        else:
            if os.path.exists(args.fileurl):
                name_id = 1
                name_new = file_name[:-4] + "(1).tar"
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = file_name[:-4] + "(" + str(name_id) + ")" + ".tar"
                    file_new = os.path.join(file_path, name_new)
                args.fileurl = file_new

        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # 生成log
        bmcres = ResultBean()
        generate_res = RestFunc.generateOnekeylogByRest(client)
        if generate_res['code'] == 404:
            bmcres.State("Not Support")
            bmcres.Message([""])
        else:
            # generate_res = RestFunc.generateOnekeylogByRest(client)
            if generate_res.get('code') != 0:
                bmcres.State("Failure")
                bmcres.Message([generate_res.get('data')])
            else:
                count = 0
                while True:
                    if count > 60:
                        break
                    count = count + 1
                    import time
                    time.sleep(5)
                # get
                res = RestFunc.getOneKeyLogByRest(client, args.fileurl)
                if res == {}:
                    bmcres.State("Failure")
                    bmcres.Message(["cannot download onekeylog"])
                elif res.get('code') == 0 and res.get('data') is not None:
                    bmcres.State("Success")
                    data = res.get('data')
                    bmcres.Message([data])
                elif res.get('code') != 0 and res.get('data') is not None:
                    bmcres.State("Failure")
                    bmcres.Message([res.get('data')])
                else:
                    bmcres.State("Failure")
                    bmcres.Message(["download onekeylog error"])
        # logout
        RestFunc.logout(client)
        return bmcres

    def getbmcinfo(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        infoList = []
        status = 0
        time_result = UpTimeBean()
        info = RestFunc.uptimeBMCByRest(client)
        if info == {}:
            result.State('Failure')
            result.Message(['get uptime failed'])
        elif info.get('code') == 0 and info.get('data') is not None:
            status = status + 1
            data = info.get('data')
            if "poh_counter_reading" in data:
                poh_counter_reading = data["poh_counter_reading"]
                day = poh_counter_reading // 24  # 取整数
                hour = poh_counter_reading % 24  # 取余数
                time_result.RunningTime(str(day) + " day " + str(hour) + " hour")
                infoList.append(time_result.dict)
            else:
                result.State('Failure')
                result.Message(['get uptime failed'])
        else:
            result.State("Failure")
            result.Message(["get uptime error, error code " + str(time_result.get('code'))])
        fru = IpmiFunc.getAllFruByIpmi(client)
        if fru:
            if fru.get('code') == 0 and fru.get('data') is not None:
                status = status + 1
                product = fru.get('data')[0]
                frubean = FruBean()
                frubean.FRUID(product.get('fru_id', None))
                frubean.ChassisType(product.get('chassis_type', None))
                frubean.ProductManufacturer(product.get('product_manufacturer', None))
                frubean.ProductName(product.get('product_name', None))
                frubean.ProductPartNumber(product.get('product_part_number', None))
                frubean.ProductSerial(product.get('product_serial', None))
                frubean.ProductAssetTag(product.get('product_asset_tag', None))
                infoList.append(frubean.dict)
            else:
                result.State('Failure')
                result.Message('Can not get Fru information')
        else:
            result.State('Failure')
            result.Message('Can not get Fru information')
        res = RestFunc.getLanByRest(client)
        if res == {}:
            result.State("Failure")
            result.Message(["cannot get lan information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            status = status + 1
            data = res.get('data')
            for lan in data:
                ipbean = NetBean()
                if lan['lan_enable'] == "Disabled":
                    ipbean.IPVersion('Disabled')
                    ipbean.PermanentMACAddress(lan['mac_address'])
                    ipv4 = IPv4Bean()
                    ipv6 = IPv6Bean()
                    ipbean.IPv4(ipv4.dict)
                    ipbean.IPv6(ipv6.dict)
                else:
                    if lan['ipv4_enable'] == "Enabled" and lan['ipv6_enable'] == "Enabled":
                        ipbean.IPVersion('IPv4andIPv6')
                    elif lan['ipv4_enable'] == "Enabled":
                        ipbean.IPVersion('IPv4')
                    elif lan['ipv6_enable'] == "Enabled":
                        ipbean.IPVersion('IPv6')
                    ipbean.PermanentMACAddress(lan['mac_address'])

                    if lan['ipv4_enable'] == "Enabled":
                        ipv4 = IPv4Bean()
                        ipv4.AddressOrigin(lan['ipv4_dhcp_enable'])
                        ipv4.Address(lan['ipv4_address'])
                        ipv4.SubnetMask(lan['ipv4_subnet'])
                        ipv4.Gateway(lan['ipv4_gateway'])
                        ipbean.IPv4(ipv4.dict)

                    if lan['ipv6_enable'] == "Enabled":
                        ipv6 = IPv6Bean()
                        ipv6.AddressOrigin(lan['ipv6_dhcp_enable'])
                        ipv6.Address(lan['ipv6_address'])
                        ipv6.PrefixLength(lan['ipv6_prefix'])
                        ipv6.Gateway(lan['ipv6_gateway'])
                        ipbean.IPv6([ipv6.dict])

                    vlanbean = vlanBean()
                    vlanbean.State(lan['vlan_enable'])
                    vlanbean.VLANId(lan['vlan_id'])
                    ipbean.VLANInfo(vlanbean.dict)
                infoList.append(ipbean.dict)
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message([res.get('data')])
        else:
            result.State("Failure")
            result.Message(["get lan information error"])
        if status == 3:
            result.State("Success")
            result.Message(infoList)
        # logout
        RestFunc.logout(client)
        return result

    def getharddisk(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        hard_info = RestFunc.getHardDiskInfoByRest(client)
        if hard_info == {}:
            result.State('Failure')
            result.Message(['get hard disk info failed'])
        elif hard_info.get('code') == 0 and hard_info.get('data') is not None:
            hard_data = hard_info.get('data')['disks']
            hard_dict = {0: 'No', 1: 'Yes'}
            FrontRear_dict = {1: 'Front', 0: 'Rear'}
            hardList = []
            idx = 0
            while idx < len(hard_data):
                hard_result = HardBackBean()
                hsrd_info = hard_data[idx]
                hard_result.Id(hsrd_info.get('id', None))
                hard_result.Present(hard_dict.get(hsrd_info.get('present', 0)))
                hard_result.FrontRear(FrontRear_dict.get(hsrd_info.get('front', 1)))
                hard_result.BackplaneIndex(hsrd_info.get('backplane_index', None))
                hard_result.Error(hard_dict.get(hsrd_info.get('error', 0)))
                hard_result.Locate(hard_dict.get(hsrd_info.get('locate', 0)))
                hard_result.Rebuild(hard_dict.get(hsrd_info.get('rebuild', 0)))
                hard_result.NVME(hard_dict.get(hsrd_info.get('nvme', 0)))
                hard_result.Model(hsrd_info.get('model', None))
                hard_result.Vendor(hsrd_info.get('vendor', None))
                hard_result.Media(hsrd_info.get('nvme_media', None))
                hard_result.Interface(hsrd_info.get('nvme_interface', None))
                hard_result.FW(hsrd_info.get('nvme_fw', None))
                hard_result.SN(hsrd_info.get('sn', None))
                idx += 1
                hardList.append(hard_result.dict)
            result.State("Success")
            result.Message(hardList)
        else:
            result.State("Failure")
            result.Message(["get hard disk info error, error code " + str(hard_info.get('code'))])
        RestFunc.logout(client)
        return result

    def getbackplane(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        back_info = RestFunc.getDiskbackplaneInfoByRest(client)
        if back_info == {}:
            result.State('Failure')
            result.Message(['get disk back plane info failed'])
        elif back_info.get('code') == 0 and back_info.get('data') is not None:
            back_data = back_info.get('data')
            back_dict = {0: 'No', 1: 'Yes'}
            backList = []
            idx = 0
            while idx < len(back_data):
                back_result = BackplaneBean()
                back_info = back_data[idx]
                back_result.Id(back_info.get('id', None))
                back_result.Present(back_dict.get(back_info.get('present', 0)))
                back_result.CPLDVersion(back_info.get('cpld_version', None))
                back_result.PortCount(back_info.get('port_count', 0))
                back_result.DriverCount(back_info.get('driver_count', 0))
                back_result.Temperature(back_info.get('temperature', None))
                idx += 1
                backList.append(back_result.dict)
            result.State("Success")
            result.Message(backList)
        else:
            result.State("Failure")
            result.Message(["get disk back plane info error, error code " + str(back_info.get('code'))])
        RestFunc.logout(client)
        return result

    def getautitlog(self, client, args):
        nicRes = ResultBean()
        if args.auditfile is not None:
            file_name = os.path.basename(args.auditfile)
            file_path = os.path.dirname(args.auditfile)
            # 用户输入路径，则默认文件名eventlog_psn_time
            if file_name == "":
                psn = "UNKNOWN"
                res = Base.getfru(self, client, args)
                if res.State == "Success":
                    frulist = res.Message[0].get("FRU", [])
                    if frulist != []:
                        psn = frulist[0].get('ProductSerial', 'UNKNOWN')
                else:
                    return res
                import time
                struct_time = time.localtime()
                logtime = time.strftime("%Y%m%d-%H%M", struct_time)
                file_name = "auditlog_" + psn + "_" + logtime
                args.auditfile = os.path.join(file_path, file_name)
            if not os.path.exists(file_path):
                try:
                    os.makedirs(file_path)
                except BaseException:
                    nicRes.State("Failure")
                    nicRes.Message(["cannot build path " + file_path])
                    return nicRes
            else:
                if os.path.exists(args.auditfile):
                    name_id = 1
                    path_new = os.path.splitext(args.auditfile)[0] + "(1)" + os.path.splitext(args.auditfile)[1]
                    while os.path.exists(path_new):
                        name_id = name_id + 1
                        path_new = os.path.splitext(args.auditfile)[0] + "(" + str(name_id) + ")" + \
                            os.path.splitext(args.auditfile)[1]
                    args.auditfile = path_new
        # check param
        if args.logtime is not None and args.count is not None:
            nicRes.State("Failure")
            nicRes.Message(["param date and count cannot be set together at one query"])
            return nicRes
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        # bmc zone in minutes
        date_res = RestFunc.getDatetimeByRest(client)
        if date_res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get bmc time"])
            RestFunc.logout(client)
            return nicRes
        elif date_res.get('code') == 0 and date_res.get('data') is not None:
            bmczone = date_res.get('data')['utc_minutes']
        elif date_res.get('code') != 0 and date_res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([date_res.get('data')])
            RestFunc.logout(client)
            return nicRes
        else:
            nicRes.State("Failure")
            nicRes.Message(["get bmc time error"])
            RestFunc.logout(client)
            return nicRes

        if args.logtime is not None:
            import time
            # self.newtime = "2018-05-31T10:10+08:00"
            if not RegularCheckUtil.checkBMCTime(args.logtime):
                nicRes.State("Failure")
                # nicRes.Message(["time param should be like YYYY-mm-ddTHH:MM±HH:MM"])
                nicRes.Message(["time param should be like YYYY-mm-ddTHH:MM+HH:MM"])
                RestFunc.logout(client)
                return nicRes
            if "+" in args.logtime:
                newtime = args.logtime.split("+")[0]
                zone = args.logtime.split("+")[1]
                we = "+"
            else:
                zone = args.logtime.split("-")[-1]
                newtime = args.logtime.split("-" + zone)[0]
                we = "-"
            hh = int(zone[0:2])
            mm = int(zone[3:5])
            # output zone in minutes
            showzone = int(we + str(hh * 60 + mm))
            # bmc zone in minutes

            try:
                # time.struct_time(tm_year=2019, tm_mon=4, tm_mday=16, tm_hour=15, tm_min=35, tm_sec=0, tm_wday=1, tm_yday=106, tm_isdst=-1)
                structtime = time.strptime(newtime, "%Y-%m-%dT%H:%M")
                # 时间戳1555400100
                stamptime = int(time.mktime(structtime))
                # 时间戳还差了 showzone - localzone的秒数
                stamptime = stamptime - (showzone * 60 - abs(int(time.timezone)))
            except ValueError as e:
                # print (str(e))
                nicRes.State("Failure")
                nicRes.Message(["illage time"])
                RestFunc.logout(client)
                return nicRes
        else:
            stamptime = ""
            showzone = bmczone

        if args.count is not None:
            if args.count <= 0:
                nicRes.State("Failure")
                nicRes.Message(["count param should be positive"])
                RestFunc.logout(client)
                return nicRes
        else:
            args.count = -1

        # check over
        res = RestFunc.getAuditLogByRest(client, args.count, stamptime, bmczone, showzone, False)
        # res = {"code":0,"data":"xxxxx"}
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get audit log"])
        elif res.get('code') == 0 and res.get('data') is not None:
            json_res = {"Auditlog": res.get('data')[::-1]}
            if args.auditfile is not None:
                try:
                    logfile = open(args.auditfile, "w")
                    # logfile.write(str(json))
                    logfile.write(
                        json.dumps(json_res, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=True))
                    logfile.close()
                except Exception as e:
                    # print  (str(e))
                    nicRes.State("Failure")
                    nicRes.Message(["cannot write log in " + args.auditfile])
                    RestFunc.logout(client)
                    return nicRes
                nicRes.State("Success")
                nicRes.Message(["Audit logs is stored in : " + args.auditfile])
            else:
                nicRes.State("Success")
                nicRes.Message([json_res])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get audit log error"])
        # logout
        RestFunc.logout(client)
        return nicRes

    def getsystemlog(self, client, args):
        nicRes = ResultBean()
        if args.systemfile is not None:
            file_name = os.path.basename(args.systemfile)
            file_path = os.path.dirname(args.systemfile)
            # 用户输入路径，则默认文件名eventlog_psn_time
            if file_name == "":
                psn = "UNKNOWN"
                res = Base.getfru(self, client, args)
                if res.State == "Success":
                    frulist = res.Message[0].get("FRU", [])
                    if frulist != []:
                        psn = frulist[0].get('ProductSerial', 'UNKNOWN')
                else:
                    return res
                import time
                struct_time = time.localtime()
                logtime = time.strftime("%Y%m%d-%H%M", struct_time)
                file_name = "systemlog_" + psn + "_" + logtime
                args.systemfile = os.path.join(file_path, file_name)
            if not os.path.exists(file_path):
                try:
                    os.makedirs(file_path)
                except BaseException:
                    nicRes.State("Failure")
                    nicRes.Message(["cannot build path " + file_path])
                    return nicRes
            else:
                if os.path.exists(args.systemfile):
                    name_id = 1
                    path_new = os.path.splitext(args.systemfile)[0] + "(1)" + os.path.splitext(args.systemfile)[1]
                    while os.path.exists(path_new):
                        name_id = name_id + 1
                        path_new = os.path.splitext(args.systemfile)[0] + "(" + str(name_id) + ")" + \
                            os.path.splitext(args.systemfile)[1]
                    args.systemfile = path_new
        # check param
        if args.logtime is not None and args.count is not None:
            nicRes.State("Failure")
            nicRes.Message(["param date and count cannot be set together at one query"])
            return nicRes
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        # bmc zone in minutes
        date_res = RestFunc.getDatetimeByRest(client)
        if date_res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get bmc time"])
            RestFunc.logout(client)
            return nicRes
        elif date_res.get('code') == 0 and date_res.get('data') is not None:
            bmczone = date_res.get('data')['utc_minutes']
        elif date_res.get('code') != 0 and date_res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([date_res.get('data')])
            RestFunc.logout(client)
            return nicRes
        else:
            nicRes.State("Failure")
            nicRes.Message(["get bmc time error"])
            RestFunc.logout(client)
            return nicRes

        if args.logtime is not None:
            import time
            if not RegularCheckUtil.checkBMCTime(args.logtime):
                nicRes.State("Failure")
                nicRes.Message(["time param should be like YYYY-mm-ddTHH:MM+HH:MM"])
                RestFunc.logout(client)
                return nicRes
            if "+" in args.logtime:
                newtime = args.logtime.split("+")[0]
                zone = args.logtime.split("+")[1]
                we = "+"
            else:
                zone = args.logtime.split("-")[-1]
                newtime = args.logtime.split("-" + zone)[0]
                we = "-"
            hh = int(zone[0:2])
            mm = int(zone[3:5])
            # output zone in minutes
            showzone = int(we + str(hh * 60 + mm))
            # bmc zone in minutes

            try:
                structtime = time.strptime(newtime, "%Y-%m-%dT%H:%M")
                # 时间戳1555400100
                stamptime = int(time.mktime(structtime))
                # 时间戳还差了 showzone - localzone的秒数
                stamptime = stamptime - (showzone * 60 - abs(int(time.timezone)))
            except ValueError as e:
                # print (str(e))
                nicRes.State("Failure")
                nicRes.Message(["illage time"])
                RestFunc.logout(client)
                return nicRes
        else:
            stamptime = ""
            showzone = bmczone

        if args.count is not None:
            if args.count <= 0:
                nicRes.State("Failure")
                nicRes.Message(["count param should be positive"])
                RestFunc.logout(client)
                return nicRes
        else:
            args.count = -1
        level_dict = {"alert": 1, "critical": 2, "error": 3, "notice": 4, "warning": 5, "debug": 6, "emergency": 7,
                      "info": 8, "all": 0}
        if args.level in level_dict:
            level = level_dict[args.level]
        else:
            level = 1

        # check over
        res = RestFunc.getSystemLogByRest(client, level, args.count, stamptime, bmczone, showzone, False)
        # res = {"code":0,"data":"xxxxx"}
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get system log"])
        elif res.get('code') == 0 and res.get('data') is not None:
            json_res = {"Systemlog": res.get('data')[::-1]}
            if args.systemfile is not None:
                try:
                    logfile = open(args.systemfile, "w")
                    # logfile.write(str(json))
                    logfile.write(
                        json.dumps(json_res, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=True))
                    logfile.close()
                except Exception as e:
                    # print  (str(e))
                    nicRes.State("Failure")
                    nicRes.Message(["cannot write log in " + args.systemfile])
                    RestFunc.logout(client)
                    return nicRes
                nicRes.State("Success")
                nicRes.Message(["System logs is stored in : " + args.systemfile])
            else:
                nicRes.State("Success")
                nicRes.Message([json_res])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get system log error"])
        # logout
        RestFunc.logout(client)
        return nicRes

    def getbmclogsettings(self, client, args):
        bmcresult = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        res = RestFunc.getBMCLogSettings(client)

        if res.get('code') == 0 and res.get('data') is not None:
            bmcresult.State("Success")
            setting = collections.OrderedDict()
            result = res.get('data')
            SystemLog = collections.OrderedDict()
            setting['SystemLog'] = SystemLog
            if result['system_log'] == 0:
                SystemLog['Status'] = str("Disable")
            else:
                SystemLog['Status'] = str("Enable")
                if result['remote'] == 1:
                    SystemLog['LogType'] = "Local"
                    SystemLog['FileSize(B)'] = str(result['file_size'])
                    SystemLog['RotateCount'] = str(result['rotate_count'])
                elif result['remote'] == 2:
                    SystemLog['LogType'] = "Remote"
                    SystemLog['ServerAddr'] = str(result['server_addr'])
                    SystemLog['Port'] = str(result['port'])
                    if 'protocol' in result:
                        SystemLog['ProtocolType'] = str('UDP' if result['protocol'] == 0 else 'TCP')
                elif result['remote'] == 3:
                    SystemLog['LogType'] = "Local & Remote"
                    SystemLog['FileSize(B)'] = str(result['file_size'])
                    SystemLog['RotateCount'] = str(result['rotate_count'])
                    SystemLog['ServerAddr'] = str(result['server_addr'])
                    SystemLog['Port'] = str(result['port'])
                    if 'protocol' in result:
                        SystemLog['ProtocolType'] = str('UDP' if result['protocol'] == 0 else 'TCP')
            AuditLog = collections.OrderedDict()
            setting['AuditLog'] = AuditLog
            if result['audit_log'] == 0:
                AuditLog['Status'] = str("Disable")
            else:
                AuditLog['Status'] = str("Enable")
                if 'remote_audit' in result:
                    if result['remote_audit'] == 1:
                        AuditLog['LogType'] = "Local"
                        AuditLog['FileSize(B)'] = str(result['file_size'])
                        AuditLog['RotateCount'] = str(result['rotate_count'])
                    elif result['remote_audit'] == 2:
                        AuditLog['LogType'] = "Remote"
                        AuditLog['ServerAddr'] = str(result['server_addr'])
                        AuditLog['Port'] = str(result['port'])
                        if 'protocol' in result:
                            AuditLog['ProtocolType'] = str('UDP' if result['protocol'] == 0 else 'TCP')
                    elif result['remote_audit'] == 3:
                        AuditLog['LogType'] = "Local & Remote"
                        AuditLog['FileSize(B)'] = str(result['file_size'])
                        AuditLog['RotateCount'] = str(result['rotate_count'])
                        AuditLog['ServerAddr'] = str(result['server_addr'])
                        AuditLog['Port'] = str(result['port'])
                        if 'protocol' in result:
                            AuditLog['ProtocolType'] = str('UDP' if result['protocol'] == 0 else 'TCP')
            bmcresult.Message([setting])
        else:
            bmcresult.State("Failure")
            bmcresult.Message(["get BMC system and audit log settings error, " + res.get('data')])

        RestFunc.logout(client)
        return bmcresult

    def setbmclogsettings(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        bmc_flag = 0
        # local 是否可以配置
        localFlag = False
        # remote 是否可以配置
        remoteFlag = False
        decodeStatus = {'disable': 0, 'enable': 1}  # default 1
        decodeType = {'remote': 2, 'local': 1, 'both': 3}  # default 0
        decodeProtocolType = {'UDP': 0, 'TCP': 1}  # default 1

        getres = RestFunc.getBMCLogSettings(client)
        if getres.get('code') == 0 and getres.get('data') is not None:
            data = getres.get('data')
            default_id = data['id']

            default_system_log = data['system_log']
            # M4版本 system_log 兼职 status 与 type
            # 远程状态下system_log==2 但是传至还是需要传1
            if default_system_log == 2:
                default_system_log = 1
            default_type = data['remote']
            default_addr = data['server_addr']
            default_port = data['port']
            # 端口默认为514
            if default_port == 0:
                default_port = 514
            default_file_size = data['file_size']
            default_rotate_count = data['rotate_count']

            default_audit_log = data['audit_log']
            # 远程状态下system_log==2 但是传至还是需要传1
            if default_audit_log == 2:
                default_audit_log = 1
            if 'protocol' in data:
                default_protocol = data['protocol']
            else:
                default_protocol = ''
            if 'remote_audit' in data:
                if bmc_flag == 0:
                    bmc_flag = 1
                default_audit_type = data['remote_audit']
            else:
                default_audit_type = ''
        else:
            result.State("Failure")
            result.Message(["get BMC system and audit log settings error, " + getres.get('data')])
            RestFunc.logout(client)
            return result

        if args.auditLogStatus is None:
            audit_log = default_audit_log
        else:
            audit_log = decodeStatus.get(args.auditLogStatus, 1)
            if audit_log != default_audit_log:
                edit_flag = True

        if args.status is None:
            system_log = default_system_log
        else:
            system_log = decodeStatus.get(args.status, 1)
            if system_log != default_system_log:
                edit_flag = True

        # 初始化
        serverPort = default_port
        serverAddr = default_addr
        fileSize = default_file_size
        rotateCount = default_rotate_count
        type = default_type
        auditType = default_audit_type
        protocolType = default_protocol
        if system_log != 0:
            if args.type is not None:
                type = decodeType.get(args.type, 0)
                if type != default_type:
                    edit_flag = True
            else:
                # 默认启动本地日志
                if type == 0:
                    type = 1
            if type == 2:
                remoteFlag = True
            elif type == 1:
                localFlag = True
            elif type == 3:
                localFlag = True
                remoteFlag = True
        else:
            if not (
                    args.type is None and args.fileSize is None and args.rotateCount is None and args.serverAddr is None and args.serverPort is None):
                result.State("Failure")
                result.Message(['type(-T),fileSize(-L),rotateCount(-C),serverAddr(-A),serverPort(-R) can not be set when Status(-S) is disable.'])
                RestFunc.logout(client)
                return result
        if audit_log != 0:
            if bmc_flag > 0:
                if args.auditType is not None:
                    auditType = decodeType.get(args.auditType, 0)
                    if auditType != default_audit_type:
                        edit_flag = True
                else:
                    # 默认启动本地日志
                    if auditType == 0:
                        auditType = 1
                if auditType == 2:
                    remoteFlag = True
                elif auditType == 1:
                    localFlag = True
                elif auditType == 3:
                    localFlag = True
                    remoteFlag = True
            else:
                if args.auditType is not None:
                    result.State("Failure")
                    result.Message(['Current BMC version do not support audit log type(-AT).'])
                    RestFunc.logout(client)
                    return result

        # 配置 local
        if localFlag:
            # rotateCount
            if args.rotateCount is not None:
                rotateCount = args.rotateCount
                edit_flag = True

            # fileSize
            if args.fileSize is not None:
                if RegularCheckUtil.checkFileSize(args.fileSize):
                    fileSize = args.fileSize
                    edit_flag = True
                else:
                    result.State("Failure")
                    result.Message(['File Size(-L) must be int and between 3 to 65535 bytes.'])
                    RestFunc.logout(client)
                    return result
            else:
                # fileSize 默认为30000
                if fileSize == 0:
                    fileSize = 30000

        else:
            if args.fileSize is not None:
                result.State("Failure")
                if bmc_flag > 0:
                    result.Message(['File Size(-L) can not be set when neither type(-T) nor auditType(-AT) is local.'])
                else:
                    result.Message(['File Size(-L) can not be set when type(-T) is remote.'])
                RestFunc.logout(client)
                return result
            if args.rotateCount is not None:
                result.State("Failure")
                if bmc_flag > 0:
                    result.Message(['Rotate Count(-C) can not be set when neither type(-T) nor auditType(-AT) is local.'])
                else:
                    result.Message(['Rotate Count(-C) can not be set when type(-T) is remote.'])
                RestFunc.logout(client)
                return result
        if remoteFlag:
            if args.serverAddr is None:
                if serverAddr == '':
                    result.State("Failure")
                    result.Message(['Server Address(-A) is needed.'])
                    RestFunc.logout(client)
                    return result
            else:
                if RegularCheckUtil.checkIP(args.serverAddr):
                    serverAddr = args.serverAddr
                    edit_flag = True
                else:
                    result.State("Failure")
                    result.Message(['Server Address(-A) must be ipv4 or ipv6 or FQDN (Fully qualified domain name) format.'])
                    RestFunc.logout(client)
                    return result

            if args.serverPort is not None:
                if RegularCheckUtil.checkPort(args.serverPort):
                    serverPort = args.serverPort
                    edit_flag = True
                else:
                    result.State("Failure")
                    result.Message(['Server Port(-R) must between 0-65535.'])
                    RestFunc.logout(client)
                    return result
            # bmc最新版本
            if bmc_flag > 0:
                if args.protocolType is not None:
                    protocolType = decodeProtocolType.get(args.protocolType, 0)
                    if protocolType != default_protocol:
                        edit_flag = True
            else:
                if args.protocolType is not None:
                    result.State("Failure")
                    result.Message(['Current BMC version do not support Protocol Type(-PT).'])
                    RestFunc.logout(client)
                    return result
        else:
            if args.serverAddr is not None:
                result.State("Failure")
                if bmc_flag > 0:
                    result.Message(['server address(-A) can not be set when neither type(-T) nor auditType(-AT) is remote.'])
                else:
                    result.Message(['server address(-A) can not be set when type(-T) is local.'])
                RestFunc.logout(client)
                return result
            if args.serverPort is not None:
                result.State("Failure")
                if bmc_flag > 0:
                    result.Message(['server port(-R) can not be set when neither type(-T) nor auditType(-AT) is remote.'])
                else:
                    result.Message(['server port(-R) can not be set when type(-T) is local.'])
                RestFunc.logout(client)
                return result
            # bmc最新版本
            if bmc_flag > 0:
                if args.protocolType is not None:
                    result.State("Failure")
                    result.Message(['protocol port(-R) can not be set when neither type(-T) nor auditType(-AT) is remote.'])
                    RestFunc.logout(client)
                    return result
            else:
                if args.protocolType is not None:
                    result.State("Failure")
                    result.Message(['Current BMC version do not support Protocol Type(-PT).'])
                    RestFunc.logout(client)
                    return result

        if not edit_flag:
            result.State("Failure")
            result.Message(['No setting changed!'])
            RestFunc.logout(client)
            return result
        data = {
            'file_size': fileSize,
            'id': default_id,
            'port': serverPort,
            'remote': type,
            'rotate_count': rotateCount,
            'server_addr': serverAddr,
            'system_log': system_log,
            'audit_log': audit_log
        }
        if bmc_flag > 0:
            data.update(protocol=protocolType)
            data.update(remote_audit=auditType)

        res = RestFunc.setBMCLogSettings(client, data)

        if res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            result.Message(["set BMC system and audit log settings success"])
        else:
            result.State("Failure")
            result.Message(["set BMC system and audit log settings error, " + res.get('data')])
        RestFunc.logout(client)
        return result

    def getservice(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        service = ResultBean()
        service_all = ServiceBean()
        list = []
        # get
        res = RestFunc.getServiceInfoByRest(client)
        if res == {}:
            service.State("Failure")
            service.Message(["cannot get information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            Info = res.get('data')
            Enabled = {1: 'Enabled', 0: 'Disabled'}
            for item_Info in Info:
                service_item = ServiceSingleBean()
                service_item.Id(item_Info.get('id', 0))
                sname = item_Info.get('service_name', '')
                service_item.Name(sname)
                service_item.Enable(Enabled.get(item_Info.get('state'), item_Info.get('state')))
                service_item.Port(None if item_Info.get('secure_port') == -1 else item_Info.get('secure_port'))
                service_item.Port2(None if item_Info.get('non_secure_port') == -1 else item_Info.get('non_secure_port'))
                service_item.InterfaceName(item_Info.get('interface_name', None))
                service_item.TimeOut(item_Info.get('time_out', 0))
                if item_Info.get('maximum_sessions', 128) == 255:
                    service_item.MaximumSessions(None)
                else:
                    service_item.MaximumSessions(item_Info.get('maximum_sessions', 128) - 128)
                service_item.ActiveSessions(item_Info.get('active_session', 128) - 128)
                list.append(service_item.dict)
            service_all.Service(list)
            service.State('Success')
            service.Message([service_all.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            service.State("Failure")
            service.Message(["get service information error, " + res.get('data')])
        else:
            service.State("Failure")
            service.Message(["get service information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return service

    def setservice(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        try:
            service = setservice(client, args)
        except BaseException:
            RestFunc.logout(client)

        RestFunc.logout(client)
        return service

    def addldisk(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        try:
            ldisk = createVirtualDrive(client, args)
        except BaseException:
            RestFunc.logout(client)
        RestFunc.logout(client)
        return ldisk

    def setldisk(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        try:
            ldisk = setVirtualDrive(client, args)
        except BaseException:
            RestFunc.logout(client)
        RestFunc.logout(client)
        return ldisk

    def getsmtp(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        smtp = ResultBean()
        SNMPList = []
        # get
        res = RestFunc.getSMTPM5ByRest(client)
        if res.get('code') == 0 and res.get('data') is not None:
            Info = res.get('data')
            channel_dict = {'eth0': 'eth0(shared)', 'eth1': 'eth1(dedicated)', 'bond0': 'bond0'}
            channelnum_dict = {'eth0': '8', 'eth1': '1', 'bond0': '1'}
            enabled_dict = {'0': 'disable', '1': 'enable'}
            for item in Info:
                smtpInfo = SMTPM5Bean()
                SenderEmail = getNone(str(item['email_id']))
                ServerName = getNone(str(item['primary_server_name']))
                Addreess = getNone(str(item['primary_server_ip']))
                Port = getNone(str(item['primary_smtp_port']))
                Username = getNone(str(item['primary_username']))
                ServerName2 = getNone(str(item['secondary_server_name']))
                Addreess2 = getNone(str(item['secondary_server_ip']))
                Port2 = getNone(str(item['secondary_smtp_port']))
                Username2 = getNone(str(item['secondary_username']))
                smtpInfo.Id(item['id'])
                smtpInfo.LanChannel(channel_dict.get(str(item['channel_interface']), 'N/A'))
                smtpInfo.ChannelNumber(channelnum_dict.get(str(item['channel_interface']), 'N/A'))
                smtpInfo.SenderEmail(SenderEmail)
                serverList = []
                serverInfo1 = SMTPServerBean()
                serverInfo1.ServerType("Primary SMTP Server")
                serverInfo1.SMTPSupport(enabled_dict.get(str(item['primary_smtp_enable']), 'N/A'))
                serverInfo1.ServerName(ServerName)
                serverInfo1.Addreess(Addreess)
                serverInfo1.Port(Port)
                serverInfo1.ServerAuth(enabled_dict.get(str(item['primary_smtp_authentication']), 'N/A'))
                serverInfo1.Username(Username)
                serverList.append(serverInfo1.dict)
                serverInfo2 = SMTPServerBean()
                serverInfo2.ServerType("secondary SMTP Server")
                serverInfo2.SMTPSupport(enabled_dict.get(str(item['secondary_smtp_enable']), 'N/A'))
                serverInfo2.ServerName(ServerName2)
                serverInfo2.Addreess(Addreess2)
                serverInfo2.Port(Port2)
                serverInfo2.ServerAuth(enabled_dict.get(str(item['secondary_smtp_authentication']), 'N/A'))
                serverInfo2.Username(Username2)
                serverList.append(serverInfo2.dict)
                smtpInfo.SMTPServer(serverList)
                SNMPList.append(smtpInfo.dict)
            smtp.State('Success')
            smtp.Message(SNMPList)
        elif res.get('code') != 0 and res.get('data') is not None:
            smtp.State("Failure")
            smtp.Message(["get SMTP information error, " + res.get('data')])
        else:
            smtp.State("Failure")
            smtp.Message(["get SMTP information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return smtp

    def setsmtp(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        smtp = setSMTP(client, args)
        RestFunc.logout(client)
        return smtp

    def getncsi(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # 5.7.2获取NCSI模式
        result = ResultBean()
        ncsi = NCSIM5Bean()
        nictype = {0: 'PHY', 1: 'OCP', 2: 'PCIE', 3: 'OCPA2', 254: 'AUTO'}
        nicmode = {1: 'Auto Failover', 0: 'Manual Switch'}
        ncsimode = RestFunc.getNCSIModeM5ByRest(client)
        if ncsimode.get('code') == 0 and ncsimode.get('data') is not None:
            data = ncsimode['data']
            ncsi.Mode(nicmode.get(data['mode'], 'N/A'))
            mode = data['mode']
        else:
            result.State("Failure")
            result.Message([" Server return " + str(ncsimode.status_code)])
            RestFunc.logout(client)
            return result
        # 5.7.1获取NCSI
        ncsiinterfaces = RestFunc.getNCSIM5ByRest(client)
        if ncsiinterfaces.get('code') == 0 and ncsiinterfaces.get('data') is not None:
            data = ncsiinterfaces['data']
            for item in data:
                ncsi.NicType(nictype.get(item['nic_type'], 'N/A'))
                if mode == 0:
                    ncsi.InterfaceName(str(item['interface_name']))
                    ncsi.PackageID(str(item['package_id']))
                    ncsi.ChannelNumber(str(item['channel_number']))
            result.State("Success")
            result.Message([ncsi.dict])
        else:
            result.State("Failure")
            result.Message([" Server return " + str(ncsiinterfaces.status_code)])
        RestFunc.logout(client)
        return result

    def setncsi(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        smtp = setNCSI(client, args)
        RestFunc.logout(client)
        return smtp

    def getpowerstatus(self, client, args):
        result = ResultBean()
        power_result = PowerStatusBean()
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        status_info = RestFunc.getChassisStatusByRest(client)
        if status_info.get('code') == 0 and status_info.get('data') is not None:
            status_data = status_info.get('data')
            power_result.PowerStatus(status_data.get('power_status', None))
            # power_result.UIDLed(status_data.get('led_status', None))
            result.State('Success')
            result.Message([power_result.dict])
        else:
            result.State("Failure")
            result.Message(["get power status error, error code " + str(status_info.get('code'))])
        RestFunc.logout(client)
        return result

    def getpsuconfig(self, client, args):
        result = ResultBean()
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        psu_info = RestFunc.getPsuInfo1ByRest(client)
        if psu_info.get('code') == 0 and psu_info.get('data') is not None:
            data = psu_info.get('data')
            present_dict = {1: 'Yes', 0: 'No'}
            AorS_dict = {0: 'Normal', 14: 'Standby', 85: 'Active', 'N/A': 'N/A'}
            if len(data) == 0:
                result.State("Failure")
                result.Message(['get psu config is empty!'])
                RestFunc.logout(client)
                return result
            psuList = []
            for item in data:
                psu = PSUConfigBean()
                if 'id' in item:
                    id = item['id']
                else:
                    id = 'N/A'
                if 'present' in item:
                    pre = item['present']
                else:
                    pre = 'N/A'
                if 'mode' in item:
                    mode = item['mode']
                else:
                    mode = 'N/A'
                psu.Id(id)
                psu.Present(present_dict.get(pre, 'N/A'))
                psu.Mode(AorS_dict.get(mode, 'N/A'))
                psuList.append(psu.dict)
            result.State('Success')
            result.Message(psuList)
        else:
            result.State("Failure")
            result.Message(["get psu config failed"])
        RestFunc.logout(client)
        return result

    def setpsuconfig(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        psu = setPsuConfig(client, args)
        RestFunc.logout(client)
        return psu

    def getpsupeak(self, client, args):
        result = ResultBean()
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        psu_info = RestFunc.getPsuPeakByRest(client)
        if psu_info.get('code') == 0 and psu_info.get('data') is not None:
            data = psu_info.get('data')
            status_dict = {1: 'Enable', 0: 'Disable'}
            psu = PSUPeakBean()
            psu.Status(status_dict.get(data.get('enable', ''), 'N/A'))
            psu.Time(data.get('time', 'N/A'))
            result.State('Success')
            result.Message([psu.dict])
        else:
            result.State("Failure")
            result.Message(["get psu config failed"])
        RestFunc.logout(client)
        return result

    def setpsupeak(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        psu = setPsuPeak(client, args)
        RestFunc.logout(client)
        return psu

    # 获取电源还原设置
    def getpowerrestore(self, client, args):
        res = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        policy_dict = {2: 'Always Power On', 0: 'Always Power Off', 1: 'Restore Last Power State', 3: 'UnKnown'}
        policy_rest = RestFunc.getPowerPolicyByRest(client)
        if policy_rest.get('code') == 0 and policy_rest.get('data') is not None:
            policy_serult = policy_rest['data']
            JSON = {}
            JSON['policy'] = policy_dict.get(policy_serult.get('power_policy', 3), 'UnKnown')
            res.State('Success')
            res.Message([JSON])
        else:
            res.State("Failure")
            res.Message(["get power restore failed"])
        RestFunc.logout(client)
        return res

    # 设置电源还原设置
    # action: on off restore
    # return
    def setpowerrestore(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        res = {}
        policy_dict = {'on': 2, 'off': 0, 'restore': 1}
        action = policy_dict.get(args.option, None)
        if action is None:
            res['State'] = -1
            res['Data'] = " parameter is invalid"
        count = 0
        while True:
            policy_rest = RestFunc.setPowerPolicyByRest(client, action)
            if policy_rest is None:
                if count == 0:
                    count += 1
                    continue
            elif policy_rest.status_code == 200:
                policy_serult = policy_rest.json()
                if policy_serult is not None and 'action' in policy_serult:
                    res['State'] = 0
                    res['Data'] = 'set power policy success'
                    break
                else:
                    if count == 0:
                        count += 1
                        continue
                    res['State'] = -1
                    res['Data'] = 'set power policy failed'
                    break
            else:
                if count == 0:
                    count += 1
                    continue
                res['State'] = -1
                res['Data'] = 'request failed'
                break
        if res['State'] == 0:
            result.State('Success')
        else:
            result.State('Failure')
        result.Message(res['Data'])
        RestFunc.logout(client)
        return result

    def getad(self, client, args):
        res = ResultBean()
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        ad_rest = RestFunc.getADByRest(client)
        if ad_rest.get('code') == 0 and ad_rest.get('data') is not None:
            data = ad_rest['data']
            ad = ADBean()
            if data['enable'] == 1:
                state = 'enable'
            else:
                state = 'disable'
            ad.ActiveDirectoryAuthentication(state)
            ad.SecretName(getNone(data['secret_username']))
            if 'timeout' in data:
                ad.Timeout(data['timeout'])
            ad.UserDomainName(getNone(data['user_domain_name']))
            ad.DomainControllerServerAddress1(getNone(data['domain_controller1']))
            ad.DomainControllerServerAddress2(getNone(data['domain_controller2']))
            ad.DomainControllerServerAddress3(getNone(data['domain_controller3']))
            res.State('Success')
            res.Message([ad.dict])
        else:
            res.State("Failure")
            res.Message(["failed to get AD settings"])
        RestFunc.logout(client)
        return res

    def setad(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setAD(client, args)
        RestFunc.logout(client)
        return result

    def getadgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = getADGroup(client, args)
        RestFunc.logout(client)
        return result

    def addadgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = addADGroup(client, args)
        RestFunc.logout(client)
        return result

    def setadgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setADGroup(client, args)
        RestFunc.logout(client)
        return result

    def deladgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = delADGroup(client, args)
        RestFunc.logout(client)
        return result

    def getldap(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        retult = getLDAP(client, args)
        RestFunc.logout(client)
        return retult

    def setldap(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setLDAP(client, args)
        RestFunc.logout(client)
        return result

    def getldapgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = getLDAPGroup(client, args)
        RestFunc.logout(client)
        return result

    def addldapgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = addLDAPGroup(client, args)
        RestFunc.logout(client)
        return result

    def setldapgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setLDAPGroup(client, args)
        RestFunc.logout(client)
        return result

    def delldapgroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = delLDAPGroup(client, args)
        RestFunc.logout(client)
        return result

    def getusergroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        responds = RestFunc.getUserGroupByRest(client)
        if responds['code'] == 0 and responds['data'] is not None:
            groupList = []
            data = responds['data']
            for item in data:
                group = collections.OrderedDict()
                group['GroupId'] = item['GroupID']
                group['GroupName'] = item['GroupName']
                group['GroupPrivilege'] = item['GroupPriv']
                if 'GroupName' not in item or 'GroupPriv' not in item:
                    result.State("Failure")
                    result.Message(["failed to get user group"])
                    return result
                groupList.append(group)
            result.State("Success")
            result.Message([{'UserGroup': groupList}])
        else:
            result.State("Failure")
            result.Message(["failed to get user group"])
            return result
        RestFunc.logout(client)
        return result

    def addusergroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = addUserGroup(client, args)
        RestFunc.logout(client)
        return result

    def setusergroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setUserGroup(client, args)
        RestFunc.logout(client)
        return result

    def delusergroup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = delUserGroup(client, args)
        RestFunc.logout(client)
        return result

    def getdns(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = getDNS(client, args)
        RestFunc.logout(client)
        return result

    def setdns(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setDNS(client, args)
        RestFunc.logout(client)
        return result

    def getnetwork(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = getNetwork(client, args)
        RestFunc.logout(client)
        return result

    def setnetwork(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setNetwork(client, args)
        RestFunc.logout(client)
        return result

    def setipv4(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setIPv4(client, args)
        RestFunc.logout(client)
        return result

    def setipv6(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setIPv6(client, args)
        RestFunc.logout(client)
        return result

    def setvlan(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = setVlan(client, args)
        RestFunc.logout(client)
        return result

    def backup(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = backup.backup(client, args)
        RestFunc.logout(client)
        return result

    def restore(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = restore.restore(client, args)
        try:
            RestFunc.logout(client)
        except BaseException:
            return result
        return result

    def resetbmc(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        res = RestFunc.resetBMC(client, 0)
        if res['code'] == 0 and res['data'] is not None:
            result.State("Success")
            result.Message(["reset BMC success"])
        else:
            result.State("Failure")
            result.Message(["failed to reset BMC"])
        try:
            RestFunc.logout(client)
        except BaseException:
            return result
        return result

    def resetkvm(self, client, args):
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        res = RestFunc.resetBMC(client, 1)
        if res['code'] == 0 and res['data'] is not None:
            result.State("Success")
            result.Message(["reset KVM success"])
        else:
            result.State("Failure")
            result.Message(["failed to reset KVM"])
        try:
            RestFunc.logout(client)
        except BaseException:
            return result
        return result


def getNone(item_str):
    if item_str is None or item_str == '':
        item_str = 'N/A'
    return item_str


def setSMTP(client, args):
    smtpResult = ResultBean()
    # get default smtp config
    res = RestFunc.getSMTPM5ByRest(client)
    if res.get('code') == 0 and res.get('data') is not None:
        result = res['data']
        isNone = True
        for item in result:
            if item['channel_interface'] != args.interface:
                continue
            isNone = False
            default_id = item['id']
            default_email_id = item['email_id']
            default_channel_interface = item['channel_interface']

            default_primary_smtp_enable = item['primary_smtp_enable']
            default_primary_server_ip = item['primary_server_ip']
            default_primary_server_name = item['primary_server_name']
            default_primary_smtp_port = item['primary_smtp_port']
            default_primary_smtp_secure_port = item['primary_smtp_secure_port']
            default_primary_smtp_authentication = item['primary_smtp_authentication']
            default_primary_username = item['primary_username']
            default_primary_ssltls_enable = item['primary_ssltls_enable']
            default_primary_starttls_enable = item['primary_starttls_enable']

            default_secondary_smtp_enable = item['secondary_smtp_enable']
            default_secondary_server_ip = item['secondary_server_ip']
            default_secondary_server_name = item['secondary_server_name']
            default_secondary_smtp_port = item['secondary_smtp_port']
            default_secondary_smtp_secure_port = item['secondary_smtp_secure_port']
            default_secondary_smtp_authentication = item['secondary_smtp_authentication']
            default_secondary_username = item['secondary_username']
            default_secondary_starttls_enable = item['secondary_starttls_enable']
            default_secondary_ssltls_enable = item['secondary_ssltls_enable']

            default_ca_info1 = item['ca_info1']
            default_ca_info2 = item['ca_info2']
            default_key_info1 = item['key_info1']
            default_key_info2 = item['key_info2']
            default_cert_info1 = item['cert_info1']
            default_cert_info2 = item['cert_info2']
            break
        if isNone:
            smtpResult.State("Failure")
            smtpResult.Message(["get " + args.interface + " error "])
            return smtpResult
    else:
        smtpResult.State("Failure")
        smtpResult.Message(["get SMTP information error, " + res.get('data')])
        return smtpResult

    id = default_id
    email_id = default_email_id
    channel_interface = default_channel_interface

    primary_smtp_enable = default_primary_smtp_enable
    primary_server_ip = default_primary_server_ip
    primary_server_name = default_primary_server_name
    primary_smtp_port = default_primary_smtp_port
    primary_smtp_secure_port = default_primary_smtp_secure_port
    primary_smtp_authentication = default_primary_smtp_authentication
    primary_username = default_primary_username
    primary_ssltls_enable = default_primary_ssltls_enable
    primary_starttls_enable = default_primary_starttls_enable

    secondary_smtp_enable = default_secondary_smtp_enable
    secondary_server_ip = default_secondary_server_ip
    secondary_server_name = default_secondary_server_name
    secondary_smtp_port = default_secondary_smtp_port
    secondary_smtp_secure_port = default_secondary_smtp_secure_port
    secondary_smtp_authentication = default_secondary_smtp_authentication
    secondary_username = default_secondary_username
    secondary_starttls_enable = default_secondary_starttls_enable
    secondary_ssltls_enable = default_secondary_ssltls_enable

    ca_info1 = default_ca_info1
    ca_info2 = default_ca_info2
    key_info1 = default_key_info1
    key_info2 = default_key_info2
    cert_info1 = default_cert_info1
    cert_info2 = default_cert_info2

    if args.interface is not None:
        channel_interface = args.interface
    if args.email is not None:
        email_id = args.email
        if not RegularCheckUtil.checkEmail(email_id):
            smtpResult.State("Failure")
            smtpResult.Message(['Invalid email.'])
            return smtpResult

    if args.primaryStatus is not None:
        if args.primaryStatus == 'enable':
            primary_smtp_enable = 1
        else:
            primary_smtp_enable = 0
    if args.primaryServerIP is not None:
        primary_server_ip = args.primaryServerIP
        if not RegularCheckUtil.checkIP(primary_server_ip):
            smtpResult.State("Failure")
            smtpResult.Message(['Invalid primary serverIP.'])
            return smtpResult
    if args.primaryServerName is not None:
        primary_server_name = args.primaryServerName
    if args.primaryServerPort is not None:
        if args.primaryServerPort < 1 or args.primaryServerPort > 65535:
            smtpResult.State("Failure")
            smtpResult.Message(['primary server port should be 1-65535.'])
            return smtpResult
        else:
            primary_smtp_port = args.primaryServerPort
    if args.primaryServerAuthentication is not None:
        if args.primaryServerAuthentication == 'enable':
            primary_smtp_authentication = 1
        else:
            primary_smtp_authentication = 0
    if primary_smtp_authentication == 1:
        if args.primaryServerUsername is not None:
            primary_username = args.primaryServerUsername
            if len(primary_username) < 4 or len(primary_username) > 64:
                smtpResult.State("Failure")
                smtpResult.Message(['primary SMTP user name lenth be 4 to 64 bits.'])
                return smtpResult
            if not RegularCheckUtil.checkSMTPName(primary_username):
                smtpResult.State("Failure")
                smtpResult.Message(["primary SMTP user name must start with letters and cannot contain ','(comma) ':'(colon) ' '(space) ';'(semicolon) '\\'(backslash)."])
                return smtpResult
        if args.primaryServerPassword is not None:
            primary_password = args.primaryServerPassword
            if len(primary_password) < 4 or len(primary_password) > 64:
                smtpResult.State("Failure")
                smtpResult.Message(['primary SMTP password lenth be 4 to 64 bits.'])
                return smtpResult
            if not RegularCheckUtil.checkSMTPPassword(primary_password):
                print ("Failure: primary SMTP  password cannot contain ' '(space)")
                smtpResult.State("Failure")
                smtpResult.Message(["primary SMTP  password cannot contain ' '(space)."])
                return smtpResult
        else:
            if primary_smtp_enable == 1:
                smtpResult.State("Failure")
                smtpResult.Message(['primary SMTP server password is needed.'])
                return smtpResult
    if primary_smtp_enable == 1:
        if primary_server_ip is None or primary_server_ip == '':
            smtpResult.State("Failure")
            smtpResult.Message(['primary SMTP server ip is needed.'])
            return smtpResult
        if primary_server_name is None or primary_server_name == '':
            smtpResult.State("Failure")
            smtpResult.Message(['primary SMTP server name is needed.'])
            return smtpResult
        if primary_smtp_port is None or primary_smtp_port == '':
            smtpResult.State("Failure")
            smtpResult.Message(['primary SMTP server port is needed.'])
            return smtpResult
        if primary_smtp_authentication is None or primary_smtp_authentication == '':
            smtpResult.State("Failure")
            smtpResult.Message(['primary SMTP server authentication is needed.'])
            return smtpResult
        elif primary_smtp_authentication == 1:
            if primary_username is None or primary_username == '':
                smtpResult.State("Failure")
                smtpResult.Message(['primary SMTP server username is needed.'])
                return smtpResult
            if primary_password is None or primary_password == '':
                smtpResult.State("Failure")
                smtpResult.Message(['primary SMTP server password is needed.'])
                return smtpResult
        if email_id is None or email_id == '':
            smtpResult.State("Failure")
            smtpResult.Message(['sender email is needed.'])
            return smtpResult
    if primary_smtp_enable == 0:
        if args.primaryServerIP is not None or args.primaryServerName is not None or args.primaryServerPort is not None or args.primaryServerAuthentication is not None or args.primaryServerUsername is not None or args.primaryServerPassword is not None:
            smtpResult.State("Failure")
            smtpResult.Message(['primaryServerIP and primaryServerName and primaryServerPort and primaryServerAuthentication and primaryServerUsername and primaryServerPassword can not be setted in primaryStatus disable.'])
            return smtpResult
    elif primary_smtp_authentication == 0:
        if args.primaryServerUsername is not None or args.primaryServerPassword is not None:
            smtpResult.State("Failure")
            smtpResult.Message(['primaryServerUsername and primaryServerPassword can not be setted in primaryServerAuthentication disable.'])
            return smtpResult

    if args.secondaryStatus is not None:
        if args.secondaryStatus == 'enable':
            secondary_smtp_enable = 1
        else:
            secondary_smtp_enable = 0
    if args.secondaryServerIP is not None:
        secondary_server_ip = args.secondaryServerIP
        if not RegularCheckUtil.checkIP(secondary_server_ip):
            smtpResult.State("Failure")
            smtpResult.Message(['Invalid secondary serverIP.'])
            return smtpResult
    if args.secondaryServerName is not None:
        secondary_server_name = args.secondaryServerName
    if args.secondaryServerPort is not None:
        if args.secondaryServerPort < 1 or args.secondaryServerPort > 65535:
            smtpResult.State("Failure")
            smtpResult.Message(['secondary server port should be 1-65535.'])
            return smtpResult
        else:
            secondary_smtp_port = args.secondaryServerPort
    if args.secondaryServerAuthentication is not None:
        if args.secondaryServerAuthentication == 'enable':
            secondary_smtp_authentication = 1
        else:
            secondary_smtp_authentication = 0
    if secondary_smtp_authentication == 1:
        if args.secondaryServerUsername is not None:
            secondary_username = args.secondaryServerUsername
            if len(secondary_username) < 4 or len(secondary_username) > 64:
                smtpResult.State("Failure")
                smtpResult.Message(['secondary SMTP user name lenth be 4 to 64 bits.'])
                return smtpResult
            if not RegularCheckUtil.checkSMTPName(secondary_username):
                smtpResult.State("Failure")
                smtpResult.Message(["secondary SMTP user name must start with letters and cannot contain ','(comma) ':'(colon) ' '(space) ';'(semicolon) '\\'(backslash)."])
                return smtpResult
        if args.secondaryServerPassword is not None:
            secondary_password = args.secondaryServerPassword
            if len(secondary_password) < 4 or len(secondary_password) > 64:
                smtpResult.State("Failure")
                smtpResult.Message(['secondary SMTP password lenth be 4 to 64 bits.'])
                return smtpResult
            if not RegularCheckUtil.checkSMTPPassword(secondary_password):
                smtpResult.State("Failure")
                smtpResult.Message(["secondary SMTP  password cannot contain ' '(space)."])
                return smtpResult
        else:
            if secondary_smtp_enable == 1:
                smtpResult.State("Failure")
                smtpResult.Message(['secondary SMTP server password is needed.'])
                return smtpResult
    if secondary_smtp_enable == 1:
        if secondary_server_ip is None or secondary_server_ip == '':
            smtpResult.State("Failure")
            smtpResult.Message(['secondary SMTP server ip is needed.'])
            return smtpResult
        if secondary_server_name is None or secondary_server_name == '':
            smtpResult.State("Failure")
            smtpResult.Message(['secondary SMTP server name is needed.'])
            return smtpResult
        if secondary_smtp_port is None or secondary_smtp_port == '':
            smtpResult.State("Failure")
            smtpResult.Message(['secondary SMTP server port is needed.'])
            return smtpResult
        if secondary_smtp_authentication is None or secondary_smtp_authentication == '':
            smtpResult.State("Failure")
            smtpResult.Message(['secondary SMTP server authentication is needed.'])
            return smtpResult
        elif secondary_smtp_authentication == 1:
            if secondary_username is None or secondary_username == '':
                smtpResult.State("Failure")
                smtpResult.Message(['secondary SMTP server username is needed.'])
                return smtpResult
            if secondary_password is None or secondary_password == '':
                smtpResult.State("Failure")
                smtpResult.Message(['secondary SMTP server password is needed.'])
                return smtpResult
        if email_id is None or email_id == '':
            smtpResult.State("Failure")
            smtpResult.Message(['sender email is needed.'])
            return smtpResult
    if secondary_smtp_enable == 0:
        if args.secondaryServerIP is not None or args.secondaryServerName is not None or args.secondaryServerPort is not None or args.secondaryServerAuthentication is not None or args.secondaryServerUsername is not None or args.secondaryServerPassword is not None:
            smtpResult.State("Failure")
            smtpResult.Message(['secondaryServerIP and secondaryServerName and secondaryServerPort and secondaryServerAuthentication and secondaryServerUsername and secondaryServerPassword can not be setted in secondaryStatus disable.'])
            return smtpResult
    elif secondary_smtp_authentication == 0:
        if args.secondaryServerUsername is not None or args.secondaryServerPassword is not None:
            smtpResult.State("Failure")
            smtpResult.Message(['secondaryServerUsername and secondaryServerPassword can not be setted in secondaryServerAuthentication disable.'])
            return smtpResult
    if primary_smtp_enable == 0 and secondary_smtp_enable == 0:
        if args.email is not None:
            smtpResult.State("Failure")
            smtpResult.Message(['email can not be setted in primaryStatus and secondaryStatus disable.'])
            return smtpResult
    data = {
        'channel_interface': channel_interface,
        'email_id': email_id,
        'id': id,
        'primary_server_ip': primary_server_ip,
        'primary_server_name': primary_server_name,
        'primary_smtp_authentication': primary_smtp_authentication,
        'primary_smtp_enable': primary_smtp_enable,
        'primary_smtp_port': primary_smtp_port,
        'primary_smtp_secure_port': primary_smtp_secure_port,
        'primary_ssltls_enable': primary_ssltls_enable,
        'primary_starttls_enable': primary_starttls_enable,
        'primary_username': primary_username,
        'secondary_server_ip': secondary_server_ip,
        'secondary_server_name': secondary_server_name,
        'secondary_smtp_authentication': secondary_smtp_authentication,
        'secondary_smtp_enable': secondary_smtp_enable,
        'secondary_smtp_port': secondary_smtp_port,
        'secondary_smtp_secure_port': secondary_smtp_secure_port,
        'secondary_ssltls_enable': secondary_ssltls_enable,
        'secondary_starttls_enable': secondary_starttls_enable,
        'secondary_username': secondary_username
    }
    if primary_smtp_authentication == 1 and primary_smtp_enable == 1:
        data.update(primary_password=primary_password)
    if secondary_smtp_authentication == 1 and secondary_smtp_enable == 1:
        data.update(secondary_password=secondary_password)
    res = RestFunc.setSMTPM5ByRest(client, id, data)
    if res.get('code') == 0 and res.get('data') is not None:
        smtpResult.State("Success")
        smtpResult.Message(['set SMTP Settings success.'])
    else:
        smtpResult.State("Failure")
        smtpResult.Message(['set SMTP Settings failure.'])
    return smtpResult


def setservice(client, args):
    global usage
    global InterFace
    global serve_list
    result = ResultBean()
    serve_list = {
        'web': 1,
        'kvm': 2,
        'cd-media': 3,
        'fd-media': 4,
        'hd-media': 5,
        'ssh': 6,
        'telnet': 7,
        'solssh': 8,
        'snmp': 9
    }
    dictraw = IpmiFunc.getM5WebByIpmi(client)
    webInfo = {}
    if "code" in dictraw and dictraw["code"] == 0:
        if "data" in dictraw:
            webInfo = dictraw["data"]
            webState = dictraw["data"].get('Status', 'Disabled')
            webFlag = False
            if webState == 'Disabled':
                webFlag = True
        else:
            result.State('Failure')
            result.Message('cannot get web status')
            return result
    else:
        result.State('Failure')
        result.Message('cannot get web status')
        return result

    if webFlag is False:
        # set时的 header
        header = client.getHearder()
        header["X-Requested-With"] = "XMLHttpRequest"
        header["Content-Type"] = "application/json;charset=UTF-8"
        header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
        # 先获取get对应name的所有信息，为了后续将上次的值赋给当前不支持设置的值
        serve_info = defaultServiceInfo(client, args)
        if serve_info is None:
            result.State('Failure')
            result.Message('Can not get service information.')
            return result
            # 判断是否可以设置-I为bond0
        InterFace = verInterface(client)
        # print(InterFace)
        if InterFace is None:
            result.State('Failure')
            result.Message('Failed to get service info.')
            return result
        if args.interface is not None and args.interface not in InterFace:
            result.State('Failure')
            result.Message(' Current interface(-I) choose from {0}.'.format(InterFace))
            return result
    else:
        InterFace = ['both', 'eth0', 'eth1']
        if args.interface is not None:
            result.State('Failure')
            result.Message('Please set web to active first,then set the interface(-I) a few seconds later.')
            return result
    # set时的输入 data
    data = {
        'service_name': args.servicename,
        'state': args.state,
        'interface_name': args.interface,
        'secure_port': args.secureport,
        'non_secure_port': args.nonsecureport,
        'time_out': args.timeout
    }
    if args.state == 'active':
        data['state'] = 1
    elif args.state == 'inactive':
        data['state'] = 0
    elif args.state is None:
        data['state'] = serve_info['state']

    # 根据输入的name，判断输入参数的个数、禁止设置的值并将其置为get的数值
    if args.servicename is not None and (args.state is None and args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
        result.State('Failure')
        result.Message('Please input a setting item.')
        return result
    if args.servicename == 'ssh':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State('Failure')
                result.Message('State(-S) is set to inactive while setting other items is not supported.')
                return result
            else:
                data = setSSH(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)   # 按照data进行服务设置
        # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setSSH(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State('Failure')
                result.Message('State(-S) is set to inactive while setting other items is not supported.')
                return result
            else:
                result.State('Failure')
                result.Message('Current state(-S) is inactive,please set it to be active before setting other items.')
                return result

    elif args.servicename == 'web':
        # 现在web处于inactive状态，需要设置为active状态。
        if webFlag is True:
            data = setWEB_flag(args, data)  # 验证当前设置参数的正确性
            if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                return data
            else:
                status_dict = {'Disabled': '00', 'Enabled': '01', 'inactive': '00', 'active': '01'}
                if args.enabled is None:
                    if webInfo['Status'] == 'Disabled':
                        result.State("Failure")
                        result.Message(["please set status to Enabled firstly."])
                        return result
                    enabled = hex(int(status_dict[webInfo['Status']]))
                else:
                    enabled = hex(int(status_dict[args.enabled]))

                if args.nonsecureport is None:
                    if webInfo['NonsecurePort'] == 'N/A':
                        nsp_hex = "0xff " * 4
                    else:
                        nsp = '{:08x}'.format(webInfo['NonsecurePort'])
                        nsp_hex = hexReverse(nsp)
                else:
                    nsp = '{:08x}'.format(args.nonsecureport)
                    nsp_hex = hexReverse(nsp)
                if args.secureport is None:
                    if webInfo['SecurePort'] == 'N/A':
                        sp_hex = "0xff " * 4
                    else:
                        sp = '{:08x}'.format(webInfo['SecurePort'])
                        sp_hex = hexReverse(sp)
                else:
                    sp = '{:08x}'.format(args.secureport)
                    sp_hex = hexReverse(sp)
                if args.interface is None:
                    if webInfo['InterfaceName'] == 'N/A':
                        interface_temp = "F" * 16
                        interface = ascii2hex(interface_temp, 17)
                    else:
                        interface = ascii2hex(webInfo['InterfaceName'], 17)
                else:
                    interface = ascii2hex(args.interface, 17)

                if args.timeout is None:
                    if webInfo['Timeout'] == 'N/A':
                        t_hex = "0xff " * 4
                    else:
                        t = '{:08x}'.format(webInfo['Timeout'])
                        t_hex = hexReverse(t)
                else:
                    t = '{:08x}'.format(args.timeout)
                    t_hex = hexReverse(t)

                dictrawset = IpmiFunc.setM5WebByIpmi(client, enabled, interface, nsp_hex, sp_hex, t_hex)
                if "code" in dictrawset and dictrawset["code"] == 0:
                    result.State("Success")
                    result.Message(["Set web success,please wait a few seconds."])
                    return result
                else:
                    result.State("Failure")
                    result.Message(["Failed to set web."])
                    return result
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setWEB(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)   # 按照data进行服务设置
    elif args.servicename == 'kvm':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setKVM(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setKVM(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'cd-media':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'fd-media':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = True
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'hd-media':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setMedia(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'telnet':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setTEL(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setTEL(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'solssh':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setTEL(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setTEL(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    elif args.servicename == 'snmp':
        # 状态“有效”则可以设置内容
        if serve_info['state'] == 1:
            if args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                data = setSNMP(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            # 状态“无效”，除非设置-S，其他都不可设置。
        elif serve_info['state'] == 0:
            if args.state is not None and args.state == 'active':
                data = setSNMP(args, serve_info, data)  # 验证当前设置参数的正确性
                if data.State == 'Failure':  # 输入了不支持的设置项,提示信息已展示
                    return data
                else:
                    num = str(serve_list[args.servicename])
                    result_set = setItem(args.servicename, client, data.Message[0], header, num)  # 按照data进行服务设置
            elif args.state is not None and args.state == 'inactive' and (args.secureport is None and args.timeout is None and args.nonsecureport is None and args.interface is None):
                result_set = ResultBean().State("Success")
            elif args.state is not None and args.state == 'inactive' and (args.secureport is not None or args.timeout is not None or args.nonsecureport is not None or args.interface is not None):
                result.State("Failure")
                result.Message(["State(-S) is set to inactive while setting other items is not supported."])
                return result
            else:
                result.State("Failure")
                result.Message(["Current state(-S) is inactive,please set it to be active before setting other items."])
                return result
    else:
        result.State("Failure")
        result.Message(["Service Name choose from: 'web', 'kvm', 'cd-media', 'fd-media', 'hd-media', 'ssh', 'telnet', 'solssh'."])
        return result

    if result_set.State == 'Success':
        item_Info = defaultServiceInfo(client, args)
        Enabled = {1: 'Enabled', 0: 'Disabled'}
        service_item = ServiceSingleBean()
        service_item.Id(item_Info.get('id', 0))
        sname = item_Info.get('service_name', '')
        service_item.Name(sname)
        service_item.Enable(Enabled.get(item_Info.get('state'), item_Info.get('state')))
        service_item.Port(None if item_Info.get('secure_port') == -1 else item_Info.get('secure_port'))
        service_item.Port2(None if item_Info.get('non_secure_port') == -1 else item_Info.get('non_secure_port'))
        service_item.InterfaceName(item_Info.get('interface_name', None))
        service_item.TimeOut(item_Info.get('time_out', 0))
        if item_Info.get('maximum_sessions', 128) == 255:
            service_item.MaximumSessions(None)
        else:
            service_item.MaximumSessions(item_Info.get('maximum_sessions', 128) - 128)
        service_item.ActiveSessions(item_Info.get('active_session', 128) - 128)
        result = ResultBean()
        result.State('Success')
        result.Message(['Set {0} success, current {1} information:'.format(args.servicename, args.servicename), service_item])
        return result


def defaultServiceInfo(client, args):
    responds = RestFunc.getServiceInfoByRest(client)
    if responds == {}:
        return None
    elif responds.get('code') == 0 and responds.get('data') is not None:
        result = responds.get('data')
        for item in result:
            if item['service_name'] == args.servicename:
                return item
    else:
        return None


def setSSH(args, serve_info, data):
    result = ResultBean()
    # 支持设置安全端口号与超时时间，如果有值，则直接赋值，如果没输入，则用get的值
    # 可设置的项 其get值不会有N/A
    # 如果其他值被设置了，需要提示不能设置，并展示可以设置的值
    if args.interface is not None and args.nonsecureport is not None:
        result.State('Failure')
        result.Message(['Info: The interface(-I) and nonsecureport(-NSP) are not support to set.', 'Available item is -SP -T.'])
        return result
    elif args.interface is not None and args.nonsecureport is None:
        result.State('Failure')
        result.Message(['Info: The interface(-I) is not support to set.', 'Available item is -SP -T.'])
        return result
    elif args.interface is None and args.nonsecureport is not None:
        result.State('Failure')
        result.Message(['Info: The nonsecureport(-NSP) is not support to set.', 'Available item is -SP -T.'])
        return result

    if args.secureport is not None:
        if args.secureport < 1 or args.secureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['secure_port'] = args.secureport
    else:
        data['secure_port'] = serve_info['secure_port']
    if args.timeout is not None and args.timeout % 60 == 0 and args.timeout >= 60 and args.timeout <= 1800:
        data['time_out'] = args.timeout
    elif args.timeout is None:
        data['time_out'] = serve_info['time_out']
    else:
        result.State('Failure')
        result.Message(['This time is invalid,please enter a multiple of 60 and range from 60 to 1800.'])
        return result

    # 其他直接用get的值
    data['interface_name'] = serve_info['interface_name']
    if serve_info['non_secure_port'] == -1:
        data['non_secure_port'] = 'N/A'
    data['non_secure_port'] = serve_info['non_secure_port']
    result.State('Success')
    result.Message([data])
    return result


def setWEB(args, serve_info, data):
    result = ResultBean()
    # InterFace = ['eth0', 'eth1', 'both']
    # 全部支持，如果有值，则直接赋值，如果没输入，则用get的值
    if args.secureport is not None:
        if args.secureport < 1 or args.secureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['secure_port'] = args.secureport
    else:
        data['secure_port'] = serve_info['secure_port']
    if args.timeout is not None and args.timeout % 60 == 0 and args.timeout >= 300 and args.timeout <= 1800:
        data['time_out'] = args.timeout
    elif args.timeout is None:
        data['time_out'] = serve_info['time_out']
    else:
        result.State('Failure')
        result.Message(['This time is invalid,please enter a multiple of 60 and range from 300 to 1800.'])
        return result

    if args.interface is not None:
        if args.interface in InterFace:
            data['interface_name'] = args.interface
        else:
            result.State('Failure')
            result.Message(['Current interface(-I) choose from {0}.'.format(InterFace)])
            return result
    else:
        data['interface_name'] = serve_info['interface_name']

    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            print("Failure: Invalid Port Number,please enter in the range of 1-65535.")
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['non_secure_port'] = args.nonsecureport
    else:
        data['non_secure_port'] = serve_info['non_secure_port']
    result.State('Success')
    result.Message([data])
    return result


def setWEB_flag(args, data):
    result = ResultBean()
    # InterFace = ['eth0', 'eth1', 'both']
    # 全部支持，如果有值，则直接赋值，如果没输入，则用get的值
    if args.secureport is not None:
        if args.secureport < 1 or args.secureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result

    if args.timeout is not None and args.timeout % 60 == 0 and args.timeout >= 300 and args.timeout <= 1800:
        data['time_out'] = args.timeout
    elif args.timeout is None:
        pass
    else:
        result.State('Failure')
        result.Message(['This time is invalid,please enter a multiple of 60 and range from 300 to 1800.'])
        return result
    if args.interface is not None:
        if args.interface not in InterFace:
            result.State('Failure')
            result.Message(['Current interface(-I) choose from {0}.'.format(InterFace)])
            return result
    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
    result.State('Success')
    result.Message([data])
    return result


def setKVM(args, serve_info, data):
    result = ResultBean()
    # InterFace = ['eth0', 'eth1', 'both']
    # 全部支持，如果有值，则直接赋值，如果没输入，则用get的值
    if args.secureport is not None:
        if args.secureport < 1 or args.secureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['secure_port'] = args.secureport
    else:
        data['secure_port'] = serve_info['secure_port']
    if args.timeout is not None and args.timeout % 60 == 0 and args.timeout >= 300 and args.timeout <= 1800:
        data['time_out'] = args.timeout
    elif args.timeout is None:
        data['time_out'] = serve_info['time_out']
    else:
        result.State('Failure')
        result.Message(['This time is invalid,please enter a multiple of 60 and range from 300 to 1800.'])
        return result

    if args.interface is not None:
        if args.interface in InterFace:
            data['interface_name'] = args.interface
        else:
            print("Failure: Current interface(-I) choose from {0}.".format(InterFace))
            result.State('Failure')
            result.Message(['Current interface(-I) choose from {0}.'.format(InterFace)])
            return result
    else:
        data['interface_name'] = serve_info['interface_name']

    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['non_secure_port'] = args.nonsecureport
    else:
        data['non_secure_port'] = serve_info['non_secure_port']
    result.State('Success')
    result.Message([data])
    return result


def setMedia(args, serve_info, data):
    result = ResultBean()
    # InterFace = ['eth0', 'eth1', 'both']
    # 如果其他值被设置了，需要提示不能设置，并展示可以设置的值
    if args.timeout is not None:
        print('Info: The timeout(-T) is not support to set.')
        print("Available item: -SP -NSP -I")
        result.State('Failure')
        result.Message(['Info: The timeout(-T) is not support to set.', 'Available item: -SP -NSP -I'])
        return result
    if args.secureport is not None:
        if args.secureport < 1 or args.secureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['secure_port'] = args.secureport
    else:
        data['secure_port'] = serve_info['secure_port']

    if args.interface is not None:
        if args.interface in InterFace:
            data['interface_name'] = args.interface
        else:
            result.State('Failure')
            result.Message(['Current interface(-I) choose from {0}.'.format(InterFace)])
            return result
    else:
        data['interface_name'] = serve_info['interface_name']

    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['non_secure_port'] = args.nonsecureport
    else:
        data['non_secure_port'] = serve_info['non_secure_port']

    # timeout 需要使用get
    if serve_info['time_out'] == -1:
        data['time_out'] = 'N/A'
    else:
        data['time_out'] = serve_info['time_out']
    result.State('Success')
    result.Message([data])
    return result


def setTEL(args, serve_info, data):
    result = ResultBean()
    # 如果其他值被设置了，需要提示不能设置，并展示可以设置的值
    if args.secureport is not None and args.interface is not None:
        result.State('Failure')
        result.Message(['Info: The secureport(-SP) and interface(-I) are not support to set.', 'Available item: -NSP -T'])
        return result
    elif args.secureport is not None and args.interface is None:
        result.State('Failure')
        result.Message(['Info: The secureport(-SP) is not support to set.', 'Available item: -NSP -T'])
        return result
    elif args.secureport is None and args.interface is not None:
        result.State('Failure')
        result.Message(['Info: The interface(-I) is not support to set.', 'Available item: -NSP -T'])
        return result
    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['non_secure_port'] = args.nonsecureport
    else:
        data['non_secure_port'] = serve_info['non_secure_port']

    if args.timeout is not None and args.timeout % 60 == 0 and args.timeout >= 60 and args.timeout <= 1800:
        data['time_out'] = args.timeout
    elif args.timeout is None:
        data['time_out'] = serve_info['time_out']
    else:
        result.State('Failure')
        result.Message(['This time is invalid,please enter a multiple of 60 and range from 60 to 1800.'])
        return result

    if serve_info['secure_port'] == -1:
        data['secure_port'] = 'N/A'
    else:
        data['secure_port'] = serve_info['secure_port']

    data['interface_name'] = serve_info['interface_name']
    result.State('Success')
    result.Message([data])
    return result


def setSNMP(args, serve_info, data):
    result = ResultBean()
    # 如果其他值被设置了，需要提示不能设置，并展示可以设置的值
    if args.secureport is not None and args.interface is not None and args.timeout is not None:
        result.State('Failure')
        result.Message(['The secureport(-SP) and interface(-I) and timeout(-T) are not support to set.', 'Available item: -NSP'])
        return result
    elif args.secureport is not None and args.interface is None and args.timeout is None:
        result.State('Failure')
        result.Message(['Info: The secureport(-SP) is not support to set.', 'Available item: -NSP'])
        return result
    elif args.secureport is None and args.interface is not None and args.timeout is None:
        result.State('Failure')
        result.Message(['Info: The interface(-I) is not support to set.', 'Available item: -NSP'])
        return result
    elif args.secureport is None and args.interface is None and args.timeout is not None:
        result.State('Failure')
        result.Message(['Info: The timeout(-T) is not support to set.', 'Available item: -NSP'])
        return result
    if args.nonsecureport is not None:
        if args.nonsecureport < 1 or args.nonsecureport > 65535:
            result.State('Failure')
            result.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return result
        else:
            data['non_secure_port'] = args.nonsecureport
    else:
        data['non_secure_port'] = serve_info['non_secure_port']

    if serve_info['secure_port'] == -1:
        data['secure_port'] = 'N/A'
    else:
        data['secure_port'] = serve_info['secure_port']

    data['interface_name'] = serve_info['interface_name']
    data['time_out'] = serve_info['time_out']
    result.State('Success')
    result.Message([data])
    return result


def setItem(name, client, data, header, num):
    result = ResultBean()
    # 服务设置
    info = RestFunc.setServiceByRest(client, data, num)
    if info == {}:
        result.State('Failure')
        result.Message(['Set {0} service failed'.format(serve_list[num])])
        return result
    elif info.get('code') == 0 and info.get('data') is not None:
        data = info.get('data')
        result.State('Success')
        result.Message([data])
        return result
    else:
        result.State('Failure')
        result.Message(['Set {0} service failed'.format(serve_list[num])])
        return result


def verInterface(client):
    # 验证是都需要设置成bond0
    info = RestFunc.getInterfaceByRest(client)
    if info == {}:
        return None
    elif info.get('code') == 0 and info.get('data') is not None:
        data = info.get('data')
        if len(data) == 1:
            respond = data[0]
            if 'interface_name' in respond:
                return respond['interface_name']
            else:
                return None
        elif len(data) >= 2:
            interface_temp = ['both']
            for i in range(len(data)):
                respond = data[i]
                if 'interface_name' in respond:
                    tep = str(respond['interface_name'])
                    interface_temp.append(tep)
                else:
                    return None
            return interface_temp
    else:
        return None


def getBiosAll(client, infoList):
    biosaAttribute = {}
    for list in infoList:
        cmd = list['getter']
        if cmd == 'None':
            continue
        bios_Info = IpmiFunc.getM5BiosByipmi(client, cmd, list)
        if bios_Info and bios_Info.get('code') == 0:
            key = bios_Info.get('data').get('key')
            value = bios_Info.get('data').get('value')
        else:
            key = list['description']
            value = None
        biosaAttribute[key] = value
        # else:
        #     continue
    return biosaAttribute


def getCtrlInfo_PMC(client):
    raid_return = ResultBean()
    raid_bean = RaidCardBean()
    ctrInfo_all = RestFunc.getPMCCtrlInfoByRest(client)
    if ctrInfo_all is None or ctrInfo_all.get('code') != 0 or ctrInfo_all.get('data') is None:  # 主要信息，id信息
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    ctrInfo = ctrInfo_all.get('data')
    sizectrlinfo = len(ctrInfo)
    health_flag = 0
    ctrl_list = []
    if sizectrlinfo == 0:
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    for i in range(sizectrlinfo):
        raid_Info = Raid()
        control_Info = Controller()
        ctrInfo_temp = ctrInfo[i]

        raid_Info.CommonName('RAID Card')
        raid_Info.Location('mainboard')
        # control_Info.Id(ctrInfo_temp.get('index', i))
        control_Info.Id(i)
        if 'vendorId' in ctrInfo_temp:
            control_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
            raid_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
        else:
            control_Info.Manufacturer(None)
            raid_Info.Manufacturer(None)
        if 'devId' in ctrInfo_temp:
            control_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
            raid_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
        else:
            control_Info.Model(None)
            raid_Info.Model(None)
        control_Info.SupportedDeviceProtocols([])
        control_Info.SASAddress(None)
        control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
        control_Info.MaintainPDFailHistory(None)
        control_Info.CopyBackState(None)
        control_Info.JBODState(None)
        # control_Info.ConfigurationVersion(str(ctrInfo_temp.get('index',None)))
        # control_Info.ConfigurationVersion(0)
        control_Info.MinStripeSizeBytes(
            int(ctrInfo_temp.get('strpMinSz')) * 1024 if 'strpMinSz' in ctrInfo_temp else None)
        control_Info.MaxStripeSizeBytes(
            int(ctrInfo_temp.get('strpMaxSz')) * 1024 if 'strpMaxSz' in ctrInfo_temp else None)
        control_Info.MemorySizeMiB(int(ctrInfo_temp.get('memSz')) if 'memSz' in ctrInfo_temp else None)
        if '3008IT' in ctrInfo_temp.get('PN', 'None'):
            control_Info.SupportedRAIDLevels([])
        else:
            control_Info.SupportedRAIDLevels(['RAID0,RAID1,RAID5,RAID6,RAID10'])
        control_Info.DDRECCCount(None)

        raid_Info.SerialNumber(ctrInfo_temp.get('SN', None))
        raid_Info.State('Enabled')
        if ctrInfo_temp.get('Health') is None:
            health_flag = 1
        # raid_Info.Health(ctrInfo_temp.get('Health', None))
        raid_Info.Health(None)
        raid_Info.Controller([control_Info.dict])
        ctrl_list.append(raid_Info.dict)
    if health_flag == 1:
        raid_bean.OverallHealth(None)
    else:
        raid_bean.OverallHealth('OK')
    raid_bean.Maximum(sizectrlinfo)
    raid_bean.RaidCard(ctrl_list)
    raid_return.State('Success')
    raid_return.Message([raid_bean.dict])
    return raid_return


def getCtrlInfo_LSI(client):
    raid_return = ResultBean()
    raid_bean = RaidCardBean()
    ctrInfo_all = RestFunc.getLSICtrlInfoByRest(client)
    if ctrInfo_all is None or ctrInfo_all.get('code') != 0 or ctrInfo_all.get('data') is None:  # 主要信息，id信息
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    ctrInfo = ctrInfo_all.get('data')
    ctrInfo_mfc = RestFunc.getLSICtrlMfcByRest(client)
    if ctrInfo_mfc is None or ctrInfo_mfc.get('code') != 0 and ctrInfo_mfc.get('data') is None:
        ctrmfc = ''
    else:
        ctrmfc = ctrInfo_mfc.get('data')
    ctrInfo_prop = RestFunc.getLSICtrlPropByRest(client)
    if ctrInfo_prop is None or ctrInfo_prop.get('code') != 0 and ctrInfo_prop.get('data') is None:
        ctrprop = ''
    else:
        ctrprop = ctrInfo_prop.get('data')
    sizectrlinfo = len(ctrInfo)
    if sizectrlinfo == 0:
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    health_flag = 0
    ctrl_list = []
    for i in range(sizectrlinfo):
        raid_Info = Raid()
        control_Info = Controller()
        ctrInfo_temp = ctrInfo[i]

        raid_Info.CommonName('RAID Card')
        raid_Info.Location('mainboard')
        # control_Info.Id(ctrInfo_temp.get('index', i))
        control_Info.Id(i)
        if 'vendorId' in ctrInfo_temp:
            control_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
            raid_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
        else:
            control_Info.Manufacturer(None)
            raid_Info.Manufacturer(None)
        if 'devId' in ctrInfo_temp:
            control_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
            raid_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
        else:
            control_Info.Model(None)
            raid_Info.Model(None)
        control_Info.SupportedDeviceProtocols([])
        if ctrmfc:
            control_Info.SASAddress(ctrmfc[i].get('sasAddr', None))
            control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
            control_Info.MaintainPDFailHistory(
                CTRLMFC_maintainPdFailHistory.get(ctrmfc[i].get('maintainPdFailHistory', None), None))
            control_Info.CopyBackState(None)
            control_Info.JBODState(None)
        else:
            control_Info.SASAddress(None)
            control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
            control_Info.MaintainPDFailHistory(None)
            control_Info.CopyBackState(None)
            control_Info.JBODState(None)
        control_Info.MinStripeSizeBytes(
            int(ctrInfo_temp.get('strpMinSz')) * 1024 if 'strpMinSz' in ctrInfo_temp else None)
        control_Info.MaxStripeSizeBytes(
            int(ctrInfo_temp.get('strpMaxSz')) * 1024 if 'strpMaxSz' in ctrInfo_temp else None)
        control_Info.MemorySizeMiB(int(ctrInfo_temp.get('memSz') if 'memSz' in ctrInfo_temp else None))
        if '3008IT' in ctrInfo_temp.get('PN', 'None'):
            control_Info.SupportedRAIDLevels([])
        else:
            control_Info.SupportedRAIDLevels(['RAID0,RAID1,RAID5,RAID6,RAID10'])
        control_Info.DDRECCCount(None)
        raid_Info.SerialNumber(ctrInfo_temp.get('SN', None))
        raid_Info.State('Enabled')
        if ctrInfo_temp.get('status') is None:
            health_flag = 1
        raid_Info.Health(ctrInfo_temp.get('status', None))
        raid_Info.Controller([control_Info.dict])
        ctrl_list.append(raid_Info.dict)
    if health_flag == 1:
        raid_bean.OverallHealth(None)
    else:
        raid_bean.OverallHealth('OK')
    raid_bean.Maximum(sizectrlinfo)
    raid_bean.RaidCard(ctrl_list)
    raid_return.State('Success')
    raid_return.Message([raid_bean.dict])
    return raid_return


def getCtrlInfo(client):
    raid_return = ResultBean()
    raid_bean = RaidCardBean()
    ctrInfo_all = RestFunc.getLSICtrlInfoByRest(client)
    if ctrInfo_all is None or ctrInfo_all.get('code') != 0 or ctrInfo_all.get('data') is None:  # 主要信息，id信息
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    ctrInfo = ctrInfo_all.get('data')
    ctrInfo_mfc = RestFunc.getLSICtrlMfcByRest(client)
    if ctrInfo_mfc is None or ctrInfo_mfc.get('code') != 0 and ctrInfo_mfc.get('data') is None:
        ctrmfc = ''
    else:
        ctrmfc = ctrInfo_mfc.get('data')
    ctrInfo_prop = RestFunc.getLSICtrlPropByRest(client)
    if ctrInfo_prop is None or ctrInfo_prop.get('code') != 0 and ctrInfo_prop.get('data') is None:
        ctrprop = ''
    else:
        ctrprop = ctrInfo_prop.get('data')
    ctrInfo_pmcall = RestFunc.getPMCCtrlInfoByRest(client)
    if ctrInfo_pmcall is None or ctrInfo_pmcall.get('code') != 0 and ctrInfo_pmcall.get('data') is None:
        ctrInfo_pmc = ''
    else:
        ctrInfo_pmc = ctrInfo_pmcall.get('data')
    sizectrllsiinfo = len(ctrInfo)
    sizectrlpmcinfo = len(ctrInfo_pmc)
    num = sizectrllsiinfo + sizectrlpmcinfo

    if num == 0:
        raid_return.State('Failure')
        raid_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return raid_return
    health_lsiflag = 0
    health_pmcflag = 0
    ctrl_list = []
    if sizectrllsiinfo > 0:
        for i in range(sizectrllsiinfo):
            raid_Info = Raid()
            control_Info = Controller()
            ctrInfo_temp = ctrInfo[i]
            raid_Info.CommonName('RAID Card')
            raid_Info.Location('mainboard')

            control_Info.Id(i)
            if 'vendorId' in ctrInfo_temp:
                control_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
                raid_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
            else:
                control_Info.Manufacturer(None)
                raid_Info.Manufacturer(None)
            if 'devId' in ctrInfo_temp:
                control_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
                raid_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
            else:
                control_Info.Model(None)
                raid_Info.Model(None)
            control_Info.SupportedDeviceProtocols([])
            if ctrmfc:
                control_Info.SASAddress(ctrmfc[i].get('sasAddr', None))
                control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
                control_Info.MaintainPDFailHistory(
                    CTRLMFC_maintainPdFailHistory.get(ctrmfc[i].get('maintainPdFailHistory', None), None))
                control_Info.CopyBackState(None)
                control_Info.JBODState(None)
            else:
                control_Info.SASAddress(None)
                control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
                control_Info.MaintainPDFailHistory(None)
                control_Info.CopyBackState(None)
                control_Info.JBODState(None)
            control_Info.MinStripeSizeBytes(
                int(ctrInfo_temp.get('strpMinSz')) * 1024 if 'strpMinSz' in ctrInfo_temp else None)
            control_Info.MaxStripeSizeBytes(
                int(ctrInfo_temp.get('strpMaxSz')) * 1024 if 'strpMaxSz' in ctrInfo_temp else None)
            control_Info.MemorySizeMiB(int(ctrInfo_temp.get('memSz')) if 'memSz' in ctrInfo_temp else None)
            if '3008IT' in ctrInfo_temp.get('PN', 'None'):
                control_Info.SupportedRAIDLevels([])
            else:
                control_Info.SupportedRAIDLevels(['RAID0,RAID1,RAID5,RAID6,RAID10'])
            control_Info.DDRECCCount(None)

            raid_Info.SerialNumber(None if ctrInfo_temp.get('SN', None) == '' else ctrInfo_temp.get('SN', None))
            raid_Info.State('Enabled')
            if ctrInfo_temp.get('status') is None:
                health_lsiflag = 1
            raid_Info.Health(ctrInfo_temp.get('status', None))
            raid_Info.Controller([control_Info.dict])
            ctrl_list.append(raid_Info.dict)
    if ctrInfo_pmc and sizectrlpmcinfo > 0:
        for i in range(sizectrlpmcinfo):
            raid_Info = Raid()
            control_Info = Controller()
            ctrInfo_temp = ctrInfo_pmc[i]

            raid_Info.CommonName('RAID Card')
            raid_Info.Location('mainboard')
            control_Info.Id(i)
            if 'vendorId' in ctrInfo_temp:
                control_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
                raid_Info.Manufacturer(PCI_IDS_LIST.get(ctrInfo_temp['vendorId'], ctrInfo_temp['vendorId']))
            else:
                control_Info.Manufacturer(None)
                raid_Info.Manufacturer(None)
            if 'devId' in ctrInfo_temp:
                control_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
                raid_Info.Model(PCI_IDS_DEVICE_LIST.get(ctrInfo_temp['devId'], ctrInfo_temp['devId']))
            else:
                control_Info.Model(None)
                raid_Info.Model(None)
            control_Info.SupportedDeviceProtocols([])
            control_Info.SASAddress(None)
            control_Info.ConfigurationVersion(ctrInfo_temp.get('fwVer', None))
            control_Info.MaintainPDFailHistory(None)
            control_Info.CopyBackState(None)
            control_Info.JBODState(None)
            control_Info.MinStripeSizeBytes(
                int(ctrInfo_temp.get('strpMinSz')) * 1024 if 'strpMinSz' in ctrInfo_temp else None)
            control_Info.MaxStripeSizeBytes(
                int(ctrInfo_temp.get('strpMaxSz')) * 1024 if 'strpMaxSz' in ctrInfo_temp else None)
            control_Info.MemorySizeMiB(int(ctrInfo_temp.get('memSz')) if 'memSz' in ctrInfo_temp else None)
            if '3008IT' in ctrInfo_temp.get('PN', 'None'):
                control_Info.SupportedRAIDLevels([])
            else:
                control_Info.SupportedRAIDLevels(['RAID0,RAID1,RAID5,RAID6,RAID10'])
            control_Info.DDRECCCount(None)

            raid_Info.SerialNumber(None if ctrInfo_temp.get('SN', None) == '' else ctrInfo_temp.get('SN', None))
            raid_Info.State('Enabled')
            if ctrInfo_temp.get('Health') is None:
                health_pmcflag = 1
            # raid_Info.Health(ctrInfo_temp.get('Health', None))
            raid_Info.Health(None)
            raid_Info.Controller([control_Info.dict])
            ctrl_list.append(raid_Info.dict)

    if health_lsiflag == 1 and health_pmcflag == 1:
        raid_bean.OverallHealth(None)
    else:
        raid_bean.OverallHealth('OK')
    raid_bean.Maximum(num)
    raid_bean.RaidCard(ctrl_list)
    raid_return.State('Success')
    raid_return.Message([raid_bean.dict])
    return raid_return


def getPdInfo_LSI(client):
    disk_return = ResultBean()
    disk_info = DiskBean()
    ctr_count = RestFunc.getLSICtrlCountByRest(client)
    if ctr_count is None or ctr_count.get('code') != 0 or ctr_count.get('data') is None:  # ctrl个数
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    else:
        count = ctr_count.get('data')
        countNumber = count.get('ctrlCount')

    if countNumber == 0:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    health_flag = 0
    disk_list = []
    lsi_num = 0
    for i in range(countNumber):
        disk_allinfo = RestFunc.getLSICtrlpdInfoByRest(client, i)
        if disk_allinfo is None or disk_allinfo.get('code') != 0 or disk_allinfo.get('data') is None:
            disk_return.State('Failure')
            disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return disk_return
        disk_data = disk_allinfo.get('data')
        sizepdinfo = len(disk_data)
        lsi_num += sizepdinfo
        for j in range(sizepdinfo):
            disk = Disk()
            disk_temp = disk_data[j]
            disk.Id(int(disk_temp.get('devId', j)))
            disk.CommonName('Disk' + str(disk_temp.get('devId', j)))
            disk.Location('from disk backplane')
            disk.Manufacturer(disk_temp.get('vendId').strip() if 'vendId' in disk_temp else None)
            disk.Model(disk_temp.get('prodId', None))
            # disk.Protocol(disk_temp.get('intfType',None))
            disk.Protocol(STR_PD_INTERFACE_TYPE.get(disk_temp.get('intfType', None), disk_temp.get('intfType', None)))

            disk.FailurePredicted(None)
            if 'rawSize' in disk_temp:
                temp = disk_temp.get('rawSize')
                if isinstance(temp, str):
                    size = re.findall(r'\d+.\d+', temp)
                    disk.CapacityGiB(float(size[0]))
                else:
                    disk.CapacityGiB(temp)
            else:
                disk.CapacityGiB(None)
            disk.HotspareType(None)
            if 'powerState' in disk_temp:
                disk.IndicatorLED('On' if disk_temp.get('powerState') == 1 else 'Off')
            else:
                disk.IndicatorLED(None)

            disk.PredictedMediaLifeLeftPercent(str(disk_temp.get('time_left')) if 'time_left' in disk_temp else None)
            # disk.MediaType(disk_temp.get('mediaType',None))
            disk.MediaType(STR_MEDIA_TYPE.get(disk_temp.get('mediaType', None), disk_temp.get('mediaType', None)))

            # disk.SerialNumber(disk_temp.get('SN',None))
            disk.SerialNumber(None)
            # if 'linkSpeed' in disk_temp:
            #     temp = disk_temp.get('linkSpeed')
            #     if type(temp) is str:
            #         size = re.findall(r'\d+.\d+', temp)
            #         # disk.CapableSpeedGbs(float(size[0]))
            #         disk.NegotiatedSpeedGbs(float(size[0]))
            #     else:
            #         # disk.CapableSpeedGbs(temp)
            #         disk.NegotiatedSpeedGbs(temp)
            # else:
            disk.NegotiatedSpeedGbs(None)
            disk.CapableSpeedGbs(None)
            disk.Revision(disk_temp.get('prodRevLev', None))
            disk.StatusIndicator(None)
            disk.TemperatureCelsius(disk_temp.get('temp', None))
            disk.HoursOfPoweredUp(None)
            # disk.FirmwareStatus(fwState(disk_temp.get('fwState', None)))
            disk.FirmwareStatus(STR_PD_FW_STATE.get(disk_temp.get('fwState', None), disk_temp.get('fwState', None)))

            # disk.FirmwareStatus(disk_temp.get('fwState', None))
            disk.SASAddress([disk_temp.get('sasAddr')] if 'sasAddr' in disk_temp else [])
            disk.PatrolState(None)
            disk.RebuildState(None)
            disk.SpareforLogicalDrives([])
            disk.Volumes(None if disk_temp.get('logicdisks', None) == '' else disk_temp.get('logicdisks', None))
            disk.State('Enabled')
            disk.Health(disk_temp.get('status', None))
            disk.RebuildProgress(disk_temp.get('pdProgress', None))
            disk_list.append(disk.dict)
    if len(disk_list) > 0:
        disk_info.Maximum(lsi_num)
        disk_info.Disk(disk_list)
        disk_info.OverallHealth('OK')  # 需咨询
        disk_return.State('Success')
        disk_return.Message([disk_info.dict])
    else:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    return disk_return


def getPdInfo_PMC(client):
    disk_return = ResultBean()
    disk_info = DiskBean()
    ctr_count = RestFunc.getPMCCtrlCountByRest(client)
    if ctr_count is None or ctr_count.get('code') != 0 or ctr_count.get('data') is None:  # ctrl个数
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    else:
        count = ctr_count.get('data')
        countNumber = count.get('ctrlCount')

    if countNumber == 0:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    health_flag = 0
    disk_list = []
    pmc_num = 0
    for i in range(countNumber):
        disk_allinfo = RestFunc.getPMCCtrlpdInfoByRest(client, i)
        # print(disk_allinfo)
        if disk_allinfo is None or disk_allinfo.get('code') != 0 or disk_allinfo.get('data') is None:
            disk_return.State('Failure')
            disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return disk_return
        disk_data = disk_allinfo.get('data')
        sizepdinfo = len(disk_data)
        pmc_num += sizepdinfo
        for j in range(sizepdinfo):
            disk = Disk()
            disk_temp = disk_data[j]
            disk.Id(int(disk_temp.get('DeviceID', j)))
            disk.CommonName('Disk' + str(disk_temp.get('DeviceID', j)))
            disk.Location('from disk backplane')
            disk.Manufacturer(disk_temp.get('vendId').strip() if 'vendId' in disk_temp else None)
            disk.Model(disk_temp.get('procId', None))
            if 'RAIDClass' in disk_temp:
                temp = disk_temp.get('RAIDClass')
                temp_split = temp.split(' ')
                disk.Protocol(temp_split[0])
            else:
                disk.Protocol(None)
            disk.FailurePredicted(None)
            if 'GBSize' in disk_temp:
                temp = disk_temp.get('GBSize')
                if isinstance(temp, str):
                    size = re.findall(r'\d+.\d+', temp)
                    disk.CapacityGiB(float(size[0]))
                else:
                    disk.CapacityGiB(temp)
            else:
                disk.CapacityGiB(None)
            disk.HotspareType(None)
            disk.IndicatorLED(None)
            disk.PredictedMediaLifeLeftPercent(None)
            disk.MediaType(disk_temp.get('RAIDClass', None))
            disk.SerialNumber(disk_temp.get('SN', None).strip())
            if 'RAIDSpeed' in disk_temp:
                temp = disk_temp.get('RAIDSpeed')
                if isinstance(temp, str):
                    size = re.findall(r'\d+.\d+', temp)
                    disk.CapableSpeedGbs(float(size[0]))
                    # disk.NegotiatedSpeedGbs(float(size[0]))
                else:
                    disk.CapableSpeedGbs(temp)
                    # disk.NegotiatedSpeedGbs(temp)
            else:
                disk.CapableSpeedGbs(None)
            disk.NegotiatedSpeedGbs(None)
            disk.Revision(disk_temp.get('revision_level', None))
            disk.StatusIndicator(None)
            disk.TemperatureCelsius(str(disk_temp.get('tempreture')) if 'tempreture' in disk_temp else None)
            disk.HoursOfPoweredUp(None)
            disk.FirmwareStatus(STR_PD_FW_STATE.get(disk_temp.get('state', None), disk_temp.get('state', None)))
            disk.SASAddress([disk_temp.get('sasAddr')] if 'sasAddr' in disk_temp else [])
            disk.PatrolState(None)
            disk.RebuildState(None)
            disk.RebuildProgress(None)
            disk.SpareforLogicalDrives([])
            disk.Volumes(None)
            disk.State('Enabled')
            disk.Health(None)
            disk_list.append(disk.dict)
    if len(disk_list) > 0:
        disk_info.OverallHealth('OK')  # 需咨询
        disk_info.Maximum(pmc_num)
        disk_info.Disk(disk_list)
        disk_return.State('Success')
        disk_return.Message([disk_info.dict])
    else:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    return disk_return


def getPdInfo(client):
    disk_return = ResultBean()
    disk_info = DiskBean()
    ctr_count_lsi = RestFunc.getLSICtrlCountByRest(client)
    ctr_count_pmc = RestFunc.getPMCCtrlCountByRest(client)
    if ctr_count_lsi is None or ctr_count_lsi.get('code') != 0 or ctr_count_lsi.get('data') is None:  # ctrl个数
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    else:
        count = ctr_count_lsi.get('data')
        countNumber_lsi = count.get('ctrlCount')

    if ctr_count_pmc is None or ctr_count_pmc.get('code') != 0 or ctr_count_pmc.get('data') is None:  # ctrl个数
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return
    else:
        count = ctr_count_pmc.get('data')
        countNumber_pmc = count.get('ctrlCount')
    num = countNumber_lsi + countNumber_pmc
    if num == 0:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return disk_return

    health_flag = 0
    disk_list = []
    sizepdinfo_lsi = 0
    sizepdinfo_pmc = 0
    lsi_num = 0
    pmc_num = 0
    if countNumber_lsi > 0:
        for i in range(countNumber_lsi):
            disk_allinfo = RestFunc.getLSICtrlpdInfoByRest(client, i)
            if disk_allinfo is None or disk_allinfo.get('code') != 0 or disk_allinfo.get('data') is None:
                disk_return.State('Failure')
                disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
                return disk_return
            disk_data = disk_allinfo.get('data')
            sizepdinfo_lsi = len(disk_data)
            lsi_num += sizepdinfo_lsi
            if sizepdinfo_lsi > 0:
                for j in range(sizepdinfo_lsi):
                    disk = Disk()
                    disk_temp = disk_data[j]
                    disk.Id(int(disk_temp.get('devId', j)))
                    disk.CommonName('Disk' + str(disk_temp.get('devId', j)))
                    disk.Location('from disk backplane')
                    disk.Manufacturer(disk_temp.get('vendId').strip() if 'vendId' in disk_temp else None)
                    disk.Model(disk_temp.get('prodId', None))
                    disk.Protocol(
                        STR_PD_INTERFACE_TYPE.get(disk_temp.get('intfType', None), disk_temp.get('intfType', None)))

                    disk.FailurePredicted(None)
                    if 'rawSize' in disk_temp:
                        temp = disk_temp.get('rawSize')
                        if isinstance(temp, str):
                            size = re.findall(r'\d+.\d+', temp)
                            disk.CapacityGiB(float(size[0]))
                        else:
                            disk.CapacityGiB(temp)
                    else:
                        disk.CapacityGiB(None)
                    disk.HotspareType(None)
                    if 'powerState' in disk_temp:
                        disk.IndicatorLED('On' if disk_temp.get('powerState') == 1 else 'Off')
                    else:
                        disk.IndicatorLED(None)
                    disk.PredictedMediaLifeLeftPercent(
                        str(disk_temp.get('time_left')) if 'time_left' in disk_temp else None)

                    disk.MediaType(
                        STR_MEDIA_TYPE.get(disk_temp.get('mediaType', None), disk_temp.get('mediaType', None)))

                    disk.SerialNumber(None)
                    disk.NegotiatedSpeedGbs(None)
                    disk.CapableSpeedGbs(None)
                    disk.Revision(disk_temp.get('prodRevLev', None))
                    disk.StatusIndicator(None)
                    disk.TemperatureCelsius(disk_temp.get('temp', None))
                    disk.HoursOfPoweredUp(None)
                    disk.FirmwareStatus(
                        STR_PD_FW_STATE.get(disk_temp.get('fwState', None), disk_temp.get('fwState', None)))
                    disk.SASAddress([disk_temp.get('sasAddr')] if 'sasAddr' in disk_temp else [])
                    disk.PatrolState(None)
                    disk.RebuildState(None)
                    disk.RebuildProgress(disk_temp.get('pdProgress', None))
                    disk.SpareforLogicalDrives([])
                    disk.Volumes(None if disk_temp.get('logicdisks', None) == '' else disk_temp.get('logicdisks', None))
                    disk.State('Enabled')
                    disk.Health(disk_temp.get('status', None))
                    disk_list.append(disk.dict)
    if countNumber_pmc > 0:
        for i in range(countNumber_pmc):
            disk_allinfo = RestFunc.getPMCCtrlpdInfoByRest(client, i)
            if disk_allinfo is None or disk_allinfo.get('code') != 0 or disk_allinfo.get('data') is None:
                disk_return.State('Failure')
                disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
                return disk_return
            disk_data = disk_allinfo.get('data')
            sizepdinfo_pmc = len(disk_data)
            pmc_num += sizepdinfo_pmc
            if sizepdinfo_pmc > 0:
                for j in range(sizepdinfo_pmc):
                    disk = Disk()
                    disk_temp = disk_data[j]
                    disk.Id(int(disk_temp.get('DeviceID', j)))
                    disk.CommonName('Disk' + str(disk_temp.get('DeviceID', j)))
                    disk.Location('from disk backplane')
                    disk.Manufacturer(disk_temp.get('vendId').strip() if 'vendId' in disk_temp else None)
                    disk.Model(disk_temp.get('procId', None))
                    if 'RAIDClass' in disk_temp:
                        temp = disk_temp.get('RAIDClass')
                        temp_split = temp.split(' ')
                        disk.Protocol(temp_split[0])
                    else:
                        disk.Protocol(None)
                    disk.FailurePredicted(None)
                    if 'GBSize' in disk_temp:
                        temp = disk_temp.get('GBSize')
                        if isinstance(temp, str):
                            size = re.findall(r'\d+.\d+', temp)
                            disk.CapacityGiB(float(size[0]))
                        else:
                            disk.CapacityGiB(temp)
                    else:
                        disk.CapacityGiB(None)
                    disk.HotspareType(None)
                    disk.IndicatorLED(None)
                    disk.PredictedMediaLifeLeftPercent(None)
                    disk.MediaType(disk_temp.get('RAIDClass', None))
                    disk.SerialNumber(disk_temp.get('SN', None).strip())
                    if 'RAIDSpeed' in disk_temp:
                        temp = disk_temp.get('RAIDSpeed')
                        if isinstance(temp, str):
                            size = re.findall(r'\d+.\d+', temp)
                            disk.CapableSpeedGbs(float(size[0]))
                        else:
                            disk.CapableSpeedGbs(temp)
                    else:
                        disk.CapableSpeedGbs(None)
                    disk.NegotiatedSpeedGbs(None)
                    disk.Revision(disk_temp.get('revision_level', None))
                    disk.StatusIndicator(None)
                    disk.TemperatureCelsius(str(disk_temp.get('tempreture')) if 'tempreture' in disk_temp else None)
                    disk.HoursOfPoweredUp(None)
                    disk.FirmwareStatus(STR_PD_FW_STATE.get(disk_temp.get('state', None), disk_temp.get('state', None)))
                    disk.SASAddress([disk_temp.get('sasAddr')] if 'sasAddr' in disk_temp else [])
                    disk.PatrolState(None)
                    disk.RebuildState(None)
                    disk.RebuildProgress(None)
                    disk.SpareforLogicalDrives([])
                    disk.Volumes(None)
                    disk.State('Enabled')
                    disk.Health(None)
                    disk_list.append(disk.dict)
    if len(disk_list) > 0:
        disk_info.OverallHealth('OK')  # 需咨询
        disk_info.Maximum(lsi_num + pmc_num)
        disk_info.Disk(disk_list)
        disk_return.State('Success')
        disk_return.Message([disk_info.dict])
    else:
        disk_return.State('Failure')
        disk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    return disk_return


def getLdInfo_LSI(client):
    ldisk_return = ResultBean()
    ldisk_info = LogicDiskBean()
    ctr_count = RestFunc.getLSICtrlCountByRest(client)
    if ctr_count is None or ctr_count.get('code') != 0 or ctr_count.get('data') is None:  # ctrl个数
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    else:
        count = ctr_count.get('data')
        countNumber = count.get('ctrlCount')
    if countNumber == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    health_flag = 0
    ldisk_list = []
    count_num = 0
    for i in range(countNumber):
        ldisk_allinfo = RestFunc.getLSICtrlLdInfoByRest(client, i)
        if ldisk_allinfo is None or ldisk_allinfo.get('code') != 0 or ldisk_allinfo.get('data') is None:
            ldisk_return.State('Failure')
            ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return ldisk_return
        ldisk_data = ldisk_allinfo.get('data')
        sizeldinfo = len(ldisk_data)
        count_num += sizeldinfo
        if sizeldinfo > 0:
            for j in range(sizeldinfo):
                ldisk = LogicDisk()
                ldisk_temp = ldisk_data[j]
                ldisk.Id(int(ldisk_temp.get('targetId')) if 'targetId' in ldisk_temp else None)
                ldisk.LogicDiskName(
                    None if str(ldisk_temp.get('name', None)) == '' else str(ldisk_temp.get('name', None)))
                ldisk.RaidControllerID(str(i))
                # ldisk.RaidLevel(ldisk_temp.get('volume_raid_level', None))
                ldisk.RaidLevel(raidlevels.get(ldisk_temp.get('PRL', None), ldisk_temp.get('PRL', None)))
                ldisk.OptimumIOSizeBytes(ldisk_temp.get('stripSize') * 1024 if 'stripSize' in ldisk_temp else None)
                ldisk.RedundantType(None)
                if 'size' in ldisk_temp:
                    temp = ldisk_temp.get('size')
                    if isinstance(temp, str):
                        size = re.findall(r'\d+.\d+', temp)
                        ldisk.CapacityGiB(float(size[0]))
                    else:
                        ldisk.CapacityGiB(temp)
                else:
                    ldisk.CapacityGiB(None)
                if 'defCaPolicy' in ldisk_temp:
                    cachePolicy = ldisk_temp.get('defCaPolicy')
                    if not str(cachePolicy).isdigit():
                        readPolicy, writePolicy, cachePolicy = None, None, None
                    else:
                        readPolicy, writePolicy, cachePolicy = Policy(cachePolicy)
                else:
                    readPolicy, writePolicy, cachePolicy = None, None, None
                ldisk.DefaultReadPolicy(readPolicy)
                ldisk.DefaultWritePolicy(writePolicy)
                ldisk.DefaultCachePolicy(cachePolicy)
                if 'curCaPolicy' in ldisk_temp:
                    cachePolicy = ldisk_temp.get('curCaPolicy')
                    if isinstance(cachePolicy, str):
                        readPolicy = ldisk_temp.get('curRePolicy')
                        writePolicy = ldisk_temp.get('curWrPolicy')
                    elif not str(cachePolicy).isdigit():
                        readPolicy, writePolicy, cachePolicy = None, None, None
                    else:
                        readPolicy, writePolicy, cachePolicy = Policy(cachePolicy)
                else:
                    readPolicy, writePolicy, cachePolicy = None, None, None
                ldisk.CurrentReadPolicy(readPolicy)
                ldisk.CurrentWritePolicy(writePolicy)
                ldisk.CurrentCachePolicy(cachePolicy)
                ldisk.AccessPolicy(
                    STR_LD_ACCESS.get(ldisk_temp.get('accPolicy', None), ldisk_temp.get('accPolicy', None)))

                ldisk.BGIEnable(ldisk_temp.get('noBGI', None))
                ldisk.BootEnable(None)
                # ldisk.DriveCachePolicy(ldisk_temp.get('pdCaPolicy', None))
                ldisk.DriveCachePolicy(None)
                ldisk.SSDCachecadeVolume(None)
                ldisk.ConsistencyCheck(True if ldisk_temp.get('isConsis', None) == 1 else False)
                ldisk.SSDCachingEnable(None)
                ldisk.Drives(ldisk_temp.get('physicaldisks', None))
                ldisk.Health(ldisk_temp.get('status', None))
                ldisk_list.append(ldisk.dict)
    if count_num == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    else:
        ldisk_info.OverallHealth('OK')  # 需咨询
        ldisk_info.Maximum(count_num)
        ldisk_info.LogicDisk(ldisk_list)
        ldisk_return.State('Success')
        ldisk_return.Message([ldisk_info.dict])
    return ldisk_return


def Policy(cachePolicy):
    Read = 0
    if (cachePolicy & MR_LD_CACHE_READ_AHEAD) and (cachePolicy & MR_LD_CACHE_READ_ADAPTIVE):
        Read = MR_LD_CACHE_READ_ADAPTIVE
    elif cachePolicy & MR_LD_CACHE_READ_AHEAD:
        Read = MR_LD_CACHE_READ_AHEAD
    else:
        Read = 0xff
    readPolicy = STR_LD_CACHE_LIST.get(Read, None)

    Write = 0
    if cachePolicy & MR_LD_CACHE_WRITE_BACK:
        Write = MR_LD_CACHE_WRITE_BACK
    elif ((cachePolicy & (MR_LD_CACHE_WRITE_BACK or MR_LD_CACHE_WRITE_CACHE_BAD_BBU))
          == (MR_LD_CACHE_WRITE_BACK | MR_LD_CACHE_WRITE_CACHE_BAD_BBU)):
        Write = MR_LD_CACHE_WRITE_CACHE_BAD_BBU
    else:
        Write = 0xfe
    writePolicy = STR_LD_CACHE_LIST.get(Write, None)

    Cache = 0
    if (cachePolicy & MR_LD_CACHE_ALLOW_WRITE_CACHE) and (cachePolicy & MR_LD_CACHE_ALLOW_READ_CACHE):
        Cache = 0xfd
    else:
        Cache = 0xfc
    cachePolicy = STR_LD_CACHE_LIST.get(Cache, None)

    return readPolicy, writePolicy, cachePolicy


def getLdInfo_PMC(client):
    ldisk_return = ResultBean()
    ldisk_info = LogicDiskBean()
    ctr_count = RestFunc.getPMCCtrlCountByRest(client)
    if ctr_count is None or ctr_count.get('code') != 0 or ctr_count.get('data') is None:  # ctrl个数
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    else:
        count = ctr_count.get('data')
        countNumber = count.get('ctrlCount')
    if countNumber == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    health_flag = 0
    ldisk_list = []
    count_num = 0
    for i in range(countNumber):
        ldisk_allinfo = RestFunc.getPMCCtrlLdInfoByRest(client, i)
        if ldisk_allinfo is None or ldisk_allinfo.get('code') != 0 or ldisk_allinfo.get('data') is None:
            ldisk_return.State('Failure')
            ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
            return ldisk_return
        ldisk_data = ldisk_allinfo.get('data')
        sizeldinfo = len(ldisk_data)
        count_num += sizeldinfo
        if sizeldinfo > 0:
            for j in range(sizeldinfo):
                ldisk = LogicDisk()
                ldisk_temp = ldisk_data[j]
                ldisk.Id(int(ldisk_temp.get('index', 0)))
                ldisk.LogicDiskName(None)
                ldisk.RaidControllerID(str(i))
                ldisk.RaidLevel(ldisk_temp.get('type'))
                if 'size_GB' in ldisk_temp:
                    temp = ldisk_temp.get('size_GB')
                    if isinstance(temp, str):
                        size = re.findall(r'\d+.\d+', temp)
                        # ldisk.CapacityGiB(float(size[0])/1024)
                        ldisk.CapacityGiB(float(size[0]))
                    else:
                        # ldisk.CapacityGiB(temp/1024)
                        ldisk.CapacityGiB(temp)
                else:
                    ldisk.CapacityGiB(None)
                ldisk.OptimumIOSizeBytes(None)
                ldisk.RedundantType(None)
                ldisk.DefaultReadPolicy(None)
                ldisk.DefaultWritePolicy(None)
                ldisk.DefaultCachePolicy(None)
                # ldisk.DefaultCachePolicy(ldisk_temp.get('defCaPolicy', None)) # 需要对应关系
                ldisk.CurrentReadPolicy(None)
                ldisk.CurrentWritePolicy(None)
                ldisk.CurrentCachePolicy(None)
                ldisk.AccessPolicy(None)
                ldisk.BGIEnable(None)
                ldisk.BootEnable(None)
                ldisk.DriveCachePolicy(None)
                ldisk.SSDCachecadeVolume(None)
                ldisk.ConsistencyCheck(None)
                ldisk.SSDCachingEnable(None)
                ldisk.Drives(None)
                ldisk.Health(ldisk_temp.get('state', None))
                ldisk_list.append(ldisk.dict)
    if count_num == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    else:
        ldisk_info.OverallHealth('OK')  # 需咨询
        ldisk_info.Maximum(count_num)
        ldisk_info.LogicDisk(ldisk_list)
        ldisk_return.State('Success')
        ldisk_return.Message([ldisk_info.dict])
    return ldisk_return


def getLdInfo(client):
    ldisk_return = ResultBean()
    ldisk_info = LogicDiskBean()
    ctr_count_lsi = RestFunc.getLSICtrlCountByRest(client)
    ctr_count_pmc = RestFunc.getPMCCtrlCountByRest(client)
    if ctr_count_lsi is None or ctr_count_lsi.get('code') != 0 or ctr_count_lsi.get('data') is None:  # ctrl个数
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    else:
        count = ctr_count_lsi.get('data')
        countNumber_lsi = count.get('ctrlCount')

    if ctr_count_pmc is None or ctr_count_pmc.get('code') != 0 or ctr_count_pmc.get('data') is None:  # ctrl个数
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return
    else:
        count = ctr_count_pmc.get('data')
        countNumber_pmc = count.get('ctrlCount')
    num = countNumber_lsi + countNumber_pmc
    if num == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
        return ldisk_return

    health_flag = 0
    ldisk_list = []
    sizeldinfo_lsi = 0
    sizeldinfo_pmc = 0
    lsi_num = 0
    pmc_num = 0
    if countNumber_lsi > 0:
        for i in range(countNumber_lsi):
            ldisk_allinfo = RestFunc.getLSICtrlLdInfoByRest(client, i)
            if ldisk_allinfo is None or ldisk_allinfo.get('code') != 0 or ldisk_allinfo.get('data') is None:
                ldisk_return.State('Failure')
                ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
                return ldisk_return
            ldisk_data = ldisk_allinfo.get('data')
            sizeldinfo_lsi = len(ldisk_data)
            lsi_num += sizeldinfo_lsi
            for j in range(sizeldinfo_lsi):
                ldisk = LogicDisk()
                ldisk_temp = ldisk_data[j]
                # ldisk.Id(int(ldisk_temp.get('targetId', 0)))
                ldisk.Id(int(ldisk_temp.get('targetId')) if 'targetId' in ldisk_temp else None)
                ldisk.LogicDiskName(
                    None if str(ldisk_temp.get('name', None)) == '' else str(ldisk_temp.get('name', None)))
                ldisk.RaidControllerID(str(i))
                # ldisk.RaidLevel(ldisk_temp.get('volume_raid_level', None))
                ldisk.RaidLevel(raidlevels.get(ldisk_temp.get('PRL', None), ldisk_temp.get('PRL', None)))
                if 'size' in ldisk_temp:
                    temp = ldisk_temp.get('size')
                    if isinstance(temp, str):
                        size = re.findall(r'\d+.\d+', temp)
                        ldisk.CapacityGiB(float(size[0]))
                    else:
                        ldisk.CapacityGiB(temp)
                else:
                    ldisk.CapacityGiB(None)
                ldisk.OptimumIOSizeBytes(ldisk_temp.get('stripSize') * 1024 if 'stripSize' in ldisk_temp else None)
                ldisk.RedundantType(None)
                if 'defCaPolicy' in ldisk_temp:
                    cachePolicy = ldisk_temp.get('defCaPolicy')
                    if not str(cachePolicy).isdigit():
                        readPolicy, writePolicy, cachePolicy = None, None, None
                    else:
                        readPolicy, writePolicy, cachePolicy = Policy(cachePolicy)
                else:
                    readPolicy, writePolicy, cachePolicy = None, None, None
                ldisk.DefaultReadPolicy(readPolicy)
                ldisk.DefaultWritePolicy(writePolicy)
                ldisk.DefaultCachePolicy(cachePolicy)
                if 'curCaPolicy' in ldisk_temp:
                    cachePolicy = ldisk_temp.get('curCaPolicy')
                    if isinstance(cachePolicy, str):
                        readPolicy = ldisk_temp.get('curRePolicy')
                        writePolicy = ldisk_temp.get('curWrPolicy')
                    elif not str(cachePolicy).isdigit():
                        readPolicy, writePolicy, cachePolicy = None, None, None
                    else:
                        readPolicy, writePolicy, cachePolicy = Policy(cachePolicy)
                else:
                    readPolicy, writePolicy, cachePolicy = None, None, None
                ldisk.CurrentReadPolicy(readPolicy)
                ldisk.CurrentWritePolicy(writePolicy)
                ldisk.CurrentCachePolicy(cachePolicy)
                ldisk.AccessPolicy(
                    STR_LD_ACCESS.get(ldisk_temp.get('accPolicy', None), ldisk_temp.get('accPolicy', None)))
                ldisk.BGIEnable(ldisk_temp.get('noBGI', None))
                ldisk.BootEnable(None)
                # ldisk.DriveCachePolicy(ldisk_temp.get('pdCaPolicy', None))
                ldisk.DriveCachePolicy(None)
                ldisk.SSDCachecadeVolume(None)
                ldisk.ConsistencyCheck(True if ldisk_temp.get('isConsis', None) == 1 else False)
                ldisk.SSDCachingEnable(None)
                ldisk.Drives(ldisk_temp.get('physicaldisks', None))
                ldisk.Health(ldisk_temp.get('status', None))
                ldisk_list.append(ldisk.dict)
    if countNumber_pmc > 0:
        for i in range(countNumber_pmc):
            ldisk_allinfo = RestFunc.getPMCCtrlLdInfoByRest(client, i)
            if ldisk_allinfo is None or ldisk_allinfo.get('code') != 0 or ldisk_allinfo.get('data') is None:
                ldisk_return.State('Failure')
                ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
                return ldisk_return
            ldisk_data = ldisk_allinfo.get('data')
            sizeldinfo_pmc = len(ldisk_data)
            pmc_num += sizeldinfo_pmc
            for j in range(sizeldinfo_pmc):
                ldisk = LogicDisk()
                ldisk_temp = ldisk_data[j]
                ldisk.Id(int(ldisk_temp.get('index', 0)))
                ldisk.LogicDiskName(None)
                ldisk.RaidControllerID(str(i))
                ldisk.RaidLevel(ldisk_temp.get('type'))
                if 'size_GB' in ldisk_temp:
                    temp = ldisk_temp.get('size_GB')
                    if isinstance(temp, str):
                        size = re.findall(r'\d+.\d+', temp)
                        ldisk.CapacityGiB(float(size[0]))
                    else:
                        ldisk.CapacityGiB(temp)
                else:
                    ldisk.CapacityGiB(None)
                ldisk.OptimumIOSizeBytes(None)
                ldisk.RedundantType(None)
                ldisk.DefaultReadPolicy(None)
                ldisk.DefaultWritePolicy(None)
                ldisk.DefaultCachePolicy(None)
                # ldisk.DefaultCachePolicy(ldisk_temp.get('defCaPolicy', None)) # 需要对应关系
                ldisk.CurrentReadPolicy(None)
                ldisk.CurrentWritePolicy(None)
                ldisk.CurrentCachePolicy(None)
                ldisk.AccessPolicy(None)
                ldisk.BGIEnable(None)
                ldisk.BootEnable(None)
                ldisk.DriveCachePolicy(None)
                ldisk.SSDCachecadeVolume(None)
                ldisk.ConsistencyCheck(None)
                ldisk.SSDCachingEnable(None)
                ldisk.Drives(None)
                ldisk.Health(ldisk_temp.get('state', None))
                ldisk_list.append(ldisk.dict)
    count_num = sizeldinfo_lsi + sizeldinfo_pmc
    if count_num == 0:
        ldisk_return.State('Failure')
        ldisk_return.Message(["Device information Not Available (Device absent or failed to get)!"])
    else:
        ldisk_info.OverallHealth('OK')
        ldisk_info.Maximum(count_num)
        ldisk_info.LogicDisk(ldisk_list)
        ldisk_return.State('Success')
        ldisk_return.Message([ldisk_info.dict])
    return ldisk_return


def powerState(var):
    if var == 0:
        return 'Active'
    elif var == 1:
        return 'Stop'
    elif var == 255:
        return 'Transitioning'
    else:
        return 'Unkonw'


def fwState(var):
    if var == 0x00:
        return 'Unconfigured Good'
    elif var == 0x01:
        return 'Unconfigured Bad'
    elif var == 0x02:
        return 'Hot Spare'
    elif var == 0x10:
        return 'Offline'
    elif var == 0x11:
        return 'Failed'
    elif var == 0x14:
        return 'Rebuild'
    elif var == 0x18:
        return 'Online'
    elif var == 0x20:
        return 'Copyback'
    elif var == 0x40:
        return 'JBOD'
    elif var == 0x80:
        return 'Sheld Unconfigured'
    elif var == 0x82:
        return 'Sheld Hot Spare'
    elif var == 0x90:
        return 'Sheld Configured'
    else:
        return var


def mediaType(var):
    if var == 0:
        return 'HDD'
    else:
        return var


def intfType(var):
    if var == 2:
        return 'SAS'
    else:
        return var


def showpdInfo(client, args):
    result = ResultBean()
    try:
        count = RestFunc.getLSICtrlCountByRest(client)
        if count.get('code') == 0 and count.get('data') is not None:
            countNumber = count['data']['ctrlCount']
            if countNumber == 0:
                result.State('Failure')
                result.Message([" Device information Not Available (Device absent or failed to get)!"])
                return result
            raidList = []
            for i in range(countNumber):
                ctrlpdinfo = RestFunc.getLSICtrlpdInfoByRest(client, i)
                if ctrlpdinfo.get('code') == 0 and ctrlpdinfo.get('data') is not None:
                    raidDict = collections.OrderedDict()
                    raidDict['Controller ID'] = i
                    pdiskList = []
                    for item in ctrlpdinfo.json():
                        pdiskDict = collections.OrderedDict()
                        if 'slotNum' in item:
                            pdiskDict['Slot Number'] = item['slotNum']
                        if 'intfType' in item:
                            pdiskDict['Interface'] = intfType(item['intfType'])
                        if 'mediaType' in item:
                            pdiskDict['Media Type'] = mediaType(item['mediaType'])
                        if 'rawSize' in item:
                            pdiskDict['Capacity'] = item['rawSize']
                        if 'fwState' in item:
                            pdiskDict['Firmware State'] = fwState(item['fwState'])
                        pdiskList.append(pdiskDict)
                    raidDict['pdisk'] = pdiskList
                    raidList.append(raidDict)
                else:
                    result.State('Failure')
                    result.Message(['Info: Controller ID is {0},No physical drive'.format(i)])
                    return result
            result.State('Success')
            result.Message(raidList)
            return result
        else:
            result.State('Failure')
            result.Message(['Device information Not Available (Device absent or failed to get)!'])
            return result
    except(AttributeError, KeyError):
        result.State('Failure')
        result.Message(['AttributeError or KeyError'])
        return result


def getpdInfo(client, cid_index):
    pd = []
    pv = {}
    px = {}
    ctrlpdinfo = RestFunc.getLSICtrlpdInfoByRest(client, cid_index)
    if ctrlpdinfo.get('code') == 0 and ctrlpdinfo.get('data') is not None:
        for item in ctrlpdinfo.json():
            if 'index' not in item:
                return [], {}, {}
            # pd[ctrlItem['index']].append(item['index'])
            if item['fwState'] == "UNCONFIGURED GOOD" or item['fwState'] == 0:
                pd.append(item['slotNum'])
                pv[item['slotNum']] = item['index']
                px[item['slotNum']] = item['devId']
        return pd, pv, px
    else:
        return [], {}, {}


def createVirtualDrive(client, args):
    if args.Info is not None:
        result = showpdInfo(client, args)
        return result
    result = ResultBean()
    if args.ctrlId is None or args.access is None or args.cache is None or args.init is None \
            or args.rlevel is None or args.slot is None or args.size is None or args.r is None or \
            args.w is None or args.io is None or args.select is None:
        result.State('Failure')
        result.Message(['some parameters are missing'])
        return result
    # 将cid转换成index,并检查
    ctrlInfo = RestFunc.getLSICtrlInfoByRest(client)
    if ctrlInfo.get('code') == 0 and ctrlInfo.get('data') is not None:
        result = ctrlInfo['data']
        if len(result) == 0:
            result.State('Failure')
            result.Message(['No controller'])
            return result
        elif args.ctrlId > len(result) - 1 or args.ctrlId < 0:
            result.State('Failure')
            result.Message(['no controller id ' + str(args.ctrlId)])
            return result
        else:
            cid_info = result[args.ctrlId]
            if 'index' in cid_info:
                cid_index = cid_info.get('index', args.ctrlId)
            else:
                result.State('Failure')
                result.Message(['get controller failed'])
                return result
    else:
        result.State('Failure')
        result.Message(['get controller failed'])
        return result
    # check pd pv
    pdset, pv, px = getpdInfo(client, args.ctrlId)

    # check select size
    if args.select < 1 or args.select > 100:
        result.State('Failure')
        result.Message(['the select size range in 1 - 100'])
        return result

    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    data = {
        'access_policy': args.access,
        'cache_policy': args.cache,
        'create_spares_flag': 0,
        'ctrlId': cid_index,
        'enctrption_type': 1,
        'init_state': args.init,
        'ld_io_policy': args.io,
        'ld_read_policy': args.r,
        'ld_write_policy': args.w,
        'logical_drive_count': 1,
        # 'number_of_pd': 1,
        # 'pd_deviceIndex0': args.pd,
        'pi_vd_support': 0,
        'power_policy': 0,
        'provide_shared_sccess': 1,
        'raid_Levels': args.rlevel,
        'size_to_used': args.select,
        'stripSize': args.size + 6
    }
    # args.pd
    args.slot = args.slot.split(',')
    pd_para_len = len(args.slot)
    if pd_para_len == 1:
        pd = RegularCheckUtil.check_arg(args.slot[0])
        if pd not in pdset:
            result.State('Failure')
            result.Message([' no SlotNumber ' + str(pd) + ' or the state is not unconfigured good'])
            return result
        # data['pd_deviceIndex0'] = pd + 1
        data['pd_deviceIndex0'] = pv[pd]
        data['pd_deviceId0'] = px[pd]
    else:
        index = 0
        for i in args.slot:
            pdstr = 'pd_deviceIndex{0}'.format(index)
            pdstr2 = 'pd_deviceId{0}'.format(index)
            n = RegularCheckUtil.check_arg(i)
            if n not in pdset:
                result.State('Failure')
                result.Message(['no SlotNumber ' + str(n) + 'or the state is not unconfigured good'])
                return result
            data[pdstr] = pv[n]
            data[pdstr2] = px[n]
            index += 1
    data['number_of_pd'] = pd_para_len
    # set raid
    if args.rlevel == 1:
        if pd_para_len < 2:
            result.State('Failure')
            result.Message(['raid 1 need 2 disks at least'])
            return result
    elif args.rlevel == 5:
        if pd_para_len < 3:
            result.State('Failure')
            result.Message(['raid 5 need 3 disks at least'])
            return result
    elif args.rlevel == 6:
        if pd_para_len < 4:
            result.State('Failure')
            result.Message(['raid 6 need 4 disks at least'])
            return result
    elif args.rlevel == 10:
        if pd_para_len < 4:
            result.State('Failure')
            result.Message(['raid 10 need 4 disks at least'])
            return result
        data['raid_Levels'] = 17

    r = RestFunc.addLDiskByRest(client, data)
    if ctrlInfo.get('code') == 0 and ctrlInfo.get('data') is not None:
        flg = getStatus(client, cid_index)
        if flg == 2:
            result.State('Success')
            result.Message(['Success:creating virtual drive, please wait several minutes'])
            time.sleep(10)
        elif flg == 3:
            result.State('Failure')
            result.Message(['create virtual drive failed'])
        elif flg == 5:
            result.State('Success')
            result.Message(['Success:creating virtual drive, please wait several minutes'])
            time.sleep(10)
        elif flg == 6:
            result.State('Success')
            result.Message(['Success:creating virtual drive, please wait several minutes'])
            time.sleep(10)
    else:
        result.State('Failure')
        result.Message(['create virtual drive failed'])
    return result


def getStatus(client, ctrlindex):
    for num in range(0, 600):
        flg = IpmiFunc.getRaidStatusByIpmi(client, ctrlindex)
        flg = flg.replace("\n", "").replace(" ", "")[0:2]
        if flg == "01":
            time.sleep(5)
            continue
        elif flg == "02":
            return 2
        elif flg == "00":
            return 4
        elif flg == "03":
            return 3
        else:
            return 5
    else:
        return 6


def state(var):
    if var == 0:
        return 'Offline'
    elif var == 1:
        return 'Partially Degraded'
    elif var == 2:
        return 'Degraded'
    elif var == 3:
        return 'Optimal'
    else:
        return 'Unknown'


def initState(var):
    if var == 0:
        return 'No Init'
    elif var == 1:
        return 'Quick Init'
    elif var == 2:
        return 'Full Init'
    else:
        return 'Unknown'


def showLogicalInfo_LSI(client, args):
    result = ResultBean()
    count = RestFunc.getLSICtrlCountByRest(client)
    if count.get('code') == 0 and count.get('data') is not None:
        if 'ctrlCount' in count['data']:
            countNumber = count['data']['ctrlCount']
        else:
            result.State('Failure')
            result.Message('Device information Not Available (Device absent or failed to get)!')
            return result
    else:
        result.State('Failure')
        result.Message('get controller information failed.')
        return result

    if countNumber == 0:
        result.State('Failure')
        result.Message('Device information Not Available (Device absent or failed to get)!')
        return result
    raidList = []
    for i in range(countNumber):
        ctrlldinfo = RestFunc.getLSICtrlLdInfoByRest(client, i)
        if ctrlldinfo.get('code') == 0 and ctrlldinfo.get('data') is not None:
            raidDict = collections.OrderedDict()
            raidDict['Controller ID'] = i
            ldiskList = []
            for item in ctrlldinfo.json():
                ldiskDict = collections.OrderedDict()
                if 'targetId' in item:
                    ldiskDict['Virtual Drive ID'] = item['targetId']
                if 'size' in item:
                    ldiskDict['Virtual Drive ID'] = item['targetId']
                if 'state' in item:
                    ldiskDict['State'] = state(item['state'])
                if 'stripSize' in item:
                    ldiskDict['Strip Size (KB)'] = item['stripSize']
                if 'initState' in item:
                    ldiskDict['nitial State'] = initState(item['initState'])
                ldiskList.append(ldiskDict)
            raidDict['ldisk'] = ldiskList
            raidList.append(raidDict)
        else:
            result.State('Failure')
            result.Message([' No Virtual Drive'])
            return result
    result.State('Success')
    result.Message(raidList)
    return result


def showLogicalInfo_PMC(client, args):
    result = ResultBean()
    count = RestFunc.getPMCCtrlCountByRest(client)
    if count.get('code') == 0 and count.get('data') is not None:
        if 'ctrlCount' in count['data']:
            countNumber = count['data']['ctrlCount']
        else:
            result.State('Failure')
            result.Message('Device information Not Available (Device absent or failed to get)!')
            return result
    else:
        result.State('Failure')
        result.Message('get controller information failed.')
        return result

    if countNumber == 0:
        result.State('Failure')
        result.Message('Device information Not Available (Device absent or failed to get)!')
        return result

    ctrlInfo = RestFunc.getPMCCtrlInfoByRest(client)
    if ctrlInfo.get('code') == 0 and ctrlInfo.get('data') is not None:
        ctrlItem = ctrlInfo['data']
    else:
        result.State('Failure')
        result.Message('Get controller information failed.')
        return result
    raidList = []
    for i in range(countNumber):
        ctrlldinfo = RestFunc.getPMCCtrlLdInfoByRest(client, i)
        if ctrlldinfo.get('code') == 0 and ctrlldinfo.get('data') is not None:
            raidDict = collections.OrderedDict()
            raidDict['Controller ID'] = i
            ldiskList = []
            for item in ctrlldinfo.json():
                ldiskDict = collections.OrderedDict()
                if 'index' in item:
                    ldiskDict['Virtual Drive ID'] = item['index']
                if 'size_GB' in item:
                    ldiskDict['Capacity (GB)'] = item['size_GB']
                if 'state' in item:
                    ldiskDict['State'] = item['state']
                if 'type' in item:
                    ldiskDict['Type'] = item['type']
                if 'size_M_blocks' in item:
                    ldiskDict['LD size(M Blocks)'] = item['size_M_blocks']
                if 'block_size_bytes' in item:
                    ldiskDict['Block size(Byte)'] = item['block_size_bytes']
                ldiskList.append(ldiskDict)
            raidDict['ldisk'] = ldiskList
            raidList.append(raidDict)
        else:
            result.State('Failure')
            result.Message([' No Virtual Drive'])
            return result
    result.State('Success')
    result.Message(raidList)
    return result


def getLogicalInfo_LSI(client, args):
    count = RestFunc.getLSICtrlCountByRest(client)
    if count.get('code') == 0 and count.get('data') is not None:
        if 'ctrlCount' in count['data']:
            countNumber = count['data']['ctrlCount']
            if countNumber == 0:
                return [], []
        else:
            return [], []
    else:
        return [], []
    cid = []
    vd = {}
    for i in range(countNumber):
        vd[i] = []
        cid.append(i)
        ctrlldinfo = RestFunc.getLSICtrlLdInfoByRest(client, i)
        if ctrlldinfo.get('code') == 0 and ctrlldinfo.get('data') is not None:
            for vditem in ctrlldinfo['data']:
                if 'targetId' not in vditem:
                    return [], []
                vd[i].append(vditem['targetId'])
    return cid, vd


def setVirtualDrive(client, args):
    result = ResultBean()
    raid_type = IpmiFunc.getRaidTypeByIpmi(client)
    if raid_type:
        if raid_type.get('code') == 0 and raid_type.get('data') is not None:
            raidtype = raid_type.get('data')
        else:
            raidtype = 'ff'
    else:
        raidtype = 'ff'
    # get
    if raidtype == '01':
        result = showLogicalInfo_PMC(client, args)
    elif raidtype == 'fe':
        result.State('Failure')
        result.Message(["Device information Not Available (Device absent or failed to get)!"])
        return result
    elif raidtype == '00' or raidtype == '02' or raidtype == '03':
        result = setLogicalDrive_LSI(args, client)
    elif raidtype == 'ff':
        if args.Info is not None:
            raidDict = {}
            LSIresult = showLogicalInfo_LSI(client, args)
            if LSIresult.State == 'Success':
                LSI = LSIresult.Message
                raidDict['LSI'] = LSI
            else:
                return LSIresult
            PMCresult = showLogicalInfo_PMC(client, args)
            if PMCresult.State() == 'Success':
                PMC = PMCresult.Message
                raidDict['PMC'] = PMC
            else:
                return PMCresult
            result.State('Success')
            result.Message([raidDict])
            return result
        else:
            print("-" * 60)
            result = setLogicalDrive_LSI(args, client)
    else:
        result.State('Failure')
        result.Message(['Failure: failed to establish connection to the host, please check the user/passcode/host/port',
                        'usage: isrest [-h] [-V] -H HOST -U USERNAME -P PASSWORD -p PORT subcommand ...'])
        return result
    return result


def setLogicalDrive_LSI(args, client):
    if args.Info is not None:
        result = showLogicalInfo_LSI(client, args)
        return result
    else:
        cid, vd = getLogicalInfo_LSI(client, args)

    result = ResultBean()
    if args.ctrlId is None or args.ldiskId is None or args.option is None:
        result.State('Failure')
        result.Message(["argument -CID, -VD or -OP is missing"])
        return result
    if args.ctrlId not in cid:
        result.State('Failure')
        result.Message(['no controller id ' + str(args.ctrlId)])
        return result
    if args.ldiskId not in vd[args.ctrlId]:
        result.State('Failure')
        result.Message(['no virtual drive id ' + str(args.ldiskId)])
        return result

    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    option = {
        'LOC': 1,
        'STL': 2,
        'FI': 3,
        'SFI': 4,
        'SI': 5,
        'DEL': 6
    }
    tips = {
        'LOC': 'locate',
        'STL': 'stop locate',
        'FI': 'fast initial',
        'SFI': 'slow/full initial',
        'SI': 'stop initial',
        'DEL': 'delete'
    }
    if args.option == 'LOC' or args.option == 'STL':
        r = RestFunc.locateLDiskByRest(client, args.ctrlId, args.ldiskId, option[args.option] - 1)
        if r.get('code') == 0 and r.get('data') is not None:
            result.State('Success')
            result.Message([tips[args.option] + ' virtual drive successfully, please wait several minutes.'])
        else:
            result.State('Failure')
            result.Message(['set virtual drive failed.'])
    elif args.option == 'FI' or args.option == 'SFI' or args.option == 'SI':
        r = RestFunc.initLDiskByRest(client, args.ctrlId, args.ldiskId, option[args.option] - 3)
        if r.get('code') == 0 and r.get('data') is not None:
            result.State('Success')
            result.Message([tips[args.option] + ' virtual drive successfully, please wait several minutes.'])
        else:
            result.State('Failure')
            result.Message(['set virtual drive failed.'])
    else:
        r = RestFunc.deleteLDiskByRest(client, args.ctrlId, args.ldiskId)
        if r.get('code') == 0 and r.get('data') is not None:
            result.State('Success')
            result.Message([tips[args.option] + ' virtual drive successfully, please wait several minutes.'])
        else:
            result.State('Failure')
            result.Message(['set virtual drive failed.'])
    return result


def setSNMPtrap(client, args):
    # get
    snmpinfo = ResultBean()
    editFlag = False
    versionFlag = False
    portFlag = False
    getres = RestFunc.getSnmpInfoByRest(client)
    trapinfo = {}
    if getres.get('code') == 0 and getres.get('data') is not None:
        trapinfo = getres.get('data')
    else:
        snmpinfo.State("Failure")
        snmpinfo.Message([getres.get('data')])
    if trapinfo == {}:
        return snmpinfo

    default_trap_version = trapinfo.get('trap_version')
    default_enent_severity = trapinfo.get('event_level')
    default_community = trapinfo.get('community', '')
    default_v3username = trapinfo.get('username')
    default_engine_Id = trapinfo.get('engine_id')
    default_auth = trapinfo.get('auth_protocol')
    default_auth_pass = trapinfo.get('auth_passwd', '')
    default_priv = trapinfo.get('priv_protocol')
    default_priv_pass = trapinfo.get('priv_passwd', '')
    default_system_name = trapinfo.get('system_name')
    default_system_id = trapinfo.get('system_id')
    default_location = trapinfo.get('location')
    default_contact = trapinfo.get('contact_name')
    default_os = trapinfo.get('host_os')
    if 'trap_port' in trapinfo:
        portFlag = True
        default_port = trapinfo.get('trap_port', 162)
    else:
        portFlag = False
        default_port = trapinfo.get('port', 162)
    if 'community' not in trapinfo.keys():
        versionFlag = True

    severityDict = {'all': 0, 'warning': 1, 'critical': 2}
    versionDict = {'1': 1, '2c': 2, '3': 3}
    authDict = {'NONE': 0, 'SHA': 1, 'MD5': 2}
    privDict = {'NONE': 0, 'DES': 1, 'AES': 2}
    if args.version is None:
        version = str(default_trap_version)
    else:
        version = str(args.version)
        editFlag = True
    if version == '3':
        if args.community is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['community will be ignored in v3 trap'])
            return snmpinfo
        community = default_community
        if args.v3username is None:
            v3username = default_v3username
        else:
            v3username = args.v3username
            editFlag = True
        if args.authProtocol is None:
            authProtocol = default_auth
        else:
            authProtocol = authDict.get(args.authProtocol, -1)
            editFlag = True
        if args.privProtocol is None:
            privProtocol = default_priv
        else:
            privProtocol = privDict.get(args.privProtocol, -1)
            editFlag = True
        if authProtocol == 1 or authProtocol == 2:
            if args.authPassword is None:
                if versionFlag:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['authentication password connot be empty,when authentication protocol exists'])
                    return snmpinfo
                else:
                    authPassword = default_auth_pass
            else:
                authPassword = args.authPassword
                editFlag = True
                if not RegularCheckUtil.checkPass(authPassword):
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['password is a string of 8 to 16 alpha-numeric characters'])
                    return snmpinfo
        else:
            if args.authPassword is not None:
                snmpinfo.State("Failure")
                snmpinfo.Message(['authentication password will be ignored with no authentication protocol'])
                return snmpinfo
            authPassword = default_auth_pass
        if privProtocol == 1 or privProtocol == 2:
            if args.privPassword is None:
                if versionFlag:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['privacy password connot be empty,when privacy protocol exists'])
                    return snmpinfo
                else:
                    privPassword = default_priv_pass
            else:
                privPassword = args.privPassword
                editFlag = True
                if not RegularCheckUtil.checkPass(privPassword):
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['password is a string of 8 to 16 alpha-numeric characters'])
                    return snmpinfo
        else:
            if args.privPassword is not None:
                snmpinfo.State("Failure")
                snmpinfo.Message(['privacy password will be ignored with no privacy protocol'])
                return snmpinfo
            privPassword = default_priv_pass

        if args.engineId is None:
            engineId = default_engine_Id
        else:
            engineId = args.engineId
            editFlag = True
            if not RegularCheckUtil.checkEngineId(engineId):
                snmpinfo.State("Failure")
                snmpinfo.Message(['Engine ID is a string of 10 to 48 hex characters, must even, can set NULL.'])
                return snmpinfo
    else:
        if args.community is None:
            if versionFlag:
                snmpinfo.State("Failure")
                snmpinfo.Message(['community connot be empty,when v1/v2c trap.'])
                return snmpinfo
            else:
                community = default_community
        else:
            community = args.community
            editFlag = True
        if args.v3username is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['username will be ignored in v1/v2c trap.'])
            return snmpinfo
        v3username = default_v3username
        if args.authProtocol is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['authentication will be ignored in v1/v2c trap.'])
            return snmpinfo
        authProtocol = default_auth
        if args.authPassword is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['authentication password will be ignored in v1/v2c trap.'])
            return snmpinfo
        authPassword = default_auth_pass
        if args.privProtocol is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['privacy protocol will be ignored in v1/v2c trap.'])
            return snmpinfo
        privProtocol = default_priv
        if args.privPassword is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['privacy password will be ignored in v1/v2c trap.'])
            return snmpinfo
        privPassword = default_priv_pass
        if args.engineId is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['engine Id will be ignored in v1/v2c trap.'])
            return snmpinfo
        engineId = default_engine_Id
    #
    if args.systemName is None:
        systemName = default_system_name
    else:
        systemName = args.systemName
        editFlag = True
    if args.systemID is None:
        systemID = default_system_id
    else:
        systemID = args.systemID
        editFlag = True
    if args.location is None:
        location = default_location
    else:
        location = args.location
        editFlag = True
    if args.contact is None:
        contact = default_contact
    else:
        contact = args.contact
        editFlag = True
    if args.os is None:
        os = default_os
    else:
        os = args.os
        editFlag = True
    if args.eventSeverity is None:
        eventSeverity = default_enent_severity
    else:
        eventSeverity = severityDict.get(args.eventSeverity, -1)
        editFlag = True

    if args.SNMPtrapPort is None:
        port = default_port
    else:
        if args.SNMPtrapPort < 1 or args.SNMPtrapPort > 65535:
            snmpinfo.State("Failure")
            snmpinfo.Message(['Invalid Port Number,please enter in the range of 1-65535.'])
            return snmpinfo
        else:
            port = args.SNMPtrapPort
            editFlag = True

    if editFlag == False:
        snmpinfo.State("Failure")
        snmpinfo.Message(['no setting changed!'])
        return snmpinfo

    data = {
        'trap_version': version,
        'event_level': eventSeverity,
        'community': community,
        'username': v3username,
        'engine_id': engineId,
        'auth_protocol': authProtocol,
        'auth_passwd': authPassword,
        'priv_protocol': privProtocol,
        'priv_passwd': privPassword,
        'system_name': systemName,
        'system_id': systemID,
        'location': location,
        'contact_name': contact,
        'host_os': os,
        'trap_port': port
    }
    if portFlag:
        data['trap_port'] = port
    else:
        data['port'] = port
    if versionFlag:
        data['id'] = 1
        data['encrypt_flag'] = 0

    res = RestFunc.setTrapComByRest(client, data)
    if res == {}:
        snmpinfo.State("Failure")
        snmpinfo.Message(["cannot get information"])
    elif res.get('code') == 0 and res.get('data') is not None:
        snmpinfo.State("Success")
        snmpinfo.Message([])
    elif res.get('code') != 0 and res.get('data') is not None:
        snmpinfo.State("Failure")
        snmpinfo.Message([res.get('data')])
    else:
        snmpinfo.State("Failure")
        snmpinfo.Message(["get information error, error code " + str(res.get('code'))])
    return snmpinfo


def getAlertPolicy(client, args):
    # get
    res = RestFunc.getLanDestinationsByRest(client)
    snmpinfo = ResultBean()
    Addr = {}
    if res == {}:
        snmpinfo.State("Failure")
        snmpinfo.Message(["cannot get lan destination information"])
    elif res.get('code') == 0 and res.get('data') is not None:
        data = res.get('data')
        dlist = []
        for item in data:
            target = ""
            if item['destination_type'] == 'snmp':
                target = item['destination_address']
            elif item['destination_type'] == 'email':
                target = item['name']
            elif item['destination_type'] == 'snmpdomain':
                target = item['destination_domain']
            id = item['id']  # 目的id
            Addr[id] = {'target': target, 'type': item['destination_type'],
                        'channel_id': item['channel_id']
                        }

        ares = RestFunc.getAlertPoliciesByRest(client)
        if ares == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get alert policy information"])
        elif ares.get('code') == 0 and ares.get('data') is not None:
            adata = ares.get('data')
            alist = []
            for i in range(3):
                item = adata[i]
                dt = DestinationTXBean()
                dt.Id(item['id'])
                if item['enable_policy'] == 0:
                    dt.Enable('disable')
                else:
                    dt.Enable('enable')

                if item['channel_number'] == 8:
                    type = 'Shared'
                elif item['channel_number'] == 1:
                    if len(Addr) > 15:
                        type = 'Dedicated'
                    else:
                        # 绑定网卡
                        type = 'Bond'
                else:
                    type = 'Unknown'
                dt.LanChannel(type)

                if type == 'Shared':
                    desType = Addr[i + 1]['type']
                    target = Addr[i + 1]['target']
                elif type == 'Dedicated':
                    desType = Addr[i + 1 + 15]['type']
                    target = Addr[i + 1 + 15]['target']
                elif type == 'Bond':
                    desType = Addr[i + 1]['type']
                    target = Addr[i + 1]['target']
                else:
                    desType = 'Unknown'
                    target = 'Unknown'
                dt.AlertType(desType)
                dt.Destination(target)
                alist.append(dt.dict)
            snmpinfo.State("Success")
            snmpinfo.Message([alist])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get alert policy information error"])
    elif res.get('code') != 0 and res.get('data') is not None:
        snmpinfo.State("Failure")
        snmpinfo.Message([res.get('data')])
    else:
        snmpinfo.State("Failure")
        snmpinfo.Message(["get lan destination information error"])
    return snmpinfo


def setAlertPolicy(client, args):
    snmpinfo = getAlertPolicy(client, args)
    defaultTag = True
    if snmpinfo.State == 'Success':
        data = snmpinfo.Message[0]
        for item in data:
            id = item['Id']
            if id == args.id:
                defaultTag = False
                default_id = item['ID']
                default_status = item['Status']
                default_channel = item['LanChannel']
                default_type = item['AlertType']
                default_target = item['Destination']
    snmpinfo = ResultBean()
    if defaultTag:
        snmpinfo.State("Failure")
        snmpinfo.Message(['get alert policy error'])
        return snmpinfo
    if args.status == 'enable':
        status = 1
    elif args.status == 'disable':
        status = 0
    else:
        status = default_status
    if status == 0:
        if args.type is not None or args.destination is not None or args.channel is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message(['alert policy is disabled, please enable it first.'])
            return snmpinfo

    # lan channel
    if args.channel == 'shared':
        channel = 8
    elif args.channel == 'dedicated':
        channel = 1
    elif args.channel is None:
        channel = default_channel
    else:
        snmpinfo.State("Failure")
        snmpinfo.Message(['argument -L: the parameter is 1 or 8.'])
        return snmpinfo

    if args.type is None:
        type = default_type
    else:
        type = args.type

    destination_snmp = ""
    destination_email = ""
    destination_domain = ""
    if type == "snmp":
        if args.destination is None:
            destination_snmp = default_target
        else:
            destination_snmp = args.destination
        if not RegularCheckUtil.checkIP(destination_snmp):
            snmpinfo.State("Failure")
            snmpinfo.Message(['destination should be ip,when type is snmp.'])
            return snmpinfo
    elif type == "snmpdomain":
        if args.destination is None:
            destination_domain = default_target
        else:
            destination_domain = args.destination
        if not RegularCheckUtil.checkDomainName(destination_domain):
            snmpinfo.State("Failure")
            snmpinfo.Message(['destination should be domain,when type is snmpdomain.'])
            return snmpinfo
    else:
        if args.destination is None:
            destination_email = default_target
        else:
            destination_email = args.destination
        responds = RestFunc.getUserByRest(client)
        userList = {}
        if res.get('code') == 0 and res.get('data') is not None:
            for itemU in responds['data']:
                if itemU == {}:
                    continue
                userList[itemU.get('name', 'name')] = itemU.get('email_id', '')
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(['get user info error.'])
            return snmpinfo
        if destination_email == "":
            snmpinfo.State("Failure")
            snmpinfo.Message(['destination should be username,type getuser to get legal username.'])
            return snmpinfo
        if destination_email not in userList:
            snmpinfo.State("Failure")
            snmpinfo.Message(
                ['user name ' + destination_email + ' does not exist,type getuser to get legal username.'])
            return snmpinfo

    data = {
        'id': args.id,
        'enable_policy': status,
        'policy_action': "always_send_alert",
        'channel_number': channel,
        'alert_string': 0,
        'alert_string_key': "0",
        'destination_id': str(args.id),
        'policy_group': str(args.id)
    }

    r = RestFunc.getAlertPoliciesByRest(client, data)
    if res.get('code') != 0:
        snmpinfo.State("Failure")
        snmpinfo.Message(['can not set alert policies.'])
        return snmpinfo

    data = {
        "id": default_id,
        "channel_id": args.id,
        "destination_address": destination_snmp,
        "lan_channel": channel,
        "destination_type": type,
        "message": "",
        "destination_domain": destination_domain,
        "name": destination_email,
        "subject": ""
    }
    r = RestFunc.setLanDestinationsByRest(client, default_id, data)
    if r.get('code') == 0 and r.get('data') is not None:
        snmpinfo.State("Success")
        snmpinfo.Message(['set alert policy Success.'])
        return snmpinfo
    else:
        snmpinfo.State("Failure")
        snmpinfo.Message(['can not set lan destinations info.'])
        return snmpinfo
    return snmpinfo


def setNTP(client, args):
    result = ResultBean()
    if args.autoDate is None and args.ntpTime is None and args.timeZone is None and args.NTPServer1 is None and args.NTPServer2 is None and args.NTPServer3 is None:
        result.State('Failure')
        result.Message(['No setting changed!'])
        return result
    # get default NTP config
    res = RestFunc.getDatetimeByRest(client)
    if res.get('code') == 0 and res.get('data') is not None:
        data = res['data']
        default_NTP_auto_date = data['auto_date']
        default_NTP_id = data['id']
        default_NTP_localized_timestamp = data['localized_timestamp']
        default_NTP_utc_minutes = data['utc_minutes']
        default_NTP_timezone = data['timezone']
        default_NTP_timestamp = data['timestamp']
        default_NTP_server1 = data['primary_ntp']
        default_NTP_server2 = data['secondary_ntp']
        default_NTP_server3 = data['third_ntp']
        if 'date_cycle' in data:
            default_NTP_date_cycle = data['date_cycle']
        else:
            default_NTP_date_cycle = None
            if args.NTPSynCycle is not None:
                result.State('Failure')
                result.Message(['NTP syn cycle does not support modification in this bmc version.'])
                return result
    else:
        result.State('Failure')
        result.Message(['can not get NTP info.'])
        return result
    default_NTP_timestamp = int(default_NTP_timestamp) + int(default_NTP_utc_minutes) * 60

    if args.autoDate == 'disable':
        auto_date = 0
    elif args.autoDate == 'enable':
        auto_date = 1
    else:
        if default_NTP_auto_date == 0:  # manual
            auto_date = 0
        else:
            auto_date = 1

    if auto_date == 0:
        if args.NTPServer1 is not None or args.NTPServer2 is not None or args.NTPServer3 is not None:
            result.State('Failure')
            result.Message(['NTPServer can not be setted when date_auto_syn is disable.'])
            return result
        if args.NTPSynCycle is not None:
            result.State('Failure')
            result.Message(['NTPSynCycle can not be setted when date_auto_syn is disable.'])
            return result
        primary_ntp = default_NTP_server1
        secondary_ntp = default_NTP_server2
        third_ntp = default_NTP_server3
        if args.ntpTime is None:
            timestamp = default_NTP_timestamp
        else:
            if len(args.ntpTime) != 14:
                result.State('Failure')
                result.Message(['time param should be 14 bits, like YYYYmmddHHMMSS, please enter again.'])
                return result
            try:
                timeArray = time.strptime(args.ntpTime, "%Y%m%d%H%M%S")
                timestamp = int(time.mktime(timeArray)) - int(time.timezone)
            except ValueError as e:
                result.State('Failure')
                result.Message(['time param should be like YYYYmmddHHMMSS, please enter again'])
                return result
    elif auto_date == 1:
        if args.ntpTime is not None:
            result.State('Failure')
            result.Message(['time can not be setted when date_auto_syn is enable'])
            return result
        timestamp = default_NTP_timestamp
        if args.NTPSynCycle is not None:
            if args.NTPSynCycle < 5 or args.NTPSynCycle > 1440:
                result.State('Failure')
                result.Message(['syn cycle should between 5-1440, please enter again'])
                return result
            default_NTP_date_cycle = args.NTPSynCycle
        if args.NTPServer1 is not None:
            if RegularCheckUtil.checkIP46d(args.NTPServer1):
                primary_ntp = args.NTPServer1
            else:
                result.State('Failure')
                result.Message(['ntp server should be ipv4 or ipv6 or FQDN (Fully qualified domain name) format, please enter again'])
                return result
        else:
            primary_ntp = default_NTP_server1
        if args.NTPServer2 is not None:
            if RegularCheckUtil.checkIP46d(args.NTPServer2):
                secondary_ntp = args.NTPServer2
            else:
                result.State('Failure')
                result.Message(['ntp server should be ipv4 or ipv6 or FQDN (Fully qualified domain name) format, please enter again'])
                return result
        else:
            secondary_ntp = default_NTP_server2
        if args.NTPServer3 is not None:
            if RegularCheckUtil.checkIP46d(args.NTPServer3):
                third_ntp = args.NTPServer3
            else:
                result.State('Failure')
                result.Message(['ntp server should be ipv4 or ipv6 or FQDN (Fully qualified domain name) format, please enter again'])
                return result
        else:
            third_ntp = default_NTP_server3
    if args.timeZone is not None:
        if RegularCheckUtil.checkZone(args.timeZone):
            NTP_UTC_zone = int(float(args.timeZone) * 60)
        else:
            result.State('Failure')
            result.Message([str(args.timeZone) + ' is illegal, please chose from {-12, -11.5, -11, ... ,11,11.5,12}'])
            return result
    else:
        NTP_UTC_zone = default_NTP_utc_minutes

    data = {
        'auto_date': auto_date,
        'id': default_NTP_id,
        'localized_timestamp': default_NTP_localized_timestamp,
        'primary_ntp': primary_ntp,
        'secondary_ntp': secondary_ntp,
        'third_ntp': third_ntp,
        'timestamp': timestamp,
        'timezone': "Baghdad",
        'utc_minutes': NTP_UTC_zone,
    }
    if default_NTP_date_cycle is not None:
        data['date_cycle'] = default_NTP_date_cycle
    res = RestFunc.setTimeByRest(client, data)
    if res.get('code') == 0 and res.get('data') is not None:
        result.State('Success')
        result.Message(['set NTP success.'])
        return result
    else:
        result.State('Failure')
        result.Message(['set NTP failed'])
        return result
    return result


def setSNMP(client, args):
    result = ResultBean()
    dict_snmp = {
        'SNMP_VERSION_ALL': 1,
        'SNMP_VERSION_DETAIL_BIT': 128,
        'SNMP_VERSION_V1_READ_BIT': 1,
        'SNMP_VERSION_V1_WRITE_BIT': 16,
        'SNMP_VERSION_V2C_READ_BIT': 2,
        'SNMP_VERSION_V2C_WRITE_BIT': 32,
        'SNMP_VERSION_V3_ONLY': 0,
        'SNMP_VERSION_V3_READ_BIT': 4,
        'SNMP_VERSION_V3_WRITE_BIT': 64,
    }
    authentication_dict = {0: "NONE", 1: "SHA", 2: "MD5"}
    privacy_dict = {0: "NONE", 1: "DES", 2: "AES"}
    # get default snmp GET/SET config
    responds = RestFunc.getSnmpM5ByRest(client)
    if responds.get('code') == 0 and responds.get('data') is not None:
        result = responds.json()
        default_username = result.get('username', '')
        default_auth_protocol = result.get('auth_protocol', '')
        default_priv_protocol = result.get('priv_protocol', '')
        if 'version' in result:
            version = result.get('version')
            snmpv1writeenable = False
            snmpv1readenable = False
            snmpv2cwriteenable = False
            snmpv2creadenable = False
            snmpv3writeenable = False
            snmpv3readenable = False
            if version == dict_snmp['SNMP_VERSION_V3_ONLY'] or version == (dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V3_READ_BIT'] | dict_snmp['SNMP_VERSION_V3_WRITE_BIT']):
                versiondisp = 2
                snmpv3writeenable = True
                snmpv3readenable = True
            elif version == (dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V2C_READ_BIT'] | dict_snmp['SNMP_VERSION_V2C_WRITE_BIT']):
                versiondisp = 1
                snmpv2cwriteenable = True
                snmpv2creadenable = True
            elif version == (dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V1_READ_BIT'] | dict_snmp['SNMP_VERSION_V1_WRITE_BIT']):
                versiondisp = 0
                snmpv1writeenable = True
                snmpv1readenable = True
            elif version == dict_snmp['SNMP_VERSION_V3_ONLY'] or version == (dict_snmp['SNMP_VERSION_DETAIL_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V3_READ_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V3_WRITE_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V2C_READ_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V2C_WRITE_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V2C_READ_BIT']
                                                                             | dict_snmp['SNMP_VERSION_V2C_WRITE_BIT']):
                versiondisp = 3
                snmpv1writeenable = True
                snmpv1readenable = True
                snmpv2cwriteenable = True
                snmpv2creadenable = True
                snmpv3writeenable = True
                snmpv3readenable = True
            else:
                versiondisp = 4
                if (version & dict_snmp['SNMP_VERSION_V1_READ_BIT'] != 0):
                    snmpv1readenable = True
                if (version & dict_snmp['SNMP_VERSION_V2C_READ_BIT'] != 0):
                    snmpv2creadenable = True
                if (version & dict_snmp['SNMP_VERSION_V3_READ_BIT'] != 0):
                    snmpv3readenable = True
                if (version & dict_snmp['SNMP_VERSION_V1_WRITE_BIT'] != 0):
                    snmpv1writeenable = True
                if (version & dict_snmp['SNMP_VERSION_V2C_WRITE_BIT'] != 0):
                    snmpv2cwriteenable = True
                if (version & dict_snmp['SNMP_VERSION_V3_WRITE_BIT'] != 0):
                    snmpv3writeenable = True
            if args.version is None:
                args.version = versiondisp
            if args.version != 4 and args.snmpstatus is not None:
                result.State('Failure')
                result.Message(['SNMP read/write status will be ignored with no SNMP trap version'])
                return result
            if args.snmpstatus is not None:
                snmpv1writeenable = False
                snmpv1readenable = False
                snmpv2cwriteenable = False
                snmpv2creadenable = False
                snmpv3writeenable = False
                snmpv3readenable = False
                dict_status = {'v1get': 'snmpv1readenable', 'v1set': 'snmpv1writeenable', 'v2cget': 'snmpv2creadenable',
                               'v2cset': 'snmpv2cwriteenable', 'v3get': 'snmpv3readenable', 'v3set': 'snmpv3writeenable'}
                snmps = str(args.snmpstatus).split(',')
                for snmp in snmps:
                    if snmp not in dict_status:
                        result.State('Failure')
                        result.Message('Invalid snmp status.')
                        return result
                    if 'snmpv1readenable' == dict_status[snmp]:
                        snmpv1readenable = True
                    elif 'snmpv2creadenable' == dict_status[snmp]:
                        snmpv2creadenable = True
                    elif 'snmpv3readenable' == dict_status[snmp]:
                        snmpv3readenable = True
                    elif 'snmpv1writeenable' == dict_status[snmp]:
                        snmpv1writeenable = True
                    elif 'snmpv2cwriteenable' == dict_status[snmp]:
                        snmpv2cwriteenable = True
                    elif 'snmpv3writeenable' == dict_status[snmp]:
                        snmpv3writeenable = True
            if args.version == 0:
                version = dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V1_READ_BIT'] | dict_snmp[
                    'SNMP_VERSION_V1_WRITE_BIT']
            elif args.version == 1:
                version = dict_snmp['SNMP_VERSION_DETAIL_BIT'] | dict_snmp['SNMP_VERSION_V2C_READ_BIT'] | dict_snmp[
                    'SNMP_VERSION_V2C_WRITE_BIT']
            elif args.version == 2:
                version = dict_snmp['SNMP_VERSION_V3_ONLY']
            elif args.version == 3:
                version = dict_snmp['SNMP_VERSION_ALL']
            else:
                version = dict_snmp['SNMP_VERSION_DETAIL_BIT']
                if snmpv1readenable:
                    version = version | dict_snmp['SNMP_VERSION_V1_READ_BIT']
                if snmpv2creadenable:
                    version = version | dict_snmp['SNMP_VERSION_V2C_READ_BIT']
                if snmpv3readenable:
                    version = version | dict_snmp['SNMP_VERSION_V3_READ_BIT']
                if snmpv1writeenable:
                    version = version | dict_snmp['SNMP_VERSION_V1_WRITE_BIT']
                if snmpv2cwriteenable:
                    version = version | dict_snmp['SNMP_VERSION_V2C_WRITE_BIT']
                if snmpv3writeenable:
                    version = version | dict_snmp['SNMP_VERSION_V3_WRITE_BIT']
            community = ''
            if (snmpv1readenable or snmpv2creadenable or snmpv1writeenable or snmpv2cwriteenable) and not (snmpv3readenable or snmpv3writeenable):
                if args.community is None:
                    result.State('Failure')
                    result.Message(['community connot be empty,when v1/v2c or v1get/v1set/v2cget/v2cset.'])
                    return result
                community = RestFunc.Encrypt(args.community)
                if args.v3username is not None:
                    result.State('Failure')
                    result.Message(['username will be ignored in v1/v2c trap.'])
                    return result
                username = default_username
                if args.authProtocol is not None:
                    result.State('Failure')
                    result.Message(['authentication will be ignored in v1/v2c trap.'])
                    return result
                authProtocol = default_auth_protocol
                if args.authPassword is not None:
                    result.State('Failure')
                    result.Message(['authentication password will be ignored in v1/v2c trap.'])
                    return result
                authPassword = ''
                if args.privacy is not None:
                    result.State('Failure')
                    result.Message(['privacy will be ignored in v1/v2c trap.'])
                    return result
                privacy = default_priv_protocol
                if args.privPassword is not None:
                    result.State('Failure')
                    result.Message(['privacy password will be ignored in v1/v2c trap.'])
                    return result
                privPassword = ''
            elif (snmpv3readenable or snmpv3writeenable) and not (snmpv1readenable or snmpv2creadenable or snmpv1writeenable or snmpv2cwriteenable):
                if args.community is not None:
                    result.State('Failure')
                    result.Message(['community will be ignored in v3 or v3get/v3set.'])
                    return result
                if args.v3username is None:
                    username = default_username
                else:
                    username = args.v3username
                if args.authProtocol is None:
                    authProtocol = default_auth_protocol
                else:
                    authProtocol = authentication_dict.get(args.authProtocol)
                if args.privacy is None:
                    privacy = default_priv_protocol
                else:
                    privacy = privacy_dict.get(args.privacy)
                authPassword = ''
                if authProtocol == 1 or authProtocol == 2:
                    if args.authPassword is None:
                        result.State('Failure')
                        result.Message(['authentication password connot be empty,when authentication protocol exists.'])
                        return result
                    else:
                        authPassword = args.authPassword
                        if not RegularCheckUtil.checkPass(authPassword):
                            result.State('Failure')
                            result.Message(['password is a string of 8 to 16 alpha-numeric characters.'])
                            return result
                        authPassword = RestFunc.Encrypt(authPassword)
                else:
                    if args.authPassword is not None:
                        result.State('Failure')
                        result.Message(['authentication password will be ignored with no authentication protocol.'])
                        return result
                privPassword = ''
                if privacy == 1 or privacy == 2:
                    if args.privPassword is None:
                        result.State('Failure')
                        result.Message(['privacy password connot be empty,when privacy protocol exists.'])
                        return result
                    else:
                        privPassword = args.privPassword
                        if not RegularCheckUtil.checkPass(privPassword):
                            result.State('Failure')
                            result.Message(['password is a string of 8 to 16 alpha-numeric characters.'])
                            return result
                        privPassword = RestFunc.Encrypt(privPassword)
                else:
                    if args.privPassword is not None:
                        result.State('Failure')
                        result.Message(['privacy password will be ignored with no privacy protocol.'])
                        return result
            else:
                if args.community is None:
                    result.State('Failure')
                    result.Message(['community connot be empty,when v1/v2c or v1get/v1set/v2cget/v2cset.'])
                    return result
                community = RestFunc.Encrypt(args.community)
                if args.v3username is None:
                    username = default_username
                else:
                    username = args.v3username
                if args.authProtocol is None:
                    authProtocol = default_auth_protocol
                else:
                    authProtocol = authentication_dict.get(args.authProtocol)
                if args.privacy is None:
                    privacy = default_priv_protocol
                else:
                    privacy = privacy_dict.get(args.privacy)
                authPassword = ''
                if authProtocol == 1 or authProtocol == 2:
                    if args.authPassword is None:
                        result.State('Failure')
                        result.Message(['authentication password connot be empty,when authentication protocol exists.'])
                        return result
                    else:
                        authPassword = args.authPassword
                        if not RegularCheckUtil.checkPass(authPassword):
                            result.State('Failure')
                            result.Message('password is a string of 8 to 16 alpha-numeric characters.')
                            return result
                        authPassword = RestFunc.Encrypt(authPassword)
                else:
                    if args.authPassword is not None:
                        result.State('Failure')
                        result.Message(['authentication password will be ignored with no authentication protocol.'])
                        return result
                privPassword = ''
                if privacy == 1 or privacy == 2:
                    if args.privPassword is None:
                        result.State('Failure')
                        result.Message(['privacy password connot be empty,when privacy protocol exists.'])
                        return result
                    else:
                        privPassword = args.privPassword
                        if not RegularCheckUtil.checkPass(privPassword):
                            result.State('Failure')
                            result.Message(['password is a string of 8 to 16 alpha-numeric characters.'])
                            return result
                        privPassword = RestFunc.Encrypt(privPassword)
                else:
                    if args.privPassword is not None:
                        result.State('Failure')
                        result.Message(['privacy password will be ignored with no privacy protocol.'])
                        return result
            data = {
                "version": version,
                "community": community,
                "username": username,
                "auth_protocol": authProtocol,
                "auth_passwd": authPassword,
                "priv_protocol": privacy,
                "priv_passwd": privPassword,
                "versiondisp": args.version,
                "encrypt_flag": 2
            }
        else:
            if args.version is not None or args.snmpstatus is not None:
                result.State('Failure')
                result.Message(['version or snmpstatus parameters cannot be set for this model .'])
                return result
            if args.community is None:
                result.State('Failure')
                result.Message(['community connot be empty.'])
                return result
            community = RestFunc.Encrypt(args.community)
            if args.username is None:
                username = default_username
            else:
                username = args.v3username
            if args.authProtocol is None:
                authProtocol = default_auth_protocol
            else:
                authProtocol = authentication_dict.get(args.authProtocol)
            if args.privacy is None:
                privacy = default_priv_protocol
            else:
                privacy = privacy_dict.get(args.privacy)
            authPassword = ''
            if authProtocol == 1 or authProtocol == 2:
                if args.authPassword is None:
                    result.State('Failure')
                    result.Message(['authentication password connot be empty,when authentication protocol exists.'])
                    return result
                else:
                    authPassword = args.authPassword
                    if not RegularCheckUtil.checkPass(authPassword):
                        result.State('Failure')
                        result.Message(['password is a string of 8 to 16 alpha-numeric characters.'])
                        return result
                    authPassword = RestFunc.Encrypt(authPassword)
            else:
                if args.authPassword is not None:
                    result.State('Failure')
                    result.Message(['authentication password will be ignored with no authentication protocol.'])
                    return result
            privPassword = ''
            if privacy == 1 or privacy == 2:
                if args.privPassword is None:
                    result.State('Failure')
                    result.Message(['privacy password connot be empty,when privacy protocol exists.'])
                    return result
                else:
                    privPassword = args.privPassword
                    if not RegularCheckUtil.checkPass(privPassword):
                        result.State('Failure')
                        result.Message(['password is a string of 8 to 16 alpha-numeric characters.'])
                        return result
                    privPassword = RestFunc.Encrypt(privPassword)
            else:
                if args.privPassword is not None:
                    result.State('Failure')
                    result.Message(['privacy password will be ignored with no privacy protocol.'])
                    return result
            data = {
                "username": username,
                "auth_protocol": authProtocol,
                "priv_protocol": privacy,
                "community": community,
                "auth_passwd": authPassword,
                "priv_passwd": privPassword,
                "encrypt_flag": 2
            }
    res = RestFunc.setSnmpM5ByRest(client, snmp)
    if res.get('code') == 0 and res.get('data') is not None:
        result.State('Success')
        result.Message(['SNMP GET/SET configuration has been modified successfully.'])
    else:
        result.State('Failure')
        result.Message(['set SNMP GET/SET configure failure.'])
    return result


def setNCSI(client, args):
    result = ResultBean()
    editFlag = False
    de_nictype = {0: 'PHY', 1: 'OCP', 2: 'PCIE', 3: 'OCPA2', 254: 'AUTO'}
    en_nictype = {'PHY': 0, 'OCP': 1, 'PCIE': 2, 'OCPA2': 3, 'AUTO': 254}
    nicmode = {1: 'Auto Failover', 0: 'Manual Switch'}
    # 获取默认配置
    ncsiinterfaces = RestFunc.getNCSIM5ByRest()
    if ncsiinterfaces.get('code') == 0 and ncsiinterfaces.get('data') is not None:
        data = ncsiinterfaces['data']
        ncsi_switch_modes_list = []
        for item in data:
            default_interface_name = str(item['interface_name'])
            default_channel_number = int(item['channel_number'])
            default_nic_type = str(item['nic_type'])
            default_package_id = str(item['package_id'])
            default_id = str(item['id'])
            default_total_channels = int(item['total_channels'])
            if "ncsi_switch_modes" in item:
                ncsi_switch_modes_list = item['ncsi_switch_modes']
            break
    else:
        result.State('Failure')
        result.Message(['can not get NCSI settings.'])
        return result

    interface_name = default_interface_name
    channel_number = default_channel_number
    package_id = default_package_id
    nic_type = default_nic_type
    id = default_id
    total_channels = default_total_channels

    if args.nic_type is not None:
        if ncsi_switch_modes_list == []:
            if args.nic_type == "auto":
                result.State('Failure')
                result.Message(['auto is not supported.'])
                return result
        else:
            nictypelist = []
            for nictype in ncsi_switch_modes_list:
                nictypelist.append(de_nictype.get(nictype["switch_mode"], ''))
            if args.nic_type not in nictypelist:
                result.State('Failure')
                result.Message(["nic type should be in " + str(nictypelist)])
                return result
        if en_nictype.get(args.nic_type, '') != nic_type:
            nic_type = en_nictype.get(args.nic_type, '')
            editFlag = True

    ncsimode = RestFunc.getNCSIModeM5ByRest(client)
    # mode
    if ncsimode.get('code') == 0 and ncsimode.get('data') is not None:
        data = ncsimode['data']
        default_mode = data['mode']
    else:
        result.State('Failure')
        result.Message(['can not get NCSI mode'])
        return result
    mode = default_mode
    if args.mode is not None:
        if args.mode == 'manual':
            args.mode = '0'
        else:
            args.mode = '1'
        if args.mode != default_mode:
            mode = args.mode
            editFlag = True
    # package_id channel_number interface_name
    if str(mode) == '0':
        if args.interface_name is not None and args.interface_name != default_interface_name:
            result.State('Failure')
            result.Message(["Invalid interface_name,interface_name should be " + default_interface_name])
            return result
        if args.channel_number is not None and args.channel_number != default_channel_number:
            if args.channel_number >= total_channels:
                result.State('Failure')
                result.Message(["Ichannel_number is 0 - " + str(total_channels - 1)])
                return result
            channel_number = args.channel_number
            editFlag = True
    else:
        if args.interface_name is not None:
            result.State('Failure')
            result.Message(["share NIC can not be setted in 'Auto Switch' mode"])
            return result
        if args.channel_number is not None:
            result.State('Failure')
            result.Message(["channel number can not be setted in 'Auto Switch' mode"])
            return result

    if not editFlag:
        result.State('Failure')
        result.Message(["No setting changed"])
        return result

    data = {
        "id": default_id,
        "interface_name": interface_name,
        "channel_number": channel_number,
        "package_id": package_id,
        "nic_type": nic_type,
        "total_channels": default_total_channels,
        "mode": mode
    }

    r = RestFunc.setNCSIModeM5ByRest(client, data)
    if ncsimode.get('code') == 0 and ncsimode.get('data') is not None:
        result.State('Success')
        result.Message(["change NSCI complete"])
    else:
        result.State('Failure')
        result.Message(["change NSCI settings error"])
    return result


def setPsuConfig(client, args):
    result = ResultBean()
    psuinfo = RestFunc.getPsuInfo1ByRest(client)
    if psuinfo.get('code') == 0 and psuinfo.get('data') is not None:
        psuinfo = psuinfo['data']
        psuNum = len(psuinfo)
        # print(psuinfo[args.id])
        if args.id < 0 or args.id > psuNum - 1:
            result.State('Failure')
            result.Message(["power id error"])
            return result

        if psuinfo[args.id]['present'] == 0:
            result.State('Failure')
            result.Message(["this psu is not present"])
            return result
        if psuinfo[args.id]['mode'] == 85 and args.switch == 'active':
            result.State('Failure')
            result.Message(["this psu is already active, no need to set"])
            return result
        elif psuinfo[args.id]['mode'] == 14 and args.switch == 'standby':
            result.State('Failure')
            result.Message([" this psu is already standby, no need to set"])
            return result
        elif psuinfo[args.id]['mode'] == 0 and args.switch == 'normal':
            result.State('Failure')
            result.Message(["this psu is already normal, no need to set"])
            return result
    else:
        result.State('Failure')
        result.Message(["get psu config failure"])
        return result

    mode = 0
    if args.switch == 'standby':
        mode = 0
    elif args.switch == 'active':
        mode = 1
    elif args.switch == 'normal':
        mode = 2

    r = RestFunc.setPsuModeByRest(client, args.id, mode)
    if r.get('code') == 0 and r.get('data') is not None:
        result.State('Success')
        if args.switch == 'standby':
            result.Message([" switch psu {0} to standby".format(args.id)])
        elif args.switch == 'normal':
            result.Message(["switch psu {0} to normal".format(args.id)])
        else:
            result.Message(["switch psu {0} to active".format(args.id)])
    else:
        result.State('Failure')
        result.Message(["can not set psu config"])
    return result


def setPsuPeak(client, args):
    result = ResultBean()
    psuinfo = RestFunc.getPsuPeakByRest(client)
    if psuinfo.get('code') == 0 and psuinfo.get('data') is not None:
        if 'time' in psuinfo:
            time = psuinfo['time']
        else:
            time = ''
    else:
        result.State('Failure')
        result.Message(["failed to get psu peak"])
        return result
    enable = 1
    if args.status == 'disable':
        if args.time is not None:
            result.State('Failure')
            result.Message(["argument time is not necessary when argument status is disable"])
            return result
        else:
            enable = 0
    elif args.time is None:
        if time == '' or time == 0:
            result.State('Failure')
            result.Message(["argument time is required"])
            return result
    elif args.time < 1 or args.time > 600:
        result.State('Failure')
        result.Message(["time value range is 1 - 600"])
        return result
    else:
        time = args.time
    r = RestFunc.setPsuPeakByRest(client, enable, time)
    if r.get('code') == 0 and r.get('data') is not None:
        result.State('Success')
        if args.status == 'disable':
            result.Message(['Disable psu peak'])
        elif args.time is None:
            result.Message(['Enable psu peak'])
        else:
            result.Message(['set psu peak time to ' + str(time) + ' second'])
    else:
        result.State('Failure')
        result.Message(["set power peak failed"])
    return result


def setAD(client, args):
    result = ResultBean()
    if args.enable is None and args.name is None and args.code is None and args.timeout is None \
            and args.domain is None and args.addr1 is None and args.addr2 is None and args.addr3 is None:
        result.State('Failure')
        result.Message(["no setting changed!"])
        return result

    r = RestFunc.getADByRest(client)
    if r.get('code') == 0 and r.get('data') is not None:
        data = r['data']
        default_name = data['secret_username']
        default_domain = data['user_domain_name']
        default_addr1 = data['domain_controller1']
        default_addr2 = data['domain_controller2']
        default_addr3 = data['domain_controller3']
        default_enable = data['enable']
        if 'timeout' in data:
            default_timeout = data['timeout']
        else:
            # 低版本无超时时间参数
            default_timeout = -1
    else:
        result.State('Failure')
        result.Message(["failed to get AD settings."])
        return result

    if args.enable is None:
        enable = default_enable
    if args.enable == 'enable':
        enable = 1
    elif args.enable == 'disable':
        enable = 0
    else:
        enable = default_enable

    if enable == 1:
        if args.name is None:
            name = default_name
        else:
            name = args.name
            if name != "":
                if not name.isalnum():
                    result.State('Failure')
                    result.Message(["name is a string of 1 to 64 alpha-numeric characters."])
                    return result
                if not name[0].isalpha():
                    result.State('Failure')
                    result.Message(["name must start with an alphabetical character."])
                    return result
                if len(name) < 1 or len(name) > 64:
                    result.State('Failure')
                    result.Message(["name is a string of 1 to 64 alpha-numeric characters."])
                    return result
        if args.code is None:
            # 不设置密码
            code = ""
        else:
            code = args.code
            if code != "":
                if len(args.code) < 6 or len(args.code) > 127:
                    result.State('Failure')
                    result.Message(["passcode is a string of 6 to 127 characters."])
                    return result
                if code.find(" ") > -1:
                    result.State('Failure')
                    result.Message(["in passcode white space is not allowed."])
                    return result

        if name == "" and code != "":
            result.State('Failure')
            result.Message(["name canno be blank."])
            return result

        if args.domain is None:
            if default_domain == '':
                result.State('Failure')
                result.Message(["domain is required."])
                return result
            domain = default_domain
        else:
            domain = args.domain
            if not RegularCheckUtil.checkDomainName(domain):
                result.State('Failure')
                result.Message(["invalid argument domain."])
                return result
        # addr
        if args.addr1 is not None:
            addr1 = args.addr1
            if addr1 == "":
                addr1 = addr1.decode("utf-8")
            else:
                if not RegularCheckUtil.checkIP(addr1):
                    result.State('Failure')
                    result.Message(["addr1 invalid ip address."])
                    return result
        else:
            addr1 = default_addr1
        if args.addr2 is not None:
            addr2 = args.addr2
            if addr2 == "":
                addr2 = addr2.decode("utf-8")
            else:
                if not RegularCheckUtil.checkIP(addr2):
                    result.State('Failure')
                    result.Message(["addr2 invalid ip address."])
                    return result
        else:
            addr2 = default_addr2
        if args.addr3 is not None:
            addr3 = args.addr3
            if addr3 == "":
                addr3 = addr3.decode("utf-8")
            else:
                if not RegularCheckUtil.checkIP(addr3):
                    result.State('Failure')
                    result.Message(["addr3 invalid ip address."])
                    return result
        else:
            addr3 = default_addr3
        if addr1 == '' and addr2 == '' and addr3 == '':
            result.State('Failure')
            result.Message(["please input at least one server address(addr1, addr2, addr3)."])
            return result
        if addr1 == addr2 and addr1 != '':
            result.State('Failure')
            result.Message(["The Domain Controller Server is address should be different for the three servers."])
            return result
        elif addr1 == addr3 and addr1 != '':
            result.State('Failure')
            result.Message(["The Domain Controller Server is address should be different for the three servers."])
            return result
        elif addr2 == addr3 and addr2 != '':
            result.State('Failure')
            result.Message(["The Domain Controller Server is address should be different for the three servers."])
            return result
        # timeout
        if default_timeout == -1:
            if args.timeout is not None:
                result.State('Failure')
                result.Message(["timeout cannot be setted by this BMC version."])
                return result
        else:
            if args.timeout is not None:
                timeout = args.timeout
                if timeout < 15 or timeout > 300:
                    result.State('Failure')
                    result.Message(["timeout should be between 15-300."])
                    return result
            else:
                timeout = default_timeout
        data = {
            'domain_controller1': addr1,
            'domain_controller2': addr2,
            'domain_controller3': addr3,
            'enable': 1,
            'id': 1,
            'secret_username': name,
            'user_domain_name': domain
        }
        if default_timeout != -1:
            data['timeout'] = timeout
        if name == "" and code == "":
            data['secret_password'] = code
        if code != "":
            data['secret_password'] = code
    # 禁用 AD
    else:
        if args.name is not None or args.code is not None or args.timeout is not None or args.domain is not None \
                or args.addr1 is not None or args.addr2 is not None or args.addr3 is not None:
            result.State('Failure')
            result.Message(["when the status is disabled,no other parameters can be set!."])
            return result
        data = {
            'domain_controller1': default_addr1,
            'domain_controller2': default_addr2,
            'domain_controller3': default_addr3,
            'enable': 0,
            'id': 1,
            'secret_username': default_name,
            'user_domain_name': default_domain
        }
    r = RestFunc.setADByRest(client, data)
    if r.get('code') == 0 and r.get('data') is not None:
        result.State('Success')
        result.Message(["set Active Directory Configuration finished."])
    else:
        result.State('Failure')
        result.Message(["failed to set AD."])
    return result


def getADGroup(client, args):
    result = ResultBean()

    res = RestFunc.getADgroupM6(client)
    if res.get('code') == 0 and res.get('data') is not None:
        ldap_group = res.get('data')
        ldap_group_list = []
        for group in ldap_group:
            ldap_res = collections.OrderedDict()
            ldap_res['Id'] = group['id']
            ldap_res['Name'] = group['role_group_name']
            ldap_res['Domain'] = group['role_group_domain']
            ldap_res['Privilege'] = group['role_group_withoem_privilege']
            ldap_res['KVM Access'] = "Enabled" if group['role_group_kvm_privilege'] == 1 else "Disabled"
            ldap_res['VMedia Access'] = "Enabled" if group['role_group_vmedia_privilege'] == 1 else "Disabled"
            ldap_group_list.append(ldap_res)
        result.State("Success")
        result.Message([{"ADgroup": ldap_group_list}])
    else:
        result.State("Failure")
        result.Message([res.get('data')])

    return result


def delADGroup(client, args):
    result = ResultBean()
    # login
    res = getADGroup(client, args)
    user_flag = False
    if res.State == "Success":
        data = res.Message[0].get("ADgroup")
        for item in data:
            name = item.get('Name', "unknown")
            if name == args.name:
                user_flag = True
                args.id = item.get('Id', 0)
    else:
        result.State("Failure")
        result.Message([res.Message[0]])
        return result

    if not user_flag:
        result.State("Failure")
        result.Message(['No group named ' + args.name])
        return result
    res = RestFunc.delADgroupM6(client, args.id)
    if res.get('code') == 0 and res.get('data') is not None:
        result.State("Success")
        result.Message(["Delete AD role group success"])
    else:
        result.State("Failure")
        result.Message([res.get('data')])

    return result


def addADGroup(client, args):

    result = ResultBean()
    if args.name is not None:
        if not RegularCheckUtil.checkHostName(args.name):
            result.State("Failure")
            result.Message(['Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.'])
            return result

    if args.domain is not None:
        if not RegularCheckUtil.checkDomainName(args.domain):
            result.State("Failure")
            result.Message(['Domain Name is a string of 255 alpha-numeric characters.Special symbols hyphen, underscore and dot are allowed..'])
            return result
    name_exist_flag = False
    add_flag = False
    res = RestFunc.getADgroupM6(client)
    if res.get('code') == 0 and res.get('data') is not None:
        for item in res.get('data'):
            name = item.get('role_group_name', "unknown")
            if name == args.name:
                name_exist_flag = True
                break
            if name == "":
                add_flag = True
                args.id = item.get('id', 0)
                break
    else:
        result.State("Failure")
        result.Message([res.get('data')])
        return result

    if name_exist_flag:
        result.State("Failure")
        result.Message(['Group ' + args.name + ' is already exist.'])
        return result

    if not add_flag:
        result.State("Failure")
        result.Message(['AD role group is full.'])
        return result

    kvm_vm = {"enable": 1, "disable": 0}
    # priv administrator user operator oem none
    adgroup = {
        'id': args.id,
        'role_group_domain': args.domain,
        'role_group_kvm_privilege': kvm_vm.get(args.kvm.lower()),
        'role_group_name': args.name,
        'role_group_privilege': "none",
        'role_group_vmedia_privilege': kvm_vm.get(args.vm.lower()),
        'role_group_withoem_privilege': args.pri
    }
    # print(adgroup)
    set_res = RestFunc.setADgroupM6(client, adgroup)
    if set_res.get('code') == 0 and set_res.get('data') is not None:

        result.State("Success")
        result.Message(["Add AD group success."])
    else:
        result.State("Failure")
        result.Message([set_res.get('data')])

    return result


def setADGroup(client, args):

    result = ResultBean()
    # login

    name_exist_flag = False
    res = RestFunc.getADgroupM6(client)
    adgroup = None
    if res.get('code') == 0 and res.get('data') is not None:
        for item in res.get('data'):
            id = str(item.get('id', 0))
            if id == args.id:
                adgroup = item
            else:
                name = item.get('role_group_name', "unknown")
                if name == args.name:
                    name_exist_flag = True
                    break
    else:
        result.State("Failure")
        result.Message([res.get('data')])
        return result

    if name_exist_flag:
        result.State("Failure")
        result.Message(['Group ' + args.name + ' is already exist.'])
        return result

    if adgroup is None:
        result.State("Failure")
        result.Message(['Group id is not exist.' + res.get('data')])
        return result

    if args.name is not None:
        if RegularCheckUtil.checkHostName(args.name):
            adgroup['role_group_name'] = args.name
        else:
            result.State("Failure")
            result.Message(['Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.'])
            return result
    if adgroup['role_group_name'] == "":
        result.State("Failure")
        result.Message(['Group name is needed.'])
        return result

    if args.domain is not None:
        if RegularCheckUtil.checkDomainName(args.domain):
            adgroup['role_group_domain'] = args.domain
        else:
            result.State("Failure")
            result.Message(['Domain Name is a string of 255 alpha-numeric characters.Special symbols hyphen, underscore and dot are allowed.'])
            return result
    if adgroup['role_group_domain'] == "":
        result.State("Failure")
        result.Message(['Group domain is needed.'])
        return result

    if args.pri is not None:
        adgroup['role_group_withoem_privilege'] = args.pri
    if adgroup['role_group_withoem_privilege'] == "":
        result.State("Failure")
        result.Message(['Group privilege is needed.'])
        return result

    kvm_vm = {"enable": 1, "disable": 0}
    if args.kvm is not None:
        adgroup['role_group_kvm_privilege'] = kvm_vm.get(args.kvm.lower())

    if args.vm is not None:
        adgroup['role_group_vmedia_privilege'] = kvm_vm.get(args.vm.lower())

    # print(ldapgroup)
    set_res = RestFunc.setADgroupM6(client, adgroup)
    if set_res.get('code') == 0 and set_res.get('data') is not None:
        result.State("Success")
        result.Message(["Set AD group success."])
    else:
        result.State("Failure")
        result.Message([set_res.get('data')])

    return result


def getLDAP(client, args):
    result = ResultBean()

    res = RestFunc.getLDAPM6(client)
    # {'enable': 0, 'common_name_type': 'ip', 'search_base': '', 'encryption_type': 0, 'server_address': '', 'bind_dn': '', 'user_login_attribute': 'cn', 'port': 389, 'id': 1}
    if res.get('code') == 0 and res.get('data') is not None:
        ldap_raw = res.get('data')

        ldap_res = collections.OrderedDict()
        ldap_res['AuthenState'] = 'Enable' if ldap_raw['enable'] == 1 else "Disabled"
        encryption_dict = {0: "No Encryption", 1: "SSL", 2: "StartTLS"}
        ldap_res['Encryption'] = encryption_dict.get(ldap_raw['encryption_type'])
        ldap_res['CommonNameType'] = ldap_raw['common_name_type']
        ldap_res['ServerAddress'] = ldap_raw['server_address']
        ldap_res['Port'] = ldap_raw['port']
        ldap_res['BindDN'] = ldap_raw['bind_dn']
        ldap_res['SearchBase'] = ldap_raw['search_base']
        ldap_res['LoginAttr'] = ldap_raw['user_login_attribute']

        result.State("Success")
        result.Message([{"LDAP": ldap_res}])
    else:
        result.State("Failure")
        result.Message([res.get('data')])

    return result


def setLDAP(client, args):
    result = ResultBean()
    res = RestFunc.getLDAPM6(client)
    if res.get('code') == 0 and res.get('data') is not None:
        data = res['data']
        dn = data['bind_dn']
        base = data['search_base']
        addr = data['server_address']
        encryType = data['encryption_type']
        port = data['port']
        attr = data['user_login_attribute']
    else:
        result.State('Failure')
        result.Message(['failed to get ldap settings'])
        return result

    if args.enable == 'enable' or args.enable is None:
        enable = 1
    else:
        enable = 0

    if enable == 1:
        if args.encry is None:
            if encryType == '':
                result.State('Failure')
                result.Message(['argument encry is required'])
                return result
            else:
                args.encry = encryType
        if args.address is None:
            if addr == '':
                result.State('Failure')
                result.Message(['argument address is required'])
                return result
            else:
                args.address = addr
        else:
            if not RegularCheckUtil.checkIP(args.address):
                result.State('Failure')
                result.Message(['invalid address value'])
                return result
        if args.server_port is None:
            if port == '':
                result.State('Failure')
                result.Message(['argument server_port is required'])
                return result
            else:
                args.server_port = port
        else:
            if args.server_port < 1 or args.server_port > 65535:
                result.State('Failure')
                result.Message(['argument server_port range in 1-65535'])
                return result
        if args.dn is None:
            if dn == '':
                result.State('Failure')
                result.Message(['argument Bind DN is required'])
                return result
            else:
                args.dn = dn
        else:
            if not args.dn[0].isalpha():
                result.State('Failure')
                result.Message(['Bind DN must start with an alphabetical character'])
                return result
            if len(args.dn) < 4 or len(args.dn) > 64:
                result.State('Failure')
                result.Message(['Bind DN is a string of 4 to 64 alpha-numeric characters'])
                return result
        if args.code is None:
            result.State('Failure')
            result.Message(['argument password is required'])
            return result
        else:
            if len(args.code) < 1 or len(args.code) > 48:
                result.State('Failure')
                result.Message(['password is a string of 1 to 48 characters'])
                return result
        if args.base is None:
            if base == '':
                result.State('Failure')
                result.Message(['argument base is required'])
                return result
            else:
                args.base = base
        else:
            if not args.base[0].isalpha():
                result.State('Failure')
                result.Message(['base must start with an alphabetical character'])
                return result
            if len(args.base) < 4 or len(args.base) > 64:
                result.State('Failure')
                result.Message(['Search base is a string of 4 to 64 alpha-numeric characters'])
                return result
        if args.attr is None:
            if attr == '':
                result.State('Failure')
                result.Message(['argument attr is required'])
                return result
            else:
                args.attr = attr

        encry = {'no': 0, 'SSL': 1, 'StartTLS': 2, 0: 0, 1: 1, 2: 2}
        if args.encry == 'StartTLS' or encryType == 2:
            if args.cn is None:
                common_name_type = 'ip'
            else:
                common_name_type = args.cn
            if args.ca is not None:
                if RegularCheckUtil.checkFile(args.ca):
                    file1 = args.ca
                else:
                    result.State('Failure')
                    result.Message(['incorrect ca file'])
                    return result
            else:
                file1 = None

            if args.ce is not None:
                if RegularCheckUtil.checkFile(args.ce):
                    file2 = args.ce
                else:
                    result.State('Failure')
                    result.Message(['incorrect ce file'])
                    return result
            else:
                file2 = None

            if args.pk is not None:
                if RegularCheckUtil.checkFile(args.pk):
                    file3 = args.pk
                else:
                    result.State('Failure')
                    result.Message(['incorrect pk file'])
                    return result
            else:
                file3 = None
            data = {
                'bind_dn': args.dn,
                'ca_certificate_file': file1,
                'certificate_file': file2,
                'common_name_type': common_name_type,
                'enable': 1,
                'encryption_type': "2",
                'id': 1,
                'password': args.code,
                'port': args.server_port,
                'private_key': file3,
                'search_base': args.base,
                'server_address': args.address,
                'user_login_attribute': args.attr

            }
            if file1:
                file1 = open(file1, 'rb')
            else:
                file1 = ''

            if file2:
                file2 = open(file2, 'rb')
            else:
                file2 = ''

            if file3:
                file3 = open(file3, 'rb')
            else:
                file3 = ''

            try:
                files = {
                    'ca_certificate_file': file1,
                    'certificate_file': file2,
                    'private_key': file3
                }
                # 修改header
                r = RestFunc.setLDAPFile(client, files)
                if res.get('code') != 0:
                    result.State('Failure')
                    result.Message(['failed to set LDAP certificates'])
                    return result
            except (IOError, TypeError):
                result.State('Failure')
                result.Message(['failed to set LDAP'])
                return result
        else:
            if args.cn is not None or args.ca is not None or args.ce is not None or args.pk is not None:
                result.State('Failure')
                result.Message(['argument cn,ca,ce,pk is needed when encry is StartTLS'])
                return result
            data = {
                'bind_dn': args.dn,
                'common_name_type': 'ip',
                'enable': 1,
                'encryption_type': encry[args.encry],
                'id': 1,
                'password': args.code,
                'port': args.server_port,
                'search_base': args.base,
                'server_address': args.address,
                'user_login_attribute': args.attr
            }
    else:
        if args.address is not None or args.server_port is not None or args.dn is not None \
                or args.code is not None or args.base is not None or args.attr is not None:
            result.State('Failure')
            result.Message(['when the status is disabled,no other parameters can be set!'])
            return result
        data = {
            'bind_dn': dn,
            'common_name_type': "ip",
            'enable': 0,
            'encryption_type': encryType,
            'id': 1,
            'port': port,
            'search_base': base,
            'server_address': addr,
            'user_login_attribute': attr
        }
    res = RestFunc.setLDAP(client, data)
    if res.get('code') == 0 and res.get('data') is not None:
        result.State('Success')
        result.Message(['set LDAP finished'])
    else:
        result.State('Failure')
        result.Message(['failed to set LDAP'])
    return result


def getLDAPGroup(client, args):
    result = ResultBean()
    # login

    res = RestFunc.getLDAPgroupM6(client)
    if res.get('code') == 0 and res.get('data') is not None:
        ldap_group = res.get('data')
        ldap_group_list = []
        for group in ldap_group:
            ldap_res = collections.OrderedDict()
            ldap_res['Id'] = group['id']
            ldap_res['Name'] = group['role_group_name']
            ldap_res['Domain'] = group['role_group_domain']
            ldap_res['Privilege'] = group['role_group_withoem_privilege']
            ldap_res['KVM Access'] = "Enabled" if group['role_group_kvm_privilege'] == 1 else "Disabled"
            ldap_res['VMedia Access'] = "Enabled" if group['role_group_vmedia_privilege'] == 1 else "Disabled"
            ldap_group_list.append(ldap_res)
        result.State("Success")
        result.Message([{"LDAPgroup": ldap_group_list}])
    else:
        result.State("Failure")
        result.Message([res.get('data')])

    return result


def delLDAPGroup(client, args):
    result = ResultBean()
    res = getLDAPGroup(client, args)
    user_flag = False
    if res.State == "Success":
        data = res.Message[0].get("LDAPgroup")
        for item in data:
            name = item.get('Name', "unknown")
            if name == args.name:
                user_flag = True
                args.id = item.get('Id', 0)
    else:

        result.State("Failure")
        result.Message([res.Message[0]])
        return result
    if not user_flag:
        result.State("Failure")
        result.Message(['No group named ' + args.name])
        return result
    res = RestFunc.delLDAPgroupM6(client, args.id)
    if res.get('code') == 0 and res.get('data') is not None:
        result.State("Success")
        result.Message(["Delete LDAP role group success"])
    else:
        result.State("Failure")
        result.Message([res.get('data')])

    return result


def addLDAPGroup(client, args):
    result = ResultBean()
    if args.name is not None:
        if not RegularCheckUtil.checkHostName(args.name):
            result.State("Failure")
            result.Message(['Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.'])
            return result

    if args.base is not None:
        if not RegularCheckUtil.checkBase(args.base):
            result.State("Failure")
            result.Message(['Searchbase is a string of 4 to 64 alpha-numeric characters.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed..Example: cn=manager,ou=login, dc=domain,dc=com'])
            return result

    name_exist_flag = False
    add_flag = False
    res = RestFunc.getLDAPgroupM6(client)
    if res.get('code') == 0 and res.get('data') is not None:
        for item in res.get('data'):
            name = item.get('role_group_name', "unknown")
            if name == args.name:
                name_exist_flag = True
                break
            if name == "":
                add_flag = True
                args.id = item.get('id', 0)
                break
    else:
        result.State("Failure")
        result.Message([res.get('data')])
        return result

    if name_exist_flag:
        result.State("Failure")
        result.Message(['Group ' + args.name + ' is already exist.'])
        return result

    if not add_flag:
        result.State("Failure")
        result.Message(['LDAP role group is full.'])
        return result

    kvm_vm = {"enable": 1, "disable": 0}
    # priv administrator user operator oem none
    ldapgroup = {
        'id': args.id,
        'role_group_domain': args.base,
        'role_group_kvm_privilege': kvm_vm.get(args.kvm.lower()),
        'role_group_name': args.name,
        'role_group_privilege': "none",
        'role_group_vmedia_privilege': kvm_vm.get(args.vm.lower()),
        'role_group_withoem_privilege': args.pri
    }
    # print(ldapgroup)
    set_res = RestFunc.setLDAPgroupM6(client, ldapgroup)
    if set_res.get('code') == 0 and set_res.get('data') is not None:

        result.State("Success")
        result.Message(["Add LDAP group success."])
    else:
        result.State("Failure")
        result.Message([set_res.get('data')])

    return result


def setLDAPGroup(client, args):
    result = ResultBean()
    name_exist_flag = False
    res = RestFunc.getLDAPgroupM6(client)
    ldapgroup = None
    if res.get('code') == 0 and res.get('data') is not None:
        for item in res.get('data'):
            id = str(item.get('id', 0))
            if id == args.id:
                ldapgroup = item
            else:
                name = item.get('role_group_name', "unknown")
                if name == args.name:
                    name_exist_flag = True
                    break
    else:
        result.State("Failure")
        result.Message([res.get('data')])
        return result

    if name_exist_flag:
        result.State("Failure")
        result.Message(['Group ' + args.name + ' is already exist.'])
        return result

    if ldapgroup is None:
        result.State("Failure")
        result.Message(['Group id is not exist.' + res.get('data')])
        return result

    if args.name is not None:
        if RegularCheckUtil.checkHostName(args.name):
            ldapgroup['role_group_name'] = args.name
        else:
            result.State("Failure")
            result.Message(['Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.'])
            return result
    if ldapgroup['role_group_name'] == "":
        result.State("Failure")
        result.Message(['Group name is needed.'])
        return result

    if args.base is not None:
        if RegularCheckUtil.checkBase(args.base):
            ldapgroup['role_group_domain'] = args.base
        else:
            result.State("Failure")
            result.Message(['Searchbase is a string of 4 to 64 alpha-numeric characters.It must start with an alphabetical character.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.Example: cn=manager,ou=login, dc=domain,dc=com'])
            return result
    if ldapgroup['role_group_domain'] == "":
        result.State("Failure")
        result.Message(['Group domain is needed.'])
        return result

    if args.pri is not None:
        ldapgroup['role_group_withoem_privilege'] = args.pri
    if ldapgroup['role_group_withoem_privilege'] == "":
        result.State("Failure")
        result.Message(['Group privilege is needed.'])
        return result

    kvm_vm = {"enable": 1, "disable": 0}
    if args.kvm is not None:
        ldapgroup['role_group_kvm_privilege'] = kvm_vm.get(args.kvm.lower())

    if args.vm is not None:
        ldapgroup['role_group_vmedia_privilege'] = kvm_vm.get(args.vm.lower())

    # print(ldapgroup)
    set_res = RestFunc.setLDAPgroupM6(client, ldapgroup)
    if set_res.get('code') == 0 and set_res.get('data') is not None:
        result.State("Success")
        result.Message(["Set LDAP group success."])
    else:
        result.State("Failure")
        result.Message([set_res.get('data')])

    return result


def addUserGroup(client, args):
    result = ResultBean()
    group = []
    Group = RestFunc.getUserGroupByRest(client)
    if Group['code'] == 0 and Group['data'] is not None:
        data = Group['data']
        try:
            for item in data:
                group.append(item['GroupName'])
        except ValueError:
            result.State("Failure")
            result.Message(['failed to get user group'])
            return result
    else:
        result.State("Failure")
        result.Message(['failed to get user group'])
        return result

    if args.name in group:
        result.State("Failure")
        result.Message(['group ' + args.name + ' already exists'])
        return result

    responds = RestFunc.addUserGroupByRest(client, args.name, args.pri)
    if responds['code'] == 0 and responds['data'] is not None:
        result.State("Success")
        result.Message(['add user group ' + args.name])
    else:
        result.State("Failure")
        result.Message(['failed to add user group'])
    return result


def setUserGroup(client, args):
    result = ResultBean()
    group = []
    default = ['Administrator', 'Operator', 'User']
    Group = RestFunc.getUserGroupByRest(client)
    id = 0
    if Group['code'] == 0 and Group['data'] is not None:
        data = Group['data']
        try:
            for item in data:
                if item['GroupName'] == args.name:
                    id = item['GroupID']
                group.append(item['GroupName'])
        except ValueError:
            result.State("Failure")
            result.Message(['failed to get user group'])
            return result
    else:
        result.State("Failure")
        result.Message(['failed to get user group'])
        return result

    # 判断用户组是否存在
    if args.name not in group:
        result.State("Failure")
        result.Message(['no group ' + args.name])
        return result
    # 保留用户组不能修改
    if args.name in default:
        result.State("Failure")
        result.Message([args.name + ' is reserved user group '])
        return result

    responds = RestFunc.setUserGroupByRest(client, id, args.name, args.pri)
    if responds['code'] == 0 and responds['data'] is not None:
        result.State("Success")
        result.Message(['modify user group ' + args.name])
    else:
        result.State("Failure")
        result.Message(['failed to set user group'])
    return result


def delUserGroup(client, args):
    result = ResultBean()
    group = []
    default = ['Administrator', 'Operator', 'User']
    Group = RestFunc.getUserGroupByRest(client)
    id = 0
    if Group['code'] == 0 and Group['data'] is not None:
        data = Group['data']
        try:
            for item in data:
                if item['GroupName'] == args.name:
                    id = item['GroupID']
                group.append(item['GroupName'])
        except ValueError:
            result.State("Failure")
            result.Message(['failed to get user group'])
            return result
    else:
        result.State("Failure")
        result.Message(['failed to get user group'])
        return result
    # 判断用户组是否存在
    if args.name not in group:
        result.State("Failure")
        result.Message(['no group ' + args.name])
        return result
    # 保留用户组不能修改
    if args.name in default:
        result.State("Failure")
        result.Message([args.name + ' is reserved user group '])
        return result
    responds = RestFunc.delUserGroupByRest(client, id, args.name)
    if responds['code'] == 0 and responds['data'] is not None:
        result.State("Success")
        result.Message(['delete user group ' + args.name])
    else:
        result.State("Failure")
        result.Message(['failed to delete user group'])
    return result


def getNetwork(client, args):
    # get
    res = RestFunc.getLanByRest(client)
    ipinfo = ResultBean()
    if res == {}:
        ipinfo.State('Failure')
        ipinfo.Message(["cannot get lan information"])
    elif res.get('code') == 0 and res.get('data') is not None:
        data = res.get('data')
        ipinfo.State('Success')
        ipList = []
        lanDict = {
            '1': 'dedicated',
            '8': 'shared'
        }
        for lan in data:
            ipbean = NetBean()
            if lan['lan_enable'] == "Disabled":
                ipbean.IPVersion('Disabled')
                ipbean.InterfaceName(lan['interface_name'])
                ipbean.LanChannel(lanDict[str(lan['channel_number'])])
                ipbean.PermanentMACAddress(lan['mac_address'])
                ipv4 = IPv4Bean()
                ipv6 = IPv6Bean()
                ipbean.IPv4(ipv4.dict)
                ipbean.IPv6(ipv6.dict)
            else:
                if lan['ipv4_enable'] == "Enabled" and lan['ipv6_enable'] == "Enabled":
                    ipbean.IPVersion('IPv4andIPv6')
                elif lan['ipv4_enable'] == "Enabled":
                    ipbean.IPVersion('IPv4')
                elif lan['ipv6_enable'] == "Enabled":
                    ipbean.IPVersion('IPv6')
                ipbean.InterfaceName(lan['interface_name'])
                ipbean.LanChannel(lanDict[str(lan['channel_number'])])
                ipbean.PermanentMACAddress(lan['mac_address'])
                if lan['ipv4_enable'] == "Enabled":
                    ipv4 = IPv4Bean()
                    ipv4.AddressOrigin(lan['ipv4_dhcp_enable'])
                    ipv4.Address(lan['ipv4_address'])
                    ipv4.SubnetMask(lan['ipv4_subnet'])
                    ipv4.Gateway(lan['ipv4_gateway'])
                    ipbean.IPv4(ipv4.dict)

                if lan['ipv6_enable'] == "Enabled":
                    ipv6 = IPv6Bean()
                    ipv6.AddressOrigin(lan['ipv6_dhcp_enable'])
                    ipv6.Address(lan['ipv6_address'])
                    ipv6.PrefixLength(lan['ipv6_prefix'])
                    ipv6.Gateway(lan['ipv6_gateway'])
                    ipv6.Index(lan['ipv6_index'])
                    ipbean.IPv6([ipv6.dict])

                vlanbean = vlanBean()
                vlanbean.State(lan['vlan_enable'])
                vlanbean.VLANId(lan['vlan_id'])
                vlanbean.VLANPriority(lan['vlan_priority'])
                ipbean.VLANInfo(vlanbean.dict)
            ipList.append(ipbean.dict)
        ipinfo.Message(ipList)
    elif res.get('code') != 0 and res.get('data') is not None:
        ipinfo.State("Failure")
        ipinfo.Message([res.get('data')])
    else:
        ipinfo.State("Failure")
        ipinfo.Message(["get lan information error"])

    return ipinfo


def setNetwork(client, args):

    # get
    ipinfo = ResultBean()
    param = getBMCNet(client, args)
    if param is None:
        ipinfo.State("Failure")
        ipinfo.Message(["get " + args.interface_name + " error "])
        return ipinfo
    else:
        id = param['id']
        interface_name = str(param['interface_name'])
        channel_number = param['channel_number']
        lan_enable = param['lan_enable']
        mac_address = str(param['mac_address'])
        ipv4_enable = param['ipv4_enable']
        ipv4_dhcp_enable = param['ipv4_dhcp_enable']
        ipv4_address = param['ipv4_address']
        ipv4_subnet = param['ipv4_subnet']
        ipv4_gateway = param['ipv4_gateway']

        ipv6_enable = param['ipv6_enable']
        ipv6_dhcp_enable = param['ipv6_dhcp_enable']
        ipv6_address = param['ipv6_address']
        ipv6_index = param['ipv6_index']
        ipv6_prefix = param['ipv6_prefix']
        ipv6_gateway = param['ipv6_gateway']

        vlan_enable = param['vlan_enable']
        vlan_id = param['vlan_id']
        vlan_priority = param['vlan_priority']

        # 网卡启用
        new_lan_enable = ""
        if args.lan_enable == "enable":
            # 启用此网卡
            new_lan_enable = '1'
        else:
            # 关闭此网卡
            new_lan_enable = '0'
        if new_lan_enable == str(lan_enable):
            # 无需操作
            ipinfo.State("Success")
            ipinfo.Message([args.interface_name + " is already " + args.lan_enable + ", no action is needed."])
            return ipinfo

        data = {
            "id": id,
            "interface_name": interface_name,
            "channel_number": channel_number,
            "mac_address": mac_address,
            "lan_enable": new_lan_enable,

            "ipv4_enable": ipv4_enable,
            "ipv4_dhcp_enable": ipv4_dhcp_enable,
            "ipv4_address": ipv4_address,
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,

            "ipv6_enable": ipv6_enable,
            "ipv6_dhcp_enable": ipv6_dhcp_enable,
            "ipv6_address": ipv6_address,
            "ipv6_index": ipv6_index,
            "ipv6_prefix": ipv6_prefix,
            "ipv6_gateway": ipv6_gateway,

            "vlan_enable": vlan_enable,
            "vlan_id": vlan_id,
            "vlan_priority": vlan_priority
        }
        setres = RestFunc.setLanByRest(client, data)
        if setres["code"] == 0:
            ipinfo.State("Success")
            ipinfo.Message([])
        else:
            ipinfo.State("Failure")
            ipinfo.Message([setres['data']])
        return ipinfo


def setIPv4(client, args):

    # get
    ipinfo = ResultBean()
    param = getBMCNet(client, args)
    if param is None:
        ipinfo.State("Failure")
        ipinfo.Message(["get " + args.interface_name + " error "])
        return ipinfo
    else:
        id = param['id']
        interface_name = str(param['interface_name'])
        channel_number = param['channel_number']
        lan_enable = param['lan_enable']
        mac_address = str(param['mac_address'])
        ipv4_enable = param['ipv4_enable']
        ipv4_dhcp_enable = param['ipv4_dhcp_enable']
        ipv4_address = param['ipv4_address']
        ipv4_subnet = param['ipv4_subnet']
        ipv4_gateway = param['ipv4_gateway']

        ipv6_enable = param['ipv6_enable']
        ipv6_dhcp_enable = param['ipv6_dhcp_enable']
        ipv6_address = param['ipv6_address']
        ipv6_index = param['ipv6_index']
        ipv6_prefix = param['ipv6_prefix']
        ipv6_gateway = param['ipv6_gateway']

        vlan_enable = param['vlan_enable']
        vlan_id = param['vlan_id']
        vlan_priority = param['vlan_priority']

        # 网卡启用
        if lan_enable == 1:
            # 启用
            # IPV4 SETTING
            if args.ipv4_status == "enable":
                ipv4_enable = 1
            elif args.ipv4_status == "disable":
                ipv4_enable = 0

            if ipv4_enable == 0:
                if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None or args.ipv4_dhcp_enable is not None:
                    ipinfo.State("Failure")
                    ipinfo.Message(["ipv4 is disabled, please enable it first."])
                    return ipinfo
            else:
                if args.ipv4_dhcp_enable == "dhcp":
                    ipv4_dhcp_enable = 1
                elif args.ipv4_dhcp_enable == "static":
                    ipv4_dhcp_enable = 0
                if ipv4_dhcp_enable == 1:
                    if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["'ip', 'subnet','gateway' is not active in DHCP mode."])
                        return ipinfo
                else:
                    if args.ipv4_address is not None:
                        if RegularCheckUtil.checkIP(args.ipv4_address):
                            ipv4_address = args.ipv4_address
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv4 IP address."])
                            return ipinfo
                    if args.ipv4_subnet is not None:
                        if RegularCheckUtil.checkSubnetMask(args.ipv4_subnet):
                            ipv4_subnet = args.ipv4_subnet
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv4 subnet mask."])
                            return ipinfo
                    if args.ipv4_gateway is not None:
                        if RegularCheckUtil.checkIP(args.ipv4_subnet):
                            ipv4_gateway = args.ipv4_gateway
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv4 default gateway."])
                            return ipinfo
        else:  # 网卡已关闭
            ipinfo.State("Failure")
            ipinfo.Message([args.interface_name + " is disable, use 'setNetwork' to enable it first."])
            return ipinfo

        data = {
            "id": id,
            "interface_name": interface_name,
            "channel_number": channel_number,
            "mac_address": mac_address,
            "lan_enable": lan_enable,

            "ipv4_enable": ipv4_enable,
            "ipv4_dhcp_enable": ipv4_dhcp_enable,
            "ipv4_address": ipv4_address,
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,

            "ipv6_enable": ipv6_enable,
            "ipv6_dhcp_enable": ipv6_dhcp_enable,
            "ipv6_address": ipv6_address,
            "ipv6_index": ipv6_index,
            "ipv6_prefix": ipv6_prefix,
            "ipv6_gateway": ipv6_gateway,

            "vlan_enable": vlan_enable,
            "vlan_id": vlan_id,
            "vlan_priority": vlan_priority
        }
        # print data
        header = client.getHearder()
        header["X-Requested-With"] = "XMLHttpRequest"
        header["Content-Type"] = "application/json;charset=UTF-8"
        header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

        setres = RestFunc.setLanByRest(client, data)
        if setres["code"] == 0:
            ipinfo.State("Success")
            ipinfo.Message(['set ipv4 complete'])
        else:
            ipinfo.State("Failure")
            ipinfo.Message([setres['data']])
        return ipinfo


def setIPv6(client, args):

    # get
    ipinfo = ResultBean()
    param = getBMCNet(client, args)
    if param is None:
        ipinfo.State("Failure")
        ipinfo.Message(["get " + args.interface_name + " error "])
        return ipinfo
    else:
        id = param['id']
        interface_name = str(param['interface_name'])
        channel_number = param['channel_number']
        lan_enable = param['lan_enable']
        mac_address = str(param['mac_address'])
        ipv4_enable = param['ipv4_enable']
        ipv4_dhcp_enable = param['ipv4_dhcp_enable']
        ipv4_address = param['ipv4_address']
        ipv4_subnet = param['ipv4_subnet']
        ipv4_gateway = param['ipv4_gateway']

        ipv6_enable = param['ipv6_enable']
        ipv6_dhcp_enable = param['ipv6_dhcp_enable']
        ipv6_address = param['ipv6_address']
        ipv6_index = param['ipv6_index']
        ipv6_prefix = param['ipv6_prefix']
        ipv6_gateway = param['ipv6_gateway']

        vlan_enable = param['vlan_enable']
        vlan_id = param['vlan_id']
        vlan_priority = param['vlan_priority']

        # 网卡启用
        if lan_enable == 1:
            if args.ipv6_status == "enable":
                ipv6_enable = 1
            elif args.ipv6_status == "disable":
                ipv6_enable = 0

            if ipv6_enable == 0:
                if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None or args.ipv6_prefix is not None or args.ipv6_dhcp_enable is not None:
                    ipinfo.State("Failure")
                    ipinfo.Message(["ipv6 is disabled, please enable it first."])
                    return ipinfo
            else:
                if args.ipv6_dhcp_enable == "dhcp":
                    ipv6_dhcp_enable = 1
                elif args.ipv6_dhcp_enable == "static":
                    ipv6_dhcp_enable = 0
                if ipv6_dhcp_enable == 1:
                    if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None or args.ipv6_prefix is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(
                            ["'ip', 'index','Subnet prefix length','gateway' is not active in DHCP mode."])
                        return ipinfo
                else:
                    if args.ipv6_address is not None:
                        if RegularCheckUtil.checkIPv6(args.ipv6_address):
                            ipv6_address = args.ipv6_address
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv6 IP address."])
                            return ipinfo
                    if args.ipv6_gateway is not None:
                        if RegularCheckUtil.checkIPv6(args.ipv6_gateway):
                            ipv6_gateway = args.ipv6_gateway
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv6 default gateway."])
                            return ipinfo
                    if args.ipv6_index is not None:
                        if RegularCheckUtil.checkIndex(args.ipv6_index):
                            ipv6_index = args.ipv6_index
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv6 index(0-15)."])
                            return ipinfo
                    if args.ipv6_prefix is not None:
                        if RegularCheckUtil.checkPrefix(args.ipv6_prefix):
                            ipv6_prefix = args.ipv6_prefix
                        else:
                            ipinfo.State("Failure")
                            ipinfo.Message(["Invalid IPv6 Subnet prefix length(0-128)."])
                            return ipinfo
        else:  # 网卡已关闭
            ipinfo.State("Failure")
            ipinfo.Message([args.interface_name + " is disable, use 'setNetwork' to enable it first."])
            return ipinfo

        data = {
            "id": id,
            "interface_name": interface_name,
            "channel_number": channel_number,
            "mac_address": mac_address,
            "lan_enable": lan_enable,

            "ipv4_enable": ipv4_enable,
            "ipv4_dhcp_enable": ipv4_dhcp_enable,
            "ipv4_address": ipv4_address,
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,

            "ipv6_enable": ipv6_enable,
            "ipv6_dhcp_enable": ipv6_dhcp_enable,
            "ipv6_address": ipv6_address,
            "ipv6_index": ipv6_index,
            "ipv6_prefix": ipv6_prefix,
            "ipv6_gateway": ipv6_gateway,

            "vlan_enable": vlan_enable,
            "vlan_id": vlan_id,
            "vlan_priority": vlan_priority
        }
        # print data
        header = client.getHearder()
        header["X-Requested-With"] = "XMLHttpRequest"
        header["Content-Type"] = "application/json;charset=UTF-8"
        header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

        setres = RestFunc.setLanByRest(client, data)
        if setres["code"] == 0:
            ipinfo.State("Success")
            ipinfo.Message(['set ipv6 complete'])
        else:
            ipinfo.State("Failure")
            ipinfo.Message([setres['data']])
        return ipinfo


def getBMCNet(client, args):
    Param = None
    res = RestFunc.getNetworkByRest(client)
    if res == {}:
        return None
    elif res.get('code') == 0 and res.get('data') is not None:
        data = res.get('data')
        for lan in data:
            if lan['interface_name'] == args.interface_name:
                Param = lan
                break
        return Param
    else:
        return None


def setVlan(client, args):

    # get
    ipinfo = ResultBean()
    param = getBMCNet(client, args)
    if param is None:
        ipinfo.State("Failure")
        ipinfo.Message(["get " + args.interface_name + " error "])
        return ipinfo
    else:
        id = param['id']
        interface_name = str(param['interface_name'])
        channel_number = param['channel_number']
        lan_enable = param['lan_enable']
        mac_address = str(param['mac_address'])
        ipv4_enable = param['ipv4_enable']
        ipv4_dhcp_enable = param['ipv4_dhcp_enable']
        ipv4_address = param['ipv4_address']
        ipv4_subnet = param['ipv4_subnet']
        ipv4_gateway = param['ipv4_gateway']

        ipv6_enable = param['ipv6_enable']
        ipv6_dhcp_enable = param['ipv6_dhcp_enable']
        ipv6_address = param['ipv6_address']
        ipv6_index = param['ipv6_index']
        ipv6_prefix = param['ipv6_prefix']
        ipv6_gateway = param['ipv6_gateway']

        vlan_enable = param['vlan_enable']
        vlan_id = param['vlan_id']
        vlan_priority = param['vlan_priority']

        # 网卡启用
        if lan_enable == 1:
            # 启用
            # IPV4 SETTING
            if args.vlan_status == "enable":
                vlan_enable = 1
            elif args.vlan_status == "disable":
                vlan_enable = 0

            if vlan_enable == 0:
                if args.vlan_id is not None or args.vlan_priority is not None:
                    ipinfo.State("Failure")
                    ipinfo.Message(["vlan is disabled, please enable it first."])
                    return ipinfo
            else:
                if args.vlan_id is not None:
                    if RegularCheckUtil.checkID(args.vlan_id):
                        vlan_id = args.vlan_id
                    else:
                        ipinfo.State("Failure")
                        ipinfo.Message(["vlan id should be 2-4094."])
                        return ipinfo
                if args.vlan_priority is not None:
                    if RegularCheckUtil.checkVP(args.vlan_priority):
                        vlan_priority = args.vlan_priority
                    else:
                        ipinfo.State("Failure")
                        ipinfo.Message(["vlan priority should be 1-7."])
                        return ipinfo
        else:  # 网卡已关闭
            ipinfo.State("Failure")
            ipinfo.Message([args.interface_name + " is disable, use 'setNetwork' to enable it first."])
            return ipinfo

        data = {
            "id": id,
            "interface_name": interface_name,
            "channel_number": channel_number,
            "mac_address": mac_address,
            "lan_enable": lan_enable,

            "ipv4_enable": ipv4_enable,
            "ipv4_dhcp_enable": ipv4_dhcp_enable,
            "ipv4_address": ipv4_address,
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,

            "ipv6_enable": ipv6_enable,
            "ipv6_dhcp_enable": ipv6_dhcp_enable,
            "ipv6_address": ipv6_address,
            "ipv6_index": ipv6_index,
            "ipv6_prefix": ipv6_prefix,
            "ipv6_gateway": ipv6_gateway,

            "vlan_enable": vlan_enable,
            "vlan_id": vlan_id,
            "vlan_priority": vlan_priority
        }
        # print data
        header = client.getHearder()
        header["X-Requested-With"] = "XMLHttpRequest"
        header["Content-Type"] = "application/json;charset=UTF-8"
        header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

        setres = RestFunc.setLanByRest(client, data)
        if setres["code"] == 0:
            ipinfo.State("Success")
            ipinfo.Message([])
        else:
            ipinfo.State("Failure")
            ipinfo.Message([setres['data']])
        return ipinfo


def getDNS(client, args):

    # get
    result = ResultBean()
    dns_result = DNSBean()
    dns_info = RestFunc.getDNSByRestM5(client)
    if dns_info.get('code') == 0 and dns_info.get('data') is not None:
        dns = dns_info.get('data')
        dns_result.DNSStatus("Disable" if dns['dns_status'] == 0 else "Enable")
        dns_result.HostSettings("manual" if dns['host_cfg'] == 0 else "auto")
        dns_result.Hostname(dns['host_name'])
        dns_result.DomainSettings("manual" if dns['domain_manual'] == 1 else "auto")
        dns_result.DomainName(dns['domain_name'])
        dns_result.DomainInterface(dns['domain_iface'])
        dns_result.DNSSettings("manual" if dns['dns_manual'] == 1 else "auto")
        dns_result.DNSServer1(dns['dns_server1'])
        dns_result.DNSServer2(dns['dns_server2'])
        dns_result.DNSServer3(dns['dns_server3'])
        dns_result.DNSServerInterface(dns['dns_iface'])
        dns_result.DNSIPPriority(dns['dns_priority'])
        result.State('Success')
        result.Message([dns_result.dict])
    else:
        result.State('Failure')
        result.Message(['get current power status failed.'])

    return result


def setDNS(client, args):

    # get
    result = ResultBean()
    dns_info = RestFunc.getDNSByRestM5()
    if dns_info.get('code') == 0 and dns_info.get('data') is not None:
        data = dns_info.get('data')
        default_dns_status = data['dns_status']
        default_host_name = data['host_name']
        default_host_cfg = data['host_cfg']
        default_domain_manual = data['domain_manual']
        default_domain_iface = data['domain_iface']
        default_domain_name = data['domain_name']
        default_dns_manual = data['dns_manual']
        default_dns_iface = data['dns_iface']
        default_dns_priority = data['dns_priority']
        default_dns_server1 = data['dns_server1']
        default_dns_server2 = data['dns_server2']
        default_dns_server3 = data['dns_server3']
        edit_flag = False
        if args.dns == 'disable':
            if default_dns_status == 0:
                result.State('Failure')
                result.Message(['DNS is already disabled.'])
                return result
            else:
                data = {
                    'dns_status': 0
                }
                restart_info = RestFunc.setDNSRestartBMCByRest(client, data)
                if restart_info.get('code') == 0 and restart_info.get('data') is not None:
                    result.State('Success')
                    result.Message(['DNS now is reseting, please wait for a few minutes.'])
                    return result
                else:
                    result.State('Failure')
                    result.Message(['set DNS Failure.'])
                    return result
        else:  # start
            if args.dns == 'enable' and default_dns_status == 0:
                edit_flag = True
            if args.dns is None and default_dns_status == 0:
                result.State('Failure')
                result.Message(['set DNS enable first, -S is needed.'])
                return result
            # hostManual
            if args.hostManual == 'auto':
                host_cfg = 1
            elif args.hostManual == 'manual':
                host_cfg = 0
            else:
                host_cfg = default_host_cfg
            if host_cfg != default_host_cfg:
                edit_flag = True
            # hostName
            if args.hostName is None:
                host_name = default_host_name
            else:
                if host_cfg == 1:
                    result.State('Failure')
                    result.Message(['host name can not be set when host settings is auto.'])
                    return result
                else:
                    if not RegularCheckUtil.checkHostName(args.hostName):
                        result.State('Failure')
                        result.Message(['-HN parameter is invalid.'])
                        return result
                    host_name = args.hostName
                    edit_flag = True
            # domainManual
            if args.domainManual == 'auto':
                domain_manual = 0
            elif args.domainManual == 'manual':
                domain_manual = 1
            else:
                domain_manual = default_domain_manual
            if domain_manual != default_domain_manual:
                edit_flag = True

            if domain_manual == 0:  # auto
                # 自动模式下domainName不起作用
                if args.domainName is not None:
                    result.State('Failure')
                    result.Message(['host name(-DN) can not be set when domain settings is auto.'])
                    return result
                domain_name = default_domain_name  # 固定无所谓
                # 获取自动模式下domain inter face 的取值
                list = []
                options_info = RestFunc.getDomainOptionsBMCByRest(client)
                if options_info.get('code') == 0 and options_info.get('data') is not None:
                    options = options_info.get('data')
                    try:
                        for item in options:
                            # 去掉打印出来的u
                            list.append(item['domain_iface'])
                    except BaseException:
                        result.State('Failure')
                        result.Message(['can not get domain options.'])
                        return result
                else:
                    result.State('Failure')
                    result.Message(['can not get domain options.'])
                    return result
                if args.domainIface is None:
                    if default_domain_manual == 0:
                        domain_iface = default_domain_iface
                    else:
                        result.State('Failure')
                        result.Message(['-DI parameter is needed, available domain interface:' + list])
                        return result
                else:
                    if args.domainIface not in list:
                        result.State('Failure')
                        result.Message(['available domain interface:' + list])
                        return result
                    else:
                        domain_iface = args.domainIface
                        edit_flag = True
                if domain_iface == "":
                    result.State('Failure')
                    result.Message(['-DI parameter is needed, available domain interface:' + list])
                    return result
            elif domain_manual == 1:
                # 手动模式下networkInterface不起作用
                if args.domainIface is not None:
                    result.State('Failure')
                    result.Message(['network interface(-DI) can not be set when domain settings is manual.'])
                    return result
                domain_iface = default_domain_iface
                if args.domainName is None:
                    if default_domain_manual == 1:
                        domain_name = default_domain_name
                    else:
                        result.State('Failure')
                        result.Message(['-DN parameter is needed.'])
                        return result
                else:
                    domain_name = args.domainName
                    if RegularCheckUtil.checkDomainName(domain_name):
                        edit_flag = True
                    else:
                        result.State('Failure')
                        result.Message(['-DN parameter is needed.'])
                        return result
                if domain_name == "":
                    result.State('Failure')
                    result.Message(['-DN parameter is needed.'])
                    return result
            else:
                result.State('Failure')
                result.Message(['get domain settings error.'])
                return result

            # dnsSettings
            if args.dnsManual == 'auto':
                dns_manual = 0
            elif args.dnsManual == 'manual':
                dns_manual = 1
            else:
                dns_manual = default_dns_manual
            if dns_manual != default_dns_manual:
                edit_flag = True

            # dnsSettings
            if dns_manual == 0:
                if args.dnsServer1 is not None:
                    result.State('Failure')
                    result.Message(['DNS server1(-S1) can not be set when DNS settings is auto.'])
                    return result
                if args.dnsServer2 is not None:
                    result.State('Failure')
                    result.Message(['DNS server1(-S2) can not be set when DNS settings is auto.'])
                    return result
                if args.dnsServer3 is not None:
                    result.State('Failure')
                    result.Message(['DNS server1(-S3) can not be set when DNS settings is auto.'])
                    return result
                dnsServer1 = default_dns_server1
                dnsServer2 = default_dns_server2
                dnsServer3 = default_dns_server3
                if args.dnsIP is None:
                    dns_priority = default_dns_priority
                else:
                    dns_priority = args.dnsIP
                    edit_flag = True
                # dnsIface
                list = []
                options_info = RestFunc.getServerOptionsBMCByRest(client)
                if options_info.get('code') == 0 and options_info.get('data') is not None:
                    options = options_info.get('data')
                    try:
                        for item in options:
                            # 去掉打印出来的u
                            list.append(item['dns_iface'])
                    except BaseException:
                        result.State('Failure')
                        result.Message(['can not get server options.'])
                        return result
                else:
                    result.State('Failure')
                    result.Message(['can not get server options.'])
                    return result
                if args.dnsIface is None:
                    if default_dns_manual == 0:
                        dns_iface = default_dns_iface
                    else:
                        result.State('Failure')
                        result.Message(['dns interface (-SI) is needed, available dns interface:' + list])
                        return result
                else:
                    if args.dnsIface not in list:
                        result.State('Failure')
                        result.Message(['available dns interface:' + list])
                        return result
                    else:
                        dns_iface = args.dnsIface
                        edit_flag = True
            elif dns_manual == 1:
                if args.dnsServer1 is None and args.dnsServer2 is None and args.dnsServer3 is None and default_dns_manual == 0:
                    result.State('Failure')
                    result.Message(['at least one dns server is needed.'])
                    return result
                else:
                    if args.dnsServer1 is None:
                        dnsServer1 = default_dns_server1
                    else:
                        if RegularCheckUtil.checkIP(args.dnsServer1):
                            dnsServer1 = args.dnsServer1
                            edit_flag = True
                        else:
                            result.State('Failure')
                            result.Message(['Invalid DNS Server Address, input ipv4 address or ipv6 address'])
                            return result
                    if args.dnsServer2 is None:
                        dnsServer2 = default_dns_server2
                    else:
                        if RegularCheckUtil.checkIP(args.dnsServer2):
                            dnsServer2 = args.dnsServer2
                            edit_flag = True
                        else:
                            result.State('Failure')
                            result.Message(['Invalid DNS Server Address, input ipv4 address or ipv6 address'])
                            return result
                    if args.dnsServer3 is None:
                        dnsServer3 = default_dns_server3
                    else:
                        if RegularCheckUtil.checkIP(args.dnsServer3):
                            dnsServer3 = args.dnsServer3
                            edit_flag = True
                        else:
                            result.State('Failure')
                            result.Message(['Invalid DNS Server Address, input ipv4 address or ipv6 address'])
                            return result
                if args.dnsIface is not None:
                    result.State('Failure')
                    result.Message(['DNS server interface(-SI) can not be set when DNS settings is manual'])
                    return result
                dns_iface = "eth0"
                if args.dnsIP is not None:
                    result.State('Failure')
                    result.Message(['IP Priority(-SP) can not be set when DNS settings is manual'])
                    return result
                dns_priority = 4
            else:
                result.State('Failure')
                result.Message(['get DNS settings error'])
                return result

            if not edit_flag:
                result.State('Failure')
                result.Message(['No setting changed!'])
                return result
        data['dns_iface'] = dns_iface
        data['dns_manual'] = dns_manual
        data['dns_priority'] = dns_priority
        data['dns_server1'] = dnsServer1
        data['dns_server2'] = dnsServer2
        data['dns_server3'] = dnsServer3
        data['dns_status'] = 1
        data['domain_iface'] = domain_iface
        data['domain_manual'] = domain_manual
        data['domain_name'] = domain_name
        data['host_cfg'] = host_cfg
        data['host_name'] = host_name
        try:
            dns_re = RestFunc.setDNSByRestM5(client, data)
            if dns_re.get('code') == 0 and dns_re.get('data') is not None:
                data = {
                    'dns_status': 1
                }
                restart_info = RestFunc.setDNSRestartBMCByRest(client, data)
                if restart_info.get('code') == 0 and restart_info.get('data') is not None:
                    result.State('Success')
                    result.Message(['DNS is reseting, please wait for a few minutes.'])
                else:
                    result.State('Failure')
                    result.Message(['set DNS Failure.'])
            else:
                result.State('Failure')
                result.Message(['set DNS Failure.'])
        except(AttributeError, KeyError):
            result.State('Failure')
            result.Message(['can not set DNS.'])
    return result


# 判断-A的值是否在选项中
def judgeAttInList(attr, descriptionList):
    flag = False
    if attr in descriptionList:
        flag = True
    return flag


# 根据-V的值是否在选项中或者是要输入一个值，验证-v的有效性
# 返回对应设置项的info，为了获得setter
def judgeValueInList(attr, value, list):
    Flag = False
    cmd = None
    infomation = None
    for info in list:
        if info['description'] == attr:
            infomation = info
            if info['input']:
                # 输入一个值,并根据attr判断该值是否在范围内，在则设为True
                try:
                    func = eval(attr)
                    Flag = func(value)
                    if Flag:
                        # 10进制转16进制
                        param = hex(int(value))
                        low_param = '0x00'
                        up_param = '0x00'
                        if len(param) == 4:
                            low_param = str(param)
                        elif len(param) > 4:
                            low_param = '0x' + str(param[-2:])
                            if len(str(param[2:-2])) == 2:
                                up_param = str(param[0:-2])
                            else:
                                up_param = '0x0' + str(param[-3])
                        elif len(param) == 3:
                            low_param = '0x0' + str(param[-1])
                        for list in info['setter']:
                            cmd = list['cmd']
                        replace_param = low_param + ' ' + up_param
                        # 将输入的数值验证成功后替换进命令行中
                        cmd = cmd.replace('$in', replace_param)
                except BaseException:
                    return Flag, cmd, infomation

            else:
                # 选择一个值
                if isinstance(value, int):
                    value = str(value)
                for list in info['setter']:
                    if list['value'] == value:
                        Flag = True
                        cmd = list['cmd']
                        break
            break
    return Flag, cmd, infomation


# 定义需要验证参数的验证函数，以输入的attr为函数名
def PatrolScrubInterval(input):
    if isinstance(input, str) and not input.isdigit():
        Flag = False
        return Flag
    else:
        if int(input) >= 0 and int(input) <= 24:
            Flag = True
            return Flag
        else:
            Flag = False
            return Flag


def PXEbootwaittime(input):
    if isinstance(input, str) and not input.isdigit():
        Flag = False
        return Flag
    else:
        if int(input) >= 0 and int(input) <= 5:
            Flag = True
            return Flag
        else:
            Flag = False
            return Flag


def Mediadetectcount(input):
    if isinstance(input, str) and not input.isdigit():
        Flag = False
        return Flag
    else:
        if int(input) >= 1 and int(input) <= 50:
            Flag = True
            return Flag
        else:
            Flag = False
            return Flag


def NGNDieSparingAggressiveness(input):
    if isinstance(input, str) and not input.isdigit():
        Flag = False
        return Flag
    else:
        if int(input) >= 0 and int(input) <= 255:
            Flag = True
            return Flag
        else:
            Flag = False
            return Flag


def CorrectableErrorThreshold(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 32767 and int(input) >= 0:
            Flag = True
    return Flag


def LegacyVGASocket(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 3 and int(input) >= 0:
            Flag = True
    return Flag


def PxeRetryCount(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 255 and int(input) >= 0:
            Flag = True
    return Flag


def WatchdogTimerTimeout(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 8 and int(input) >= 2:
            Flag = True
    return Flag


def BMCWarmupTime(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 240 and int(input) >= 0 and int(input) % 3 == 0:
            Flag = True
    return Flag


def UncoreFrequency(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 23 and int(input) >= 13:
            Flag = True
    return Flag


def BusResourcesAllocationRatio3(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 8 and int(input) >= 0:
            Flag = True
    return Flag


def BusResourcesAllocationRatio2(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 8 and int(input) >= 0:
            Flag = True
    return Flag


def BusResourcesAllocationRatio1(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 8 and int(input) >= 0:
            Flag = True
    return Flag


def BusResourcesAllocationRatio0(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 8 and int(input) >= 0:
            Flag = True
    return Flag


def LegacyVGAStack(input):
    Flag = False
    if not str(input).isdigit():
        Flag = False
    else:
        if int(input) <= 5 and int(input) >= 0:
            Flag = True
    return Flag


def PreLocatedisk(client):
    flag = 0
    cid = []
    pc = {}
    ctr_count_lsi = RestFunc.getLSICtrlCountByRest(client)
    ctr_count_pmc = RestFunc.getPMCCtrlCountByRest(client)
    if ctr_count_lsi is None or ctr_count_lsi.get('code') != 0 or ctr_count_lsi.get('data') is None:  # ctrl个数
        flag = 1
        return cid, pc, flag
    else:
        count = ctr_count_lsi.get('data')
        countNumber_lsi = count.get('ctrlCount')

    if ctr_count_pmc is None or ctr_count_pmc.get('code') != 0 or ctr_count_pmc.get('data') is None:  # ctrl个数
        flag = 1
        return cid, pc, flag
    else:
        count = ctr_count_pmc.get('data')
        countNumber_pmc = count.get('ctrlCount')

    num = countNumber_lsi + countNumber_pmc
    if num == 0:
        return cid, pc, flag


def restore_bios(client, path_service):
    # 读取
    f = open(path_service, 'r')
    biosInfo = f.read()
    f.close()
    biosJson = json.loads(biosInfo)
    return biosJson
    # for bios in biosJson:


def getbiosVersion(client):
    biosVersion = IpmiFunc.getM5BiosVersionByIpmi(client)
    if biosVersion and biosVersion.get('code') == 0 and biosVersion.get('data') is not None:
        bios_data = biosVersion.get('data')
        if 'Version' in bios_data:
            version = bios_data.get('Version')
        else:
            version = None
    else:
        version = None
    return version


def typeconvert(var):
    if var == 1:
        return "Other"
    elif var == 2:
        return "Unknown"
    elif var == 3:
        return "DRAM"
    elif var == 4:
        return "EDRAM"
    elif var == 5:
        return "VRAM"
    elif var == 6:
        return "SRAM"
    elif var == 7:
        return "RAM"
    elif var == 8:
        return "ROM"
    elif var == 9:
        return "FLASH"
    elif var == 10:
        return "EEPROM"
    elif var == 11:
        return "FEPROM"
    elif var == 12:
        return "EPROM"
    elif var == 13:
        return "CDRAM"
    elif var == 14:
        return "3DRAM"
    elif var == 15:
        return "SDRAM"
    elif var == 16:
        return "SGRAM"
    elif var == 17:
        return "RDRAM"
    elif var == 18:
        return "DDR"
    elif var == 19:
        return "DDR2"
    elif var == 20:
        return "DDR2 FB-DIMM"
    elif var == 21:
        return "Reserved"
    elif var == 22:
        return "Reserved"
    elif var == 23:
        return "Reserved"
    elif var == 24:
        return "DDR3"
    elif var == 25:
        return "FBD2"
    elif var == 26:
        return "DDR4"
    elif var == 27:
        return "LPDDR"
    elif var == 28:
        return "LPDDR2"
    elif var == 29:
        return "LPDDR3"
    elif var == 30:
        return "LPDDR4"
    else:
        return var


def fwState(var):
    if var == 0x00:
        return 'Unconfigured Good'
    elif var == 0x01:
        return 'Unconfigured Bad'
    elif var == 0x02:
        return 'Hot Spare'
    elif var == 0x10:
        return 'Offline'
    elif var == 0x11:
        return 'Failed'
    elif var == 0x14:
        return 'Rebuild'
    elif var == 0x18:
        return 'Online'
    elif var == 0x20:
        return 'Copyback'
    elif var == 0x40:
        return 'JBOD'
    elif var == 0x80:
        return 'Sheld Unconfigured'
    elif var == 0x82:
        return 'Sheld Hot Spare'
    elif var == 0x90:
        return 'Sheld Configured'
    else:
        return var


if __name__ == "__main__":
    # class tex():
    #     def service(self,value):
    #         tex.service = value
    #     def enabled(self,value):
    #         tex.enabled = value
    #     def port(self,value):
    #         tex.port = value
    #     def port2(self,value):
    #         tex.port2 = value
    #     def sslenable(self,value):
    #         tex.sslenable = value
    class tex():
        def image(self, value):
            tex.image = value

        def operatortype(self, value):
            tex.operatortype = value

    client = RequestClient.RequestClient()
    client.setself("100.2.39.104", "root", "root", 0, "lanplus")
    # client.setself("100.2.73.207","admin","admin",0,"lanplus")
    # client.setself("100.2.73.207","root","root",0,"lanplus")
    # client.setself("100.2.73.172","root","root",0,"lanplus")
    print(client.host, client.username, client.password, client.lantype, client.port)
    com5 = CommonM5()
    args = tex()
    # args.service('kvm')
    # args.enabled(None)
    # args.port(None)
    # args.port2(7578)
    # args.sslenable(None)
    args.image('protocol://[root:inspur@2018@]100.2.28.203[:22]/data/nfs/server/CentOS-7-x86_64-Everything-1511.a')
    args.operatortype('Mount')
    # args.image(None)
    # res= com5.getproduct(client,args)
    # res= com5.getraid(client,args)
    # res= com5.getpdisk(client,args)
    # res= com5.getpcie(client,args)
    # res= com5.getpsu(client,args)
    # res= com5.getcpu(client,args)
    # res= com5.getmemory(client,args)
    res = com5.gettemp(client, args)
    # res= com5.gethealth(client,args)
    # res= com5.getfan(client,args)
    # res= com5.getsensor(client,args)
    # res= com5.mountvmm(client,args)
    # res= com5.getbios(client,args)
    # res= com5.getldisk(client,args)
    # a=com5.locatedisk(client, args)
    # a=com5.setservice(client, args)
    # a=com5.setservice(client, args)
    # a=com5.getfw(client, args)
    # a = com5.getfw(client, None)
    # args = tex()
    # args.state('on')
    # args.frequency(10)
    # a = com5.locateserver(client, args)
    print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=True, indent=4))

    '''
    data = {
        "username": strAsciiHex("admin"),
        "password": strAsciiHex("admin"),
        "encrypt_flag": 1
    }
    response=client.request("POST", "api/session", data=data)
    headers={}
    if response is not None and response.status_code == 200:
        headers = {
            "X-CSRFToken": response.json()["CSRFToken"],
            "Cookie": response.headers["set-cookie"]
        }
    else:
        print ("Failure: get token error")
    client.setHearder(headers)
    print (headers)
    com5 = CommonM5()
    a=com5.getip(client, None)
    print(json.dumps(a, default=lambda o: o.__dict__, sort_keys=True, indent=4))
    #执行完退出
    responds = client.request("DELETE", "api/session", client.getHearder())
    if responds is not None and responds.status_code == 200:
        print ("log out ok")
    else:
        print ("Failure: logout error" + responds.json()['error'])
            timeinfo.State("Failure")
    '''
