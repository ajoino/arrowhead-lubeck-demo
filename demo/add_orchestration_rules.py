from pyrrowhead.management.orchestrator import _add_orchestration_rule

from demo.utils import (
    address,
    zipped_ports
)

for room_name, sensor_a_port, actuator_a_port, controller_a_port, sensor_b_port, actuator_b_port, controller_b_port in zipped_ports():
    _add_orchestration_rule(
            'temperature',
            'HTTP-INSECURE-JSON',
            provider_system=(f'{room_name}_temp_sensor'.lower(), address, sensor_a_port),
            consumer_name=f'{room_name}_controller'.lower(),
            consumer_address=address,
            consumer_port=controller_a_port,
            add_auth_rule=True
    )
    _add_orchestration_rule(
            'actuator',
            'HTTP-INSECURE-JSON',
            provider_system=(f'{room_name}_actuator'.lower(), address, actuator_a_port),
            consumer_name=f'{room_name}_controller'.lower(),
            consumer_address=address,
            consumer_port=controller_a_port,
            add_auth_rule=True
    )
    _add_orchestration_rule(
            'temperature',
            'HTTP-INSECURE-JSON',
            provider_system=(f'temp_sensor_cooler', address, sensor_b_port),
            consumer_name=f'controller_cooler',
            consumer_address=address,
            consumer_port=controller_b_port,
            add_auth_rule=True
    )
    _add_orchestration_rule(
            'actuator',
            'HTTP-INSECURE-JSON',
            provider_system=(f'actuator_cooler', address, actuator_b_port),
            consumer_name=f'controller_cooler',
            consumer_address=address,
            consumer_port=controller_b_port,
            add_auth_rule=True
    )
