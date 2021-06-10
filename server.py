#!/usr/bin/env python3
import argparse
import socket
import errno
from threading import Thread
from tftp_help import OpCodes, ErrorCodes, BaseTFTP

HOST =              BaseTFTP.HOST
PORT =              BaseTFTP.PORT
USHRT_MAX =         BaseTFTP.USHRT_MAX
MIN_BLOCK_SIZE =    BaseTFTP.MIN_BLOCK_SIZE
MAX_BLOCK_SIZE =    BaseTFTP.MAX_BLOCK_SIZE
MIN_WINDOW_SIZE =   BaseTFTP.MIN_WINDOW_SIZE
MAX_WINDOW_SIZE =   BaseTFTP.MAX_WINDOW_SIZE
BLOCK_SIZE =        BaseTFTP.BLOCK_SIZE
WINDOW_SIZE =       BaseTFTP.WINDOW_SIZE
TIMEOUT =           BaseTFTP.TIMEOUT
MAX_TIMEOUTS =      BaseTFTP.MAX_TIMEOUTS

parser = argparse.ArgumentParser()
parser.add_argument('--host', default=HOST)
parser.add_argument('--port', default=PORT)
parser.add_argument('dir')
# python3 server.py /home/dziaro44/TFTP_test
args = parser.parse_args()

BASE_DIR = args.dir


class Server(BaseTFTP):
    def __init__(self, host, first_packet):
        super().__init__()
        self.client_addr = first_packet[1]
        self.block_size = BLOCK_SIZE
        self.window_size = WINDOW_SIZE
        self.first_packet = first_packet
        self.sock.bind((host, 0))

    def send_part_of_file(self, file, current_id):
        data = file.read(self.block_size)
        self.send(OpCodes.DATA + current_id.to_bytes(2, byteorder='big') + data)
        return len(data) == self.block_size

    def send_file(self, file):
        block_id = 1
        last = 0

        while True:
            TOCounter = 0
            while TOCounter <= MAX_TIMEOUTS:
                try:
                    end = True

                    for i in range(self.window_size):
                        end = not self.send_part_of_file(file, (block_id + i) % (USHRT_MAX+1))
                        last = (block_id + i) % (USHRT_MAX)
                        if end:
                            break

                    ack_id = self.receive_ACK()
                    if (block_id <= ack_id <= last) or (last < block_id <= ack_id <= USHRT_MAX) or (ack_id <= last < block_id):
                        block_id = (ack_id + 1) % (USHRT_MAX+1)

                    if end and last == ack_id:
                        return
                    break

                except socket.timeout:
                    TOCounter += 1
            else:
                raise TimeoutError

    def receive_ACK(self):
        opcode, data = self.receive_data_from_packet(OpCodes.ACK)
        # opcode = OpCodes.ACK
        return int.from_bytes(data, byteorder='big')

    def receive_RRQ(self):
        opcode, data = self.receive_data_from_packet(OpCodes.RRQ)
        # opcode == OpCodes.RRQ
        file_name, mode, *options = data.split(b'\0')
        if self.set_options(options):
            self.send(OpCodes.OACK + data[len(file_name) + len(mode) + 2:])
            self.receive_ACK()
        file_name = file_name.decode('utf-8')
        mode = mode.decode('utf-8')
        if mode != 'octet':
            self.send_ERROR_and_close(ErrorCodes.ILLEGAL_TFTP_OPERATION, 'Illegal TFTP operation, rrq must have octet mode')
        return file_name, mode

    def errno_value(self, e):
        if e.errno == errno.ENOENT:
            error_code = ErrorCodes.FILE_NOT_FOUND
            error_message = 'File not found'
        elif e.errno == errno.EPERM or e.errno == errno.EACCES:
            error_code = ErrorCodes.ACCESS_VIOLATION
            error_message = 'Access violation'
        elif e.errno == errno.EFBIG or e.errno == errno.ENOSPC:
            error_code = ErrorCodes.DISK_FULL_OR_ALLOCATION_EXCEEDED
            error_message = 'Disk full or allocation exceeded'
        else:
            error_code = ErrorCodes.NOT_DEFINED
            error_message = e.strerror
        self.send_ERROR_and_close(error_code, error_message)

    def new_client(self):
        file_name, mode = self.receive_RRQ()
        try:
            path_to_file = BASE_DIR + '/' + file_name
            file = open(path_to_file, 'rb')
            self.send_file(file)
        except OSError as exc:
            self.errno_value(exc)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print('Server is working on', (args.host, args.port))
sock.bind((args.host, args.port))
while True:
    data = sock.recvfrom(USHRT_MAX+1)
    Thread(target=Server(args.host, data).new_client).start()
