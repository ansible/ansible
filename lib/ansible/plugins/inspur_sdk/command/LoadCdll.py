# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: LoadCdll Class
#
#   @author:
#   @Date:
#=========================================================================
'''
import os
import ctypes
import platform

current_path = os.path.abspath(os.path.dirname(__file__))
cdllNameWin = "inspur_ipmi_shared.dll"
clibdllNameWin = "lib_acl.dll"
clibfiberdllNameWin = "libfiber.dll"
clibmsvcr120dllNameWin = "msvcr120.dll"
cdllNameLinux = "inspur_ipmi_shared.so"


# load cdll libary type
class LoadCdll():

    # init
    def __init__(self):
        pass

    # override singleton
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    # load cdll so libary
    def loadCdll(self):
        cdll = None
        if platform.system() == "Windows":
            if os.path.exists(current_path + os.sep + clibdllNameWin):
                clibdll = ctypes.cdll.LoadLibrary(current_path + os.sep + clibdllNameWin)
            if os.path.exists(current_path + os.sep + clibfiberdllNameWin):
                clibfiberdll = ctypes.cdll.LoadLibrary(current_path + os.sep + clibfiberdllNameWin)
            if os.path.exists(current_path + os.sep + clibmsvcr120dllNameWin):
                cdll = ctypes.cdll.LoadLibrary(current_path + os.sep + clibmsvcr120dllNameWin)
            if os.path.exists(current_path + os.sep + cdllNameWin):
                cdll = ctypes.cdll.LoadLibrary(current_path + os.sep + cdllNameWin)
        elif platform.system() == "Linux":
            if os.path.exists(current_path + os.sep + cdllNameLinux):
                cdll = ctypes.cdll.LoadLibrary(current_path + os.sep + cdllNameLinux)

        return cdll


# main test version
if __name__ == "__main__":
    cdll = LoadCdll()
    lib = cdll.loadCdll()
    if not lib:
        print("file not loaded ")
