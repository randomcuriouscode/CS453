This is an implementation of an asynchronous socket
client and server.

Dependency: Python 3.5.2

Tested on: Mac OS X High Sierra

Supported protocols: TCP and UDP 

General Documentation:

- help can be accessed using the '-h' flag on each executable
- both TCP and UDP support exponential backoff.
	- if exp backoff is used, timeout must be less than 2
- the underlying sockets are closed automatically on process
  termination
- see writeup.pdf for the full documentation of the design and
  implementation
- client-server-uml.xml can be opened in draw.io

TCP Documentation:

- Since TCP is connection oriented, the server must be alive
  before the client is started. No robust reconnection has
  been implemented in this version.

1. Run server with the following (configurable) parameters
	python server.py --mode TCP --host localhost:50000
2. Run client with the following (configurable) parameters
	python client.py --mode TCP --timeout 15 --host localhost:50000

UDP Documentation:

- Since UDP is connectionless, either the server or client
  may be started first.
- A --success flag of 1.0 indicates 100% acceptance rate of
  incoming UDP packets

1. Run server with the following (configurable) parameters
	python server.py --mode UDP --host localhost:50000 --success 1
2. Run client with the following (configurable) parameters
	python client.py --mode UDP --timeout .1 --expb

	--expb does not necessarily need to be set. If it is not
	set, the client will timeout after 1 failed attempt to receive
	a response from the server.

	if --expb is set, timeout must be less than 2 as previouly
	stated