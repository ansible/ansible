# -*- coding:utf-8 -*-

sensorEventStr_EN = {}
sensorEventStr_EN[1] = {}
sensorEventStr_EN[1][0] = "Lower Non-Critical - Going Low"
sensorEventStr_EN[1][1] = "Lower Non-Critical - Going High"
sensorEventStr_EN[1][2] = "Lower Critical - Going Low"
sensorEventStr_EN[1][3] = "Lower Critical - Going High"
sensorEventStr_EN[1][4] = "Lower Non-Recoverable - Going Low"
sensorEventStr_EN[1][5] = "Lower Non-Recoverable - Going High"
sensorEventStr_EN[1][6] = "Upper Non-Critical - Going Low"
sensorEventStr_EN[1][7] = "Upper Non-Critical - Going High"
sensorEventStr_EN[1][8] = "Upper Critical - Going Low"
sensorEventStr_EN[1][9] = "Upper Critical - Going High"
sensorEventStr_EN[1][10] = "Upper Non-Recoverable - Going Low"
sensorEventStr_EN[1][11] = "Upper Non-Recoverable - Going High"

#/******* Generic Discrete Event Type Codes *********/
sensorEventStr_EN[2] = {};
sensorEventStr_EN[2][0] = "Transition to Idle"
sensorEventStr_EN[2][1] = "Transition to Active"
sensorEventStr_EN[2][2] = "Transition to Busy"

#/******* Digital Discrete Event Type Codes *********/
sensorEventStr_EN[3] = {}
sensorEventStr_EN[3][0] = "State Deasserted"
sensorEventStr_EN[3][1] = "State Asserted"

sensorEventStr_EN[4] = {}
sensorEventStr_EN[4][0] = "Predictive Failure Deasserted"
sensorEventStr_EN[4][1] = "Predictive Failure Asserted"

sensorEventStr_EN[5] = {}
sensorEventStr_EN[5][0] = "Limit Not Exceeded"
sensorEventStr_EN[5][1] = "Limit Exceeded"

sensorEventStr_EN[6] = {}
sensorEventStr_EN[6][0] = "Performance Met"
sensorEventStr_EN[6][1] = "Performance Lags"

sensorEventStr_EN[7] = {}
sensorEventStr_EN[7][0] = "Transition to OK"
sensorEventStr_EN[7][1] = "Transition to Non-Critical from OK"
sensorEventStr_EN[7][2] = "Transition to Critical from less severe"
sensorEventStr_EN[7][3] = "Transition to Non-Recoverable from less severe"
sensorEventStr_EN[7][4] = "Transition to Non-Critical from more severe"
sensorEventStr_EN[7][5] = "Transition to Critical from Non-Recoverable"
sensorEventStr_EN[7][6] = "Transition to Non-Recoverable"
sensorEventStr_EN[7][7] = "Monitor"
sensorEventStr_EN[7][8] = "Informational"

sensorEventStr_EN[8] = {}
sensorEventStr_EN[8][0] = "Device Removed / Device Absent"
sensorEventStr_EN[8][1] = "Device Inserted / Device Present"

sensorEventStr_EN[9] = {}
sensorEventStr_EN[9][0] = "Device Disabled"
sensorEventStr_EN[9][1] = "Device Enabled"

sensorEventStr_EN[10] = {}
sensorEventStr_EN[10][0] = "Transition to Running"
sensorEventStr_EN[10][1] = "Transition to In Test"
sensorEventStr_EN[10][2] = "Transition to Power Off"
sensorEventStr_EN[10][3] = "Transition to On Line"
sensorEventStr_EN[10][4] = "Transition to Off Line"
sensorEventStr_EN[10][5] = "Transition to Off Duty"
sensorEventStr_EN[10][6] = "Transition to Degraded"
sensorEventStr_EN[10][7] = "Transition to Power Save"
sensorEventStr_EN[10][8] = "Install Error"

sensorEventStr_EN[11] = {}
sensorEventStr_EN[11][0] = "Fully Redundant (Redundancy Regained)"
sensorEventStr_EN[11][1] = "Redundancy Lost"
sensorEventStr_EN[11][2] = "Redundancy Degraded"
sensorEventStr_EN[11][3] = "Non-redundant: Sufficient Resources from Redundant"
sensorEventStr_EN[11][4] = "Non-redundant: Sufficient Resources from Insufficient Resources"
sensorEventStr_EN[11][5] = "Non-redundant: Insufficient Resources"
sensorEventStr_EN[11][6] = "Redundancy Degraded From Fully Redundant"
sensorEventStr_EN[11][7] = "Redundancy Degraded From Non-redundant"

sensorEventStr_EN[12] = {}
sensorEventStr_EN[12][0] = "D0 Power State"
sensorEventStr_EN[12][1] = "D1 Power State"
sensorEventStr_EN[12][2] = "D2 Power State"
sensorEventStr_EN[12][3] = "D3 Power State"

