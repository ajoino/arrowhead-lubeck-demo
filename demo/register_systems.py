from pyrrowhead.management.systemregistry import _add_system

from demo.utils import (
    address,
    zipped_ports
)

print('Adding systems to local cloud')
for room_name, sensor_a_port, actuator_a_port, controller_a_port, sensor_b_port, actuator_b_port, controller_b_port in zipped_ports():
    _add_system(f'{room_name}_temp_sensor', address, sensor_a_port)
    _add_system(f'{room_name}_actuator', address, actuator_a_port)
    _add_system(f'{room_name}_controller', address, controller_a_port)
    _add_system(f'temp_sensor_cooler', address, sensor_b_port)
    _add_system(f'actuator_cooler', address, actuator_b_port)
    _add_system(f'controller_cooler', address, controller_b_port)
