import asyncio
from typing import Any, Dict, List

from arrowhead_client.client import provided_service
from arrowhead_client.client.implementations import AsyncClient
from arrowhead_client.errors import NoAvailableServicesError
from demo.devices.ipc_mixin import IPyCMixin
from ipyc import AsyncIPyCClient, AsyncIPyCLink

#import equipment

MAX_POWER = 1500

class TemperatureSensorNoArrowhead:
    pass


class Controller(IPyCMixin, AsyncClient):
    def __init__(self, *args, k_P=40, k_I=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.integral = 0.0
        self.k_P = k_P
        self.k_I = k_I
        self.control = 0.0
        self.setpoint = 293.15
        self.temperature = 293.15
        self.timestep = 0

    @property
    def room_name(self):
        return self.system.system_name.split('_')[0]

    async def get_setpoint(self):
        await self.ipyc_connection.send({"name": self.room_name, "system": "controller", "unit": "heater"})
        res = await self.ipyc_connection.receive()

        return res["setpoint"], res["timestep"]

    def read_temperature(self, temperature_message):
        measurement = temperature_message[0]
        if measurement["n"] != f'{self.room_name}_temp_sensor':
            raise RuntimeError(f'Unexpected name in message: {temperature_message}')

        return measurement["v"]

    def control_message(self):
        return [{"n": self.system.system_name, "t": self.timestep, "u": "W", "v": max(0.0, self.control)}]

    def control_loop(self, dt):
        error = self.setpoint - self.temperature
        old_integral = self.integral
        self.integral = max(-10 * self.k_P, min(self.integral + error * dt, 10 * self.k_P))
        return self.k_P * error + self.k_I * self.integral, old_integral

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



class Heater(IPyCMixin, AsyncClient):
    def __init__(self, *args, max_power: float = MAX_POWER, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_power = max_power

    @property
    def room_name(self):
        return self.system.system_name.split('_')[0]

    @provided_service(
            'actuator',
            service_uri='/actuation',
            protocol='HTTP',
            method='POST',
            payload_format='JSON',
            access_policy='NOT_SECURE',
    )
    async def update_actuation(self, actuation_message: List[Dict[str, Any]]):
        name = actuation_message[0]["n"]
        value = max(0, min(actuation_message[0]["v"], self.max_power))
        print(f"Current heater power: {value}")

        await self.ipyc_connection.send({"name": self.room_name, "unit": "heater", "system": "actuator", "actuation": value})
        temp_message = await self.ipyc_connection.receive()

class TemperatureSensor(IPyCMixin, AsyncClient):
    @property
    def room_name(self):
        return self.system.system_name.split('_')[0]

    @provided_service(
            'temperature',
            service_uri='/temperature',
            protocol='HTTP',
            method='GET',
            payload_format='JSON',
            access_policy='NOT_SECURE',
    )
    async def get_temperature(self):
        await self.ipyc_connection.send({"name": self.room_name, "unit": "heater", "system": "sensor"})
        temp_message = await self.ipyc_connection.receive()

        return [{"n": self.system.system_name, "t": temp_message["timestep"], "u": "K", "v": temp_message["temp"]}]


if __name__ == '__main__':
    import json
    from pprint import pprint
    with open('../../core_config.json', 'r') as config_json:
        config = json.load(config_json)
    pprint(config)
    test_temp = Heater.create(
            system_name='test',
            address='172.16.1.1',
            port=5555,
            config=config,
    )
    test_temp.run_forever()