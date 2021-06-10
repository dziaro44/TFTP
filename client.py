#!/usr/bin/env python3
import argparse
import socket
from tftp_help import OpCodes, Options, BaseTFTP

HOST =              BaseTFTP.HOST
PORT =              BaseTFTP.PORT
USHRT_MAX =         BaseTFTP.USHRT_MAX
BLOCK_SIZE =        BaseTFTP.BLOCK_SIZE
WINDOW_SIZE =       BaseTFTP.WINDOW_SIZE
TIMEOUT =           BaseTFTP.TIMEOUT
MAX_TIMEOUTS =      BaseTFTP.MAX_TIMEOUTS
DEFAULT_DIR = '/home/dziaro44/Pulpit/Sieci Komputerowe/TFTP/test'

parser = argparse.ArgumentParser()
parser.add_argument('--host', default=HOST)
parser.add_argument('--port', default=PORT)
parser.add_argument('--block-size', default=BLOCK_SIZE)
parser.add_argument('--window-size', default=WINDOW_SIZE)
parser.add_argument('--dir', default=DEFAULT_DIR)
parser.add_argument('file')
args = parser.parse_args()

# python3 client.py 1 & python3 client.py 2 & python3 client.py 3 & python3 client.py 4 & python3 client.py 5 &

BASE_DIR = args.dir


class Client(BaseTFTP):
    def __init__(self, host, port, block_size, window_size):
        super().__init__()
        self.server_addr = (host, port)
        self.client_addr = None
        self.block_size = block_size
        self.window_size = window_size
        self.first_packet = None

    def get_file(self, file_name):
        options = b''
        if self.block_size != BLOCK_SIZE:
            options += Options.BLOCKSIZE
            options += b'\x00'
            options += bytes(str(self.block_size), 'utf-8')
            options += b'\x00'
        if self.window_size != WINDOW_SIZE:
            options += Options.WINDOWSIZE
            options += b'\x00'
            options += bytes(str(self.window_size), 'utf-8')
            options += b'\x00'

        self.sock.sendto(OpCodes.RRQ + bytes(file_name, 'utf-8') + b'\x00' + bytes('octet', 'utf-8') + b'\x00' + options, self.server_addr)

        opcode, data = self.receive_data_from_packet([OpCodes.OACK, OpCodes.DATA])
        if opcode == OpCodes.DATA:
            self.first_packet = (opcode + data, self.client_addr)
        else:
            options = data.split(b'\0')
            self.set_options(options)
            self.send(OpCodes.ACK + b'\x00\x00')

        last = 0
        last_to_send = 0
        file = open(path_to_file, 'wb')
        TOCounter = 0

        while TOCounter <= MAX_TIMEOUTS:
            for i in range(self.window_size):
                try:
                    opcode, data = self.receive_data_from_packet(OpCodes.DATA)
                    # opcode == OpCodes.DATA
                    block_id = int.from_bytes(data[0:2], byteorder='big')
                    data = data[2:]

                    if last == block_id - 1:
                        file.write(data)
                        last_to_send = last = block_id
                        if block_id == USHRT_MAX:
                            last = -1
                        if len(data) < self.block_size:
                            self.send(OpCodes.ACK + last_to_send.to_bytes(2, byteorder='big'))
                            return
                except socket.timeout:
                    TOCounter += 1
                    break
                TOCounter = 0

            if TOCounter <= MAX_TIMEOUTS:
                self.send(OpCodes.ACK + last_to_send.to_bytes(2, byteorder='big'))

        raise TimeoutError


client = Client(args.host, args.port, args.block_size, args.window_size)
path_to_file = BASE_DIR + '/' + args.file
client.get_file(args.file)
