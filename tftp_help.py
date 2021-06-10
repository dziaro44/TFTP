import socket


class OpCodes:
    RRQ = b'\x00\x01'
    WRQ = b'\x00\x02'  # unused
    DATA = b'\x00\x03'
    ACK = b'\x00\x04'
    ERROR = b'\x00\x05'
    OACK = b'\x00\x06'


class ErrorCodes:
    NOT_DEFINED = 0
    FILE_NOT_FOUND = 1
    ACCESS_VIOLATION = 2
    DISK_FULL_OR_ALLOCATION_EXCEEDED = 3
    ILLEGAL_TFTP_OPERATION = 4
    UNKNOWN_TRANSFER_ID = 5
    FILE_ALREADY_EXISTS = 6
    NO_SUCH_USER = 7
    INVALID_OPTIONS = 8


class Options:
    BLOCKSIZE = b'blksize'
    WINDOWSIZE = b'windowsize'


class BaseTFTP:
    HOST = '127.0.0.1'
    PORT = 6969
    USHRT_MAX = 65535
    MIN_BLOCK_SIZE = 8
    MAX_BLOCK_SIZE = 65464
    MIN_WINDOW_SIZE = 1
    MAX_WINDOW_SIZE = 65535
    BLOCK_SIZE = 512
    WINDOW_SIZE = 1
    TIMEOUT = 1
    MAX_TIMEOUTS = 20

    def __init__(self):
        self.client_addr = None
        self.block_size = None
        self.window_size = None
        self.first_packet = None

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.TIMEOUT)
        self.last_packet = None

    def send(self, data):
        self.last_packet = data
        self.sock.sendto(data, self.client_addr)

    def send_ERROR_and_close(self, error_code, error_message):
        error_code = error_code.to_bytes(2, byteorder='big')
        if error_message is None:
            error_message = '???'
        error_message = error_message.encode('utf-8')
        self.send(OpCodes.ERROR + error_code + error_message + b'\x00')
        self.sock.close()

    def set_options(self, options):
        accept_options = False
        for i in range(len(options)):
            if options[i] == Options.BLOCKSIZE:
                new_block_size = int(options[i + 1].decode('utf-8'))
                if self.MIN_BLOCK_SIZE <= new_block_size <= self.MAX_BLOCK_SIZE:
                    self.block_size = new_block_size
                    accept_options = True
                else:
                    self.send_ERROR_and_close(ErrorCodes.INVALID_OPTIONS, 'Invalid options, wrong block size')

            if options[i] == Options.WINDOWSIZE:
                new_window_size = int(options[i + 1].decode('utf-8'))
                if self.MIN_WINDOW_SIZE <= new_window_size <= self.MAX_WINDOW_SIZE:
                    self.window_size = new_window_size
                    accept_options = True
                else:
                    self.send_ERROR_and_close(ErrorCodes.INVALID_OPTIONS, 'Invalid options, wrong block size')
        return accept_options

    def receive_packet(self):
        if self.first_packet is not None:
            data, addr = self.first_packet
            self.first_packet = None
            return data, addr

        TOCounter = 0
        while TOCounter <= self.MAX_TIMEOUTS:
            try:
                data, addr = self.sock.recvfrom(self.USHRT_MAX+1)
                return data, addr
            except socket.timeout:
                TOCounter += 1
                if TOCounter <= self.MAX_TIMEOUTS:
                    self.send(self.last_packet)
        raise TimeoutError

    def receive_data_from_packet(self, opcodes):
        data, addr = self.receive_packet()
        if self.client_addr is None:
            self.client_addr = addr
        if addr != self.client_addr:
            self.send(OpCodes.ERROR + ErrorCodes.UNKNOWN_TRANSFER_ID.to_bytes(2, byteorder='big') + b'\x00')
        if len(data) < 4:
            self.send_ERROR_and_close(ErrorCodes.ILLEGAL_TFTP_OPERATION, 'Illegal TFTP operation, too small packet')
        if data[0:2] not in opcodes:
            self.send_ERROR_and_close(ErrorCodes.ILLEGAL_TFTP_OPERATION, 'Illegal TFTP operation, wrong opcode')

        return data[0:2], data[2:]
