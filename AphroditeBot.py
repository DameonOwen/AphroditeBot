import discord
import asyncio
import BotCommands
import config
import ast

loop = asyncio.get_event_loop()
queue = asyncio.Queue(loop=loop)

@asyncio.coroutine
def parse_command(message, client, loop):

    command = BotCommands.get_command(message)

    if message.content.startswith(config.triggerString) == False:
        return BotCommands.Command(client, loop, message)

    if command[0] == "ping":
        return BotCommands.Ping(client, loop, message)
    elif command[0] == "status":
        return BotCommands.Status(client, loop, message)
    elif command[0] == "players":
        return BotCommands.Players(client, loop, message)
    elif command[0] == "manifest":
        return BotCommands.Manifest(client, loop, message)
    elif command[0] == "revision":
        return BotCommands.Revision(client, loop, message)
    elif command[0] == "info":
        if BotCommands.has_perms(message.author) == True:
            return BotCommands.Info(client, loop, message)
        else:
            return BotCommands.Command(client, loop, message)
    elif command[0] == "msg":
        if BotCommands.has_perms(message.author):
            return BotCommands.AdminMsg(client, loop, message)
        else:
            return BotCommands.Command(client, loop, message)
    elif command[0] == "notes":
        if BotCommands.has_perms(message.author):
            return BotCommands.Notes(client, loop, message)
        else:
            return BotCommands.Command(client, loop, message)
    elif command[0] == "age":
        if BotCommands.has_perms(message.author):
            return BotCommands.Age(client, loop, message)
        else:
            return BotCommands.Command(client, loop, message)
    elif command[0] == "ip":
        if BotCommands.has_perms(message.author):
            return BotCommands.IP(client, loop, message)
        else:
            return BotCommands.Command(client, loop, message)
    elif command[0] == "help":
        return BotCommands.Help(client, loop, message)
    else:
        return BotCommands.Command(client, loop, message)

class Aphrodite(discord.Client):

    @asyncio.coroutine
    def on_ready(self):
        print("Bot is ready.")

    @asyncio.coroutine
    def on_message(self, message):

        author = message.author

        if author.id == self.user.id:
            return

        cmd = yield from parse_command(message, self, loop)
        yield from cmd.do_command()

ourBot = Aphrodite()

def admin_message(message):

    if "@here" in message:
        message = message.strip("@here ")
    if "@everyone" in message:
        message = message.strip("@everyone ")
    if message.startswith("Request for Help") \
        or message.startswith("Reply") \
        or message.startswith("ADMIN") \
        or message.startswith("URGENT") \
        or message.endswith("no more admins online.") \
        or message.partition("PM")[1] == "PM" \
        or message == "Round has started with no admins online." \
        or message.startswith("Adminhelp") \
		or message.startswith("Mentorhelp") \
		or message.endswith("inactive staff."):
        return True

def general_message(message):

    if "@here" in message:
        message = message.strip("@here ")
    if "@everyone" in message:
        message = message.strip("@everyone ")
    if message.startswith("RADIO - "):
        message = message.strip("RADIO - ")
        return True

def command_message(message):

    if "@here" in message:
        message = message.strip("@here ")
    if "@everyone" in message:
        message = message.strip("@everyone ")
    if message.startswith("ANNOUNCEMENT - "):
        return True
		
@asyncio.coroutine
def handle_incoming(reader, writer):
    data = yield from reader.read(-1)
    message = data.decode()
    print("Message Recieved:  "+"'"+message+"'\n\n")
    cleanMessage = " ".join(ast.literal_eval(message))

    loop.create_task(queue.put(cleanMessage))
    if  "Round has started with no admins online." in queuedMsg \
        or queuedMsg.endswith("no more admins online.") \
        or "All admins AFK" in queuedMsg:
        queuedMsg = "URGENT " + queuedMsg

@asyncio.coroutine
def handle_queue():

    queuedMsg = yield from queue.get()
    loop.create_task(handle_queue())
    queuedMsg = queuedMsg.strip("'")
    if admin_message(queuedMsg):
        if "help" in queuedMsg:
            queuedMsg = "@here " + queuedMsg
        elif "has requested additional admins" in queuedMsg:
            queuedMsg = "@here " + queuedMsg
        yield from ourBot.send_message(ourBot.get_channel(config.ahelpID), queuedMsg)
        print("'"+queuedMsg+"'" +" sent to ahelp channel\n\n")

    elif command_message(queuedMsg):
        queuedMsg = queuedMsg.replace("@", "(at)")
        queuedMsg = queuedMsg.strip("ANNOUNCEMENT - ")
        cmdMsg = queuedMsg.split("\n")
        yield from ourBot.send_message(ourBot.get_channel(config.commandID), cmdMsg[0])
        yield from ourBot.send_message(ourBot.get_channel(config.commandID), cmdMsg[1])
        print("'"+header+"'"+"\n'"+contents+"'\n"+" sent to command channel\n\n")

    elif general_message(queuedMsg):
        yield from ourBot.send_message(ourBot.get_channel(config.generalID), queuedMsg)
        print("'"+queuedMsg+"'" +" sent to general channel\n\n")

    else:
        yield from ourBot.send_message(ourBot.get_channel(config.mainID), queuedMsg)
        print("'"+queuedMsg+"'" +" sent to main channel\n\n")

def main():

    serverCoro = asyncio.start_server(handle_incoming, config.host, config.port, loop=loop)
    server = loop.run_until_complete(serverCoro)

    try:
        loop.create_task(ourBot.start(config.token))
        loop.create_task(handle_queue())
        loop.run_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()