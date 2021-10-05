import asyncio
import random
from typing import Dict, Mapping
from functools import partial
import sys
from pprint import pprint

from ipyc import AsyncIPyCHost, AsyncIPyCLink
from aioconsole import ainput
from numpy.random import RandomState
import numpy.typing as npt

#import environment
from room import Room

class ArrowheadEnvironment():
    ipyc_host: AsyncIPyCHost
    prng: RandomState
    room_names = ('A11', 'A12', 'A13', 'A14', 'A21', 'A22', 'A23', 'A24')
    room_coordinates = ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (4, 1))
    outside: Room
    rooms: Dict[str, Room]
    actuation_updated: Dict[str, bool]
    temperatures_read: Dict[str, bool]

    def __init__(self):
        self.room_init()
        self.timestep = 0
        self._started = False
        self.heating_power = {room_name: 0.0 for room_name in self.room_names}
        self.cooling_power = {room_name: 0.0 for room_name in self.room_names}
        self.setpoints = {room_name: 293.15 for room_name in self.room_names}
        self.actuation_updated = {room_name: False for room_name in self.room_names}
        self.temperatures_read = {room_name: False for room_name in self.room_names}
        self.temperatures_updated = {room_name: False for room_name in self.room_names}
        self.setpoints_updated = {room_name: False for room_name in self.room_names}

        #@self.ipc_host.on_connect
    async def on_connect(self, connection: AsyncIPyCLink):
        await self.simulation_started.wait()
        while connection.is_active():
            message = await connection.receive()
            try:
                if message.get("unit") == "heater":
                    async with self.temp_read_cond:
                        print('Waiting to read temperature')
                        await self.temp_read_cond.wait()
                        await connection.send(self.send_temperature(message))
                        self.temperatures_read = {name: True for name in self.room_names}
                        if self.all_temperatures_read():
                            self.temp_read_cond.notify_all()
                    print(f'Finished one temp sensor reading')
                elif message.get("unit") == "actuator":
                    async with self.temp_update_cond:
                        #await self.temp_update_cond.wait()
                        confirmation_message = self.send_actuation_confirmation(message)
                        await connection.send(confirmation_message)
                        self.temperatures_updated = {name: True for name in self.room_names}
                        if self.all_temperatures_updated():
                            self.temp_update_cond.notify_all()
                    print(f'Finished one actuator reading')
                elif message.get("unit") == "controller":
                    async with self.setpoint_read_cond:
                        #await self.setpoint_read_cond.wait()
                        await connection.send(self.send_controller_setpoint(message))
                    print(f'Finished one setpoint reading')
                else:
                    raise RuntimeError(
                            f'Message "{message}" is malformed, '
                            f'"unit" field must be either "heater" or "actuator"'
                    )
            except AttributeError as e:
                raise RuntimeError(f'Recevied message {message} of non-mapping type.') from e

    @property
    def current_heat_output(self) -> Dict[str, float]:
        return {
            room_name: cool_pow + heat_pow
            for (room_name, cool_pow), heat_pow
            in zip(self.cooling_power.items(), self.heating_power.values())
        }

    def started(self):
        return self._started


    def send_temperature(self, message: Dict) -> Dict:
        room_name = message["name"]
        temperature = self.rooms[room_name].temperature # + random.uniform(-2, 2)
        return {"temp": temperature, "timestep": self.timestep}

    def send_actuation_confirmation(self, message) -> Dict:
        room_name = message["name"]
        new_actuation = message["actuation"]

        if new_actuation >= 0.0:
            self.heating_power[room_name] = new_actuation
            self.cooling_power[room_name] = 0.0
        else:
            self.heating_power[room_name] = 0.0
            self.cooling_power[room_name] = new_actuation
        #self.actuation_updated[room_name] = True
        self.actuation_updated = {name: True for name in self.room_names}

        return {"status": True, "timestep": self.timestep}

    def send_controller_setpoint(self, message):
        room_name = message["name"]

        if room_name not in self.room_names:
            return {"status": False, "timestep": self.timestep}

        return {"setpoint": self.setpoints[room_name], "timestep": self.timestep}

    def room_init(self):
        self.outside = Room(
                name='OO',
                temperature=273.0,
                heat_capacity=float('inf'),
                position=(0, 2),
                static=True
        )

        self.rooms = {self.outside.name: self.outside} | {
            name: Room(
                    name=name,
                    temperature=273.0,
                    heat_capacity=46e3,
                    position=pos,
            ) for name, pos in zip(self.room_names, self.room_coordinates)
        }

        # Bottom row
        self.rooms['A11'].add_neighbors({(2, self.outside), (1, self.rooms['A12']), (1, self.rooms['A21'])})
        self.rooms['A12'].add_neighbors(
                {(1, self.outside), (1, self.rooms['A11']), (1, self.rooms['A13']), (1, self.rooms['A22'])})
        self.rooms['A13'].add_neighbors(
                {(1, self.outside), (1, self.rooms['A12']), (1, self.rooms['A14']), (1, self.rooms['A23'])})
        self.rooms['A14'].add_neighbors({(2, self.outside), (1, self.rooms['A13']), (1, self.rooms['A24'])})
        # Top row
        self.rooms['A21'].add_neighbors({(2, self.outside), (1, self.rooms['A22']), (1, self.rooms['A11'])})
        self.rooms['A22'].add_neighbors(
                {(1, self.outside), (1, self.rooms['A21']), (1, self.rooms['A23']), (1, self.rooms['A12'])})
        self.rooms['A23'].add_neighbors(
                {(1, self.outside), (1, self.rooms['A22']), (1, self.rooms['A24']), (1, self.rooms['A13'])})
        self.rooms['A24'].add_neighbors({(2, self.outside), (1, self.rooms['A23']), (1, self.rooms['A14'])})

    def equipment_init(self):
        pass

    def update_random_setpoints(self):
        self.setpoints = {name: 298.0 for name in self.room_names}

    def all_actuations_updated(self) -> bool:
        return all(cond for cond in self.actuation_updated.values())

    def all_setpoints_updated(self) -> bool:
        return all(cond for cond in self.setpoints_updated.values())

    def all_temperatures_read(self) -> bool:
        return all(cond for cond in self.temperatures_read.values())

    def all_temperatures_updated(self) -> bool:
        return all(cond for cond in self.temperatures_updated.values())

    def update_room_temperatures(
            self,
            previous_room_temperatures: Mapping[str, float],
            current_heat_output: Mapping[str, float],
            time_delta: float
    ):
        for room_name, output in current_heat_output.items():
            self.rooms[room_name].update_temperature(
                    previous_room_temperatures, time_delta, 1e-4, output
        )
    async def step(
            self,
            dt: float,
            current_time: float,
            outside_temperature: float,
            noise_vector: npt.ArrayLike = None,
    ):
        async with self.temp_read_cond:
            self.outside.static_temp = outside_temperature + 273.15
            current_room_temperatures = {name: room.temperature for name, room in self.rooms.items()}
            print(f'{current_room_temperatures = }')
            await asyncio.sleep(0.2)
            self.temp_read_cond.notify_all()
            await self.temp_read_cond.wait_for(self.all_temperatures_read)
            self.temperatures_read = {name: False for name in self.room_names}

        self.update_random_setpoints()

        async with self.temp_update_cond:
            heat_output = self.current_heat_output
            self.update_room_temperatures(current_room_temperatures, heat_output, dt)
            await asyncio.sleep(0.2)
            self.temp_update_cond.notify_all()
            await self.temp_update_cond.wait_for(self.all_temperatures_updated)
            self.temperatures_updates = {name: False for name in self.room_names}

    async def run_simulation(self):
        self.simulation_started = asyncio.Event()
        self.temp_read_cond = asyncio.Condition()
        self.setpoint_read_cond = asyncio.Condition()
        self.temp_update_cond = asyncio.Condition()
        # Wrapper function for the handling of ipc
        async def on_connect_linker(connection):
            return await self.on_connect(connection)
        self.ipc_host = AsyncIPyCHost()
        self.ipc_host.add_connection_handler(on_connect_linker)
        asyncio.create_task(self.ipc_host.start())
        await ainput("Press enter to start simulation >")
        self._started = True
        self.simulation_started.set()
        print("Waiting five seconds to let everything start up")
        await asyncio.sleep(1)
        while True:
            print('----------------------------')
            await self.step(10, 0, 25)
            print('Finished one simulation step')
            await asyncio.sleep(2)


async def main(env: ArrowheadEnvironment):
    try:
        await env.run_simulation()
    except KeyboardInterrupt:
        await env.ipc_host.close()

if __name__ == '__main__':
    from pprint import pprint
    env = ArrowheadEnvironment()
    pprint(env.rooms)

    asyncio.run(main(env))
