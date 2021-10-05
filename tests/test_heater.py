import json

from demo.devices.arrowhead_a_devices import Heater

with open('core_config.json', 'r') as json_config:
    config = json.load(json_config)

heater = Heater.create(
        system_name='A11',
        address='172.16.1.1',
        port=5556,
        config=config
)

if __name__ == '__main__':
    heater.run_forever()