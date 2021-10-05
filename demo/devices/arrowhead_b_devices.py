import asyncio
from typing import Any, Dict, List, Tuple

from arrowhead_client.client import provided_service
from arrowhead_client.client.implementations import AsyncClient
from arrowhead_client.errors import NoAvailableServicesError
from demo.devices.ipc_mixin import IPyCMixin
from ipyc import AsyncIPyCClient, AsyncIPyCLink

#import equipment

MAX_POWER = 1500


class Controller(IPyCMixin, AsyncClient):
    def __init__(self, *args, k_P=0.1, k_I=0.01, room_name: str = '', coordinate: Tuple[int, int] = (-1, -1), **kwargs):
        super().__init__(*args, **kwargs)
        self.integral = 0.0
        self.k_P = k_P
        self.k_I = k_I
        self.control = 0.0
        self.setpoint = 293.15
        self.temperature = 293.15
        self.timestep = 0
        self.coordinate = coordinate
        self.room_name = room_name

    async def get_setpoint(self):
        print('Retrieving setpoint')
        await self.ipyc_connection.send({"name": self.room_name, "unit": "cooler", "system": "controller"})
        res = await self.ipyc_connection.receive()
        print('Setpoint received')

        return res["setpoint"], res["timestep"]

    def read_temperature(self, temperature_message):
        print(f'{temperature_message=}')
        for measurement in temperature_message:
            if "bn" in measurement:
                name = measurement["bn"]
            elif measurement["u"] in {"Lon", "lat"}:
                if measurement["v"] < 0:
                    raise RuntimeError(f'{measurement["u"]} = {measurement["v"]} < 0!!')
            elif measurement["u"] == "Cel":
                break
        else:
            raise RuntimeError(f'Message {temperature_message} does not contain a celsius measurement')

        return measurement["v"] + 273.15

    def control_message(self):
        print(f'room {self.room_name} cooler: {-min(0.0, self.control) = }')
        return [
            {"bn": self.system.system_name, "bt": self.timestep},
            {"u": "Lon", "v": self.coordinate[0]},
            {"u": "Lat", "v": self.coordinate[1]},
            {"u": "/", "v": -min(0.0, self.control)}
        ]

    def control_loop(self, dt):
        error = self.setpoint - self.temperature
        old_integral = self.integral
        self.integral = max(-10 * self.k_P, min(self.integral + error * dt, 10 * self.k_P))
        control = max(-1.0, min(self.k_P * error + self.k_I * self.integral, 1.0))
        return control, old_integral

    async def main(self):
        async with self:
            await self.client_setup()
            await self.add_orchestration_rule(
                    'temperature',
                    'GET',
            )
            await self.add_orchestration_rule(
                    'actuator',
                    'POST',
            )
            print('STARTED')
            while True:
                try:
                    temp_message = await self.consume_service('temperature')
                except asyncio.TimeoutError:
                    continue
                except NoAvailableServicesError:
                    print(f'No available services found for service "temperature", sleeping for 10 seconds then retrying')
                    await asyncio.sleep(10)
                    continue

                old_control = self.control
                self.setpoint, self.timestep = await self.get_setpoint()
                self.temperature = self.read_temperature(temp_message.read_json())
                self.control, old_integral = self.control_loop(10.0)
                try:
                    await self.consume_service('actuator', json=self.control_message())
                except NoAvailableServicesError:
                    print(f'No available services found for service "actuation", sleeping for 10 seconds then retrying')
                    # Reset controller state if actuator is unavailable
                    self.control = old_control
                    self.integral = old_integral
                    await asyncio.sleep(10)
                #await asyncio.sleep(3)

class TemperatureSensor(IPyCMixin, AsyncClient):
    def __init__(self, *args, room_name: str = '', coordinate: Tuple[int, int] = (-1, -1), **kwargs):
        super().__init__(*args, **kwargs)
        self.coordinate = coordinate
        self.room_name = room_name

    @provided_service(
            'temperature',
            service_uri='/temperature',
            protocol='HTTP',
            method='GET',
            payload_format='JSON',
            access_policy='NOT_SECURE',
    )
    async def get_temperature(self):
        await self.ipyc_connection.send({"name": self.room_name, "unit": "cooler", "system": "sensor"})
        temp_message = await self.ipyc_connection.receive()

        return [
            {"bn": "temp_sensor", "bt": temp_message["timestep"]},
            {"u": "Lon", "v": self.coordinate[0]},
            {"u": "Lat", "v": self.coordinate[1]},
            {"u": "Cel", "v": temp_message["temp"] - 273.15},
        ]


class Cooler(IPyCMixin, AsyncClient):
    def __init__(self, *args, room_name: str = '', coordinate: Tuple[int, int] = (-1, -1), **kwargs):
        super().__init__(*args, **kwargs)
        self.max_power = MAX_POWER
        self.coordinate = coordinate
        self.room_name = room_name

    @provided_service(
            'actuator',
            service_uri='/actuation',
            protocol='HTTP',
            method='POST',
            payload_format='JSON',
            access_policy='NOT_SECURE',
    )
    async def update_actuation(self, actuation_message: List[Dict[str, Any]]):
        name = actuation_message[0]["bn"]
        for measurement in actuation_message:
            if "bn" in measurement:
                name = measurement["bn"]
            elif measurement["u"] == "/":
                value = measurement["v"]
        value = min(-self.max_power * value, 0)
        print(f"Current heater power: {value}")

        await self.ipyc_connection.send({"name": self.room_name, "unit": "cooler", "system": "actuator", "actuation": value})
        temp_message = await self.ipyc_connection.receive()

