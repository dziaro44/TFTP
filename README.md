# TFTP
Trivial File Transfer Protocol (TFTP) - "is a simple lockstep File Transfer Protocol which allows a client to get a file from or put a file onto a remote host."
This TFTP can only send files from server to user.

client.py - TFTP client implementation
server.py - TFTP server implementation
tftp_help.py - Utility file

protocols:
- RFC 1350, but only RRQ (server -> client)
- RFC 2347
- RFC 2348
- RFC 2349
- RFC 7440  


Run example:

$ python3 server.py --host '127.0.0.1' --port 6969 /home/TEST 
server runs on ('127.0.0.1', 6969) and can send files from folder /home/TEST

$ python3 client.py --host '127.0.0.1' --port 6969 --dir /home/user/download example.mp4
client will receive file example.mp4 from server and save it to /home/user/download

There can be multiple clients at the same time.
