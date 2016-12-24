import discord
import asyncio
import struct
import ast
import urllib.parse

host = "localhost"
port = 45678
gameport = 61926
token = "MjYxNDI2NDM1OTcxODc0ODE2.Cz4GvQ.nEJwFbd61MzZ_HXXldhAJgOyeiE"
ahelpID = "260863607661658112"
mainID = "260863628582977547"

loop = asyncio.get_event_loop()
queue = asyncio.Queue(loop=loop)

class Aphrodite(discord.Client):
    
    @asyncio.coroutine
    def on_message(self, message):
    
        author = message.author
        if message.content.startswith("!q"):
            yield from self.send_message(message.channel, "See ya, %s!" % author)
            yield from self.logout()
            loop.stop()
            
        elif message.content.startswith("!status"):
            response = yield from handle_outgoing("status", loop)
            yield from self.send_message(message.channel, response)
            
            
        elif message.content.startswith("!manifest"):
            response = yield from handle_outgoing("manifest", loop)
            yield from self.send_message(message.channel, response)
            
ourBot = Aphrodite()

def admin_message(message):
    if message.startswith("Request for Help") or message.startswith("Reply") or message.endswith("no more admins online."):
        return True

def format_packet(msg):
    return b"\x00\x83" + struct.pack(">H", len(msg) + 6) + \
    b"\x00\x00\x00\x00\x00" + bytes(msg, "ascii") + b"\x00"
    
@asyncio.coroutine
def handle_outgoing(payload, loop):

    
    reader, writer = yield from asyncio.open_connection(host, gameport, loop=loop)
    packet = format_packet(payload)
    
    writer.write(packet)
    
    headerReceived = yield from reader.read(2)
    if headerReceived != b"\x00\x83":
        print("Unexpected packet.")
        
    packetLength = yield from reader.read(2)
    packetLength = int.from_bytes(packetLength, "big")
    received = yield from reader.read(packetLength)
    received = received[1:-1]
    
    writer.close()
    return received
    

@asyncio.coroutine
def handle_incoming(reader, writer):

    data = yield from reader.read(-1)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    cleanMessage = " ".join(ast.literal_eval(message))

    loop.create_task(queue.put(cleanMessage))
    
    writer.write(data)
    yield from writer.drain()
    
@asyncio.coroutine
def handle_queue():
    
    queuedMsg = yield from queue.get()
    loop.create_task(handle_queue())
    if admin_message(queuedMsg):
        yield from ourBot.send_message(ourBot.get_channel(ahelpID), queuedMsg)
    else:
        yield from ourBot.send_message(ourBot.get_channel(mainID), queuedMsg)
    
def main():
 
    serverCoro = asyncio.start_server(handle_incoming, host, port, loop=loop)
    server = loop.run_until_complete(serverCoro)
    
    try:
        loop.create_task(ourBot.start(token))
        loop.create_task(handle_queue())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    
if __name__ == "__main__":
    main()