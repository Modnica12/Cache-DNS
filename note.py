import time


class Note:
    def __init__(self, type, ttl, data):
        self.name = 'c00c'
        self.type = type
        self.ttl = ttl
        self.data = data
        self.data_length = len(data) // 2

        self.expiration_time = get_current_time() + ttl

    def serialize(self):
        return self.expiration_time > get_current_time(), self.name + self.type + '0001' + \
               hex(self.expiration_time - get_current_time()).rjust(8, '0')[:2] + \
               hex(self.data_length)[:2].rjust(4, '0') + self.data


def get_current_time():
    return int(round(time.time()))
