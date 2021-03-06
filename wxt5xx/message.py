# pyWXT5xx parses and creates messages for the Vaisala WXT5xx series Weather Station.
# Copyright (C) 2016  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging

SDI12_COMMAND_TERM = "!"
ASCII_COMMAND_TERM = "\r\n"
ASCII_RESET = b'xZ'
ASCII_RESET_PRECIPITATION_INTENSITY = b'xZRI'
ASCII_RESET_PRECIPITATION_COUNTERS = b'xZRU'

ASCII_PTU_SETTINGS = b'xTU'
ASCII_WIND_SETTINGS = b'xWU'
ASCII_PRECIPITATION_SETTINGS = b'xRU'
ASCII_SUPERVISOR_SETTINGS = b'xSU'

WIND_RESULT = "r1"
PTU_RESULT = "r2"
RAIN_RESULT = "r3"
STATUS_RESULT = "r5"

ASCII_CONNECTION_INFO = b'xU'
SDI12_CONNECTION_INFO = b'XXU'

ASCII_COMMAND_RESPONSE = b'tX'

ASCII_READ_DATA = b'R'


class CommunicationProtocol:
    ASCII_Automatic = "A"
    ASCII_Automatic_CRC = "a"
    ASCII_Polled = "P"
    ASCII_Polled_CRC = "p"
    NMEA_Automatic = "N"
    NMEA_Polled = "Q"

    __first__ = True
    __valid__ = []

    @staticmethod
    def is_valid(value):
        if CommunicationProtocol.__first__:
            CommunicationProtocol.__first__ = False
            for i in CommunicationProtocol.__dict__:
                if not i.startswith("__") and type(CommunicationProtocol.__dict__[i]) != staticmethod:
                    CommunicationProtocol.__valid__.append(CommunicationProtocol.__dict__[i])
        return value in CommunicationProtocol.__valid__

    @staticmethod
    def lookup_protocol(protocol):
        if protocol == CommunicationProtocol.ASCII_Automatic or protocol == CommunicationProtocol.ASCII_Automatic_CRC or protocol == CommunicationProtocol.ASCII_Polled or protocol == CommunicationProtocol.ASCII_Polled_CRC:
            return ASCIIMessage

    @staticmethod
    def has_crc(protocol):
        if protocol == CommunicationProtocol.ASCII_Automatic_CRC or protocol == CommunicationProtocol.ASCII_Polled_CRC:
            return True
        return False


class CommunicationParameters:
    Address = "A"
    Protocol = "M"
    Test = "T"
    SerialInterface = "C"
    CompositeDataRepeat = "I"
    BaudRate = "B"
    DataBits = "D"
    Parity = "P"
    StopBits = "S"
    RS485LineDelay = "L"
    DeviceName = "N"
    SoftwareVersion = "V"
    ParameterLock = "H"
    __first__ = True
    __valid__ = []

    @staticmethod
    def is_valid(value):
        if CommunicationParameters.__first__:
            CommunicationParameters.__first__ = False
            for i in CommunicationParameters.__dict__:
                if not i.startswith("__") and type(CommunicationParameters.__dict__[i]) != staticmethod:
                    CommunicationParameters.__valid__.append(CommunicationParameters.__dict__[i])
        return value in CommunicationParameters.__valid__


class SerialInterface:
    SDI12 = "1"
    RS232 = "2"
    RS485 = "3"
    RS422 = "4"

    __first__ = True
    __valid__ = []

    @staticmethod
    def is_valid(value):
        if SerialInterface.__first__:
            SerialInterface.__first__ = False
            for i in SerialInterface.__dict__:
                if not i.startswith("__") and type(SerialInterface.__dict__[i]) != staticmethod:
                    SerialInterface.__valid__.append(SerialInterface.__dict__[i])
        return value in SerialInterface.__valid__


valid_baud_rates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
valid_data_bits = [7, 8]


def crc16(msg):
    c = 0
    for a in msg:
        c ^= ord(a)
        for _ in range(8):
            if c & 1:
                c >>= 1
                c ^= 0xA001
            else:
                c >>= 1
    bytes_ = [0x40 | (c >> 12), 0x40 | ((c >> 6) & 0x3f), 0x40 | (c & 0x3f)]
    return "".join(map(chr, bytes_)).encode()


class InvalidCRC(Exception):
    pass


