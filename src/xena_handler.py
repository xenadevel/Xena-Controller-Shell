
from os import path
import json
import csv
import io

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.traffic.handler import TrafficHandler
from cloudshell.traffic.tg_helper import (get_reservation_resources, get_address, attach_stats_csv,
                                          get_family_attribute, is_blocking)

from xenamanager.xena_app import init_xena
from xenamanager.xena_port import XenaPort
from xenamanager.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats


class XenaHandler(TrafficHandler):

    def initialize(self, context, logger):

        self.logger = logger

        user = context.resource.attributes['User']
        self.xm = init_xena(self.logger, user)

    def tearDown(self):
        self.xm.session.release_ports()

    def load_config(self, context, xena_configs_folder):

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = get_reservation_resources(my_api, reservation_id,
                                                      'Xena Chassis Shell 2G.GenericTrafficGeneratorPort')
        for reserved_port in reservation_ports:
            config = get_family_attribute(my_api, reserved_port, 'Logical Name').Value.strip()
            address = get_address(reserved_port)
            self.logger.debug('Configuration {} will be loaded on Physical location {}'.format(config, address))
            chassis = my_api.GetResourceDetails(reserved_port.Name.split('/')[0])
            encripted_password = my_api.GetAttributeValue(chassis.Name, 'Xena Chassis Shell 2G.Password').Value
            password = CloudShellSessionContext(context).get_api().DecryptPassword(encripted_password).Value
            tcp_port = my_api.GetAttributeValue(chassis.Name, 'Xena Chassis Shell 2G.Controller TCP Port').Value
            if not tcp_port:
                tcp_port = '22611'
            ip, module, port = address.split('/')
            self.xm.session.add_chassis(ip, int(tcp_port), password)
            xena_port = XenaPort(self.xm.session.chassis_list[ip], '{}/{}'.format(module, port))
            xena_port.reserve(force=True)
            xena_port.load_config(path.join(xena_configs_folder, config) + '.xpc')

    def start_traffic(self, blocking):
        self.xm.session.clear_stats()
        self.xm.session.start_traffic(is_blocking(blocking))

    def stop_traffic(self):
        self.xm.session.stop_traffic()

    def get_statistics(self, context, view_name, output_type):
        """ stats view not supported yet. """

        stats_obj = view_name_2_object[view_name.lower()](self.xm.session)
        stats_obj.read_stats()
        if output_type.lower().strip() == 'json':
            statistics_str = json.dumps(stats_obj.get_flat_stats(), indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == 'csv':
            output = io.BytesIO()
            captions = [view_name] + stats_obj.get_flat_stats().values()[0].keys()
            writer = csv.DictWriter(output, captions)
            writer.writeheader()
            for obj_name in stats_obj.get_flat_stats():
                d = {view_name: obj_name}
                d.update((stats_obj.get_flat_stats()[obj_name]))
                writer.writerow(d)
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))


view_name_2_object = {'port': XenaPortsStats,
                      'stream': XenaStreamsStats,
                      'tpld': XenaTpldsStats}
