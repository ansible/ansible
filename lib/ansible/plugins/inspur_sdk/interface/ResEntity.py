import json
import collections


class ResultBean():
    # def __init__(self):
    #     self.Result = collections.OrderedDict()

    def State(self):
        return self.State

    def State(self, value):
        self.State = value

    def Message(self):
        return self.Message

    def Message(self, value):
        self.Message = value

    # def Result(self):
    #     return self.Result


class VncBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def KeyboardLayout(self):
        return self.dict['KeyboardLayout']

    def KeyboardLayout(self, value):
        self.dict['KeyboardLayout'] = value

    def SessionTimeoutMinutes(self):
        return self.dict['SessionTimeoutMinutes']

    def SessionTimeoutMinutes(self, value):
        self.dict['SessionTimeoutMinutes'] = value

    def SSLEncryptionEnabled(self):
        return self.dict['SSLEncryptionEnabled']

    def SSLEncryptionEnabled(self, value):
        self.dict['SSLEncryptionEnabled'] = value

    def MaximumNumberOfSessions(self):
        return self.dict['MaximumNumberOfSessions']

    def MaximumNumberOfSessions(self, value):
        self.dict['MaximumNumberOfSessions'] = value

    def NumberOfActivatedSessions(self):
        return self.dict['NumberOfActivatedSessions']

    def NumberOfActivatedSessions(self, value):
        self.dict['NumberOfActivatedSessions'] = value

    def SessionMode(self):
        return self.dict['SessionMode']

    def SessionMode(self, value):
        self.dict['SessionMode'] = value


class VncSessionBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ClientIP(self):
        return self.dict['ClientIP']

    def ClientIP(self, value):
        self.dict['ClientIP'] = value

    def SessionId(self):
        return self.dict['SessionId']

    def SessionId(self, value):
        self.dict['SessionId'] = value

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def SessionType(self):
        return self.dict['SessionType']

    def SessionType(self, value):
        self.dict['SessionType'] = value

    def UserId(self):
        return self.dict['UserId']

    def UserId(self, value):
        self.dict['UserId'] = value

    def UserName(self):
        return self.dict['UserName']

    def UserName(self, value):
        self.dict['UserName'] = value

    def UserPrivilege(self):
        return self.dict['UserPrivilege']

    def UserPrivilege(self, value):
        self.dict['UserPrivilege'] = value


class CapabilitiesBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def GetCommandList(self):
        return self.dict['GetCommandList']

    def GetCommandList(self, value):
        self.dict['GetCommandList'] = value

    def SetCommandList(self):
        return self.dict['SetCommandList']

    def SetCommandList(self, value):
        self.dict['SetCommandList'] = value


class ProductBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ProductName(self):
        return self.dict['ProductName']

    def ProductName(self, value):
        self.dict['ProductName'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def UUID(self):
        return self.dict['UUID']

    def UUID(self, value):
        self.dict['UUID'] = value

    def HostingRole(self):
        return self.dict['HostingRole']

    def HostingRole(self, value):
        self.dict['HostingRole'] = value

    def DeviceOwnerID(self):
        return self.dict['DeviceOwnerID']

    def DeviceOwnerID(self, value):
        self.dict['DeviceOwnerID'] = value

    def DeviceSlotID(self):
        return self.dict['DeviceSlotID']

    def DeviceSlotID(self, value):
        self.dict['DeviceSlotID'] = value

    def PowerState(self):
        return self.dict['PowerState']

    def PowerState(self, value):
        self.dict['PowerState'] = value

    def TotalPowerWatts(self):
        return self.dict['TotalPowerWatts']

    def TotalPowerWatts(self, value):
        self.dict['TotalPowerWatts'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value


class PowerBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Power(self):
        return self.dict['Power']

    def Power(self, value):
        self.dict['Power'] = value


class PowerSingleBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def SensorNumber(self):
        return self.dict['SensorNumber']

    def SensorNumber(self, value):
        self.dict['SensorNumber'] = value

    def ReadingWatt(self):
        return self.dict['ReadingWatt']

    def ReadingWatt(self, value):
        self.dict['ReadingWatt'] = value


class fwBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Firmware(self):
        return self.dict['Firmware']

    def Firmware(self, value):
        self.dict['Firmware'] = value


class fwSingleBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def Type(self):
        return self.dict['Type']

    def Type(self, value):
        self.dict['Type'] = value

    def Version(self):
        return self.dict['Version']

    def Version(self, value):
        self.dict['Version'] = value

    def Updateable(self):
        return self.dict['Updateable']

    def Updateable(self, value):
        self.dict['Updateable'] = value

    def SupportActivateType(self):
        return self.dict['SupportActivateType']

    def SupportActivateType(self, value):
        self.dict['SupportActivateType'] = value

    def toDict(self):
        return {"Name": self.Name, "Type": self.Type, "Version": self.Version, "Updateable": self.Updateable,
                "SupportActivateType": self.SupportActivateType}


# caplist=[]
# cap =CapabilitiesBean()
# a=[]
# a.append("1")
# a.append("2")
# cap.GetCommand=a
# cap.SetCommand=""

# caplist.append(cap)
# res = ResultBean()
# res.State="Success"
# res.Message=caplist

# print("111",repr(res))
# jsonstr = json.dumps(res, default=lambda o: o.__dict__, sort_keys=True, indent=4)
# print(jsonstr)

# single=fwSingleBean()
# single.Name=1
# single.Version="2x"
# single2=fwSingleBean()
# single2.Name="2"
# single2.Version="x"
# fw = fwBean()
# abc=[]
# abc.append(single)
# abc.append(single2)
# fw.Firmware=abc
#
# print(res.State)
# res.Message=[fw]
# jsonstr1 = json.dumps(res, default=lambda o: o.__dict__,sort_keys=True, indent=4)
# print(jsonstr1)


class NetBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def InterfaceName(self):
        return self.dict['InterfaceName']

    def InterfaceName(self, value):
        self.dict['InterfaceName'] = value

    def IPVersion(self):
        return self.dict['IPVersion']

    def IPVersion(self, value):
        self.dict['IPVersion'] = value

    def PermanentMACAddress(self):
        return self.dict['PermanentMACAddress']

    def PermanentMACAddress(self, value):
        self.dict['PermanentMACAddress'] = value

    def LanChannel(self):
        return self.dict['LanChannel']

    def LanChannel(self, value):
        self.dict['LanChannel'] = value

    def IPv4(self):
        return self.dict['IPv4']

    def IPv4(self, value):
        self.dict['IPv4'] = value

    def IPv6(self):
        return self.dict['IPv6']

    def IPv6(self, value):
        self.dict['IPv6'] = value

    def VLANInfo(self):
        return self.dict['VLANInfo']

    def VLANInfo(self, value):
        self.dict['VLANInfo'] = value


class vlanBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def VLANId(self):
        return self.dict['VLANId']

    def VLANId(self, value):
        self.dict['VLANId'] = value

    def VLANPriority(self):
        return self.dict['VLANPriority']

    def VLANPriority(self, value):
        self.dict['VLANPriority'] = value


class IPBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def AddressOrigin(self):
        return self.dict['AddressOrigin']

    def AddressOrigin(self, value):
        self.dict['AddressOrigin'] = value

    def Address(self):
        return self.dict['Address']

    def Address(self, value):
        self.dict['Address'] = value

    def Gateway(self):
        return self.dict['Gateway']

    def Gateway(self, value):
        self.dict['Gateway'] = value

    def vlanStatus(self):
        return self.dict['vlanStatus']

    def vlanStatus(self, value):
        self.dict['vlanStatus'] = value

    def vlanId(self):
        return self.dict['vlanId']

    def vlanId(self, value):
        self.dict['vlanId'] = value


class IPv4Bean(IPBean):
    def __init__(self):
        self.dict = collections.OrderedDict()

    def SubnetMask(self):
        return self.dict['SubnetMask']

    def SubnetMask(self, value):
        self.dict['SubnetMask'] = value


class IPv6Bean(IPBean):
    def __init__(self):
        self.dict = collections.OrderedDict()

    def PrefixLength(self):
        return self.dict['PrefixLength']

    def PrefixLength(self, value):
        self.dict['PrefixLength'] = value

    def Index(self):
        return self.dict['Index']

    def Index(self, value):
        self.dict['Index'] = value


class PSUBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def PsuPresentTotalPower(self):
        return self.dict['PsuPresentTotalPower']

    def PsuPresentTotalPower(self, value):
        self.dict['PsuPresentTotalPower'] = value

    def PsuRatedPower(self):
        return self.dict['PsuRatedPower']

    def PsuRatedPower(self, value):
        self.dict['PsuRatedPower'] = value

    def PsuStatus(self):
        return self.dict['PsuStatus']

    def PsuStatus(self, value):
        self.dict['PsuStatus'] = value

    def PSU(self):
        return self.dict['PSU']

    def PSU(self, value):
        self.dict['PSU'] = value


class PSUSingleBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Protocol(self):
        return self.dict['Protocol']

    def Protocol(self, value):
        self.dict['Protocol'] = value

    def PowerOutputWatts(self):
        return self.dict['PowerOutputWatts']

    def PowerOutputWatts(self, value):
        self.dict['PowerOutputWatts'] = value

    def InputAmperage(self):
        return self.dict['InputAmperage']

    def InputAmperage(self, value):
        self.dict['InputAmperage'] = value

    def ActiveStandby(self):
        return self.dict['ActiveStandby']

    def ActiveStandby(self, value):
        self.dict['ActiveStandby'] = value

    def OutputVoltage(self):
        return self.dict['OutputVoltage']

    def OutputVoltage(self, value):
        self.dict['OutputVoltage'] = value

    def PowerInputWatts(self):
        return self.dict['PowerInputWatts']

    def PowerInputWatts(self, value):
        self.dict['PowerInputWatts'] = value

    def OutputAmperage(self):
        return self.dict['OutputAmperage']

    def OutputAmperage(self, value):
        self.dict['OutputAmperage'] = value

    def PartNumber(self):
        return self.dict['PartNumber']

    def PartNumber(self, value):
        self.dict['PartNumber'] = value

    def PowerSupplyType(self):
        return self.dict['PowerSupplyType']

    def PowerSupplyType(self, value):
        self.dict['PowerSupplyType'] = value

    def LineInputVoltage(self):
        return self.dict['LineInputVoltage']

    def LineInputVoltage(self, value):
        self.dict['LineInputVoltage'] = value

    def PowerCapacityWatts(self):
        return self.dict['owerCapacityWatts']

    def PowerCapacityWatts(self, value):
        self.dict['PowerCapacityWatts'] = value

    def FirmwareVersion(self):
        return self.dict['FirmwareVersion']

    def FirmwareVersion(self, value):
        self.dict['FirmwareVersion'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def Temperature(self):
        return self.dict['Temperature']

    def Temperature(self, value):
        self.dict['Temperature'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Present(self):
        return self.dict['Present']

    def Present(self, value):
        self.dict['Present'] = value

    def Mode(self):
        return self.dict['Mode']

    def Mode(self, value):
        self.dict['Mode'] = value


class FanBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def FanSpeedLevelPercents(self):
        return self.dict['FanSpeedLevelPercents']

    def FanSpeedLevelPercents(self, value):
        self.dict['FanSpeedLevelPercents'] = value

    def FanSpeedAdjustmentMode(self):
        return self.dict['FanSpeedAdjustmentMode']

    def FanSpeedAdjustmentMode(self, value):
        self.dict['FanSpeedAdjustmentMode'] = value

    def FanTotalPowerWatts(self):
        return self.dict['FanTotalPowerWatts']

    def FanTotalPowerWatts(self, value):
        self.dict['FanTotalPowerWatts'] = value

    def FanManualModeTimeoutSeconds(self):
        return self.dict['FanManualModeTimeoutSeconds']

    def FanManualModeTimeoutSeconds(self, value):
        self.dict['FanManualModeTimeoutSeconds'] = value

    def Fan(self):
        return self.dict['Fan']

    def Fan(self, value):
        self.dict['Fan'] = value


class Fan():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def RatedSpeedRPM(self):
        return self.dict['RatedSpeedRPM']

    def RatedSpeedRPM(self, value):
        self.dict['RatedSpeedRPM'] = value

    def SpeedRPM(self):
        return self.dict['SpeedRPM']

    def SpeedRPM(self, value):
        self.dict['SpeedRPM'] = value

    def LowerThresholdRPM(self):
        return self.dict['LowerThresholdRPM']

    def LowerThresholdRPM(self, value):
        self.dict['LowerThresholdRPM'] = value

    def DutyRatio(self):
        return self.dict['DutyRatio']

    def DutyRatio(self, value):
        self.dict['DutyRatio'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value


class CPUBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def TotalPowerWatts(self):
        return self.dict['TotalPowerWatts']

    def TotalPowerWatts(self, value):
        self.dict['TotalPowerWatts'] = value

    def CPU(self):
        return self.dict['CPU']

    def CPU(self, value):
        self.dict['CPU'] = value


class Cpu():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def L1CacheKiB(self):
        return self.dict['L1CacheKiB']

    def L1CacheKiB(self, value):
        self.dict['L1CacheKiB'] = value

    def L2CacheKiB(self):
        return self.dict['L2CacheKiB']

    def L2CacheKiB(self, value):
        self.dict['L2CacheKiB'] = value

    def L3CacheKiB(self):
        return self.dict['L3CacheKiB']

    def L3CacheKiB(self, value):
        self.dict['L3CacheKiB'] = value

    def Temperature(self):
        return self.dict['Temperature']

    def Temperature(self, value):
        self.dict['Temperature'] = value

    def EnabledSetting(self):
        return self.dict['EnabledSetting']

    def EnabledSetting(self, value):
        self.dict['EnabledSetting'] = value

    def ProcessorType(self):
        return self.dict['ProcessorType']

    def ProcessorType(self, value):
        self.dict['ProcessorType'] = value

    def ProcessorArchitecture(self):
        return self.dict['ProcessorArchitecture']

    def ProcessorArchitecture(self, value):
        self.dict['ProcessorArchitecture'] = value

    def InstructionSet(self):
        return self.dict['InstructionSet']

    def InstructionSet(self, value):
        self.dict['InstructionSet'] = value

    def MaxSpeedMHz(self):
        return self.dict['MaxSpeedMHz']

    def MaxSpeedMHz(self, value):
        self.dict['MaxSpeedMHz'] = value

    def TotalCores(self):
        return self.dict['TotalCores']

    def TotalCores(self, value):
        self.dict['TotalCores'] = value

    def TotalThreads(self):
        return self.dict['TotalThreads']

    def TotalThreads(self, value):
        self.dict['TotalThreads'] = value

    def Socket(self):
        return self.dict['Socket']

    def Socket(self, value):
        self.dict['Socket'] = value

    def PPIN(self):
        return self.dict['PPIN']

    def PPIN(self, value):
        self.dict['PPIN'] = value

    def TDP(self):
        return self.dict['TDP']

    def TDP(self, value):
        self.dict['TDP'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value


class MemoryBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def TotalSystemMemoryGiB(self):
        return self.dict['TotalSystemMemoryGiB']

    def TotalSystemMemoryGiB(self, value):
        self.dict['TotalSystemMemoryGiB'] = value

    def TotalPowerWatts(self):
        return self.dict['TotalPowerWatts']

    def TotalPowerWatts(self, value):
        self.dict['TotalPowerWatts'] = value

    def Memory(self):
        return self.dict['Memory']

    def Memory(self, value):
        self.dict['Memory'] = value


class Memory():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def MemId(self):
        return self.dict['MemId']

    def MemId(self, value):
        self.dict['MemId'] = value

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def CapacityMiB(self):
        return self.dict['CapacityMiB']

    def CapacityMiB(self, value):
        self.dict['CapacityMiB'] = value

    def OperatingSpeedMhz(self):
        return self.dict['OperatingSpeedMhz']

    def OperatingSpeedMhz(self, value):
        self.dict['OperatingSpeedMhz'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def MemoryDeviceType(self):
        return self.dict['MemoryDeviceType']

    def MemoryDeviceType(self, value):
        self.dict['MemoryDeviceType'] = value

    def DataWidthBits(self):
        return self.dict['DataWidthBits']

    def DataWidthBits(self, value):
        self.dict['DataWidthBits'] = value

    def RankCount(self):
        return self.dict['RankCount']

    def RankCount(self, value):
        self.dict['RankCount'] = value

    def PartNumber(self):
        return self.dict['PartNumber']

    def PartNumber(self, value):
        self.dict['PartNumber'] = value

    def Technology(self):
        return self.dict['Technology']

    def Technology(self, value):
        self.dict['Technology'] = value

    def MinVoltageMillivolt(self):
        return self.dict['MinVoltageMillivolt']

    def MinVoltageMillivolt(self, value):
        self.dict['MinVoltageMillivolt'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value


class DiskBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def Disk(self):
        return self.dict['Disk']

    def Disk(self, value):
        self.dict['Disk'] = value


class Disk():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Protocol(self):
        return self.dict['Protocol']

    def Protocol(self, value):
        self.dict['Protocol'] = value

    def FailurePredicted(self):
        return self.dict['FailurePredicted']

    def FailurePredicted(self, value):
        self.dict['FailurePredicted'] = value

    def CapacityGiB(self):
        return self.dict['CapacityGiB']

    def CapacityGiB(self, value):
        self.dict['CapacityGiB'] = value

    def HotspareType(self):
        return self.dict['HotspareType']

    def HotspareType(self, value):
        self.dict['HotspareType'] = value

    def IndicatorLED(self):
        return self.dict['IndicatorLED']

    def IndicatorLED(self, value):
        self.dict['IndicatorLED'] = value

    def PredictedMediaLifeLeftPercent(self):
        return self.dict['PredictedMediaLifeLeftPercent']

    def PredictedMediaLifeLeftPercent(self, value):
        self.dict['PredictedMediaLifeLeftPercent'] = value

    def MediaType(self):
        return self.dict['MediaType']

    def MediaType(self, value):
        self.dict['MediaType'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def CapableSpeedGbs(self):
        return self.dict['CapableSpeedGbs']

    def CapableSpeedGbs(self, value):
        self.dict['CapableSpeedGbs'] = value

    def NegotiatedSpeedGbs(self):
        return self.dict['NegotiatedSpeedGbs']

    def NegotiatedSpeedGbs(self, value):
        self.dict['NegotiatedSpeedGbs'] = value

    def Revision(self):
        return self.dict['Revision']

    def Revision(self, value):
        self.dict['Revision'] = value

    def StatusIndicator(self):
        return self.dict['StatusIndicator']

    def StatusIndicator(self, value):
        self.dict['StatusIndicator'] = value

    def TemperatureCelsius(self):
        return self.dict['TemperatureCelsius']

    def TemperatureCelsius(self, value):
        self.dict['TemperatureCelsius'] = value

    def HoursOfPoweredUp(self):
        return self.dict['HoursOfPoweredUp']

    def HoursOfPoweredUp(self, value):
        self.dict['HoursOfPoweredUp'] = value

    def FirmwareStatus(self):
        return self.dict['FirmwareStatus']

    def FirmwareStatus(self, value):
        self.dict['FirmwareStatus'] = value

    def SASAddress(self):
        return self.dict['SASAddress']

    def SASAddress(self, value):
        self.dict['SASAddress'] = value

    def PatrolState(self):
        return self.dict['PatrolState']

    def PatrolState(self, value):
        self.dict['PatrolState'] = value

    def RebuildState(self):
        return self.dict['RebuildState']

    def RebuildState(self, value):
        self.dict['RebuildState'] = value

    def RebuildProgress(self):
        return self.dict['RebuildProgress']

    def RebuildProgress(self, value):
        self.dict['RebuildProgress'] = value

    def SpareforLogicalDrives(self):
        return self.dict['SpareforLogicalDrives']

    def SpareforLogicalDrives(self, value):
        self.dict['SpareforLogicalDrives'] = value

    def Volumes(self):
        return self.dict['Volumes']

    def Volumes(self, value):
        self.dict['Volumes'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value


'''
RaidCardBean
'''


class RaidCardBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def RaidCard(self):
        return self.dict['RaidCard']

    def RaidCard(self, value):
        self.dict['RaidCard'] = value


class Raid():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value

    def Controller(self):
        return self.dict['Controller']

    def Controller(self, value):
        self.dict['Controller'] = value


class Controller():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def SupportedDeviceProtocols(self):
        return self.dict['SupportedDeviceProtocols']

    def SupportedDeviceProtocols(self, value):
        self.dict['SupportedDeviceProtocols'] = value

    def SASAddress(self):
        return self.dict['SASAddress']

    def SASAddress(self, value):
        self.dict['SASAddress'] = value

    def ConfigurationVersion(self):
        return self.dict['ConfigurationVersion']

    def ConfigurationVersion(self, value):
        self.dict['ConfigurationVersion'] = value

    def MaintainPDFailHistory(self):
        return self.dict['MaintainPDFailHistory']

    def MaintainPDFailHistory(self, value):
        self.dict['MaintainPDFailHistory'] = value

    def CopyBackState(self):
        return self.dict['CopyBackState']

    def CopyBackState(self, value):
        self.dict['CopyBackState'] = value

    def JBODState(self):
        return self.dict['JBODState']

    def JBODState(self, value):
        self.dict['JBODState'] = value

    def MinStripeSizeBytes(self):
        return self.dict['MinStripeSizeBytes']

    def MinStripeSizeBytes(self, value):
        self.dict['MinStripeSizeBytes'] = value

    def MaxStripeSizeBytes(self):
        return self.dict['MaxStripeSizeBytes']

    def MaxStripeSizeBytes(self, value):
        self.dict['MaxStripeSizeBytes'] = value

    def MemorySizeMiB(self):
        return self.dict['MemorySizeMiB']

    def MemorySizeMiB(self, value):
        self.dict['MemorySizeMiB'] = value

    def SupportedRAIDLevels(self):
        return self.dict['SupportedRAIDLevels']

    def SupportedRAIDLevels(self, value):
        self.dict['SupportedRAIDLevels'] = value

    def DDRECCCount(self):
        return self.dict['DDRECCCount']

    def DDRECCCount(self, value):
        self.dict['DDRECCCount'] = value


'''
LogicDiskBean
'''


class LogicDiskBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def LogicDisk(self):
        return self.dict['LogicDisk']

    def LogicDisk(self, value):
        self.dict['LogicDisk'] = value


class LogicDisk():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def LogicDiskName(self):
        return self.dict['LogicDiskName']

    def LogicDiskName(self, value):
        self.dict['LogicDiskName'] = value

    def RaidControllerID(self):
        return self.dict['RaidControllerID']

    def RaidControllerID(self, value):
        self.dict['RaidControllerID'] = value

    def RaidLevel(self):
        return self.dict['RaidLevel']

    def RaidLevel(self, value):
        self.dict['RaidLevel'] = value

    def CapacityGiB(self):
        return self.dict['CapacityGiB']

    def CapacityGiB(self, value):
        self.dict['CapacityGiB'] = value

    def OptimumIOSizeBytes(self):
        return self.dict['OptimumIOSizeBytes']

    def OptimumIOSizeBytes(self, value):
        self.dict['OptimumIOSizeBytes'] = value

    def RedundantType(self):
        return self.dict['RedundantType']

    def RedundantType(self, value):
        self.dict['RedundantType'] = value

    def DefaultReadPolicy(self):
        return self.dict['DefaultReadPolicy']

    def DefaultReadPolicy(self, value):
        self.dict['DefaultReadPolicy'] = value

    def DefaultWritePolicy(self):
        return self.dict['DefaultWritePolicy']

    def DefaultWritePolicy(self, value):
        self.dict['DefaultWritePolicy'] = value

    def DefaultCachePolicy(self):
        return self.dict['DefaultCachePolicy']

    def DefaultCachePolicy(self, value):
        self.dict['DefaultCachePolicy'] = value

    def CurrentReadPolicy(self):
        return self.dict['CurrentReadPolicy']

    def CurrentReadPolicy(self, value):
        self.dict['CurrentReadPolicy'] = value

    def CurrentWritePolicy(self):
        return self.dict['CurrentWritePolicy']

    def CurrentWritePolicy(self, value):
        self.dict['CurrentWritePolicy'] = value

    def CurrentCachePolicy(self):
        return self.dict['CurrentCachePolicy']

    def CurrentCachePolicy(self, value):
        self.dict['CurrentCachePolicy'] = value

    def AccessPolicy(self):
        return self.dict['AccessPolicy']

    def AccessPolicy(self, value):
        self.dict['AccessPolicy'] = value

    def BGIEnable(self):
        return self.dict['BGIEnable']

    def BGIEnable(self, value):
        self.dict['BGIEnable'] = value

    def BootEnable(self):
        return self.dict['BootEnable']

    def BootEnable(self, value):
        self.dict['BootEnable'] = value

    def DriveCachePolicy(self):
        return self.dict['DriveCachePolicy']

    def DriveCachePolicy(self, value):
        self.dict['DriveCachePolicy'] = value

    def SSDCachecadeVolume(self):
        return self.dict['SSDCachecadeVolume']

    def SSDCachecadeVolume(self, value):
        self.dict['SSDCachecadeVolume'] = value

    def ConsistencyCheck(self):
        return self.dict['ConsistencyCheck']

    def ConsistencyCheck(self, value):
        self.dict['ConsistencyCheck'] = value

    def SSDCachingEnable(self):
        return self.dict['SSDCachingEnable']

    def SSDCachingEnable(self, value):
        self.dict['SSDCachingEnable'] = value

    def Drives(self):
        return self.dict['Drives']

    def Drives(self, value):
        self.dict['Drives'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value

    '''
    NicBean
    '''


class NicAllBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def NIC(self):
        return self.dict['NIC']

    def NIC(self, value):
        self.dict['NIC'] = value


class NICBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Serialnumber(self):
        return self.dict['Serialnumber']

    def Serialnumber(self, value):
        self.dict['Serialnumber'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value

    def Controller(self):
        return self.dict['Controller']

    def Controller(self, value):
        self.dict['Controller'] = value


class NICController():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Manufacturer(self):
        return self.dict['Manufacturer']

    def Manufacturer(self, value):
        self.dict['Manufacturer'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Serialnumber(self):
        return self.dict['Serialnumber']

    def Serialnumber(self, value):
        self.dict['Serialnumber'] = value

    def FirmwareVersion(self):
        return self.dict['FirmwareVersion']

    def FirmwareVersion(self, value):
        self.dict['FirmwareVersion'] = value

    def PortCount(self):
        return self.dict['PortCount']

    def PortCount(self, value):
        self.dict['PortCount'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value


class NicPort():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def MACAddress(self):
        return self.dict['MACAddress']

    def MACAddress(self, value):
        self.dict['MACAddress'] = value

    def LinkStatus(self):
        return self.dict['LinkStatus']

    def LinkStatus(self, value):
        self.dict['LinkStatus'] = value

    def MediaType(self):
        return self.dict['MediaType']

    def MediaType(self, value):
        self.dict['MediaType'] = value

    # "{
    # ""OverallHealth"": ""OK"",
    # ""Maximum"": ""2"",
    # ""NIC"": [
    # {
    # ""CommonName"": ""LOM"",
    # ""Location"": ""mainboard"",
    # ""Manufacturer"": ""intel"",
    # ""Model"": ""xxxxx"",
    # ""Serialnumber"": ""xxxxxxx"",
    # ""State"": ""Enabled"",
    # ""Health"": ""OK"",
    # ""Controller"": [
    # {
    # ""Id"": ""0"",
    # ""Manufacturer"": ""intel"",
    # ""Model"": ""X710"",
    # ""Serialnumber"": ""xxxxxx"",
    # ""FirmwareVersion"": ""1.5"",
    # ""PortCount"": ""2"",
    # ""Port"": [
    # {
    # ""Id"": ""0"",
    # ""MACAddress"": ""00:12:34:56:78:90"",
    # ""LinkStatus"": ""up""
    # },
    # {
    # ""Id"": ""1”,
    # ""MACAddress"": ""00:12:34:56:78:91“,
    # ""LinkStatus"": ""down”
    ##


'''
SensorBean
'''
'''
class SensorBean():
    def Name(self):
        return self.Name

    def Name(self, value):
        self.Name = value

    def SensorNumber(self):
        return self.SensorNumber

    def SensorNumber(self, value):
        self.SensorNumber = value

    def UpperThresholdFatal(self):
        return self.UpperThresholdFatal

    def UpperThresholdFatal(self, value):
        self.UpperThresholdFatal = value

    def UpperThresholdCritical(self):
        return self.UpperThresholdCritical

    def UpperThresholdCritical(self, value):
        self.UpperThresholdCritical = value

    def UpperThresholdNonCritical(self):
        return self.UpperThresholdNonCritical

    def UpperThresholdNonCritical(self, value):
        self.UpperThresholdNonCritical = value

    def ReadingCelsius(self):
        return self.ReadingCelsius

    def ReadingCelsius(self, value):
        self.ReadingCelsius = value

    def LowerThresholdNonCritical(self):
        return self.LowerThresholdNonCritical

    def LowerThresholdNonCritical(self, value):
        self.LowerThresholdNonCritical = value

    def LowerThresholdCritical(self):
        return self.LowerThresholdCritical

    def LowerThresholdCritical(self, value):
        self.LowerThresholdCritical = value

    def LowerThresholdFatal(self):
        return self.LowerThresholdFatal

    def LowerThresholdFatal(self, value):
        self.LowerThresholdFatal = value
'''


class ServiceBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Service(self):
        return self.dict['Service']

    def Service(self, value):
        self.dict['Service'] = value


class ServiceSingleBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value

    def InterfaceName(self):
        return self.dict['InterfaceName']

    def InterfaceName(self, value):
        self.dict['InterfaceName'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value

    def Port2(self):
        return self.dict['Port2']

    def Port2(self, value):
        self.dict['Port2'] = value

    def SSLEnable(self):
        return self.dict['SSLEnable']

    def SSLEnable(self, value):
        self.dict['SSLEnable'] = value

    def TimeOut(self):
        return self.dict['TimeOut']

    def TimeOut(self, value):
        self.dict['TimeOut'] = value

    def MaximumSessions(self):
        return self.dict['MaximumSessions']

    def MaximumSessions(self, value):
        self.dict['MaximumSessions'] = value

    def ActiveSessions(self):
        return self.dict['ActiveSessions']

    def ActiveSessions(self, value):
        self.dict['ActiveSessions'] = value


class UserBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def UserId(self):
        return self.dict['UserId']

    def UserId(self, value):
        self.dict['UserId'] = value

    def UserName(self):
        return self.dict['UserName']

    def UserName(self, value):
        self.dict['UserName'] = value

    def RoleId(self):
        return self.dict['RoleId']

    def RoleId(self, value):
        self.dict['RoleId'] = value

    def Privilege(self):
        return self.dict['Privilege']

    def Privilege(self, value):
        self.dict['Privilege'] = value

    def Locked(self):
        return self.dict['Locked']

    def Locked(self, value):
        self.dict['Locked'] = value

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value


class PcieBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def OverallHealth(self):
        return self.dict['OverallHealth']

    def OverallHealth(self, value):
        self.dict['OverallHealth'] = value

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def PCIeDevice(self):
        return self.dict['PCIeDevice']

    def PCIeDevice(self, value):
        self.dict['PCIeDevice'] = value


class Pcie():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def CommonName(self):
        return self.dict['CommonName']

    def CommonName(self, value):
        self.dict['CommonName'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def Type(self):
        return self.dict['Type']

    def Type(self, value):
        self.dict['Type'] = value

    def SlotBus(self):
        return self.dict['SlotBus']

    def SlotBus(self, value):
        self.dict['SlotBus'] = value

    def SlotDevice(self):
        return self.dict['SlotDevice']

    def SlotDevice(self, value):
        self.dict['SlotDevice'] = value

    def SlotFunction(self):
        return self.dict['SlotFunction']

    def SlotFunction(self, value):
        self.dict['SlotFunction'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Health(self):
        return self.dict['Health']

    def Health(self, value):
        self.dict['Health'] = value

    def DeviceID(self):
        return self.dict['DeviceID']

    def DeviceID(self, value):
        self.dict['DeviceID'] = value

    def VendorID(self):
        return self.dict['VendorID']

    def VendorID(self, value):
        self.dict['VendorID'] = value

    def RatedLinkSpeed(self):
        return self.dict['RatedLinkSpeed']

    def RatedLinkSpeed(self, value):
        self.dict['RatedLinkSpeed'] = value

    def RatedLinkWidth(self):
        return self.dict['RatedLinkWidth']

    def RatedLinkWidth(self, value):
        self.dict['RatedLinkWidth'] = value

    def CurrentLinkSpeed(self):
        return self.dict['CurrentLinkSpeed']

    def CurrentLinkSpeed(self, value):
        self.dict['CurrentLinkSpeed'] = value

    def CurrentLinkWidth(self):
        return self.dict['CurrentLinkWidth']

    def CurrentLinkWidth(self, value):
        self.dict['CurrentLinkWidth'] = value

    def BoardLocation(self):
        return self.dict['BoardLocation']

    def BoardLocation(self, value):
        self.dict['BoardLocation'] = value


class TemperatureBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Temperature(self):
        return self.dict['Temperature']

    def Temperature(self, value):
        self.dict['Temperature'] = value


class Temperature():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def SensorNumber(self):
        return self.dict['SensorNumber']

    def SensorNumber(self, value):
        self.dict['SensorNumber'] = value

    def Status(self):
        return self.dict['Status']

    def Status(self, value):
        self.dict['Status'] = value

    def UpperThresholdFatal(self):
        return self.dict['UpperThresholdFatal']

    def UpperThresholdFatal(self, value):
        self.dict['UpperThresholdFatal'] = value

    def UpperThresholdCritical(self):
        return self.dict['UpperThresholdCritical']

    def UpperThresholdCritical(self, value):
        self.dict['UpperThresholdCritical'] = value

    def UpperThresholdNonCritical(self):
        return self.dict['UpperThresholdNonCritical']

    def UpperThresholdNonCritical(self, value):
        self.dict['UpperThresholdNonCritical'] = value

    def ReadingCelsius(self):
        return self.dict['ReadingCelsius']

    def ReadingCelsius(self, value):
        self.dict['ReadingCelsius'] = value

    def LowerThresholdNonCritical(self):
        return self.dict['LowerThresholdNonCritical']

    def LowerThresholdNonCritical(self, value):
        self.dict['LowerThresholdNonCritical'] = value

    def LowerThresholdCritical(self):
        return self.dict['LowerThresholdCritical']

    def LowerThresholdCritical(self, value):
        self.dict['LowerThresholdCritical'] = value

    def LowerThresholdFatal(self):
        return self.dict['LowerThresholdFatal']

    def LowerThresholdFatal(self, value):
        self.dict['LowerThresholdFatal'] = value


class VoltBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Voltage(self):
        return self.dict['Voltage']

    def Voltage(self, value):
        self.dict['Voltage'] = value


class Voltage():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def SensorNumber(self):
        return self.dict['SensorNumber']

    def SensorNumber(self, value):
        self.dict['SensorNumber'] = value

    def Status(self):
        return self.dict['Status']

    def Status(self, value):
        self.dict['Status'] = value

    def UpperThresholdFatal(self):
        return self.dict['UpperThresholdFatal']

    def UpperThresholdFatal(self, value):
        self.dict['UpperThresholdFatal'] = value

    def UpperThresholdCritical(self):
        return self.dict['UpperThresholdCritical']

    def UpperThresholdCritical(self, value):
        self.dict['UpperThresholdCritical'] = value

    def UpperThresholdNonCritical(self):
        return self.dict['UpperThresholdNonCritical']

    def UpperThresholdNonCritical(self, value):
        self.dict['UpperThresholdNonCritical'] = value

    def ReadingVolts(self):
        return self.dict['ReadingVolts']

    def ReadingVolts(self, value):
        self.dict['ReadingVolts'] = value

    def LowerThresholdNonCritical(self):
        return self.dict['LowerThresholdNonCritical']

    def LowerThresholdNonCritical(self, value):
        self.dict['LowerThresholdNonCritical'] = value

    def LowerThresholdCritical(self):
        return self.dict['LowerThresholdCritical']

    def LowerThresholdCritical(self, value):
        self.dict['LowerThresholdCritical'] = value

    def LowerThresholdFatal(self):
        return self.dict['LowerThresholdFatal']

    def LowerThresholdFatal(self, value):
        self.dict['LowerThresholdFatal'] = value


class SensorBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Maximum(self):
        return self.dict['Maximum']

    def Maximum(self, value):
        self.dict['Maximum'] = value

    def Sensor(self):
        return self.dict['Sensor']

    def Sensor(self, value):
        self.dict['Sensor'] = value


class Sensor():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def SensorNumber(self):
        return self.dict['SensorNumber']

    def SensorNumber(self, value):
        self.dict['SensorNumber'] = value

    def SensorName(self):
        return self.dict['SensorName']

    def SensorName(self, value):
        self.dict['SensorName'] = value

    def Reading(self):
        return self.dict['Reading']

    def Reading(self, value):
        self.dict['Reading'] = value

    def Unit(self):
        return self.dict['Unit']

    def Unit(self, value):
        self.dict['Unit'] = value

    def Status(self):
        return self.dict['Status']

    def Status(self, value):
        self.dict['Status'] = value

    def unr(self):
        return self.dict['unr']

    def unr(self, value):
        self.dict['unr'] = value

    def uc(self):
        return self.dict['uc']

    def uc(self, value):
        self.dict['uc'] = value

    def unc(self):
        return self.dict['unr']

    def unc(self, value):
        self.dict['unc'] = value

    def lnc(self):
        return self.dict['lnc']

    def lnc(self, value):
        self.dict['lnc'] = value

    def lc(self):
        return self.dict['lc']

    def lc(self, value):
        self.dict['lc'] = value

    def lnr(self):
        return self.dict['lnr']

    def lnr(self, value):
        self.dict['lnr'] = value


class HealthBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def PowerStatus(self):
        return self.dict['PowerStatus']

    def PowerStatus(self, value):
        self.dict['PowerStatus'] = value

    def UIDLed(self):
        return self.dict['UIDLed']

    def UIDLed(self, value):
        self.dict['UIDLed'] = value

    def System(self):
        return self.dict['System']

    def System(self, value):
        self.dict['System'] = value

    def CPU(self):
        return self.dict['CPU']

    def CPU(self, value):
        self.dict['CPU'] = value

    def Memory(self):
        return self.dict['Memory']

    def Memory(self, value):
        self.dict['Memory'] = value

    def Storage(self):
        return self.dict['Storage']

    def Storage(self, value):
        self.dict['Storage'] = value

    def Network(self):
        return self.dict['Network']

    def Network(self, value):
        self.dict['Network'] = value

    def PSU(self):
        return self.dict['PSU']

    def PSU(self, value):
        self.dict['PSU'] = value

    def Fan(self):
        return self.dict['Fan']

    def Fan(self, value):
        self.dict['Fan'] = value

    def Voltage(self):
        return self.dict['Voltage']

    def Voltage(self, value):
        self.dict['Voltage'] = value

    def Temperature(self):
        return self.dict['Temperature']

    def Temperature(self, value):
        self.dict['Temperature'] = value

    def ME(self):
        return self.dict['ME']

    def ME(self, value):
        self.dict['ME'] = value


class BiosDebugBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value


class BiosResultBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ApplyTime(self):
        return self.dict['ApplyTime']

    def ApplyTime(self, value):
        self.dict['ApplyTime'] = value

    def ApplyResult(self):
        return self.dict['ApplyResult']

    def ApplyResult(self, value):
        self.dict['ApplyResult'] = value

    def ApplyDetail(self):
        return self.dict['ApplyTime']

    def ApplyDetail(self, value):
        self.dict['ApplyDetail'] = value


# "ApplyTime": "2017-08-11T15:30:36+00:00",
# "ApplyResult": "Failure",
# "ApplyDetail":
# "{
# ""System"": ""Warning"",
# ""CPU"": ""OK"",
# ""Memory"": ""Warning"",
# ""Storage"": ""OK"",
# ""Network"": ""OK"",
# ""PSU"": ""Warning"",
# ""Fan"": ""OK""
# }"
# "{
# Maximum"": ""180"",
# ""Sensor"": [
# {
# ""SensorNumber"": ""1"",
# ""SensorName"": ""inlet temp"",
# ""Reading"": ""23.5"",
# ""Unit"": ""degrees C"",
# ""Status"": ""ok"",
# ""unr"": ""45.0"",
# ""uc"": ""42.0"",
# ""unc"": ""none"",
# ""lnc"": ""none"",
# ""lc"": ""4.0"",
# ""lnr"": ""0.0""
# ......
# ]
# }"
# "{
# ""User"": [
# {
# ""UserId"": ""2"",
# ""UserName"": ""root"",
# ""RoleId"": ""Administrator"",
# ""Privilege"":[],
# ""Locked"": ""False"",
# ""Enabled"": ""True""
# },
# {
# ""UserId"": ""3"",
# ""UserName"": ""test"",
# ""RoleId"": ""NoAccess"",
# ""Privilege"":[""KVM"",""SOL""],
# ""Locked"": ""False"",
# ""Enabled"": ""True""
# }
# ……
# ]
# }"
# "{
# ""System"": ""Warning"",
# ""CPU"": ""OK"",
# ""Memory"": ""Warning"",
# ""Storage"": ""OK"",
# ""Network"": ""OK"",
# ""PSU"": ""Warning"",
# ""Fan"": ""OK""
# }"
# "{
# ""BootDevice"": ""PXE"",
# ""BootMode"": ""Legacy"",
# ""Effective"": ""Once""
# }"
# "{
# ......
# ]
# }"
# "{
# Maximum"": ""180"",
# ""Sensor"": [
# {
# ""SensorNumber"": ""1"",
# ""SensorName"": ""inlet temp"",
# ""Reading"": ""23.5"",
# ""Unit"": ""degrees C"",
# ""Status"": ""ok"",
# ""unr"": ""45.0"",
# ""uc"": ""42.0"",
# ""unc"": ""none"",
# ""lnc"": ""none"",
# ""lc"": ""4.0"",
# ""lnr"": ""0.0""
# },
# {
# ""SensorNumber"": ""2"",
# ""SensorName"": ""outlet temp"",
# ""Reading"": ""23.5"",
# ""Unit"": ""degrees C"",
# ""Status"": ""ok"",
# ""unr"": ""90.0"",
# ""uc"": ""85.0"",
# ""unc"": ""none"",
# ""lnc"": ""none"",
# ""lc"": ""4.0"",
# ""lnr"": ""0.0""
# },
# ......
# ]
# }"
# "{
# ""HostName"": ""SUX03061289"",
# ""FQDN"": ""test.com"",
# ""DNSAddressOrigin"": ""Static/DHCP"",
# ""PreferredServer"": ""x.x.x.x"",
# ""AlternateServer"": ""x.x.x.x""
# }"
# "{
# ""MLCSpatialPrefetcherEnable"": ""Enabled"",
# ""CoherencySupport"": ""Enabled"",
# ""InterruptRemap"": ""Enabled"",
# ""OSCx"": ""ACPIC2"",
# ""ProcessorEISTEnable"": ""Enabled"",
# ""DCUStreamerPrefetcherEnable"": ""Enabled"",
# ""OSWDTTimeout"": ""5"",
# ""PCIeARISupport"": ""Disabled"",
# ""ATS"": ""Enabled"",
# ""BMCWDTTimeout"": ""5"",
# ""QuietBoot"": ""Disabled"",
# ......
# }"
# "{
# ""MLCSpatialPrefetcherEnable"": ""Disabled"",
# ""CoherencySupport"": ""Disabled"",
# ......
# }"
# "{
# ""ApplyTime"": ""2017-08-11T15:30:36+00:00"",
# ""ApplyResult"": ""Failure"",
# ""ApplyDetail"": [
# {
# ""Attribute"": ""MLCSpatialPrefetcherEnable"",
# ""FailReason"": ""Value out of bounds""
# },
# {
# ""Attribute"": ""CoherencySupport"",
# ""FailReason"": ""Value out of bounds""
# },
# ......
# ]
# }"
# "{
# ""EventLog"": [
# {
# ""Id"": ""1"",
# ""Severity"": ""Critical"",
# ""EventTimestamp"": ""2017-08-11T15:30:36+00:00"",
# ""Entity"": ""CPU0"",
# ""EntitySN"": ""0321201809234378"",
# ""Message"": ""CPU0 Thermal trip."",
# ""MessageId"": ""iBMCEvents.2.0.BmcEventSelClearedInfo"",
# ""EventId"": ""0x5A00010F"",
# ""Status"": ""Assert""
# },
# {
# ""Id"": ""2"",
# ""Severity"": ""OK"",
# ""EventTimestamp"": ""2017-08-11T15:30:36+00:00"",
# ""Entity"": ""BMC"",
# ""EntitySN"": ""0321201809234378"",
# ""Message"": ""BMC event records are cleared."",
# ""MessageId"": ""iBMCEvents.2.0.BmcEventSelClearedInfo"",
# ""EventId"": ""0x1A00000F"",
# ""Status"": ""Deassert""
# }
# ......
# ]
# }"
# "{
# ""HealthEvents"": [
# {
# ""Id"": ""1"",
# ""Severity"": ""Critical"",
# ""EventTimestamp"": ""2017-08-11T15:30:36+00:00"",
# ""Entity"": ""CPU0"",
# ""Message"": ""CPU0 Thermal trip."",
# ""MessageId"": ""BMCEvents.2.0.BmcEventThermalTrip"",
# ""EventId"": ""0x5A00010F""
# },
# {
# ""Id"": ""2"",
# ""Severity"": ""Warning"",
# ""EventTimestamp"": ""2017-08-10T09:18:10+00:00"",
# ""Entity"": ""BMC"",
# ""Message"": ""BMC event records are cleared."",
# ""MessageId"": ""BMCEvents.2.0.BmcEventSelClearedInfo"",
# ""EventId"": ""0x1A00000F""
# },
# ......
# ]
# }"
# "{
# ""Service"":[
# {
# ""Name"": ""VirtualMedia"",
# ""Enabled"": ""Enable"",
# ""Port"": ""8208"",
# ""Port2"":""18208"",
# ""SSLEnable"":""Enable""
# },
# {
# ""Name"": ""KVM"",
# ""Enabled"": ""Enable"",
# ""Port"": ""2198"",
# ""Port2"":""12198"",
# ""SSLEnable"":""Enable""
# },
# {
# ""Name"": ""IPMI""，
# ""Enabled"": ""Enable""，
# ""Port"": ""623"",
# ""Port2"":""None"",
# ""SSLEnable"":""None""
# },
# {
# ""Name"": ""SSH"",
# ""Enabled"": ""Enable"",
# ""Port"": ""22"",
# ""Port2"":""None"",
# ""SSLEnable"":""Enable""
# },
# {
# ""Name"": ""HTTPS"",
# ""Enabled"": ""Enable"",
# ""Port"": ""80""
# },
# {
# ""Name"": ""SNMP"",
# ""Enabled"": ""Enable"",
# ""Port"": ""161"",
# ""Port2"":""None"",
# ""SSLEnable"":""None""
# },
# {
# ""Name"": ""HTTP"",
# ""Enabled"": ""Enable"",
# ""Port"": ""80"",
# ""Port2"":""443"",
# ""SSLEnable"":""Enable""
#
# },
# {
# ""Name"": ""SSDP"",
# ""Enabled"": ""Enable"",
# ""Port "": ""1900"",
# ""Port2"":""None"",
# ""SSLEnable"":""None""
# }
# ],
# ""SSDP"":
# {
# ""NotifyTTL "": ""2"",
# ""NotifyIPv6Scope "": ""Site"",
# ""NotifyMulticastIntervalSeconds "": ""600""
# }
# }"
# "{
# ""Subscriber"": [
# {
# ""Id"": ""1"",
# ""Destination"": ""https://10.10.10.10"",
# ""EventTypes"": ""StatusChange"",
# ""HttpHeaders"": ""None"",
# ""Protocol"": ""Redfish"",
# ""Context"": ""123"",
# ""MessageIds"": ""None"",
# ""OriginResources"": ""None""
# },
# {
# ""Id"": ""2"",
# ""Destination"": ""https://10.10.10.11"",
# ""EventTypes"": ""Alert"",
# ""HttpHeaders"": ""None"",
# ""Protocol"": ""Redfish"",
# ""Context"": ""123"",
# ""MessageIds"": ""None"",
# ""OriginResources"": ""None""
# }
# ......
# ]
# }"
# "{
# ""Enabled"": ""Enable"",
# ""LimitInWatts"": ""500"",
# ""LimitException"": ""NoAction""
# }"
# "{
# ""AdaptivePort"": [
# {
# ""PortNumber"": ""0"",
# ""Location"": ""MGMT"",
# ""Type"": ""Dedicated"",
# ""LinkStatus"": ""up""
# }
# {
# ""PortNumber"": ""1"",
# ""Location"": ""mainboard"",
# ""Type"": ""LOM"",
# ""LinkStatus"": ""up""
# }
# ......
# ],
# ""AllowablePorts"": [
# {
# ""PortNumber"": ""0"",
# ""Location"": ""MGMT"",
# ""Type"": ""Dedicated"",
# ""LinkStatus"": ""up""
# },
# {
# ""PortNumber"": ""0"",
# ""Location"": ""mainboard"",
# ""Type"": ""LOM"",
# ""LinkStatus"": ""up""
# },
# {
# ""PortNumber"": ""1"",
# ""Location"": ""mainboard"",
# ""Type"": ""LOM"",
# ""LinkStatus"": ""down""
# },
# {
# ""PortNumber"": ""0"",
# ""Location"": ""MEZZ NIC"",
# ""Type"": ""MEZZ"",
# ""LinkStatus"": ""up""
# },
# {
# ""PortNumber"": ""1"",
# ""Location"": ""MEZZ NIC"",
# ""Type"": ""MEZZ"",
# ""LinkStatus"": ""up""
# }
# ......
# ]
# }"
# "{
# ""Enabled"": ""enable"",
# ""TrapVersion"": ""V1"",
# ‘Community"": ""comunity"",
# ""Severity"": ""All"",
# ""Destination"": [
# {
# ""Id"": ""1"",
# ""Enabled"": ""enable"",
# ""Address"": ""192.168.0.100"",
# ""Port"": ""162""
# },
# {
# ""Id"": ""2"",
# ""Enabled"": ""enable"",
# ""Address"": ""none"",
# ""Port"": ""162""
# },
# {
# Id"": ""3
# Enabled"": ""enable
# Address"": ""192.168.0.102
# Port"": ""162
# ----------------------------------------
# Id"": ""4
# Enabled"": ""enable
# Address"": ""192.168.0.103
# Port"": ""162
# [/Destination]"
# "{
# ""update"": [
# {
# ""Firmware"": ""BMC"",
# ""Component"": ""BMC"",
# ""State"": ""downloading"",
# ""Progress"": ""45"",
# ""Activation"": [""automatic""]
# },
# {
# ""Firmware"": ""BIOS"",
# ""Component"": ""BIOS"",
# ""State"": ""waittoapply"",
# ""Progress"": ""45"",
# ""Activation"": [""poweroff"",""dcpowercycle"",""systemreboot""]
# },
# ……
# ]
# }"
# "{
# ""PanelComSource"": ""BMC"",
# ""SOLSource"": ""Host""
# }
#
# "
# "{
# ""OverallHealth"": ""OK"",
# Maximum"": ""12"",
# ""PCIeDevice"": [
# {
# ""Id"": ""0"",
# ""CommonName"": ""MEZZ NIC"",
# ""Location"": ""mainboard"",
# ""Type"": ""MEZZ"",
# ""SlotBus"": ""0x02"",
# ""SlotDevice"": ""0x00"",
# ""SlotFunction"": ""0x00"",
# ""State"": ""Enabled"",
# ""Health"": ""OK""
# }，
# {
# ""Id"": ""1"",
# ""CommonName"": ""PCIe0"",
# ""Location"": ""mainboard"",
# ""Type"": ""External PCIe"",
# ""SlotBus"": ""0x03"",
# ""SlotDevice"": ""0x00"",
# ""SlotFunction"": ""0x00"",
# ""State"": ""Absent""
# },
# {
# ""Id"": ""2"",
# ""CommonName"": ""PCIe1"",
# ""Location"": ""PCIe Riser0"",
# ""Type"": ""External PCIe"",
# ""SlotBus"": ""0x04"",
# ""SlotDevice"": ""0x00"",
# ""SlotFunction"": ""0x00"",
# ""State"": ""Enabled"",
# ""Health"": ""OK""
# },
# ......
# ]
# }"
# "{
# ""KeyboardLayout"": ""jp"",
# ""SessionTimeoutMinutes"": ""240"",
# ""SSLEncryptionEnabled"": ""True"",
# ""MaximumNumberOfSessions"": ""5"",
# ""NumberOfActivatedSessions"": ""0"",
# ""SessionMode"": ""None""
# }"
# "{
# ""task"": [
# {
# ""TaskId"": ""0"",
# ""TaskType"": ""upgrade"",
# ""TaskDesc"": ""BMC upgrade"",
# ""State"": ""notstart"",
# ""EstimatedTime"": ""300"",
# ""Trigger"": [""automatic""]
# },
# {
# ""TaskId"": ""1"",
# ""TaskType"": ""upgrade"",
# ""TaskDesc"": ""BIOS upgrade"",
# ""State"": ""inprogress"",
# ""EstimatedTime"": ""240"",
# ""Trigger"": [""poweroff"",""dcpowercycle"",""systemreboot""]
# },
# ……
# ]
# }"
# "{
#    ""Enabled"":""enable""
# }"
# "{
#    ""ReservedBlock"":""10"",
#    ""RemainLife"":""5"",
#    ""PrefailCount"":""0"",
#    ""MediaError"":""1""
# }
# "
# "{
#    ""PortCode"":[""0x23"",""0x2a"",……]
# }
#
class Port80():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def PortCode(self):
        return self.dict['PortCode']

    def PortCode(self, value):
        self.dict['PortCode'] = value


class Threshold():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ReservedBlock(self):
        return self.dict['ReservedBlock']

    def ReservedBlock(self, value):
        self.dict['ReservedBlock'] = value

    def RemainLifePercents(self):
        return self.dict['RemainLifePercents']

    def RemainLifePercents(self, value):
        self.dict['RemainLifePercents'] = value

    def PrefailCount(self):
        return self.dict['PrefailCount']

    def PrefailCount(self, value):
        self.dict['PrefailCount'] = value

    def MediaError(self):
        return self.dict['MediaError']

    def MediaError(self, value):
        self.dict['MediaError'] = value


class FruBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def FRUID(self):
        return self.dict['FRUID']

    def FRUID(self, value):
        self.dict['FRUID'] = value

    def FRUName(self):
        return self.dict['FRUName']

    def FRUName(self, value):
        self.dict['FRUName'] = value

    def ChassisType(self):
        return self.dict['ChassisType']

    def ChassisType(self, value):
        self.dict['ChassisType'] = value

    def ChassisPartNumber(self):
        return self.dict['ChassisPartNumber']

    def ChassisPartNumber(self, value):
        self.dict['ChassisPartNumber'] = value

    def ChassisSerial(self):
        return self.dict['ChassisSerial']

    def ChassisSerial(self, value):
        self.dict['ChassisSerial'] = value

    def BoardMfgDate(self):
        return self.dict['BoardMfgDate']

    def BoardMfgDate(self, value):
        self.dict['BoardMfgDate'] = value

    def BoardMfg(self):
        return self.dict['BoardMfg']

    def BoardMfg(self, value):
        self.dict['BoardMfg'] = value

    def BoardProduct(self):
        return self.dict['BoardProduct']

    def BoardProduct(self, value):
        self.dict['BoardProduct'] = value

    def BoardSerial(self):
        return self.dict['BoardSerial']

    def BoardSerial(self, value):
        self.dict['BoardSerial'] = value

    def BoardPartNumber(self):
        return self.dict['BoardPartNumber']

    def BoardPartNumber(self, value):
        self.dict['BoardPartNumber'] = value

    def ProductManufacturer(self):
        return self.dict['ProductManufacturer']

    def ProductManufacturer(self, value):
        self.dict['ProductManufacturer'] = value

    def ProductName(self):
        return self.dict['ProductName']

    def ProductName(self, value):
        self.dict['ProductName'] = value

    def ProductPartNumber(self):
        return self.dict['ProductPartNumber']

    def ProductPartNumber(self, value):
        self.dict['ProductPartNumber'] = value

    def ProductVersion(self):
        return self.dict['ProductVersion']

    def ProductVersion(self, value):
        self.dict['ProductVersion'] = value

    def ProductSerial(self):
        return self.dict['ProductSerial']

    def ProductSerial(self, value):
        self.dict['ProductSerial'] = value

    def ProductAssetTag(self):
        return self.dict['ProductAssetTag']

    def ProductAssetTag(self, value):
        self.dict['ProductAssetTag'] = value


class SnmpBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value

    def TrapVersion(self):
        return self.dict['TrapVersion']

    def TrapVersion(self, value):
        self.dict['TrapVersion'] = value

    def Community(self):
        return self.dict['Community']

    def Community(self, value):
        self.dict['Community'] = value

    def Severity(self):
        return self.dict['Severity']

    def Severity(self, value):
        self.dict['Severity'] = value

    def Destination(self):
        return self.dict['Destination']

    def Destination(self, value):
        self.dict['Destination'] = value

    def AUTHProtocol(self):
        return self.dict['AUTHProtocol']

    def AUTHProtocol(self, value):
        self.dict['AUTHProtocol'] = value

    def AUTHPwd(self):
        return self.dict['AUTHPwd']

    def AUTHPwd(self, value):
        self.dict['AUTHPwd'] = value

    def PRIVProtocol(self):
        return self.dict['PRIVProtocol']

    def PRIVProtocol(self, value):
        self.dict['PRIVProtocol'] = value

    def PRIVPwd(self):
        return self.dict['PRIVPwd']

    def PRIVPwd(self, value):
        self.dict['PRIVPwd'] = value

    def EngineID(self):
        return self.dict['EngineID']

    def EngineID(self, value):
        self.dict['EngineID'] = value

    def HostID(self):
        return self.dict['HostID']

    def HostID(self, value):
        self.dict['HostID'] = value

    def UserName(self):
        return self.dict['UserName']

    def UserName(self, value):
        self.dict['UserName'] = value

    def DeviceType(self):
        return self.dict['DeviceType']

    def DeviceType(self, value):
        self.dict['DeviceType'] = value

    def SystemName(self):
        return self.dict['SystemName']

    def SystemName(self, value):
        self.dict['SystemName'] = value

    def SystemId(self):
        return self.dict['SystemId']

    def SystemId(self, value):
        self.dict['SystemId'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def ContactName(self):
        return self.dict['ContactName']

    def ContactName(self, value):
        self.dict['ContactName'] = value

    def HostOS(self):
        return self.dict['HostOS']

    def HostOS(self, value):
        self.dict['HostOS'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value


class DestinationTXBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value

    def Address(self):
        return self.dict['Address']

    def Address(self, value):
        self.dict['Address'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value

    def LanChannel(self):
        return self.dict['LanChannel']

    def LanChannel(self, value):
        self.dict['LanChannel'] = value

    def AlertType(self):
        return self.dict['AlertType']

    def AlertType(self, value):
        self.dict['AlertType'] = value

    def Destination(self):
        return self.dict['Destination']

    def Destination(self, value):
        self.dict['Destination'] = value


class DestinationBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def ChannelId(self):
        return self.dict['ChannelId']

    def ChannelId(self, value):
        self.dict['ChannelId'] = value

    def LanChannel(self):
        return self.dict['LanChannel']

    def LanChannel(self, value):
        self.dict['LanChannel'] = value

    def Address(self):
        return self.dict['Address']

    def Address(self, value):
        self.dict['Address'] = value

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def Domain(self):
        return self.dict['Domain']

    def Domain(self, value):
        self.dict['Domain'] = value

    def Type(self):
        return self.dict['Type']

    def Type(self, value):
        self.dict['Type'] = value

    def Subject(self):
        return self.dict['Subject']

    def Subject(self, value):
        self.dict['Subject'] = value

    def Message(self):
        return self.dict['Message']

    def Message(self, value):
        self.dict['Message'] = value


class AlertBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def PolicyGroup(self):
        return self.dict['PolicyGroup']

    def PolicyGroup(self, value):
        self.dict['PolicyGroup'] = value

    def ChannelNumber(self):
        return self.dict['ChannelNumber']

    def ChannelNumber(self, value):
        self.dict['ChannelNumber'] = value

    def EnablePolicy(self):
        return self.dict['EnablePolicy']

    def EnablePolicy(self, value):
        self.dict['EnablePolicy'] = value

    def PolicyAction(self):
        return self.dict['PolicyAction']

    def PolicyAction(self, value):
        self.dict['PolicyAction'] = value

    def DestinationId(self):
        return self.dict['DestinationId']

    def DestinationId(self, value):
        self.dict['DestinationId'] = value

    def AlertString(self):
        return self.dict['AlertString']

    def AlertString(self, value):
        self.dict['AlertString'] = value

    def AlertStringKey(self):
        return self.dict['AlertStringKey']

    def AlertStringKey(self, value):
        self.dict['AlertStringKey'] = value


class EventLogTXBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Severity(self):
        return self.dict['Severity']

    def Severity(self, value):
        self.dict['Severity'] = value

    def EventTimestamp(self):
        return self.dict['EventTimestamp']

    def EventTimestamp(self, value):
        self.dict['EventTimestamp'] = value

    def Entity(self):
        return self.dict['Entity']

    def Entity(self, value):
        self.dict['Entity'] = value

    def EntitySN(self):
        return self.dict['EntitySN']

    def EntitySN(self, value):
        self.dict['EntitySN'] = value

    def Message(self):
        return self.dict['Message']

    def Message(self, value):
        self.dict['Message'] = value

    def EventId(self):
        return self.dict['EventId']

    def EventId(self, value):
        self.dict['EventId'] = value

    def Status(self):
        return self.dict['Status']

    def Status(self, value):
        self.dict['Status'] = value

    def Type(self):
        return self.dict['Type']

    def Type(self, value):
        self.dict['Type'] = value


class Task():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def TaskId(self):
        return self.dict['TaskId']

    def TaskId(self, value):
        self.dict['TaskId'] = value

    def TaskType(self):
        return self.dict['TaskType']

    def TaskType(self, value):
        self.dict['TaskType'] = value

    def TaskDesc(self):
        return self.dict['TaskDesc']

    def TaskDesc(self, value):
        self.dict['TaskDesc'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Trigger(self):
        return self.dict['Trigger']

    def Trigger(self, value):
        self.dict['Trigger'] = value

    def EstimatedTimeSeconds(self):
        return self.dict['EstimatedTimeSeconds']

    def EstimatedTimeSeconds(self, value):
        self.dict['EstimatedTimeSeconds'] = value

    def Progress(self):
        return self.dict['Progress']

    def Progress(self, value):
        self.dict['Progress'] = value


class TaskProgress():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Firmware(self):
        return self.dict['Firmware']

    def Firmware(self, value):
        self.dict['Firmware'] = value

    def Component(self):
        return self.dict['Component']

    def Component(self, value):
        self.dict['Component'] = value

    def State(self):
        return self.dict['State']

    def State(self, value):
        self.dict['State'] = value

    def Progress(self):
        return self.dict['Progress']

    def Progress(self, value):
        self.dict['Progress'] = value

    def Activation(self):
        return self.dict['Activation']

    def Activation(self, value):
        self.dict['Activation'] = value


class PowerStatusBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def PowerStatus(self):
        return self.dict['PowerStatus']

    def PowerStatus(self, value):
        self.dict['PowerStatus'] = value

    def UIDLed(self):
        return self.dict['UIDLed']

    def UIDLed(self, value):
        self.dict['UIDLed'] = value


class UpTimeBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def RunningTime(self):
        return self.dict['RunningTime']

    def RunningTime(self, value):
        self.dict['RunningTime'] = value


class SessionBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def SessionID(self):
        return self.dict['SessionID']

    def SessionID(self, value):
        self.dict['SessionID'] = value

    def SessionType(self):
        return self.dict['SessionType']

    def SessionType(self, value):
        self.dict['SessionType'] = value

    def ClientIP(self):
        return self.dict['ClientIP']

    def ClientIP(self, value):
        self.dict['ClientIP'] = value

    def UserName(self):
        return self.dict['UserName']

    def UserName(self, value):
        self.dict['UserName'] = value

    def UserPrivilege(self):
        return self.dict['UserPrivilege']

    def UserPrivilege(self, value):
        self.dict['UserPrivilege'] = value


class HardBackBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def FrontRear(self):
        return self.dict['FrontRear']

    def FrontRear(self, value):
        self.dict['FrontRear'] = value

    def BackplaneIndex(self):
        return self.dict['BackplaneIndex']

    def BackplaneIndex(self, value):
        self.dict['BackplaneIndex'] = value

    def Error(self):
        return self.dict['Error']

    def Error(self, value):
        self.dict['Error'] = value

    def Locate(self):
        return self.dict['Locate']

    def Locate(self, value):
        self.dict['Locate'] = value

    def Rebuild(self):
        return self.dict['Rebuild']

    def Rebuild(self, value):
        self.dict['Rebuild'] = value

    def NVME(self):
        return self.dict['NVME']

    def NVME(self, value):
        self.dict['NVME'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Vendor(self):
        return self.dict['Vendor']

    def Vendor(self, value):
        self.dict['Vendor'] = value

    def Media(self):
        return self.dict['Media']

    def Media(self, value):
        self.dict['Media'] = value

    def Interface(self):
        return self.dict['Interface']

    def Interface(self, value):
        self.dict['Interface'] = value

    def FW(self):
        return self.dict['FW']

    def FW(self, value):
        self.dict['FW'] = value

    def SN(self):
        return self.dict['SN']

    def SN(self, value):
        self.dict['SN'] = value

    def Present(self):
        return self.dict['Present']

    def Present(self, value):
        self.dict['Present'] = value


class BackplaneBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def CPLDVersion(self):
        return self.dict['CPLDVersion']

    def CPLDVersion(self, value):
        self.dict['CPLDVersion'] = value

    def PortCount(self):
        return self.dict['PortCount']

    def PortCount(self, value):
        self.dict['PortCount'] = value

    def DriverCount(self):
        return self.dict['DriverCount']

    def DriverCount(self, value):
        self.dict['DriverCount'] = value

    def Temperature(self):
        return self.dict['Temperature']

    def Temperature(self, value):
        self.dict['Temperature'] = value

    def Present(self):
        return self.dict['Present']

    def Present(self, value):
        self.dict['Present'] = value


class HardBoardBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Model(self):
        return self.dict['Model']

    def Model(self, value):
        self.dict['Model'] = value

    def Capacity(self):
        return self.dict['Capacity']

    def Capacity(self, value):
        self.dict['Capacity'] = value

    def Location(self):
        return self.dict['Location']

    def Location(self, value):
        self.dict['Location'] = value

    def SN(self):
        return self.dict['SN']

    def SN(self, value):
        self.dict['SN'] = value

    def Present(self):
        return self.dict['Present']

    def Present(self, value):
        self.dict['Present'] = value


class BMCNicBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Name(self):
        return self.dict['Name']

    def Name(self, value):
        self.dict['Name'] = value

    def MACAddress(self):
        return self.dict['MACAddress']

    def MACAddress(self, value):
        self.dict['MACAddress'] = value

    def IPAddress(self):
        return self.dict['IPAddress']

    def IPAddress(self, value):
        self.dict['IPAddress'] = value


class DNSBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def DNSStatus(self):
        return self.dict['DNSStatus']

    def DNSStatus(self, value):
        self.dict['DNSStatus'] = value

    def HostSettings(self):
        return self.dict['HostSettings']

    def HostSettings(self, value):
        self.dict['HostSettings'] = value

    def Hostname(self):
        return self.dict['Hostname']

    def Hostname(self, value):
        self.dict['Hostname'] = value

    def DomainSettings(self):
        return self.dict['DomainSettings']

    def DomainSettings(self, value):
        self.dict['DomainSettings'] = value

    def DomainName(self):
        return self.dict['DomainName']

    def DomainName(self, value):
        self.dict['DomainName'] = value

    def DomainInterface(self):
        return self.dict['DomainInterface']

    def DomainInterface(self, value):
        self.dict['DomainInterface'] = value

    def DNSSettings(self):
        return self.dict['DNSSettings']

    def DNSSettings(self, value):
        self.dict['DNSSettings'] = value

    def DNSServer1(self):
        return self.dict['DNSServer1']

    def DNSServer1(self, value):
        self.dict['DNSServer1'] = value

    def DNSServer2(self):
        return self.dict['DNSServer2']

    def DNSServer2(self, value):
        self.dict['DNSServer2'] = value

    def DNSServer3(self):
        return self.dict['DNSServer3']

    def DNSServer3(self, value):
        self.dict['DNSServer3'] = value

    def DNSServerInterface(self):
        return self.dict['DNSServerInterface']

    def DNSServerInterface(self, value):
        self.dict['DNSServerInterface'] = value

    def DNSIPPriority(self):
        return self.dict['DNSIPPriority']

    def DNSIPPriority(self, value):
        self.dict['DNSIPPriority'] = value


class SMTPBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def SmtpEnable(self):
        return self.dict['SmtpEnable']

    def SmtpEnable(self, value):
        self.dict['SmtpEnable'] = value

    def ServerAddr(self):
        return self.dict['ServerAddr']

    def ServerAddr(self, value):
        self.dict['ServerAddr'] = value

    def SmtpPort(self):
        return self.dict['SmtpPort']

    def SmtpPort(self, value):
        self.dict['SmtpPort'] = value

    def SmtpSecurePort(self):
        return self.dict['SmtpSecurePort']

    def SmtpSecurePort(self, value):
        self.dict['SmtpSecurePort'] = value

    def EnableSTARTTLS(self):
        return self.dict['EnableSTARTTLS']

    def EnableSTARTTLS(self, value):
        self.dict['EnableSTARTTLS'] = value

    def EnableSSLTLS(self):
        return self.dict['EnableSSLTLS']

    def EnableSSLTLS(self, value):
        self.dict['EnableSSLTLS'] = value

    def SMTPAUTH(self):
        return self.dict['SMTPAUTH']

    def SMTPAUTH(self, value):
        self.dict['SMTPAUTH'] = value

    def UserName(self):
        return self.dict['UserName']

    def UserName(self, value):
        self.dict['UserName'] = value

    def PassWord(self):
        return self.dict['PassWord']

    def PassWord(self, value):
        self.dict['PassWord'] = value

    def SenderAddr(self):
        return self.dict['SenderAddr']

    def SenderAddr(self, value):
        self.dict['SenderAddr'] = value

    def Subject(self):
        return self.dict['Subject']

    def Subject(self, value):
        self.dict['Subject'] = value

    def HostName(self):
        return self.dict['HostName']

    def HostName(self, value):
        self.dict['HostName'] = value

    def SerialNumber(self):
        return self.dict['SerialNumber']

    def SerialNumber(self, value):
        self.dict['SerialNumber'] = value

    def AssetTag(self):
        return self.dict['AssetTag']

    def AssetTag(self, value):
        self.dict['AssetTag'] = value

    def EventLevel(self):
        return self.dict['EventLevel']

    def EventLevel(self, value):
        self.dict['EventLevel'] = value

    def Destination(self):
        return self.dict['Destination']

    def Destination(self, value):
        self.dict['Destination'] = value


class SmtpDestBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Enable(self):
        return self.dict['Enable']

    def Enable(self, value):
        self.dict['Enable'] = value

    def EmailAddress(self):
        return self.dict['EmailAddress']

    def EmailAddress(self, value):
        self.dict['EmailAddress'] = value

    def Description(self):
        return self.dict['Description']

    def Description(self, value):
        self.dict['Description'] = value


class SnmpGetSetBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def SnmpV1Enable(self):
        return self.dict['SnmpV1Enable']

    def SnmpV1Enable(self, value):
        self.dict['SnmpV1Enable'] = value

    def SnmpV2Enable(self):
        return self.dict['SnmpV2Enable']

    def SnmpV2Enable(self, value):
        self.dict['SnmpV2Enable'] = value

    def ReadOnlyCommunity(self):
        return self.dict['ReadOnlyCommunity']

    def ReadOnlyCommunity(self, value):
        self.dict['ReadOnlyCommunity'] = value

    def ReadWriteCommunity(self):
        return self.dict['ReadWriteCommunity']

    def ReadWriteCommunity(self, value):
        self.dict['ReadWriteCommunity'] = value

    def SnmpV3Enable(self):
        return self.dict['SnmpV3Enable']

    def SnmpV3Enable(self, value):
        self.dict['SnmpV3Enable'] = value

    def AUTHProtocol(self):
        return self.dict['AUTHProtocol']

    def AUTHProtocol(self, value):
        self.dict['AUTHProtocol'] = value

    def PrivProtocol(self):
        return self.dict['PrivProtocol']

    def PrivProtocol(self, value):
        self.dict['PrivProtocol'] = value

    def AUTHUserName(self):
        return self.dict['AUTHUserName']

    def AUTHUserName(self, value):
        self.dict['AUTHUserName'] = value


class NCSIBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def NicType(self):
        return self.dict['NicType']

    def NicType(self, value):
        self.dict['NicType'] = value

    def NicName(self):
        return self.dict['NicName']

    def NicName(self, value):
        self.dict['NicName'] = value

    def PortNum(self):
        return self.dict['PortNum']

    def PortNum(self, value):
        self.dict['PortNum'] = value


class SMTPM5Bean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def LanChannel(self):
        return self.dict['LanChannel']

    def LanChannel(self, value):
        self.dict['LanChannel'] = value

    def ChannelNumber(self):
        return self.dict['ChannelNumber']

    def ChannelNumber(self, value):
        self.dict['ChannelNumber'] = value

    def SenderEmail(self):
        return self.dict['SenderEmail']

    def SenderEmail(self, value):
        self.dict['SenderEmail'] = value

    def SMTPServer(self):
        return self.dict['SMTPServer']

    def SMTPServer(self, value):
        self.dict['SMTPServer'] = value


class SMTPServerBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ServerType(self):
        return self.dict['ServerType']

    def ServerType(self, value):
        self.dict['ServerType'] = value

    def SMTPSupport(self):
        return self.dict['SMTPSupport']

    def SMTPSupport(self, value):
        self.dict['SMTPSupport'] = value

    def ServerName(self):
        return self.dict['ServerName']

    def ServerName(self, value):
        self.dict['ServerName'] = value

    def Addreess(self):
        return self.dict['Addreess']

    def Addreess(self, value):
        self.dict['Addreess'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value

    def ServerAuth(self):
        return self.dict['ServerAuth']

    def ServerAuth(self, value):
        self.dict['ServerAuth'] = value

    def Username(self):
        return self.dict['Username']

    def Username(self, value):
        self.dict['Username'] = value


class SnmpGetSetM5Bean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def GETSETVersion(self):
        return self.dict['GETSETVersion']

    def GETSETVersion(self, value):
        self.dict['GETSETVersion'] = value

    def snmpv1readenable(self):
        return self.dict['snmpv1readenable']

    def snmpv1readenable(self, value):
        self.dict['snmpv1readenable'] = value

    def snmpv1writeenable(self):
        return self.dict['snmpv1writeenable']

    def snmpv1writeenable(self, value):
        self.dict['snmpv1writeenable'] = value

    def snmpv2creadenable(self):
        return self.dict['snmpv2creadenable']

    def snmpv2creadenable(self, value):
        self.dict['snmpv2creadenable'] = value

    def snmpv2cwriteenable(self):
        return self.dict['snmpv2cwriteenable']

    def snmpv2cwriteenable(self, value):
        self.dict['snmpv2cwriteenable'] = value

    def snmpv3readenable(self):
        return self.dict['snmpv3readenable']

    def snmpv3readenable(self, value):
        self.dict['snmpv3readenable'] = value

    def snmpv3writeenable(self):
        return self.dict['snmpv3writeenable']

    def snmpv3writeenable(self, value):
        self.dict['snmpv3writeenable'] = value

    def Community(self):
        return self.dict['Community']

    def Community(self, value):
        self.dict['Community'] = value

    def Username(self):
        return self.dict['Username']

    def Username(self, value):
        self.dict['Username'] = value

    def AuthProtocol(self):
        return self.dict['AuthProtocol']

    def AuthProtocol(self, value):
        self.dict['AuthProtocol'] = value

    def AuthPasswd(self):
        return self.dict['AuthPasswd']

    def AuthPasswd(self, value):
        self.dict['AuthPasswd'] = value

    def PrivProtocol(self):
        return self.dict['PrivProtocol']

    def PrivProtocol(self, value):
        self.dict['PrivProtocol'] = value

    def PrivPasswd(self):
        return self.dict['PrivPasswd']

    def PrivPasswd(self, value):
        self.dict['PrivPasswd'] = value


class NCSIM5Bean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Mode(self):
        return self.dict['Mode']

    def Mode(self, value):
        self.dict['Mode'] = value

    def NicType(self):
        return self.dict['NicType']

    def NicType(self, value):
        self.dict['NicType'] = value

    def InterfaceName(self):
        return self.dict['InterfaceName']

    def InterfaceName(self, value):
        self.dict['InterfaceName'] = value

    def PackageID(self):
        return self.dict['PackageID']

    def PackageID(self, value):
        self.dict['PackageID'] = value

    def ChannelNumber(self):
        return self.dict['ChannelNumber']

    def ChannelNumber(self, value):
        self.dict['ChannelNumber'] = value


class PSUConfigBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Id(self):
        return self.dict['Id']

    def Id(self, value):
        self.dict['Id'] = value

    def Present(self):
        return self.dict['Present']

    def Present(self, value):
        self.dict['Present'] = value

    def Mode(self):
        return self.dict['Mode']

    def Mode(self, value):
        self.dict['Mode'] = value


class PSUPeakBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def Status(self):
        return self.dict['Status']

    def Status(self, value):
        self.dict['Status'] = value

    def Time(self):
        return self.dict['Time']

    def Time(self, value):
        self.dict['Time'] = value


class ADBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def ActiveDirectoryAuthentication(self):
        return self.dict['ActiveDirectoryAuthentication']

    def ActiveDirectoryAuthentication(self, value):
        self.dict['ActiveDirectoryAuthentication'] = value

    def SecretName(self):
        return self.dict['SecretName']

    def SecretName(self, value):
        self.dict['SecretName'] = value

    def Timeout(self):
        return self.dict['Timeout']

    def Timeout(self, value):
        self.dict['Timeout'] = value

    def UserDomainName(self):
        return self.dict['UserDomainName']

    def UserDomainName(self, value):
        self.dict['UserDomainName'] = value

    def DomainControllerServerAddress1(self):
        return self.dict['DomainControllerServerAddress1']

    def DomainControllerServerAddress1(self, value):
        self.dict['DomainControllerServerAddress1'] = value

    def DomainControllerServerAddress2(self):
        return self.dict['DomainControllerServerAddress2']

    def DomainControllerServerAddress2(self, value):
        self.dict['DomainControllerServerAddress2'] = value

    def DomainControllerServerAddress3(self):
        return self.dict['DomainControllerServerAddress3']

    def DomainControllerServerAddress3(self, value):
        self.dict['DomainControllerServerAddress3'] = value


class ADGroupBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def GroupID(self):
        return self.dict['GroupID']

    def GroupID(self, value):
        self.dict['GroupID'] = value

    def GroupName(self):
        return self.dict['GroupName']

    def GroupName(self, value):
        self.dict['GroupName'] = value

    def GroupDomain(self):
        return self.dict['GroupDomain']

    def GroupDomain(self, value):
        self.dict['GroupDomain'] = value

    def GroupPrivilege(self):
        return self.dict['GroupPrivilege']

    def GroupPrivilege(self, value):
        self.dict['GroupPrivilege'] = value

    def KVM(self):
        return self.dict['KVM']

    def KVM(self, value):
        self.dict['KVM'] = value

    def VMedia(self):
        return self.dict['VMedia']

    def VMedia(self, value):
        self.dict['VMedia'] = value


class LDAPBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def AuthenState(self):
        return self.dict['AuthenState']

    def AuthenState(self, value):
        self.dict['AuthenState'] = value

    def Encryption(self):
        return self.dict['Encryption']

    def Encryption(self, value):
        self.dict['Encryption'] = value

    def CommonNameType(self):
        return self.dict['CommonNameType']

    def CommonNameType(self, value):
        self.dict['CommonNameType'] = value

    def ServerAddress(self):
        return self.dict['ServerAddress']

    def ServerAddress(self, value):
        self.dict['ServerAddress'] = value

    def Port(self):
        return self.dict['Port']

    def Port(self, value):
        self.dict['Port'] = value

    def BindDN(self):
        return self.dict['BindDN']

    def BindDN(self, value):
        self.dict['BindDN'] = value

    def SearchBase(self):
        return self.dict['SearchBase']

    def SearchBase(self, value):
        self.dict['SearchBase'] = value

    def LoginAttr(self):
        return self.dict['LoginAttr']

    def LoginAttr(self, value):
        self.dict['LoginAttr'] = value


class LDAPGroupBean():
    def __init__(self):
        self.dict = collections.OrderedDict()

    def GroupID(self):
        return self.dict['GroupID']

    def GroupID(self, value):
        self.dict['GroupID'] = value

    def GroupName(self):
        return self.dict['GroupName']

    def GroupName(self, value):
        self.dict['GroupName'] = value

    def GroupSearchBase(self):
        return self.dict['GroupSearchBase']

    def GroupSearchBase(self, value):
        self.dict['GroupSearchBase'] = value

    def GroupPrivilege(self):
        return self.dict['GroupPrivilege']

    def GroupPrivilege(self, value):
        self.dict['GroupPrivilege'] = value