class BaseMessageParser:
    logger = logging.getLogger("Message")

    def __init__(self): pass

    def parse(self, address, message):
        raise Exception("Not implemented")

    def parse_unit(self, label_value):
        temperature_units = {'C': 'C', 'F': 'F'}
        speed_units = {'M': 'm/s', 'K': 'km/h', 'S': 'mph', 'N': 'kn'}
        direction_units = {'D': 'deg'}
        pressure_units = {'H': 'hPa', 'P': 'Pa', 'B': 'bar', 'M': 'mmHg', 'I': 'inHg'}
        humidity_units = {'P': '%'}
        rain_accumulation_units = {'M': 'mm', 'I': 'in'}
        duration_units = {'S': 's', 's': 's'}  # error in doc!
        rain_intensity_units = {'M': 'mm/h', 'I': 'in/h'}
        hail_accumulation_units = {'M': 'hits/cm2', 'I': 'hits/in2', 'H': 'hits'}
        hail_intensity_units = {'M': 'hits/cm2h', 'I': 'hits/in2h', 'H': 'hits/h'}
        voltage_units = {'V': 'V'}
        heating_status = {'N': '0% hi-',
                          'V': '50% mid-hi',
                          'W': '100% lo-mid',
                          'F': '50% -lo'}

        self.logger.log(logging.TRACE, label_value)
        label, value = label_value.split("=")
        unit_chr = value[-1]
        unit = ''
        val = value[:-1]
        try:
            if label == 'Id':  # prevent this to reach the duration block
                return None
            elif label[0] == 'T':
                unit = temperature_units[unit_chr]
            elif label[0] == 'S':
                unit = speed_units[unit_chr]
            elif label[0] == 'D':
                unit = direction_units[unit_chr]
            elif label == 'Pa':
                unit = pressure_units[unit_chr]
            elif label == 'Ua':
                unit = humidity_units[unit_chr]
            elif label[-1] == 'd':
                unit = duration_units[unit_chr]
            elif label == 'Ri' or label == 'Rp':
                unit = rain_intensity_units[unit_chr]
            elif label == 'Rc':
                unit = rain_accumulation_units[unit_chr]
            elif label == 'Hi' or label == 'Hp':
                unit = hail_intensity_units[unit_chr]
            elif label == 'Hc':
                unit = hail_accumulation_units[unit_chr]
            elif label == 'Vh':
                unit = heating_status[unit_chr]
            elif label[0] == 'V':
                unit = voltage_units[unit_chr]
        except KeyError:
            if unit_chr == '#':
                unit = 'invalid'
            else:
                raise ValueError('Cannot parse unit character {}'.format(unit_chr))
        return [val, unit]

    def lookup(self, map, key):
        # print self.parse_unit(map[key])
        result = self.parse_unit(map[key])
        return result

    def create_lookup(self, values):
        vmap = {}
        for i in values:
            key, val = i.split("=")
            vmap[key] = i
        return vmap

    def add_field(self, data, name, field, vmap, transform=lambda a: a):

        if type(field) == list:
            tmp = []
            for i in field:
                if i in vmap:
                    tmp.append(transform(self.parse_unit(vmap[i])))
            data[name] = tmp
        else:
            if field in vmap:
                data[name] = transform(self.parse_unit(vmap[field]))





class WindDataMessageParser(BaseMessageParser):
    def parse(self, address, message):
        values = message.split(",")
        if values[0] == WIND_RESULT:
            vmap = self.create_lookup(values[1:])
            data = {
                "Type": "Wind",
                "Data": {
                    "Speed": {
                        # "Average": self.parse_unit(vmap['Sm']),
                        # "Limits": [self.parse_unit(vmap['Sn']), self.parse_unit(vmap['Sx'])]
                    },
                    "Direction": {
                        # "Average": self.parse_unit(vmap['Dm']),
                        # "Limits": [self.parse_unit(vmap['Dn']), self.parse_unit(vmap['Dx'])]
                    },

                }
            }
            self.add_field(data['Data']['Speed'], "Average", "Sm", vmap)
            self.add_field(data['Data']['Speed'], "Limits", ["Sn", "Sx"], vmap)
            self.add_field(data['Data']['Direction'], "Average", "Dm", vmap)
            self.add_field(data['Data']['Direction'], "Limits", ["Dn", "Dx"], vmap)
            return data


