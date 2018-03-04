import asyncore
import socket
from my_socket_stuff import AsyncServerSocket
import sys
import argparse
import random

VALID_CODES = [ '+', '-', '*', '/']

class TCPSocketHandler(asyncore.dispatcher_with_send):
    def _send_err(self):
        self.send("300;-1".encode("ascii"))

    '''
        Read some bytes from the TCP socket.
    '''
    def handle_read(self):
        data = self.recv(8192)
        if data:
            print("Server recieved request: {}".format(
                data.decode('ascii')))

            tokens = data.decode("ascii").strip().split(',')
            if (len(tokens) != 3):
                self._send_err()
                return
            if (tokens[0] not in VALID_CODES):
                self._send_err()
                return

            try:
                op = tokens[0]
                int(tokens[1]) # make sure tokens are ints
                int(tokens[2])

                result = eval(tokens[1] + op + tokens[2])
                print("Responding with result: {}".format(result))
                self.send(("200," + str(result)).encode('ascii'))

            except Exception as e:
                print("Server encountered an error {}".format(e))
                self._send_err()

class UDPSocketHandler(asyncore.dispatcher_with_send):
    _success = 0. # success static variable

    def _send_err(self, addr):
        self.sendto("300;-1".encode("ascii"), addr)

    '''
        Read some bytes from the UDP socket.
        Supports variable floating point success rate.
    '''
    def handle_read(self):
        data, addr = self.recvfrom(8192)
        if data:
            print("Server recieved request: {} from: {}".format(
                data.decode('ascii'), addr))

            tokens = data.decode("ascii").strip().split(',')

            # get random float between [0,1)
            failure_diceroll = random.random()

            if failure_diceroll >= UDPSocketHandler._success:
                print("You've won the lottery! Your dice rolled {}, greater than success chance {}. Discarding request.".format(
                        failure_diceroll, UDPSocketHandler._success))
                return

            if (len(tokens) != 3): # didn't recieve 3 tokens
                print("Error: Expected 3 tokens, got {}".format(len(tokens)))
                self._send_err(addr)
                return
            if (tokens[0] not in VALID_CODES): # opcode invalid
                print("Error: Invalid opcode recieved")
                self._send_err(addr)
                return

            try:
                op = tokens[0]
                int(tokens[1]) # make sure tokens are ints
                int(tokens[2])

                result = eval(tokens[1] + op + tokens[2])
                print("Responding with result: {}".format(result))
                self.sendto(("200," + str(result)).encode('ascii'), addr)

            except Exception as e:
                print("Server encountered an error {}".format(e))
                self._send_err(addr)

    def handle_write(self):
        # discard write events
        pass

    def handle_connect(self):
        # discard connect events
        pass

    def writable(self):
        # be extra sure we're not writable
        return False

    def handle_accepted(self, sock, addr):
        # connections need not be accepted
        pass


'''
    Start server with certain mode at certain ip:port with 
    success rate for simulating dropped packets.
'''
def main(mode, ipport, success, timeout):
    socket_handler = None
    ipport = ipport.strip().split(':')

    if mode == 'TCP':
        if success != 1:
            raise argparse.ArgumentTypeError('Server encountered fatal error, cannot host a TCP server with success rate.')
        args = socket.getaddrinfo(ipport[0], int(ipport[1]), 
            family=socket.AF_INET, type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP)
        socket_handler = TCPSocketHandler
    elif mode == 'UDP':
        args = socket.getaddrinfo(ipport[0], int(ipport[1]), 
            family=socket.AF_INET, type=socket.SOCK_DGRAM,
            proto=socket.IPPROTO_UDP)

        print("UDPSocketHandler with success {}".format(success))
        UDPSocketHandler._success = success
        socket_handler = UDPSocketHandler

    try:
        server_socket = AsyncServerSocket(*args, socket_handler)
        asyncore.loop(timeout=timeout / 4) # timeout = 0 means poll with 0 timeout, immediately react to callback data at cost of 100% cpu usage.

    except Exception as e:
        print(e)
        print("Error occurred in server socket")

    finally:
        if server_socket:
            server_socket.close()


if __name__ == '__main__':
    def check_success_choices(arg): # filter function for success process argument
        try:
            value = float(arg)
        except ValueError as err:
           raise argparse.ArgumentTypeError(str(err))

        if value < 0.0 or value > 1:
            message = "Expected 0.0 <= success <= 1.0, got value = {}".format(value)
            raise argparse.ArgumentTypeError(message)

        return value

    def check_timeout_choices(arg): # filter function for success process argument
        try:
            value = float(arg)
        except ValueError as err:
           raise argparse.ArgumentTypeError(str(err))

        if value < 0.0:
            message = "Expected 0.0 >= timeout, got value = {}".format(value)
            raise argparse.ArgumentTypeError(message)

        return value

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    required = parser.add_argument_group('required named arguments')
    required.add_argument('--mode', metavar='TCP/UDP', help='Host a TCP or UDP server', choices=['TCP', 'UDP'], 
                        dest='mode', required=True)
    parser.add_argument('--host', help='target Hostname:Port or IP:Port', 
                        dest='ipport', required=False, default="localhost:50000")
    parser.add_argument('--success', metavar= 'FloatRange[0,1]',help='success modifier, 1.0: 100%% success, 0.0: 0%% success. TCP does not support < 1 success modifier', type=check_success_choices,
                        dest='success', required=False, default=1.)
    parser.add_argument('--timeout', metavar= 'FloatRange[0,+inf]',help='client timeout, this will be used to set the asyncore polling loop timeout. defaults to 0. Note: with 0 timeout' + 
                        'the asyncore loop will consume a lot of CPU due to infinite loop.\n' +
                        'if timeout is set, server will poll with a timeout 2x faster than the client. ', type=check_timeout_choices,
                        dest='timeout', required=False, default=0.)

    main(**vars(parser.parse_args(sys.argv[1::])))
