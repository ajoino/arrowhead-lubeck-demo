from typing import Tuple
import itertools
from multiprocessing import Process
import time

from demo.devices.arrowhead_a_devices import TemperatureSensor as TemperatureSensorA
from demo.devices.arrowhead_b_devices import TemperatureSensor as TemperatureSensorB

from demo.utils import get_core_config
from demo.utils import ROOM_COORDINATES, ROOM_NAMES, sensor_a_ports, sensor_b_ports

def start_sensor_a(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()
    system_name = f'{room_name}_temp_sensor'

    temp_sensor = TemperatureSensorA.create(
            system_name=system_name,
            address='172.16.1.1',
            port=port,
            config=config
    )

    temp_sensor.run_forever()

def start_sensor_b(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()

    temp_sensor = TemperatureSensorB.create(
            system_name='temp_sensor_cooler',
            address='172.16.1.1',
            port=port,
            config=config,
            room_name=room_name,
            coordinate=room_position,
    )

    temp_sensor.run_forever()

def main():
    sensor_a_processes = [
        Process(target=start_sensor_a, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, sensor_a_ports())
    ]
    sensor_b_processes = [
        Process(target=start_sensor_b, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, sensor_b_ports())
    ]
    processes = itertools.chain(sensor_a_processes, sensor_b_processes)
    for process in processes:
        process.start()
        print(f'Started process with {process.pid = }')
    while True:
            time.sleep(20)


if __name__ == '__main__':
    main()