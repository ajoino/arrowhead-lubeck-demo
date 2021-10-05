import json

from demo.devices.arrowhead_a_devices import TemperatureSensor

with open('core_config.json', 'r') as json_config:
    config = json.load(json_config)

temp_sensor = TemperatureSensor.create(
        system_name='A11',
        address='172.16.1.1',
        port=5555,
        config=config
)

if __name__ == '__main__':
    temp_sensor.run_forever()