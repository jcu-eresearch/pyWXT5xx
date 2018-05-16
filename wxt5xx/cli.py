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
from argparse import ArgumentParser

import sys
from pprint import pprint

import logging

def add_arguments(argParse):
    argParse.add_argument("-v", "--verbosity", default=0, action="count", help="increase output verbosity")

def configure_logging(args):
    logging.TRACE = 5

    levels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        4: logging.TRACE,
        5: logging.NOTSET
    }
    if args.verbosity > 5:
        args.verbosity = 5

    LOGGING_FORMAT = '%(asctime)-15s %(levelname)-7s %(process)-6d %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT, level=levels[args.verbosity])
    logging.addLevelName(logging.TRACE, "TRACE")
    args.logger = logging.getLogger("Main")

def add_serial_arguments(argParse):
    from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE
    import serial

    parity_choices = [serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE]
    stop_choices = [serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO]
    byte_choices = [serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]

    argParse.add_argument("--baudrate", metavar="<baudrate>" ,default=19200, type=int, help="The buad rate, default: 19200.")
    argParse.add_argument("--bytesize", default=EIGHTBITS, type=int, choices=byte_choices, help="The byte size, default: %s."%EIGHTBITS)
    argParse.add_argument("--stopbits", default=STOPBITS_ONE, type=float, choices=stop_choices, help="The stop bits, default: %s."%STOPBITS_ONE)
    argParse.add_argument("--parity", default=PARITY_NONE, type=str, choices=parity_choices, help="The stop bits, default: %s."%PARITY_NONE)
    argParse.add_argument("port", metavar="<port>", help="The serial port connected to the Vaisala.")

def get_serial_config(args):
    return dict(baudrate=args.baudrate, bytesize=args.bytesize, stopbits=args.stopbits, parity=args.parity, port=args.port)


def create_device(args):
    from wxt5xx.comms import WXT5xx
    from wxt5xx.message import CommunicationProtocol

    from serial import Serial
    configure_logging(args)

    device = WXT5xx(Serial(**get_serial_config(args)), service_port=False, address=None, protocol=CommunicationProtocol.ASCII_Polled_CRC)
    return device

def read(args):

    device = create_device(args)
    pprint(device.get_all_data())
    device.close()