class PTUDataMessageParser(BaseMessageParser):
    def parse(self, address, message):
        values = message.split(",")
        if values[0] == PTU_RESULT:
            vmap = self.create_lookup(values[1:])
            data = {
                "Type": "PTU",
                "Data":{
                    "Temperature":{
                        # 'Ambient': self.parse_unit(vmap['Ta']),
                        # 'Internal': self.parse_unit(vmap['Tp'])
                    },
                    # "Humidity": self.parse_unit(vmap['Ua']),
                    # "Pressure": self.parse_unit(vmap['Pa'])
                }
            }

            # if 'Tp' in vmap:
            #     data['Temperature']['Internal'] = self.parse_unit(vmap['Tp'])
            # else:
            #     logging.warning("Internal Temperature not reported")

            self.add_field(data['Data']['Temperature'], "Ambient", "Ta", vmap)
            self.add_field(data['Data']['Temperature'], "Internal", "Tp", vmap)
            self.add_field(data['Data'], "Humidity", "Ua", vmap)
            self.add_field(data['Data'], "Pressure", "Pa", vmap)

            # return {
            #     "Type": "PTU",
            #     "Data": data
            # }

            return data


class RainDataMessageParser(BaseMessageParser):

    def parse(self, address, message):
        values = message.split(",")
        if values[0] == RAIN_RESULT:
            vmap = self.create_lookup(values[1:])
            data = {
                "Type":"Rain",
                "Data": {
                    "Rain": {
                        # "Intensity": self.parse_unit(vmap['Ri']),
                        # "Peak": self.parse_unit(vmap['Rp']),
                        # "Accumulation": self.parse_unit(vmap['Rc']),
                        # "Duration": self.parse_unit(vmap['Rd']),
                    },
                    "Hail": {
                        # "Intensity": self.parse_unit(vmap['Hi']),
                        # "Peak": self.parse_unit(vmap['Hp']),
                        # "Accumulation": self.parse_unit(vmap['Hc']),
                        # "Duration": self.parse_unit(vmap['Hd']),
                    }
                }
            }

            self.add_field(data['Data']['Rain'], "Intensity", "Ri", vmap)
            self.add_field(data['Data']['Rain'], "Peak", "Rp", vmap)
            self.add_field(data['Data']['Rain'], "Accumulation", "Rc", vmap)
            self.add_field(data['Data']['Rain'], "Duration", "Rd", vmap)

            self.add_field(data['Data']['Hail'], "Intensity", "Hi", vmap)
            self.add_field(data['Data']['Hail'], "Peak", "Hp", vmap)
            self.add_field(data['Data']['Hail'], "Accumulation", "Hc", vmap)
            self.add_field(data['Data']['Hail'], "Duration", "Hd", vmap)

            return data



class StatusMessageParser(BaseMessageParser):
    def parse(self, address, message):
        values = message.split(",")
        if values[0] == STATUS_RESULT:

            vmap = self.create_lookup(values[1:])
            data = {
                "Type" : "Status",
                "Data":{
                    "Voltages": {
                        # "Supply": self.parse_unit(vmap['Vs']),
                        # "Reference": self.parse_unit(vmap['Vr']),
                        # "Heating": [self.parse_unit(vmap['Vh'])[0], "V"]
                    },
                    "Heating": {
                        # "Temperature": self.parse_unit(vmap["Th"]),
                        # "Status":  self.parse_unit(vmap['Vh'])[1],
                    }
                }
            }

            self.add_field(data['Data']['Voltages'], "Supply", "Vs", vmap)
            self.add_field(data['Data']['Voltages'], "Reference", "Vr", vmap)
            self.add_field(data['Data']['Voltages'], "Heating", "Vh", vmap, lambda a: [a[0], "V"])

            self.add_field(data['Data']['Heating'], "Temperature", "Th", vmap)
            self.add_field(data['Data']['Heating'], "Status", "Vh", vmap, lambda a: a[1])

            return data


class CommsMessageParser(BaseMessageParser):
    def parse(self, address, message):
        values = message.split(",")
        command = values[0].upper()
        if command == ASCII_CONNECTION_INFO.upper() or command == SDI12_CONNECTION_INFO.upper():
            return values


class CommandResponseMessageParser(BaseMessageParser):
    def parse(self, address, message):
        values = message.split(",")
        command = values[0]
        if command == ASCII_COMMAND_RESPONSE:
            return {"Type": "Command Response", "Data": { "Result": values[1]}}

