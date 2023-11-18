import time

import serial
import random


class Csma:
    jam_signal = "js"

    def bool_based_on_probability(self, probability: float) -> bool:
        # probability to return True
        return random.random() < probability

    def generate_busy(self, port: serial.Serial) -> bool:
        if port.inWaiting():
            return True
        return self.bool_based_on_probability(0.3)

    def generate_collision(self) -> bool:
        return self.bool_based_on_probability(0.7)

    def start_back_off(self, collision_counter: int):
        bit_time = 100 / 10 ** 9  # 100 наносекунд
        l = random.choice(range(0, 2 ** min(collision_counter, 10)))
        time.sleep(l * bit_time * 512)

    def carrier_transmission(self, port: serial.Serial, data: str) -> int:
        encoded_data = data.encode("utf-8")

        collision_counter = 0

        is_busy = self.generate_busy(port)
        while is_busy:
            is_busy = self.generate_busy(port)

        port.write(encoded_data)

        is_collision = self.generate_collision()
        while is_collision:
            port.write(self.jam_signal.encode("utf-8"))

            collision_counter += 1
            if collision_counter == 16:
                return -1

            self.start_back_off(collision_counter)

            is_busy = self.generate_busy(port)
            while is_busy:
                is_busy = self.generate_busy(port)

            port.write(encoded_data)

            is_collision = self.generate_collision()

        return collision_counter