def add_ptu_arguments(parser):
    parser.add_argument("--interval", metavar="<interval>", default=60, type=int, choices=range(1, 3600), help="The update interval (for automatic mode) from 1 to 3600 seconds.")
    parser.add_argument("--pressure_unit", type=str, choices=["H", "P", "B", "M", "I"], help="The Pressure Unit: H = hPa, P = Pascal, B = bar, M = mmHg, I = inHG.")
    parser.add_argument("--temperature_unit", type=str, choices=["C", "F"], help="The Temperature Unit: C = Celsius, F = Fahrenheit.")

    parser.add_argument("--Pa" ,type=bool, choices=[True, False], help="(En/Dis)able Air Pressure")
    parser.add_argument("--Ta" ,type=bool, choices=[True, False], help="(En/Dis)able Air Temperature")
    parser.add_argument("--Ua" ,type=bool, choices=[True, False], help="(En/Dis)able Air Humidity")
    parser.add_argument("--Tp" ,type=bool, choices=[True, False], help="(En/Dis)able Internal Temperature (Used in pressure caculation)")

    parser.add_argument("--cPa" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Air Pressure")
    parser.add_argument("--cTa" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Air Temperature")
    parser.add_argument("--cUa" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Air Humidity")
    parser.add_argument("--cTp" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Internal Temperature (Used in pressure caculation)")


def add_precip_arguments(parser):
    parser.add_argument("--interval", metavar="<interval>", default=60, type=int, choices=range(1, 3600), help="The update interval (for automatic mode) from 1 to 3600 seconds.")
    parser.add_argument("--precip_unit", type=str, choices=["M", "I"], help="The Precipitation Units: M = Metric, I = Imperial.")
    parser.add_argument("--hail_unit", type=str, choices=["M", "I"], help="The Hail Units: M = Metric, I = Imperial.")
    parser.add_argument("--send_mode", type=str, choices=["R", "C", "T"], help="The Auto send mode: R = on/off, C = tiping bucket, T = time based. See P.140 of the Manual for further details.")
    parser.add_argument("--counter_reset", type=str, choices=["M", "A", "L", "Y"], help="The Counter Reset: M = Manual, A = Automatic, L = Overflow, Y = Immediate reset. See P.140 of the Manual for further details.")
    parser.add_argument("--rain_accum_limit", metavar="<rain_accum_limit>", type=str, choices=range(100, 65535), help="The Rain Accumulation Limit: 100-65535")
    parser.add_argument("--hail_accum_limit", metavar="<hail_accum_limit>", type=str, choices=range(100, 65535), help="The Rain Accumulation Limit: 100-65535")

    parser.add_argument("--Rc" ,type=bool, choices=[True, False], help="(En/Dis)able Rain amount")
    parser.add_argument("--Rd" ,type=bool, choices=[True, False], help="(En/Dis)able Rain duration")
    parser.add_argument("--Ri" ,type=bool, choices=[True, False], help="(En/Dis)able Rain intensity")
    parser.add_argument("--Hc" ,type=bool, choices=[True, False], help="(En/Dis)able Hail amount")
    parser.add_argument("--Hd" ,type=bool, choices=[True, False], help="(En/Dis)able Hail duration")
    parser.add_argument("--Hi" ,type=bool, choices=[True, False], help="(En/Dis)able Hail intensity")
    parser.add_argument("--Rp" ,type=bool, choices=[True, False], help="(En/Dis)able Rain peak")
    parser.add_argument("--Hp" ,type=bool, choices=[True, False], help="(En/Dis)able Hail peak")

    parser.add_argument("--cRc" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Rain amount")
    parser.add_argument("--cRd" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Rain duration")
    parser.add_argument("--cRi" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Rain intensity")
    parser.add_argument("--cHc" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Hail amount")
    parser.add_argument("--cHd" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Hail duration")
    parser.add_argument("--cHi" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Hail intensity")
    parser.add_argument("--cRp" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Rain peak")
    parser.add_argument("--cHp" ,type=bool, choices=[True, False], help="Composite Message (En/Dis)able Hail peak")

def get_ptu(args):

    device = create_device(args)
    pprint(device.get_ptu_settings())
    device.close()

def set_ptu(args):

    print args
    device = create_device(args)
    settings = device.get_ptu_settings()

    args.logger.info("Original: %s"%settings)


    if args.interval is not None:
        settings['I'] = str(args.interval)
    if args.pressure_unit is not None:
        settings['P'] = str(args.pressure_unit)
    if args.temperature_unit is not None:
        settings['T'] = str(args.temperature_unit)


    if args.Pa is not None:
        settings['R']['Requested']['Pa'] = args.Pa
    if args.Ua is not None:
        settings['R']['Requested']['Ua'] = args.Ua
    if args.Ta is not None:
        settings['R']['Requested']['Ta'] = args.Ta
    if args.Tp is not None:
        settings['R']['Requested']['Tp'] = args.Tp

    if args.cPa is not None:
        settings['R']['Composite']['Pa'] = args.cPa
    if args.cUa is not None:
        settings['R']['Composite']['Ua'] = args.cUa
    if args.cTa is not None:
        settings['R']['Composite']['Ta'] = args.cTa
    if args.cTp is not None:
        settings['R']['Composite']['Tp'] = args.cTp

    args.logger.info("Updated : %s"%settings)

    device.set_ptu_settings(settings)

    device.close()


def get_precip(args):
    device = create_device(args)
    pprint(device.get_precipitation_settings())
    device.close()

def set_precip(args):
    print args
    device = create_device(args)
    settings = device.get_precipitation_settings()

    args.logger.info("Original: %s"%settings)


    if args.interval is not None:
        settings['I'] = str(args.interval)
    if args.precip_unit is not None:
        settings['U'] = str(args.precip_unit)
    if args.hail_unit is not None:
        settings['S'] = str(args.hail_unit)
    if args.send_mode is not None:
        settings['M'] = str(args.send_mode)
    if args.counter_reset is not None:
        settings['Z'] = str(args.counter_reset)
    if args.rain_accum_limit is not None:
        settings['X'] = str(args.rain_accum_limit)
    if args.hail_accum_limit is not None:
        settings['Y'] = str(args.hail_accum_limit)


    if args.Rc is not None:
        settings['R']['Requested']['Rc'] = args.Rc
    if args.Rd is not None:
        settings['R']['Requested']['Rd'] = args.Rd
    if args.Ri is not None:
        settings['R']['Requested']['Ri'] = args.Ri
    if args.Hc is not None:
        settings['R']['Requested']['Hc'] = args.Hc
    if args.Hd is not None:
        settings['R']['Requested']['Hd'] = args.Hd
    if args.Hi is not None:
        settings['R']['Requested']['Hi'] = args.Hi
    if args.Rp is not None:
        settings['R']['Requested']['Rp'] = args.Rp
    if args.Hp is not None:
        settings['R']['Requested']['Hp'] = args.Hp

    if args.cRc is not None:
        settings['R']['Composite']['Rc'] = args.cRc
    if args.cRd is not None:
        settings['R']['Composite']['Rd'] = args.cRd
    if args.cRi is not None:
        settings['R']['Composite']['Ri'] = args.cRi
    if args.cHc is not None:
        settings['R']['Composite']['Hc'] = args.cHc
    if args.cHd is not None:
        settings['R']['Composite']['Hd'] = args.cHd
    if args.cHi is not None:
        settings['R']['Composite']['Hi'] = args.cHi
    if args.cRp is not None:
        settings['R']['Composite']['Rp'] = args.cRp
    if args.cHp is not None:
        settings['R']['Composite']['Hp'] = args.cHp

    args.logger.info("Updated : %s"%settings)

    device.set_precipitation_settings(settings)

    device.close()

def main():

    parser = ArgumentParser(description="Manage a Vaisala device.")

    subparsers = parser.add_subparsers(title='Commands',
                           dest="command")

    read_parser = subparsers.add_parser("read", help="Make a reading from the device.")
    add_arguments(read_parser)
    add_serial_arguments(read_parser)

    ptu_parser = subparsers.add_parser("get_ptu", help="Retrieve the PTU settings.")
    add_arguments(ptu_parser)
    add_serial_arguments(ptu_parser)

    ptu_parser = subparsers.add_parser("set_ptu", help="Set the PTU settings.")
    add_arguments(ptu_parser)
    add_serial_arguments(ptu_parser)
    add_ptu_arguments(ptu_parser)

    precip_parser = subparsers.add_parser("get_precip", help="Set the Precipitation settings.")
    add_arguments(precip_parser)
    add_serial_arguments(precip_parser)

    precip_parser = subparsers.add_parser("set_precip", help="Get the Precipitation settings, for more detail see Page 138-143 of the Manual for more details.")
    add_arguments(precip_parser)
    add_serial_arguments(precip_parser)
    add_precip_arguments(precip_parser)


    args = parser.parse_args()

    # func_name = sys.argv[1]
    # sys.argv = sys.argv[1:]
    globals()[args.command](args)

if __name__ == "__main__":
    main()
    # func_name = sys.argv[1]
    # sys.argv = sys.argv[1:]
    # locals()[func_name]

