import socket
import binascii
from note import Note, get_current_time
import pickle
from threading import Thread


E1_DNS = '195.19.220.238'
cache = dict()
cache_filename = 'cache.txt'

previous_cleaning = get_current_time()

check_time = 10

#cache[('e1.ru', '0001')] = [Note('0001', 30, '000404dd')]  # test cache


def extract_name_from_request(question, index=0):
    Q_NAME = ''
    part_len = int(question[index:2], 16)
    count = 0
    print('quest', question)
    for i in range(2, len(question[:-8]), 2):
        if int(question[i:i + 2], 16) == 0:
            break
        if count == part_len:
            part_len = int(question[i:i + 2], 16)
            count = 0
            Q_NAME += '.'
        else:
            count += 1
            char = chr(int(question[i:i + 2], 16))
            Q_NAME += f'{char}'
    return Q_NAME


def parse_request(request):
    HEADER = request[:24]
    ID = HEADER[:4]
    QUESTIONS_COUNT = HEADER[8:12]
    NS_COUNT = HEADER[16:20]
    AR_COUNT = HEADER[20:24]

    QUESTION = request[24:]

    Q_NAME = extract_name_from_request(QUESTION)
    Q_TYPE = QUESTION[-8:-4]

    print(Q_NAME, Q_TYPE)
    print(cache)
    if (Q_NAME, Q_TYPE) in cache:
        print('Using cache...')
        res = []
        for note in cache[(Q_NAME, Q_TYPE)]:
            is_valid, data = note.serialize()
            if is_valid:
                res.append(data)

        if len(res) > 0:
            answers_count = hex(len(res))[2:].rjust(4, '0')
            header = ID + '8180' + QUESTIONS_COUNT + answers_count + NS_COUNT + AR_COUNT
            return header + QUESTION + "".join(res)

    return parse_response(send_message(request, E1_DNS, 53))


def parse_response(response):
    #print('resp  ', response)
    HEADER = response[0:24]
    QUESTION = response[24:]
    ANSWERS_COUNT = int(HEADER[12:16], 16)
    NS_COUNT = int(HEADER[16:20], 16)
    AR_COUNT = int(HEADER[20:24], 16)

    name, offset = extract_name_from_response(QUESTION)

    Q_TYPE = response[offset - 8:offset - 4]
    answer = response[offset:]

    counts = [ANSWERS_COUNT, NS_COUNT, AR_COUNT]

    rest = answer

    for count in counts:
        answers = []
        previous_name = name

        ans_name = ''
        ans_type = ''
        for i in range(count):
            #ans_name = extract_name_from_request(rest)
            #print('ans name', ans_name)
            ans_type = rest[4:8]
            ttl = int(rest[12:20], 16)
            ans_data_len = int(rest[20:24], 16) * 2
            ans_data = rest[24: 24 + ans_data_len]

            note = Note(ans_type, ttl, ans_data)

            rest = rest[24 + ans_data_len:]
            if name != previous_name:
                cache[(name, ans_type)] = [note]
                answers = []
            else:
                answers.append(note)

            previous_name = name

        if len(answers) > 0:
            cache[(name, ans_type)] = answers

    with open(cache_filename, 'wb+') as file:
        pickle.dump(cache, file)

    return response


def extract_name_from_response(question, index=24):
    offset = index + 2  # заголовок + длина первой секции
    name = ''
    part_len = int(question[:2], 16)
    count = 0
    for i in range(2, len(question[:-8]), 2):
        if int(question[i:i + 2], 16) == 0:
            offset += 2
            break
        if count == part_len:
            part_len = int(question[i:i + 2], 16)
            count = 0
            name += '.'
        else:
            count += 1
            char = chr(int(question[i:i + 2], 16))
            name += f'{char}'
        offset += 2
    return name, offset + 8


def send_message(message, ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(binascii.unhexlify(message), (ip, port))
    return binascii.hexlify(s.recvfrom(2048)[0]).decode('utf-8')


def clean_cache():
    global previous_cleaning
    while True:
        curr_time = get_current_time()
        if curr_time - previous_cleaning > check_time:
            notes_to_delete = []
            for k, v in cache.items():
                for item in v:
                    if item.expiration_time <= curr_time:
                        del item
                        print("TIME IS UP")
                if len(v) == 0:
                    notes_to_delete.append(k)
                print("CLEAN")
            for note in notes_to_delete:
                del cache[note]
            previous_cleaning = get_current_time()

            with open(cache_filename, 'wb+') as file:
                pickle.dump(cache, file)


def main():
    IP = '127.0.0.1'
    PORT = 53
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((IP, PORT))

    try:
        with open(cache_filename, 'rb') as file:
            cache = pickle.load(file)
    except:
        pass

    while True:
        data, addr = sock.recvfrom(2048)
        print(addr)
        data = binascii.hexlify(data).decode('UTF-8')
        response = parse_request(data)
        print('resp ', response)
        sock.sendto(binascii.unhexlify(response), addr)


if __name__ == '__main__':
    try:
        Thread(target=clean_cache).start()
        Thread(target=main).start()
    except KeyboardInterrupt:
        with open(cache_filename, 'wb+') as file:
            pickle.dump(cache, file)
