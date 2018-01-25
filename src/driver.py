
from cloudshell.traffic.driver import TrafficControllerDriver

from xena_handler import XenaHandler


class XenaControllerDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = XenaHandler()

    def load_config(self, context, xena_configs_folder):
        """ Reserve ports and load Xena configuration files from the given directory.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param xena_config_file_name: full path to Xena configuration file (xpc).
        """

        super(self.__class__, self).load_config(context)
        self.handler.load_config(context, xena_configs_folder)
        return 'ports reserved, configurations loaded'

    def start_traffic(self, context, blocking):
        """ Start traffic on all ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param blocking: True - wait until traffic stops, False - start traffic and return immediately.
        """

        self.handler.start_traffic(blocking)

    def stop_traffic(self, context):
        """ Stop traffic on all ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_traffic()

    def get_statistics(self, context, view_name, output_type):
        """ Get statistics for specific view.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: requested statistics view name.
        :param output_type: JSON/CSV.
        """

        return self.handler.get_statistics(context, view_name, output_type)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
