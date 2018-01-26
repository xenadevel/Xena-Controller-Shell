#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import logging

from cloudshell.traffic.tg_helper import get_reservation_resources, get_address, set_family_attribute

from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

from driver import XenaControllerDriver

address = '176.22.65.114'
user = 'yshamir'

ports = ['xena 2g/Module6/Port0', 'xena 2g/Module6/Port1']
attributes = {'User': user}


class TestXenaControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'Xena Controller', attributes)
        self.driver = XenaControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def tearDown(self):
        self.driver.cleanup()
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        self.reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                           'Xena Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, self.reservation_ports[0], 'Logical Name', 'test_config')
        set_family_attribute(self.session, self.reservation_ports[1], 'Logical Name', 'test_config')
        self.driver.load_config(self.context, path.dirname(__file__))

    def test_run_traffic(self):
        self.test_load_config()

        self.driver.start_traffic(self.context, 'True')
        port_stats = self.driver.get_statistics(self.context, 'Port', 'JSON')
        port_name = get_address(self.reservation_ports[0])
        assert(int(port_stats[port_name]['pt_total_packets']) == 16000)
        stream_stats = self.driver.get_statistics(self.context, 'Stream', 'JSON')
        stream_name = get_address(self.reservation_ports[0])[-3:] + '/0'
        assert(int(stream_stats[stream_name]['packets']) == 8000)
        tpld_stats = self.driver.get_statistics(self.context, 'TPLD', 'JSON')
        tpld_name = get_address(self.reservation_ports[0])[-3:] + '/0'
        assert(int(tpld_stats[tpld_name]['pr_tpldtraffic_pac']) == 8000)

        print(self.driver.get_statistics(self.context, 'Port', 'CSV'))
        print(self.driver.get_statistics(self.context, 'Stream', 'CSV'))
        print(self.driver.get_statistics(self.context, 'TPLD', 'CSV'))

        self.driver.start_traffic(self.context, 'False')
        stats = self.driver.get_statistics(self.context, 'Port', 'JSON')
        assert(int(stats[get_address(self.reservation_ports[0])]['pt_total_packets']) < 16000)
        self.driver.stop_traffic(self.context)


if __name__ == '__main__':
    sys.exit(unittest.main())
