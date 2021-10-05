from pyrrowhead.management.serviceregistry import _add_service

from demo.utils import (
    address,
    zipped_ports
)
for room_name, sensor_a_port, actuator_a_port, controller_a_port, sensor_b_port, actuator_b_port, controller_b_port in zipped_ports():
    _add_service(
            'temperature',
            '/temperature',
            'HTTP-INSECURE-JSON',
            access_policy='NOT_SECURE', # type: ignore
            system=(f'{room_name}_temp_sensor', address, sensor_a_port),
            system_id=None,
    )
    _add_service(
            'actuator',
            '/actuator',
            'HTTP-INSECURE-JSON',
            access_policy='NOT_SECURE', # type: ignore
            system=(f'{room_name}_actuator', address, actuator_a_port),
            system_id=None,
    )
    _add_service(
            'temperature',
            '/temperature',
            'HTTP-INSECURE-JSON',
            access_policy='NOT_SECURE', # type: ignore
            system=(f'temp_sensor_cooler', address, sensor_b_port),
            system_id=None,
    )
    _add_service(
            'actuator',
            '/actuator',
            'HTTP-INSECURE-JSON',
            access_policy='NOT_SECURE', # type: ignore
            system=(f'actuator_cooler', address, actuator_b_port),
            system_id=None,
    )
