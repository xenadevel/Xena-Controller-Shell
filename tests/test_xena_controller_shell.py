#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute, get_address

from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

address = '176.22.65.114'
user = 'yshamir'
password = 'xena'

ports = ['xena 2g/Module6/Port4', 'xena 2g/Module6/Port5']
attributes = [AttributeNameValue('User', user),
              AttributeNameValue('Password', password)]


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'Xena Controller', attributes)

    def tearDown(self):
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_load_config(self):
        self.reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                           'Xena Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, self.reservation_ports[0], 'Logical Name', 'test_config')
        set_family_attribute(self.session, self.reservation_ports[1], 'Logical Name', 'test_config')
        self._exec_command('load_config', InputNameValue('xena_configs_folder', path.dirname(__file__)))

    def test_run_traffic(self):
        self.test_load_config()
        self._exec_command('start_traffic', InputNameValue('blocking', 'True'))

        port_stats = self._exec_command('get_statistics',
                                        InputNameValue('view_name', 'Port'), InputNameValue('output_type', 'JSON'))
        port_name = get_address(self.reservation_ports[0])
        assert(int(json.loads(port_stats.Output)[port_name]['pt_total_packets']) == 16000)
        stream_stats = self._exec_command('get_statistics',
                                          InputNameValue('view_name', 'Stream'), InputNameValue('output_type', 'JSON'))
        stream_name = get_address(self.reservation_ports[0])[-3:] + '/0'
        assert(int(json.loads(stream_stats.Output)[stream_name]['packets']) == 8000)
        tpld_stats = self._exec_command('get_statistics',
                                        InputNameValue('view_name', 'TPLD'), InputNameValue('output_type', 'JSON'))
        tpld_name = get_address(self.reservation_ports[0])[-3:] + '/0'
        assert(int(json.loads(tpld_stats.Output)[tpld_name]['pr_tpldtraffic_pac']) == 8000)

        self._exec_command('start_traffic', InputNameValue('blocking', 'False'))
        port_stats = self._exec_command('get_statistics',
                                        InputNameValue('view_name', 'Port'), InputNameValue('output_type', 'JSON'))
        assert(int(json.loads(port_stats.Output)[port_name]['pt_total_packets']) < 16000)
        self._exec_command('stop_traffic')

    def _exec_command(self, command, *params):
        return self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Xena Controller', 'Service',
                                           command, list(params))


if __name__ == '__main__':
    sys.exit(unittest.main())
