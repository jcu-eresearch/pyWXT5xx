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
import time

from wxt5xx.message import MessageParser, Message, ASCIIMessage, CommunicationProtocol


class WXT5xx:
    def __init__(self, ser, service_port=False, address=None, protocol=CommunicationProtocol.ASCII_Polled_CRC):
        self.ser = ser
        self.parser = MessageParser(CommunicationProtocol.has_crc(protocol))
        self.logger = logging.getLogger(str(WXT5xx))

        if service_port:
            time.sleep(10)

        if address is None:
            self.__write(ASCIIMessage.enumerate_devices())
            message = self.ser.readline()
            self.logger.debug("Received Address: %s"%message.strip())

            if message is not None:
                self.address = int(message.strip())
            else:
                raise Exception("No devices found")
        else:
            self.address = address

        self.protocol = CommunicationProtocol.lookup_protocol(protocol)(self.address, CommunicationProtocol.has_crc(protocol))

        self.__write(self.protocol.set_communication_settings(protocol=protocol))
        self.logger.info("Set comms reponse: %s"%self.read_message())
        self.__write(self.protocol.set_communication_settings())
        self.coms_settings = self.read_message()

    def __write(self, message):
        self.logger.debug("Sending Message: "+message.strip())
        self.ser.write(message)
        self.ser.flush()

    def read_message(self):
        # self.ser.flushInput()
        message = self.ser.readline().strip()
        self.logger.debug("Received message: "+message)
        parsed = self.parser.parse_message(message)
        self.logger.debug("Parsed Message: %s"%parsed)
        return parsed

    def get_all_data(self):
        self.__write(self.protocol.read_all_data())
        time.sleep(0.1)
        results = []
        results.append(self.read_message())
        results.append(self.read_message())
        results.append(self.read_message())
        results.append(self.read_message())
        return results

    def get_ptu_settings(self):
        self.__write(self.protocol.get_ptu_settings())
        time.sleep(0.1)
        return self.read_message()

    def set_ptu_settings(self, settings):
        self.__write(self.protocol.set_ptu_settings(settings))
        time.sleep(0.1)
        return self.read_message()

    def get_precipitation_settings(self):
        self.__write(self.protocol.get_precipitation_settings())
        time.sleep(0.1)
        return self.read_message()

    def set_precipitation_settings(self, settings):
        self.__write(self.protocol.set_precipitation_settings(settings))
        time.sleep(0.1)
        return self.read_message()



    def reset_precipitation(self):
        results = []
        self.__write(self.protocol.reset_precipation_intensity())
        results.append(self.read_message())
        self.__write(self.protocol.reset_precipation_counter())
        results.append(self.read_message())
        return results

    def get_supervisor_settings(self):
        self.__write(self.protocol.get_supervisor_settings())
        time.sleep(0.1)
        return self.read_message()

    def set_supervisor_settings(self, settings):
        self.__write(self.protocol.set_supervisor_settings(settings))
        time.sleep(0.1)
        return self.read_message()

    def close(self):
        self.ser.close()
