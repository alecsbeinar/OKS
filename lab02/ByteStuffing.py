def s2hex(text: str) -> str:
    return text.encode("cp1251").hex()


def hex2s(string_hex: str) -> str:
    return bytes.fromhex(string_hex).decode("cp1251")


def i2hex(num: int) -> str:
    return hex(int(num))[2:].zfill(2)


def hex2i(hex_num: str) -> int:
    return int(hex_num, 16)


def grouper(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)


class ByteStuffing:
    def __init__(self):
        self.n = 3
        self.flag = s2hex("#") + s2hex(chr(ord('a') + self.n - 1))
        self.esc = s2hex("$")

        self.replaced_flag_byte = s2hex("a")
        self.replaced_esc_byte = s2hex("b")

        self.null_str = s2hex("0")
        self.destination_address = self.null_str
        self.FCS = self.null_str

    def create_package(self, data: str, com_port: str) -> str:
        source_address = i2hex(int(com_port))
        hex_data = s2hex(data)
        return self.flag + self.destination_address + source_address + hex_data + self.FCS

    def get_payload(self, package: str) -> str:
        hex_payload = package[len(self.flag + self.destination_address) + 2:-len(self.FCS)]
        return hex2s(hex_payload)

    def package2string(self, package: str) -> str:
        string = hex2s(package[:len(self.flag)])
        package = package[len(self.flag):]
        string += hex2s(package[:len(self.destination_address)])
        package = package[len(self.destination_address):]
        string += str(hex2i(package[:2]))
        package = package[2:]
        string += hex2s(package[:-len(self.FCS)])
        package = package[-len(self.FCS):]
        string += hex2s(package)
        return string

    def get_index_of_stuffs(self, stuff_package: str) -> list:
        all_stuffs = []

        stuff_package_list = [''.join(i) for i in grouper(stuff_package, 2)]

        it = iter(range(len(stuff_package_list)))
        for i in it:
            if i < len(stuff_package_list) - 1:
                if (stuff_package_list[i] == self.esc and
                        stuff_package_list[i + 1] == self.replaced_flag_byte):
                    all_stuffs += [i, i + 1]
                if (stuff_package_list[i] == self.esc and
                        stuff_package_list[i + 1] == self.replaced_esc_byte):
                    all_stuffs += [i, i + 1]
                next(it)

        all_stuffs.sort()
        return all_stuffs

    def stuffing(self, data: str, com_port: str) -> str:
        package = self.create_package(data, com_port)
        package_wo_flag = package[len(self.flag):]
        package_wo_flag_list = [''.join(i) for i in grouper(package_wo_flag, 2)]

        it = iter(range(len(package_wo_flag_list)))
        for i in it:
            if package_wo_flag_list[i] == self.esc:
                package_wo_flag_list[i] = self.esc + self.replaced_esc_byte
            elif i < len(package_wo_flag_list) - 1 and package_wo_flag_list[i] + package_wo_flag_list[
                i + 1] == self.flag:
                package_wo_flag_list[i] = self.esc
                package_wo_flag_list[i + 1] = self.replaced_flag_byte
                next(it)

        stuffed_package = ''.join(package_wo_flag_list)
        return self.flag + stuffed_package

    def unstuffing(self, stuff_package: str) -> str:
        if stuff_package.startswith(self.flag):
            stuff_package_wo_flag = stuff_package[len(self.flag):]

            stuff_package_wo_flag_list = [''.join(i) for i in grouper(stuff_package_wo_flag, 2)]

            it = iter(range(len(stuff_package_wo_flag_list)))
            for i in it:
                if i < len(stuff_package_wo_flag_list) - 1:
                    if stuff_package_wo_flag_list[i] == self.esc and stuff_package_wo_flag_list[
                        i + 1] == self.replaced_flag_byte:
                        stuff_package_wo_flag_list[i] = self.flag[:2]
                        stuff_package_wo_flag_list[i + 1] = self.flag[2:]
                    if stuff_package_wo_flag_list[i] == self.esc and stuff_package_wo_flag_list[
                        i + 1] == self.replaced_esc_byte:
                        stuff_package_wo_flag_list[i] = self.esc
                        stuff_package_wo_flag_list[i + 1] = ""
                    next(it)

            return self.flag + "".join(stuff_package_wo_flag_list)
        else:
            return ""


if __name__ == "__main__":
    byte_stuffing = ByteStuffing()
    val = byte_stuffing.stuffing("#c$", "1")
    un_val = byte_stuffing.unstuffing(val)
    print(byte_stuffing.package2string(val))
    print(byte_stuffing.package2string(un_val))
    print(byte_stuffing.get_payload(un_val))
