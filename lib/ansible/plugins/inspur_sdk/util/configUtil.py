# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: configUtil Class
#
#   @author:
#   @Date:
#=========================================================================
'''
import os
import yaml
import xml.etree.ElementTree as ET

routePath = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "route", "route.yml")


# get yaml config util,singleton type
class configUtil():
    def __init__(self):
        pass

    # sinlge
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    # get all configuration option
    def getRouteConfig(self):
        '''
        get route configuration to dict
        :return: all route  dict
        '''
        if os.path.exists(routePath):
            with open(routePath, 'r') as f:
                serverconfig = yaml.load(f.read())
                return serverconfig

    # get Product and BmcVersion configuration option
    def getRouteOption(self, productName, bmcVersion):
        '''
        :param productName: Product Name
        :param bmcVersion: BMC Version X.XX
        :return:
        '''
        config = None
        if os.path.exists(routePath):
            with open(routePath, 'r') as f:
                serverconfig = yaml.load(f.read())
                # if route.yml has configuration get
                productName = productName.upper()
                if serverconfig.get(productName):
                    if serverconfig.get(productName).get(float(bmcVersion)):
                        config = serverconfig.get(productName).get(float(bmcVersion))
                    elif int(bmcVersion.split(".")[0]) > 13 and int(bmcVersion.split(".")[0]) < 16 and serverconfig.get(productName).get('blackstone'):
                        config = serverconfig.get(productName).get('blackstone')
                    elif serverconfig.get(productName).get('common'):
                        config = serverconfig.get(productName).get('common')
                    else:
                        config = "Error: Not Supported Version: " + bmcVersion
                elif "M5" in productName:
                    if serverconfig.get('M5') and serverconfig.get('M5').get('common'):
                        config = serverconfig.get('M5').get('common')
                    else:
                        config = "Error: Not Supported ProductName: " + productName
                elif "M4" in productName:
                    if serverconfig.get('M4') and serverconfig.get('M4').get('common'):
                        config = serverconfig.get('M4').get('common')
                    else:
                        config = "Error: Not Supported ProductName: " + productName
                elif "T6" in productName:
                    if serverconfig.get('T6') \
                            and serverconfig.get('T6').get('common'):
                        config = serverconfig.get('T6').get('common')
                    else:
                        config = "Error: Not Supported ProductName: " + productName
                else:
                    config = "Error: Not Supported ProductName: " + productName
        else:
            config = "Error: route.yml is not Exist " + routePath
        return config

    # xmlfilepath 文件路径
    def getSetOption(self, xmlfilepath):
        '''python在安装时默认编码是ascii，出现非ascii编码时会报错，
           此时需要自己设置python的默认编码，一般设为utf-8
           直接setdefaulttencoding会AttributeError，需要先执行reload(sys)
        '''
        tree = ET.parse(xmlfilepath)  # 调用parse方法返回解析树
        server = tree.getroot()  # 获取根节点

        blongtoSet = set()  # 存储所有的分类
        descriptionList = []  # 存储所有的描述
        infoList = []  # 存储所有xml表示的数据 字典列表

        for cfgItems in server:
            for cfgItem in cfgItems:
                info = {}  # 字典
                # name标签
                blongto_text = ''  # 此处只允许有个Item有一个描述和分类
                description_text = ''  # 只有一个描述,
                for name in cfgItem.getiterator('name'):
                    for belongto in name.getiterator('belongto'):
                        blongto_text = belongto.text
                    for description in name.getiterator('description'):
                        description_text = str(description.text).replace(" ", "")

                blongtoSet.add(blongto_text)
                descriptionList.append(description_text)

                # getter标签
                getterCMD = ''
                for getter in cfgItem.getiterator('getter'):
                    getterCMD = str(getter.text).replace('raw', '')

                # setters标签
                setterlist = []  # 后面嵌套了setOption，是一个字典列表，每一项都是一个字典，字典里面包含{cmd，value，validation}
                sin = False
                for setters in cfgItem.getiterator('setters'):
                    for setter in setters.getiterator('setter'):
                        setOption = {}
                        for cmd in setter.getiterator('cmd'):
                            # 将tab键替换，换行键替换
                            setOption['cmd'] = cmd.text.replace("\\t", "") \
                                .replace("\\n", " xxxxx ").replace('raw', '')
                        for value in setter.getiterator('value'):
                            setOption['value'] = value.text
                        for validation in setter.getiterator('validation'):
                            setOption['validation'] = validation.text
                            sin = True
                        setterlist.append(setOption)

                info['getter'] = getterCMD
                info['key'] = blongto_text + "_" + description_text
                info['description'] = description_text
                info['blongto'] = blongto_text
                info['input'] = sin
                info['setter'] = setterlist
                infoList.append(info)

        return blongtoSet, descriptionList, infoList