# sensorEventStr_EN["OEM_DISCRETE"] = "OEM Discrete"


sensorEventStr_CN = {}
sensorEventStr_CN[1] = {}
sensorEventStr_CN[1][0] = "非关键性较低-变低"
sensorEventStr_CN[1][1] = "非关键性较低-变高"
sensorEventStr_CN[1][2] = "关键性较低-变低"
sensorEventStr_CN[1][3] = "关键性较低-变高"
sensorEventStr_CN[1][4] = "不可恢复性较低-变低"
sensorEventStr_CN[1][5] = "不可恢复性较低-变高"
sensorEventStr_CN[1][6] = "关键性较高-变低"
sensorEventStr_CN[1][7] = "非关键性较高-变高"
sensorEventStr_CN[1][8] = "关键性较高-变低"
sensorEventStr_CN[1][9] = "关键性较高-变高"
sensorEventStr_CN[1][10] = "不可恢复性较高-变低"
sensorEventStr_CN[1][11] = "不可恢复性较高-变高"
sensorEventStr_CN[2] = {}
sensorEventStr_CN[2][0] = "过渡到空闲"
sensorEventStr_CN[2][1] = "过渡到活动"
sensorEventStr_CN[2][2] = "过渡到忙"
sensorEventStr_CN[3] = {}
sensorEventStr_CN[3][0] = "状态解除"
sensorEventStr_CN[3][1] = "状态触发"
sensorEventStr_CN[4] = {}
sensorEventStr_CN[4][0] = "预测性故障无效"
sensorEventStr_CN[4][1] = "预测性故障生效"
sensorEventStr_CN[5] = {}
sensorEventStr_CN[5][0] = "未超出范围"
sensorEventStr_CN[5][1] = "超出限制"
sensorEventStr_CN[6] = {}
sensorEventStr_CN[6][0] = "性能指标均达到"
sensorEventStr_CN[6][1] = "性能落后"
sensorEventStr_CN[7] = {}
sensorEventStr_CN[7][0] = "过渡到OK"
sensorEventStr_CN[7][1] = "从OK过渡到非关键性告警"
sensorEventStr_CN[7][2] = "从不严重过渡到关键性告警"
sensorEventStr_CN[7][3] = "从不严重过渡到不可恢复告警"
sensorEventStr_CN[7][4] = "从更严重过渡到非关键性告警"
sensorEventStr_CN[7][5] = "从不可恢复过渡到关键性告警"
sensorEventStr_CN[7][6] = "过渡到不可恢复告警"
sensorEventStr_CN[7][7] = "监测"
sensorEventStr_CN[7][8] = "信息"
sensorEventStr_CN[8] = {}
sensorEventStr_CN[8][0] = "设备移除/设备不存在"
sensorEventStr_CN[8][1] = "设备插入/设备存在"
sensorEventStr_CN[9] = {}
sensorEventStr_CN[9][0] = "设备禁用"
sensorEventStr_CN[9][1] = "设备启用"
sensorEventStr_CN[10] = {}
sensorEventStr_CN[10][0] = "过渡到运行"
sensorEventStr_CN[10][1] = "过渡到测试中"
sensorEventStr_CN[10][2] = "过渡到关机"
sensorEventStr_CN[10][3] = "过渡到上线"
sensorEventStr_CN[10][4] = "过渡到下线"
sensorEventStr_CN[10][5] = "过渡到下班"
sensorEventStr_CN[10][6] = "过渡到退化"
sensorEventStr_CN[10][7] = "过渡到省电模式"
sensorEventStr_CN[10][8] = "安装失败"
sensorEventStr_CN[11] = {}
sensorEventStr_CN[11][0] = "完全冗余(重获冗余)"
sensorEventStr_CN[11][1] = "丢失冗余性"
sensorEventStr_CN[11][2] = "冗余退化"
sensorEventStr_CN[11][3] = "非冗余：冗余足够的资源"
sensorEventStr_CN[11][4] = "非冗余：从资源不足变为足够资源"
sensorEventStr_CN[11][5] = "非冗余：资源不足"
sensorEventStr_CN[11][6] = "从完全冗余变为冗余退化"
sensorEventStr_CN[11][7] = "从非冗余变为冗余退化"
sensorEventStr_CN[12] = {}
sensorEventStr_CN[12][0] = "系统开机状态"
sensorEventStr_CN[12][1] = "D1电源状态"
sensorEventStr_CN[12][2] = "D2电源状态"
sensorEventStr_CN[12][3] = "系统关机状态"

sensorEventStr = {}
sensorEventStr["cn"] = sensorEventStr_CN
sensorEventStr["en"] = sensorEventStr_EN