class SettingsMessageParser(BaseMessageParser):

    def __init__(self):
        BaseMessageParser.__init__(self)
        self.message = None
        self.order = None
        self.ignore=[]

    def parse(self, address, message):
        values = message.split(",")
        command = values[0]
        if command == self.message :
            result = {}
            for i in values[1:]:
                key, value = i.split("=")
                result[key] = value

            m,c = result['R'].split("&")
            m = [[False, True][int(x)] for x in list(m)]
            c = [[False, True][int(x)] for x in list(c)]

            result['R']= {
                "Requested":{},
                "Composite":{}
            }

            for i in range(len(self.order)):
                result['R']['Requested'][self.order[i]] = m[i]
                result['R']['Composite'][self.order[i]] = c[i]


            return result

    def create_message(self, settings):
        R = settings['R']
        R['Composite'] = "".join([str(int(R["Composite"][x])) for x in self.order])
        R['Requested'] = "".join([str(int(R["Requested"][x])) for x in self.order])
        settings['R'] = "%s%s&%s%s"%(R['Requested'], (8 - len(self.order)) * '0', R['Composite'], (8 - len(self.order)) * '0')
        tmp = []
        for i in settings:
            if i in self.ignore: continue
            tmp.append("%s=%s"%(i, settings[i]))

        return ",".join(tmp)

class PTUSettingsMessageParser(SettingsMessageParser):
    def __init__(self):
        SettingsMessageParser.__init__(self)
        self.order = ["Pa", "Ta", "Tp", "Ua"]
        self.message = ASCII_PTU_SETTINGS


class PrecipationSettingsMessageParser(SettingsMessageParser):
    def __init__(self):
        SettingsMessageParser.__init__(self)
        self.order = ["Rc", "Rd", "Ri", "Hc", "Hd", "Hi", "Rp", "Hp"]
        self.message = ASCII_PRECIPITATION_SETTINGS

class SupervisorSettingsMessageParser(SettingsMessageParser):
    def __init__(self):
        SettingsMessageParser.__init__(self)
        self.order = ["Th", "Vh", "Vs", "Vr", "Id"]
        self.message = ASCII_SUPERVISOR_SETTINGS
        self.ignore=['a', 'b', 'c','d','e','f', 'g', 'h', 'j', 'k']

class MessageParser:
    parsers = [
        WindDataMessageParser(),
        PTUDataMessageParser(),
        RainDataMessageParser(),
        StatusMessageParser(),
        CommsMessageParser(),
        CommandResponseMessageParser(),
        PTUSettingsMessageParser(),
        PrecipationSettingsMessageParser(),
        SupervisorSettingsMessageParser()
    ]

    def __init__(self, has_crc):
        self.has_crc = has_crc
        self.logger = logging.getLogger(str(MessageParser))

    def check_crc(self, message):
        message = message.strip()
        return message[:-3], crc16(message[:-3]) == message[-3:]

    def parse_message(self, message):
        if self.has_crc:
            message, result = self.check_crc(message)
        else:
            result = True

        if result:
            address = message[0]
            message = message[1:]

            result = None

            for parser in self.parsers:
                result = parser.parse(address, message)
                if result is not None:
                    break

            if result is None:
                self.logger.debug("Could not find parser for message: " + message)
                raise Exception("Parser for message not found")

            return result

        else:
            raise InvalidCRC()


