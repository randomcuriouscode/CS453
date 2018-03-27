# Python Asynchronous Client Server Application

This is an implementation of an asynchronous socket
client and server.

Dependency: Python 3.5.2

Tested on: Mac OS X High Sierra

Supported protocols: TCP and UDP 

## General Documentation:

- help can be accessed using the '-h' flag on each executable
- both TCP and UDP support exponential backoff.
	- if exp backoff is used, timeout must be less than 2. 
	  the timeout parameter is used as the STARTING value for 
	  exponential backoff following timeout *= 2 per failed 
	  request
- the underlying sockets are closed automatically on process
  termination
- see writeup.pdf for the full documentation of the design and
  implementation
- client-server-uml.xml can be opened in draw.io

- it is highly reccommended to set the server.py --timeout parameter to 
	the minimum client timeout. this is to avoid an infinite asyncore polling loop
	with 0 block time, and thus indefinite CPU time used. this parameter has nothing
	to do with the TCP/UDP request timeout behavior, however a server polling timeout
	that is too long may cause requests to be overwritten in the read buffer, 
	because there is one global read buffer on the server side. This parameter 
	controls the time interval that dictates when the server will 
	poll the underlying socket for bytes and thus the time interval that will
	elapse between each read/write of the read buffer.

- the client REQUEST timeout is configurable using the --timeout parameter.
- the client ASYNC EVENT LOOP timeout is hardcoded to .0025 seconds. This means the request timeout
must be greater than .05 seconds for proper function of the client.

## TCP Documentation:

- Since TCP is connection oriented, the server must be alive
  before the client is started. No robust reconnection has
  been implemented in this version.

1. Run server with the following (configurable) parameters
	python server.py --mode TCP --host localhost:50000 --timeout .1
2. Run client with the following (configurable) parameters
	python client.py --mode TCP --timeout 15 --host localhost:50000

## UDP Documentation:

- Since UDP is connectionless, either the server or client
  may be started first.
- A --success flag of 1.0 indicates 100% acceptance rate of
  incoming UDP packets

1. Run server with the following (configurable) parameters
	python server.py --mode UDP --host localhost:50000 --success 1 --timeout .1
2. Run client with the following (configurable) parameters
	python client.py --mode UDP --timeout .1 --expb

	--expb does not necessarily need to be set. If it is not
	set, the client will timeout after 1 failed attempt to receive
	a response from the server.

	if --expb is set, timeout must be less than 2 as previouly
	stated.