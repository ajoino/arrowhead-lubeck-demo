from typing import Tuple, Set, Dict, Mapping


class Temperature:
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance._temp

    def __set__(self, instance, value: float) -> None:
        if instance.static:
            return
        if value < 0.0:
            instance._temp = 0.0

        instance._temp = value


class StaticTemperature:
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance._temp

    def __set__(self, instance, value: float) -> None:
        if not instance.static:
            return
        if value < 0.0:
            instance._temp = 0.0

        instance._temp = value


class StaticBool:
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance._static

    def __set__(self, instance, value: bool):
        instance._static = value

class Room:
    temperature = Temperature()
    static_temp = StaticTemperature()
    neighbors: Dict[str, Tuple[int, "Room"]]
    static = StaticBool()

    def __init__(
            self,
            name: str,
            temperature: float,
            heat_capacity: float,
            position: Tuple[float, float],
            static: bool = False,
            metadata: Dict = None,
    ):
        self.static = False
        self.name = name
        self.temperature = temperature
        self.neighbors = {}
        self.heat_capacity = heat_capacity
        self.position = position
        self.static = static
        self.metadata = metadata or {}

    def __repr__(self):
        return f'Room(name={self.name}, temperature={self.temperature}, neighbors={ {room for room in self.neighbors} }, heat_capacity={self.heat_capacity}, position={self.position}, static={self.static})'

    def __str__(self):
        return f'Room {self.name}'

    def update_temperature(
            self,
            current_temperatures: Mapping[str, float],
            dt: float,
            coefficient: float,
            equipment_power: float,
    ) -> None:
        if self.static:
            return

        neighbor_temperatures = (
            (self.neighbors[room_name][0], temp) for room_name, temp in current_temperatures.items()
            if room_name in self.neighbors
        )

        self.temperature -= dt * (coefficient * sum(
                neighbor_multiplier * (self.temperature - neighbor_temperature)
                for neighbor_multiplier, neighbor_temperature in neighbor_temperatures
        ) - equipment_power / self.heat_capacity)

    def add_neighbors(self, neighbors: Set[Tuple[int, "Room"]]) -> None:
        """

        """
        self.neighbors = {**self.neighbors, **{room.name: (multiplier, room) for multiplier, room in neighbors}}
        """
        for neighbor in neighbors:
            if not isinstance(neighbor, Room):
                print(f'\n{neighbor} is not of class Room')
                continue
            if neighbor is self:
                print(f'\n{self} cannot be its own neighbor')
                continue
            self.neighbors.add(neighbor)
            neighbor.neighbors.add(self)
        """


"""
class Office(Room):
    def __init__(
            self,
            name: str,
            temperature: float,
            heat_capacity: float,
            position: Tuple[float, float],
    ):
        super().__init__(name, temperature, heat_capacity, temperature_sensor)
        self.heater = heater
        self.cooler = cooler
        self.controller = controller

    def __str__(self):
        return f'Office {self.name}'

    def update_temperature(self, dt: float, coefficient: float) -> None:
        super().update_temperature(dt, coefficient)
        self.new_temperature = dt / self.heat_capacity * (self.heater.produce() + self.cooler.produce())

    def update_control(self, dt, time):
        temperature_message = self.temperature_sensor.temperature_service(time)
        self.controller.read_and_update(temperature_message, dt, time)
        heater_message = self.controller.heater_message(time)
        cooler_message = self.controller.cooler_message(time)
        self.heater.regulate_output(heater_message)
        self.cooler.regulate_output(cooler_message)
        return temperature_message, heater_message, cooler_message
"""


class Outside(Room):
    pass


if __name__ == '__main__':
    test_room = Room('test', 0)
    print(test_room)
    test_room.update_temperature(273)
    print(test_room)
    static_room = Room('static', 298, True)
    print(static_room)
    static_room.update_temperature(273)
    print(static_room)

    test_room.add_neighbors([static_room])
    print(test_room.neighbors)
    print(static_room.neighbors)
    test_room.add_neighbors([static_room])
    test_room.add_neighbors([test_room])

    test_office = Office('Office', 295)
    print(test_office)
