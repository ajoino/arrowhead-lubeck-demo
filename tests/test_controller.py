import json
import asyncio

from demo.devices.arrowhead_a_devices import Controller

with open('core_config.json', 'r') as json_config:
    config = json.load(json_config)

controller = Controller.create(
        system_name='A11',
        address='172.16.1.1',
        port=5557,
        config=config
)

if __name__ == '__main__':
    asyncio.run(controller.main())
