from gevent.server import StreamServer
from adbk_struct import SPacket

HOST = '0.0.0.0',1024

def handle(socket, address):
 packet = SPacket.recv(socket)
 #print packet
 answer_packet = SPacket(answer = packet.command.handle())
 #print answer_packet
 answer_packet.send(socket)

def run():
 server = StreamServer(HOST, handle)
 print 'ADBK Serving on {0}:{1}...'.format(*HOST)
 server.serve_forever()