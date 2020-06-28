# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: IBase interface
#
#   @author: zhong
#   @Date:
#=========================================================================
'''


class IBase():
    def __init__(self):
        pass

    def getfru(self, client, args):
        '''
        get product Fru information
        :return:
        '''

    def getProdcut(self, client, args):
        '''

        :return:
        '''

    def getcapabilities(self, client, args):
        '''

        :return:
        '''
        print('cap')

    def getcpu(self, client, args):
        '''

        :return:
        '''

    def getmemory(self, client, args):
        '''

        :return:
        '''

    def powercontrol(self, client, args):
        '''

        :return:
        '''

    def gethealth(self, client, args):
        '''

        :return:
        '''

    def getsysboot(self, client, args):
        '''

        :return:
        '''

    def geteventlog(self, client, args):
        '''

        :return:
        '''

    def downloadtfalog(self, client, args):
        '''

        :return:
        '''

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

        :return:
        '''

    def getnic(self, client, args):
        '''

        :return:
        '''

    def setsysboot(self, client, args):
        '''

        :return:
        '''

    def powerctrldisk(self, client, args):
        '''

        :return:
        '''

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
        '''

        :return:
        '''

    def mountvmm(self, client, args):
        '''

        :return:
        '''

    def setthreshold(self, client, args):
        '''

        :return:
        '''

    def downloadfandiag(self, client, args):
        '''

        :return:
        '''

    def downloadsol(self, client, args):
        '''

        :return:
        '''

    def sethsc(self, client, args):
        '''

        :return:
        '''

    def chassis(self, client, args):
        '''

        :return:
        '''

    def getproduct(self, client, args):
        '''

        :return:
        '''

    def setproductserial(self, client, args):
        '''

        :return:
        '''

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

        :return:
        '''

    def gettemp(self, client, args):
        '''

        :return:
        '''

    def getvolt(self, client, args):
        '''

        :return:
        '''

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
        '''

        :return:
        '''

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

    def settime(self, client, args):
        '''

        :return:
        '''

    def settimezone(self, client, args):
        '''

        :return:
        '''

    def resetbmc(self, client, args):
        '''

        :return:
        '''

    def setip(self, client, args):
        '''

        :return:
        '''

    def setvlan(self, client, args):
        '''

        :return:
        '''

    def getvnc(self, client, args):
        '''

        :return:
        '''

    def setvnc(self, client, args):
        '''

        :return:
        '''

    def getservice(self, client, args):
        '''

        :return:
        '''

    def setservice(self, client, args):
        '''

        :return:
        '''

    def getmgmtport(self, client, args):
        '''

        :return:
        '''

    def getserialport(self, client, args):
        '''

        :return:
        '''

    def setserialport(self, client, args):
        '''

        :return:
        '''

    def setadaptiveport(self, client, args):
        '''

        :return:
        '''

    def settrapcom(self, client, args):
        '''

        :return:
        '''

    def settrapdest(self, client, args):
        '''

        :return:
        '''

    def triggernmi(self, client, args):
        '''

        :return:
        '''

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

        :return:
        '''

    def importbioscfg(self, client, args):
        '''

        :return:
        '''

    def delvncsession(self, client, args):
        '''

        :return:
        '''

    def sendipmirawcmd(self, client, args):
        '''

        :return:
        '''

    def AccountService(self, client, args):
        '''

        :return:
        '''

    def getuser(self, client, args):
        '''

        :return:
        '''

    def adduser(self, client, args):
        '''

        :return:
        '''

    def deluser(self, client, args):
        '''

        :return:
        '''

    def setpwd(self, client, args):
        '''

        :return:
        '''

    def setpriv(self, client, args):
        '''

        :return:
        '''

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

    def EventServices(self, client, args):
        '''

        :return:
        '''

    def geteventsub(self, client, args):
        '''

        :return:
        '''

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
