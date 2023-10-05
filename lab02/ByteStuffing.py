class ByteStuffing:
    def __init__(self):
        self.n = 3
        self.flag = "#" + chr(ord('a') + self.n - 1)
        self.esc = "$"

        self.replaced_flag_byte = "a"
        self.replaced_esc_byte = "b"

        self.len_source_address = 1

        self.null_str = "0"
        self.destination_address = self.null_str
        self.FCS = self.null_str

    def create_package(self, data: str, com_port: str) -> str:
        source_address = chr(int(com_port))
        return self.flag + self.destination_address + source_address + data + self.FCS

    def get_payload(self, package: str) -> str:
        payload = package[len(self.flag + self.destination_address) + self.len_source_address:-len(self.FCS)]
        return payload

    def package2string(self, package: str) -> str:
        string = package[:len(self.flag + self.destination_address)]
        package = package[len(self.flag + self.destination_address):]
        string += str(int(ord(package[:self.len_source_address])))
        package = package[self.len_source_address:]
        string += package
        return string

    def get_index_of_stuffs(self, stuff_package: str) -> list:
        all_stuffs = []

        for i in range(len(stuff_package)):
            if i < len(stuff_package) - 1:
                if (stuff_package[i] == self.esc and
                        stuff_package[i + 1] == self.replaced_flag_byte):
                    all_stuffs += [i, i + 1]
                if (stuff_package[i] == self.esc and
                        stuff_package[i + 1] == self.replaced_esc_byte):
                    all_stuffs += [i, i + 1]
        all_stuffs.sort()
        return all_stuffs

    def stuffing(self, data: str, com_port: str) -> str:
        package = self.create_package(data, com_port)
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
            return ""


if __name__ == "__main__":
    byte_stuffing = ByteStuffing()
    val = byte_stuffing.stuffing("#c$", "1")
    un_val = byte_stuffing.unstuffing(val)
    print(byte_stuffing.package2string(val))
    print(byte_stuffing.package2string(un_val))
    print(byte_stuffing.get_payload(un_val))
