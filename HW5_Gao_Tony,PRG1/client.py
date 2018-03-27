from my_socket_stuff import *
import asyncore
import argparse
import sys
import threading
import traceback

client = None
client_thread = None

'''
    Worker function running asyncore callback loop
'''
def asyncore_worker(timeout):
    try:
        asyncore.loop(timeout)
    except socket.error as e:
        print('Something happened with socket, gracefully exiting\n')
        traceback.print_exc(file=sys.stdout)
    except Exception as e:
        print('asyncore_worker(): Fatal error occurred in async loop: {}\n'.format(e))
        traceback.print_exc(file=sys.stdout)
    finally:
        client.close()

'''
    Initialize the TCP client
'''
def init_tcp_client(ipport, timeout):
    global client

    args = socket.getaddrinfo(ipport[0], int(ipport[1]), 
        family=socket.AF_INET, type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP)
    client = AsyncClientSocket(*args)

    client_thread = threading.Thread(target=asyncore_worker, kwargs={'timeout': .0025}, #timeout is asyncore polling interval
                                     daemon=True)
    client_thread.start()

'''
    Initialize the UDP client
'''
def init_udp_client(ipport, timeout):
    global client

    args = socket.getaddrinfo(ipport[0], int(ipport[1]), 
        family=socket.AF_INET, type=socket.SOCK_DGRAM,
        proto=socket.IPPROTO_UDP)
    client = AsyncClientSocket(*args)

    client_thread = threading.Thread(target=asyncore_worker, kwargs={'timeout': .0025}, #timeout is asyncore polling interval
                                     daemon=True) # start as daemon so thread is killed when client dies
    client_thread.start()

def main(mode, ipport, timeout, exponential_backoff):
    '''
        Timeout must be <= 2 if exponential_backoff is set.
    '''
    if exponential_backoff and timeout > 2.:
        raise argparse.ArgumentError("Error : cannot use exponential_backoff with timeout > 2")

    try:
        ipport = ipport.split(':')

        if mode == 'TCP':
            init_tcp_client(ipport, timeout)
        else:
            init_udp_client(ipport, timeout)

        to_send = input('Input opcode[+,-,*,/],a,b; q to quit:')

        while to_send != 'q':
            while len(to_send) == 0:
                print("Error: Length of send buffer is 0. Input 1 or more characters.")
                to_send = input('Input opcode[+,-,*,/],a,b; q to quit:')

            resp = None
            try:
                resp = client.write_wait_response(to_send.encode('ascii'), timeout, exponential_backoff)
                resp = resp.decode('ascii')
                if '300' in resp:
                    print("Server encountered error 300")

                print("Recieved response: {}".format(resp))
            except TimeoutError as e:
                print("Request timed out: {}. Server dead or connection closed unexpectedly".format(e))
            to_send = input('Input opcode[+,-,*,/],a,b; q to quit:')
    finally:
        client.close()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    required = parser.add_argument_group('required named arguments')
    required.add_argument('--mode', help='TCP/UDP', choices=['TCP', 'UDP'], 
                        dest='mode', required=True)
    parser.add_argument('--host', help='target Hostname:Port or IP:Port', 
                        dest='ipport', required=False, default="localhost:50000")
    parser.add_argument('--timeout', help='Request timeout in seconds. The asyncore callback loop will poll at a rate of .0025 seconds.', type=float,
                        dest='timeout', required=False, default=5)
    parser.add_argument('--expb', help='Exponential backoff setting. Set timeout to the appropriate value < 2', action='store_true',
                        dest='exponential_backoff', required=False, default=False)

    main(**vars(parser.parse_args(sys.argv[1::])))