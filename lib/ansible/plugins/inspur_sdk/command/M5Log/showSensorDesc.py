# -*- coding:utf-8 -*-
class ShowSensorDesc():
    def __init__(self):
        pass
    def __getitem__(self, item):
        return item
    def showSensorDesc(self, eventLogString, sensorSpecificEventStr, biosPostEventStr, sensorEventStr, curLang, commonInfoStr,item):
        eventLogStrings = eventLogString[curLang]
        sensor_specific_event = sensorSpecificEventStr[curLang]
        sensorEvent_Str =sensorEventStr[curLang]
        biosPostEvent_Str =biosPostEventStr[curLang]
        commonInfo_Str =commonInfoStr[curLang]
        eventdesc = ""
        m_Max_allowed_offset = {}
        m_Max_allowed_offset[0] = 0x0
        m_Max_allowed_offset[1] = 0x0b
        m_Max_allowed_offset[2] = 0x3
        m_Max_allowed_offset[3] = 0x2
        m_Max_allowed_offset[4] = 0x2
        m_Max_allowed_offset[5] = 0x2
        m_Max_allowed_offset[6] = 0x2
        m_Max_allowed_offset[7] = 0x8
        m_Max_allowed_offset[8] = 0x2
        m_Max_allowed_offset[9] = 0x2
        m_Max_allowed_offset[10] = 0x8
        m_Max_allowed_offset[11] = 0x7
        m_Max_allowed_offset[12] = 0x3



        m_Max_allowed_SensorSpecific_offset = {}
        m_Max_allowed_SensorSpecific_offset[5] = 6
        m_Max_allowed_SensorSpecific_offset[6] = 5
        m_Max_allowed_SensorSpecific_offset[7] = 12
        m_Max_allowed_SensorSpecific_offset[8] = 6
        m_Max_allowed_SensorSpecific_offset[9] = 7
        m_Max_allowed_SensorSpecific_offset[12] = 10
        m_Max_allowed_SensorSpecific_offset[13] = 8
        m_Max_allowed_SensorSpecific_offset[15] = 2
        m_Max_allowed_SensorSpecific_offset[16] = 6
        m_Max_allowed_SensorSpecific_offset[17] = 7
        m_Max_allowed_SensorSpecific_offset[18] = 5
        m_Max_allowed_SensorSpecific_offset[19] = 11

        m_Max_allowed_SensorSpecific_offset[20] = 4
        m_Max_allowed_SensorSpecific_offset[25] = 1
        m_Max_allowed_SensorSpecific_offset[27] = 1
        m_Max_allowed_SensorSpecific_offset[29] = 7
        m_Max_allowed_SensorSpecific_offset[30] = 4
        m_Max_allowed_SensorSpecific_offset[31] = 6
        m_Max_allowed_SensorSpecific_offset[32] = 5
        m_Max_allowed_SensorSpecific_offset[33] = 9
        m_Max_allowed_SensorSpecific_offset[34] = 13
        m_Max_allowed_SensorSpecific_offset[35] = 8
        m_Max_allowed_SensorSpecific_offset[36] = 3
        m_Max_allowed_SensorSpecific_offset[37] = 2
        m_Max_allowed_SensorSpecific_offset[39] = 1
        m_Max_allowed_SensorSpecific_offset[40] = 5
        m_Max_allowed_SensorSpecific_offset[41] = 2
        m_Max_allowed_SensorSpecific_offset[42] = 3
        m_Max_allowed_SensorSpecific_offset[43] = 7
        m_Max_allowed_SensorSpecific_offset[44] = 7
        m_Max_allowed_SensorSpecific_offset[200] = 8
        m_Max_allowed_SensorSpecific_offset[201] = 2

        def getbits(orig, startbit, endbit):
            temp = orig
            mask = 0x00
            for i in range(startbit, endbit-1, -1):
                mask = mask | (1 << i)

            return (temp & mask)

        if (item['record_type'] >= 0x0 and item['record_type'] <= 0xBF):
            type = getbits(item['event_dir_type'], 6, 0)
            if (type == 0x0):
                pass

            elif(type == 0x6F):
                offset = getbits(item.event_data1, 3, 0)
                if (m_Max_allowed_SensorSpecific_offset[item['sensor_type']] >= offset):
                    eventdesc = sensor_specific_event[item['sensor_type']][offset]
                else:
                    eventdesc = eventLogStrings.STR_EVENT_LOG_INVALID_OFFSET;


            elif (type >= 0x01) and (type <= 0x0C):
                offset = getbits(item['event_data1'], 3, 0)
                if (m_Max_allowed_offset[type] >= offset):
                    eventdesc = sensorEvent_Str[type][offset]
                else:
                    eventdesc = eventLogStrings['STR_EVENT_LOG_INVALID_OFFSET']


            else:
                eventdesc = "OEM Discrete"

            if (item['gen_id1'] == 0x21 and item['sensor_type'] == 0xf):
                if (getbits(item['event_data1'], 7, 6) == 0xC0 and (offset >= 0 and offset <= 2)):
                    if (2 == offset):
                        offset = 1

                    eventdesc += "-" + biosPostEvent_Str[offset][getbits(item['event_data2'], 3, 0)]

                else:
                    eventdesc += "-" + "Unknown"

            if item['gen_id1'] == 0x20:
                if item['sensor_type'] == 0x12:
                    if(getbits(item['event_data2'], 7, 7) == 0):
                        eventdesc += " " + commonInfo_Str['STR_START']
                    else:
                        eventdesc += " " + commonInfo_Str['STR_STOP']


            if getbits(item['event_dir_type'], 7, 7) == 0:
                if (eventdesc is not None):
                    if (eventdesc.indexOf("Asserted") == -1):
                        eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_ASSERT']
                else:
                    eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_ASSERT']
            else:
                if (eventdesc is not None):
                    if eventdesc.indexOf("Deasserted") == -1:
                        eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_DEASSERT']

                else:
                    eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_DEASSERT']


        elif (item['record_type']>= 0xC0 and item['RecordType'] <= 0xDF):
            eventdesc = "OEM timestamped"

        elif (item['record_type'] >= 0xE0 and item['record_type'] <= 0xFF):
            eventdesc = "OEM non-timestamped"

        return eventdesc





