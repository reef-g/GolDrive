class PortsHandler:
    unused_ports = (port for port in range(1235, 2235))

    @staticmethod
    def get_next_port():
        """
        :return: returns the next port in the generator
        """
        return next(PortsHandler.unused_ports)