class Message:
    def __init__(self, address, has_checksum):
        self.has_checksum = has_checksum
        self.address = str(address)
        self.term = None
        self.comms_settings = None

    def set_address(self, address):
        self.address = str(address)

    @staticmethod
    def enumerate_devices():
        raise Exception("Unimplemented")

    def checksum(self, message):
        if self.has_checksum:
            return message + crc16(message)
        return message

    def read_all_data(self):
        return self.address + ASCII_READ_DATA + self.term

    def reset(self):
        return self.checksum(self.address + ASCII_RESET) + self.term

    def reset_precipation_intensity(self):
        return self.address + ASCII_RESET_PRECIPITATION_INTENSITY + self.term

    def reset_precipation_counter(self):
        return self.address + ASCII_RESET_PRECIPITATION_COUNTERS + self.term

    def get_connection_info(self):
        return self.checksum(self.address + ASCII_CONNECTION_INFO) + self.term

    def get_communication_settings(self):
        return self.checksum(self.address + self.comms_settings) + self.term


    def __get_settings(self, message_handler):
        return self.checksum(self.address + message_handler.message) + self.term

    def __set_settings(self, settings, message_handler):
        return self.checksum(
            self.address +
            message_handler.message +
            "," +
            message_handler.create_message(settings)
        ) + self.term

    def get_ptu_settings(self):
        # return self.checksum(self.address + ASCII_PTU_SETTINGS) + self.term
        return self.__get_settings(PTUSettingsMessageParser())

    def set_ptu_settings(self, settings):
        # msg = PTUSettingsMessageParser()
        # return self.checksum(
        #     self.address +
        #     msg.message +
        #     "," +
        #     msg.create_message(settings)
        # ) + self.term
        return self.__set_settings(settings, PTUSettingsMessageParser())

    def get_precipitation_settings(self):
        # return self.checksum(self.address + ASCII_PRECIPITATION_SETTINGS) + self.term
        return self.__get_settings(PrecipationSettingsMessageParser())

    def set_precipitation_settings(self, settings):
        # msg = PrecipationSettingsMessageParser()
        # return self.checksum(
        #     self.address +
        #     msg.message +
        #     "," +
        #     msg.create_message(settings)
        # ) + self.term
        return self.__set_settings(settings, PrecipationSettingsMessageParser())


    def set_supervisor_settings(self, settings):
        # return self.checksum(
        #     self.address +
        #     ASCII_SUPERVISOR_SETTINGS +
        #     "," +
        #     SupervisorSettingsMessageParser().create_message(settings)
        # ) + self.term
        return self.__set_settings(settings, SupervisorSettingsMessageParser())

    def get_supervisor_settings(self):
        return self.__get_settings(SupervisorSettingsMessageParser())

    # Page 79
    def set_communication_settings(self,
                                   protocol=None,
                                   serial_interface=None,
                                   composite_data_repeat=None,
                                   baud_rate=None,
                                   data_bits=None,
                                   parity=None,
                                   stop_bits=None,
                                   rs485_line_delay=None,
                                   lock=None):
        result = self.address + self.comms_settings

        if protocol is not None:
            if not CommunicationProtocol.is_valid(protocol):
                raise Exception(
                    "Invalid Protocol: %s, expected: %s" % (protocol, CommunicationProtocol.__valid__.__repr__()))
            result += "," + CommunicationParameters.Protocol + "=" + protocol

        if serial_interface is not None:
            if not SerialInterface.is_valid(serial_interface):
                raise Exception("Invalid Serial interface: %s, expected: %s" % (
                serial_interface, SerialInterface.__valid__.__repr__()))
            result += "," + CommunicationParameters.SerialInterface + "=" + serial_interface

        if composite_data_repeat is not None:
            cdr = int(composite_data_repeat)
            if cdr < 0 or cdr > 3600:
                raise Exception("Composite Data Repeat invalid: %s, valid range 0...3600" % str(composite_data_repeat))
            result += "," + CommunicationParameters.CompositeDataRepeat + "=" + str(composite_data_repeat)

        if baud_rate is not None:
            if int(baud_rate) not in valid_baud_rates:
                raise Exception("Invalid Baud Rate: %s, expected: %s" % (baud_rate, valid_baud_rates.__repr__()))
            result += "," + CommunicationParameters.BaudRate + "=" + str(baud_rate)

        if data_bits is not None:
            if int(data_bits) not in valid_baud_rates:
                raise Exception("Invalid Data Bits: %s, expected: %s" % (data_bits, valid_data_bits.__repr__()))
            result += "," + CommunicationParameters.DataBits + "=" + str(data_bits)

        return self.checksum(result) + self.term


class ASCIIMessage(Message):
    term = ASCII_COMMAND_TERM

    def __init__(self, address, has_checksum):
        Message.__init__(self, address, has_checksum)
        self.comms_settings = ASCII_CONNECTION_INFO
        self.term = ASCII_COMMAND_TERM

    @staticmethod
    def enumerate_devices():
        return "?" + ASCII_COMMAND_TERM


class SDI12Message(Message):
    term = SDI12_COMMAND_TERM

    def __init__(self, address, has_checksum):
        Message.__init__(self, address, has_checksum)
        self.comms_settings = SDI12_CONNECTION_INFO
        self.term = SDI12_COMMAND_TERM

    @staticmethod
    def enumerate_devices():
        return "?" + SDI12_COMMAND_TERM
