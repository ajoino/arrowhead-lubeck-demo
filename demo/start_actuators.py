from typing import Tuple
import itertools
from multiprocessing import Process
import time

from demo.devices.arrowhead_a_devices import Heater
from demo.devices.arrowhead_b_devices import Cooler

from demo.utils import get_core_config
from demo.utils import ROOM_COORDINATES, ROOM_NAMES, actuator_a_ports, actuator_b_ports


def start_actuator_a(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()
    system_name = f'{room_name}_actuator'

    heater = Heater.create(
            system_name=system_name,
            address='172.16.1.1',
            port=port,
            config=config
    )

    heater.run_forever()


def start_actuator_b(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()

    cooler = Cooler.create(
            system_name='actuator_cooler',
            room_name=room_name,
            coordinates=room_position,
            address='172.16.1.1',
            port=port,
            config=config,
    )

    cooler.run_forever()


def main():
    actuator_a_processes = [
        Process(target=start_actuator_a, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, actuator_a_ports())
    ]
    actuator_b_processes = [
        Process(target=start_actuator_b, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, actuator_b_ports())
    ]
        #Process(target=start_sensor_b, args=(room_name, pos, port))
        #for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, itertools.count(5010))
    #]
    processes = itertools.chain(actuator_a_processes, actuator_b_processes)
    for process in processes:
        process.start()
        print(f'Started process with {process.pid = }')
    while True:
        time.sleep(20)


if __name__ == '__main__':
    main()
