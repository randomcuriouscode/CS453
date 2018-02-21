import socket
import asyncore
import threading
import time
from types import MethodType

def sendto(self, data, sa):
    try:
        result = self.socket.sendto(data,sa)
        return result
    except OSError as why:
        if why.args[0] == EWOULDBLOCK:
            return 0
        elif why.args[0] in _DISCONNECTED:
            self.handle_close()
            return 0
        else:
            raise

def recvfrom(self, buffer_size):
    try:
        data, addr = self.socket.recvfrom(buffer_size)
        if not data:
            # a closed connection is indicated by signaling
            # a read condition, and having recv() return 0.
            self.handle_close()
            return b''
        else:
            return data, addr
    except OSError as why:
        # winsock sometimes raises ENOTCONN
        if why.args[0] in _DISCONNECTED:
            self.handle_close()
            return b''
        else:
            raise

# hack sendto and recvfrom into asyncore dispatcher class
asyncore.dispatcher.sendto = sendto
asyncore.dispatcher.recvfrom = recvfrom

"""
    Implementation of simple asynchronous server socket.
"""
class AsyncServerSocket(asyncore.dispatcher):

    def __init__(self, socketargs, handler_class):
        asyncore.dispatcher.__init__(self)
        family, type, proto, canonname, sa = socketargs
        self.sa = sa
        self.handler_class = handler_class
        if type == socket.SOCK_STREAM:
            self.create_socket(family=family, type=type)
            self.bind(sa)
            self.listen(5) # allows multiple connections
            print("AsyncServerSocket:TCP Listen on {}".format(sa))
        elif type == socket.SOCK_DGRAM:
            # bind read handler to handler_class read
            self.socket = socket.socket(family, type, proto)
            self.handler_class = self.handler_class(self.socket)
            self.handle_read = self.handler_class.handle_read
            self.bind(sa) # datagram sockets do not need to listen    
            print("AsyncServerSocket:UDP socket bound to {}".format(sa))

    def handle_accepted(self, sock, addr):
        print('AsyncServerSocket:Incoming connection from %s' % repr(addr))
        handler = self.handler_class(sock)

'''
    Implementation of (somewhat) asynchronous client socket.
    Asyncore is designed for connection oriented protocols.. 
    So UDP is hacked in.
'''
class AsyncClientSocket(asyncore.dispatcher):
    def __init__(self, socketargs):
        try:
            asyncore.dispatcher.__init__(self)
            family, type, proto, canonname, sa = socketargs
            self.sa = sa
            self.create_socket(family, type)

            if type == socket.SOCK_STREAM:
                self.connect( sa )
            elif type == socket.SOCK_DGRAM:
                pass

            self.buffer = b''
            self.lock = threading.RLock()
            self.cond = threading.Condition(self.lock)
            self.readbuffer = b''
        except Exception as e:
            print("AsyncClientSocket abort: Error occurred in creating socket")
            raise e

    '''
            Write and wait for response
            Params:
                Buffer BYTE encoded data
                Timeout timeout to wait for response
            Returns: 
                response str if successful
        '''
    def write_wait_response(self, buffer, timeout=30, exponential_backoff=False): 
        if not exponential_backoff: # do a regular write
            self.buffer = buffer

            if self.waitLock(timeout):
                # condition var was signaled, we can return a response
                readbuf = bytes(self.readbuffer)
                self.readbuffer = b''
                return readbuf
            else:
                print("AsyncClientSocket: No response recieved from {} in {} seconds, dumping write and read buffer".format(
                        self.sa, timeout))
                self.buffer = b''
                raise TimeoutError("AsyncClientSocket Timed Out")
        else:
            while timeout <= 2: 
                self.buffer = buffer

                if self.waitLock(timeout):
                    # condition var was signaled, we can return a response
                    readbuf = bytes(self.readbuffer)
                    self.readbuffer = b''
                    return readbuf
                else:
                    print("AsyncClientSocket: No response recieved from {} in {} seconds, dumping write and read buffer".format(
                            self.sa, timeout))
                    self.readbuffer = b''
                    timeout *= 2
                    print("AsyncClientSocket: Retrying with timeout {}".format(timeout))
            
            raise TimeoutError("AsyncClientSocket: Exponential backoff failed, request timed out")

    '''
        Unused, flush read and write buffers.
    '''
    def flush_buffers(self):
        self.flush_write_buffer()
        self.flush_read_buffer()

    def flush_write_buffer(self):
        self.buffer = b''

    def purge_read_buffer(self):
        self.readbuffer = b''

    '''
        Wait for timeout seconds on the condition variable.
        The condition variable is signalled when the socket 
        writes bytes on the underlying input stream to the 
        read buffer.
    '''
    def waitLock(self, timeout):
        '''
            Wait for timeout seconds on CV
        '''
        try:
            self.cond.acquire()
            print("waiting")
            timeout_time = time.time() + timeout
            while len(self.readbuffer) == 0 and time.time() < timeout_time:
                self.cond.wait(timeout)
            print("Returning from condition wait, read %s bytes" % len(self.readbuffer))
            return len(self.readbuffer) != 0
        finally:
            self.cond.release()


    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    '''
        Read bytes on the socket. 
    '''
    def handle_read(self):
        try:
            self.cond.acquire()
            self.readbuffer, address = self.recvfrom(2048)
            print('handle_read(): readbuffer: {} from: {}'.format(self.readbuffer, address))
            self.cond.notify() 
        finally:
            self.cond.release()

    '''
        Returns true if contents can be written to socket
    '''
    def writable(self):
        return (len(self.buffer) > 0)

    '''
        called when writable returns True, writes buffer
        to the socket.
    '''
    def handle_write(self):
        print("AsyncClientSocket: writing {} bytes".format(len(self.buffer)))
        self.readbuffer = b''
        sent = self.sendto(self.buffer, self.sa)
        self.buffer = self.buffer[sent:]