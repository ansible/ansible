# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: RedfishFunc Class
#
#   @author: zhong
#   @Date:
#=========================================================================
'''
import RedfishClient


def getBiosByRedfish(client):

    JSON = {}
    response = client.request("GET", "redfish/v1/Systems/Self/Bios", headers=client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result.get('Attributes')
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def getBiosSDByRedfish(client):

    JSON = {}
    response = client.request("GET", "redfish/v1/Systems/Self/Bios/SD", headers=client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 200:
        result = response.json()
        # print(result)
        JSON['code'] = 0
        JSON['data'] = result.get('Attributes')
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def setBiosSDByRedfish(client, data):

    JSON = {}
    # print(data)
    response = client.request("POST", "redfish/v1/Systems/Self/Bios/SD", data=None, json=data, headers=client.getHearder())
    # print(response)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 204 or response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = ""
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def getBiosSRByRedfish(client):

    JSON = {}
    response = client.request("GET", "redfish/v1/Systems/Self/Bios/SR", headers=client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 200:
        result = response.json()
        # print(result)
        JSON['code'] = 0
        JSON['data'] = result.get('SettingResult')
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def setBiosPwdByRedfish(client, data):

    JSON = {}
    response = client.request("POST", "redfish/v1/Systems/Self/Bios/Actions/Bios.ChangePassword", data=None, json=data, headers=client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 204 or response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = ""
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
            # data = res["error"]['@Message.ExtendedInfo']
            # ldata = len(data)
            # message = ''
            # for i in range(ldata):
            #     message += str(data[i].get('Message'))+' '
            # JSON['data']='request failed, response content: ' + str(message)+ 'the status code is ' + str(response.status_code)+"."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def clearBiosPwdByRedfish(client, data):

    JSON = {}
    response = client.request("POST", "redfish/v1/Systems/Self/Bios/Actions/Bios.ChangePassword", data=None, json=data, headers=client.getHearder())
    # print(response.status_code)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 204:
        JSON['code'] = 0
        JSON['data'] = ""
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON


def resetBiosByRedfish(client, data):

    JSON = {}
    response = client.request("POST", "redfish/v1/Systems/Self/Bios/Actions/Bios.ResetBios", data=None, json=data, headers=client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'response is none'
    elif response.status_code == 204 or response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = ""
    else:
        try:
            res = response.json()
            JSON['code'] = 2
            JSON['data'] = 'request failed, response content: ' + str(res["error"]["message"]) + ' the status code is ' + str(response.status_code) + "."
            # data = res["error"]['@Message.ExtendedInfo']
            # ldata = len(data)
            # message = ''
            # for i in range(ldata):
            #     message += str(data[i].get('Message'))+' '
            # JSON['data']='request failed, response content: ' + str(message)+ 'the status code is ' + str(response.status_code)+"."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'request failed, response status code is ' + str(response.status_code)
    return JSON
# def login(client):
#
#     data = {
#         "UserName": 'Administrator',
#         "Password": 'superuser',
#     }
#     headers = {'Content-Type': 'application/json'}
#     header = {}
#     print('responds')
#     responds = client.request('POST', 'redfish/v1/SessionService/Sessions', headers=headers, data=data)
#     print(responds.headers)
#     if responds is not None:
#         if responds.status_code == 201:  # 登录成功
#             XCSRFToken = responds.headers['X-Auth-Token']
#             header = {
#                 "X-Auth-Token": XCSRFToken,
#             }
#     return header
#
# def logout(client):
#
#     token = client.getHearder().get('X-Auth-Token')
#     headers = {"X-Auth-Token": token}
#     # headers = {'Content-Type': 'application/json'}
#     responds = client.request("DELETE", "redfish/v1/SessionService/Sessions/" + token[0:30], headers=headers)
#     print(responds)
