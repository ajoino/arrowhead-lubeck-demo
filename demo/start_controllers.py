import asyncio
from typing import Tuple
import itertools
from multiprocessing import Process
import time

from pyrrowhead.management.systemregistry import _add_system

from demo.devices.arrowhead_a_devices import Controller as ControllerA
from demo.devices.arrowhead_b_devices import Controller as ControllerB
from demo.utils import get_core_config
from demo.utils import ROOM_COORDINATES, ROOM_NAMES, controller_a_ports, controller_b_ports


def start_controller_a(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()
    system_name = f'{room_name}_controller'

    controller = ControllerA.create(
            system_name=system_name,
            address='172.16.1.1',
            port=port,
            config=config
    )

    system = controller.system
    try:
        _add_system(system.system_name, system.address, system.port)
    except:
        print("NOPE, PYRROWHEAD DOESN'T WORK IN YOUR SHODDY PROGRAM")

    asyncio.run(controller.main())


def start_controller_b(room_name: str, room_position: Tuple[int, int], port: int):
    config = get_core_config()

    controller = ControllerB.create(
            system_name='controller_cooler',
            room_name=room_name,
            coordinates=room_position,
            address='172.16.1.1',
            port=port,
            config=config,
    )

    system = controller.system
    try:
        _add_system(system.system_name, system.address, system.port)
    except:
        print("NOPE, PYRROWHEAD DOESN'T WORK IN YOUR SHODDY PROGRAM")

    asyncio.run(controller.main())


def main():
    controller_a_processes = [
        Process(target=start_controller_a, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, controller_a_ports())
    ]
    controller_b_processes = [
        Process(target=start_controller_b, args=(room_name, pos, port))
        for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, controller_b_ports())
    ]
    #Process(target=start_sensor_b, args=(room_name, pos, port))
    #for room_name, pos, port in zip(ROOM_NAMES, ROOM_COORDINATES, itertools.count(5010))
    #]
    processes = itertools.chain(controller_a_processes, controller_b_processes)
    for process in processes:
        process.start()
        print(f'Started process with {process.pid = }')
    while True:
        time.sleep(20)


if __name__ == '__main__':
    main()
