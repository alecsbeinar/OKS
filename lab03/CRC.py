import random
import textwrap
from typing import Tuple

from ByteStuffing import ByteStuffing


class CRC:
    def __init__(self):
        # self.key = "100000111"
        # self.lkey = 8
        self.key = "100101"
        self.lkey = 5

        self.byte_stuffing = ByteStuffing()

    def xor(self, a, b):
        result = []
        for i in range(1, len(b)):
            if a[i] == b[i]:
                result.append('0')
            else:
                result.append('1')

        return ''.join(result)

    def mod2div(self, dividend, divisor):
        pick = len(divisor)
        tmp = dividend[0: pick]
        while pick < len(dividend):
            if tmp[0] == '1':
                tmp = self.xor(divisor, tmp) + dividend[pick]
            else:
                tmp = self.xor('0' * pick, tmp) + dividend[pick]
            pick += 1
        if tmp[0] == '1':
            tmp = self.xor(divisor, tmp)
        else:
            tmp = self.xor('0' * pick, tmp)
        checkword = tmp
        return checkword

    def get_fcs(self, bin_data: str) -> int:
        appended_data = bin_data + '0' * self.lkey
        remainder = self.mod2div(appended_data, self.key)
        return int(remainder, 2)

    def shift(self, data: str, steps: int):
        lst = list(data)
        if steps < 0:
            steps = abs(steps)
            for i in range(steps):
                lst.append(lst.pop(0))
        else:
            for i in range(steps):
                lst.insert(0, lst.pop())
        return ''.join(lst)

    @staticmethod
    def invert_bit(bit: str):
        return "0" if bit == "1" else "1"

    def binary_to_string(self, bits: str):
        split_bits = textwrap.wrap(bits, 8)
        return ''.join([chr(int(i, 2)) for i in split_bits])

    def string_to_binary(self, line: str):
        return ''.join(format(ord(x), '08b') for x in line)

    def fix_data(self, stuff_package: str):
        clear_datas = []
        payload = self.byte_stuffing.get_payload(stuff_package)
        bin_payload = self.string_to_binary(payload)
        fcs = ord(self.byte_stuffing.get_fcs(stuff_package))
        for i in range(len(bin_payload)):
            fix_data = bin_payload[:i] + self.invert_bit(bin_payload[i])
            if i < len(bin_payload) - 1:
                fix_data += bin_payload[i + 1:]

            new_payload = self.binary_to_string(fix_data)
            new_package = self.byte_stuffing.insert_payload(stuff_package, new_payload)
            un_stuff_package = self.byte_stuffing.unstuffing(new_package)
            real_data = self.byte_stuffing.get_payload(un_stuff_package)
            real_bin_data = self.string_to_binary(real_data)
            remainder = self.get_fcs(real_bin_data)

            if remainder == fcs and len(real_data) == self.byte_stuffing.len_data:
                clear_datas.append(real_data)
        print(clear_datas)
        return clear_datas[0]

    def generate_mistake(self, data: str) -> Tuple[bool, str]:
        is_mistake = True if random.random() < 3 / 10 else False
        # is_mistake = True
        rdata = data
        if is_mistake:
            position = random.randrange(len(data))
            rdata = data[:position] + self.invert_bit(data[position])
            if position < len(data) - 1:
                rdata += data[position + 1:]
        return is_mistake, rdata

    def reciverSide(self, stuff_package: str) -> tuple:
        stuff_data = self.byte_stuffing.get_payload(stuff_package)
        stuff_bin_data = self.string_to_binary(stuff_data)
        is_mistake, error_data = self.generate_mistake(stuff_bin_data)

        if not is_mistake:
            un_stuff_package = self.byte_stuffing.unstuffing(stuff_package)
            real_data = self.byte_stuffing.get_payload(un_stuff_package)
            return False, real_data
        else:
            # new_payload = self.binary_to_string(error_data)
            # new_package = self.byte_stuffing.insert_payload(stuff_package, new_payload)
            # return True, self.fix_data(new_package)
            un_stuff_package = self.byte_stuffing.unstuffing(stuff_package)
            real_data = self.byte_stuffing.get_payload(un_stuff_package)
            return True, real_data
