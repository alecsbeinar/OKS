from typing import List


class ByteStuffing:
    def __init__(self):
        self.n = 3
        self.flag = "#" + chr(ord('a') + self.n - 1)
        self.esc = "$"

        self.replaced_flag_byte = "a"
        self.replaced_esc_byte = "b"

        self.len_flag = 2
        self.len_source_address = 1
        self.len_destination_address = 1
        self.len_data = 3
        self.lfcs = 1
        self.package_len = self.len_flag + self.len_destination_address + self.len_source_address + self.len_data + self.lfcs

        self.null_str = "0"
        self.destination_address = self.null_str

    def create_package(self, data: str, com_port: str, fcs: str) -> str:
        source_address = chr(int(com_port))
        return self.flag + self.destination_address + source_address + data + fcs

    def dynamic_slicing(self, package: str, start_index: int, length: int) -> str:
        previous_el = ''
        slc = []
        for i in range(len(package)):
            if previous_el == '$' and package[i] == self.replaced_esc_byte and i <= start_index:
                start_index += 1

            if i >= start_index:
                slc += package[i]
                if i < len(package) - 1 and package[i] + package[i + 1] == self.esc + self.replaced_esc_byte:
                    length += 1
                if len(slc) == length:
                    return ''.join(slc)

            previous_el = package[i]
        return ''.join(slc)

    def is_valid_package(self, package: str) -> bool:
        return len(package) - package.count(self.esc + self.replaced_esc_byte) == self.package_len


    def get_payload(self, stuff_pack: str) -> str:
        start_index = self.len_flag + self.len_destination_address + self.len_source_address
        length = 3
        # return self.dynamic_slicing(stuff_pack, start_index, length)
        if stuff_pack.endswith(self.get_fcs(stuff_pack)):
            return self.dynamic_slicing(stuff_pack, start_index, length)
        else:
            # Если пакет был (#c01$b$b$b0)
            # После ошибки (#c01$b$b$â0)
            # После дестаффинга (#c01$$$â0)
            # payload возвращаем $$$â
            return self.dynamic_slicing(stuff_pack, start_index, length + 1)

    def insert_payload(self, old_package: str, new_payload: str) -> str:
        len_before_data = self.len_flag + self.len_source_address + self.len_destination_address
        before_data = self.dynamic_slicing(old_package, 0, len_before_data)
        after_data = self.dynamic_slicing(old_package, len_before_data + self.len_data, self.lfcs)
        return before_data + new_payload + after_data

    def get_fcs(self, package: str) -> str:
        len_before_data = self.len_flag + self.len_source_address + self.len_destination_address
        after_data = self.dynamic_slicing(package, len_before_data + self.len_data, self.lfcs)
        return after_data

    def package2string(self, package: str) -> str:
        string = package[:self.len_flag + self.len_destination_address]
        cur_index = self.len_flag + self.len_destination_address
        num_port = package[
                   cur_index:cur_index + self.len_source_address]
        number = int(ord(num_port))
        string += str(number)
        cur_index += self.len_source_address
        data = package[cur_index:self.get_start_index_fcs(package, "1")]
        string += data
        cur_index = self.get_start_index_fcs(package, "1")
        fcs = package[cur_index:]
        fcs_value = ''.join([str(hex(ord(c)))[2:] for c in fcs])
        string += "0x" + ("0" if len(fcs_value) == 1 else "") + fcs_value
        return string

    def get_index_of_stuffs(self, stuff_package: str, com_port: str) -> list:
        all_stuffs = []
        addition = len(com_port) - 1

        for i in range(len(stuff_package)):
            if i < len(stuff_package) - 1:
                if (stuff_package[i] == self.esc and
                        stuff_package[i + 1] == self.replaced_flag_byte):
                    all_stuffs += [i + addition, i + 1 + addition]
                if (stuff_package[i] == self.esc and
                        stuff_package[i + 1] == self.replaced_esc_byte):
                    all_stuffs += [i + addition, i + 1 + addition]
        all_stuffs.sort()
        return all_stuffs

    def get_index_of_num_port(self, stuff_package: str, com_port: str) -> list:
        all_indexes = []
        start = stuff_package.index(chr(int(com_port)))
        for i in range(start, start + len(com_port)):
            all_indexes.append(i)
        return all_indexes

    def get_start_index_fcs(self, stuff_package: str, com_port: str):
        fcs = self.get_fcs(stuff_package)
        return len(stuff_package) + len(com_port) - 1 - len(fcs)

    def stuffing(self, data: str, com_port: str, fcs: str) -> str:
        package = self.create_package(data, com_port, fcs)
        package_wo_flag = list(package[len(self.flag):])

        for i in range(len(package_wo_flag)):
            if package_wo_flag[i] == self.esc:
                package_wo_flag[i] = self.esc + self.replaced_esc_byte
            elif i < len(package_wo_flag) - 1 and package_wo_flag[i] + package_wo_flag[i + 1] == self.flag:
                package_wo_flag[i] = self.esc
                package_wo_flag[i + 1] = self.replaced_flag_byte

        stuffed_package = ''.join(package_wo_flag)
        return self.flag + stuffed_package

    def unstuffing(self, stuff_package: str) -> str:
        if stuff_package.startswith(self.flag):
            stuff_package_wo_flag = list(stuff_package[len(self.flag):])

            for i in range(len(stuff_package_wo_flag)):
                if i < len(stuff_package_wo_flag) - 1:
                    if stuff_package_wo_flag[i] == self.esc and stuff_package_wo_flag[i + 1] == self.replaced_flag_byte:
                        stuff_package_wo_flag[i] = self.flag
                        stuff_package_wo_flag[i + 1] = ""
                    if stuff_package_wo_flag[i] == self.esc and stuff_package_wo_flag[i + 1] == self.replaced_esc_byte:
                        stuff_package_wo_flag[i] = self.esc
                        stuff_package_wo_flag[i + 1] = ""

            return self.flag + "".join(stuff_package_wo_flag)
        else:
            print(f"Unstuffing error: {stuff_package}")
            return ""

# if __name__ == "__main__":
#     byte_stuffing = ByteStuffing()
#     val = byte_stuffing.stuffing("#c$", "1")
#     un_val = byte_stuffing.unstuffing(val)
#     print(byte_stuffing.package2string(val))
#     print(byte_stuffing.package2string(un_val))
#     print(byte_stuffing.get_payload(un_val))
