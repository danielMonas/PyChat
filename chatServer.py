# Python Chat Server - April 2018
import socket
from threading import Thread
import struct
from time import gmtime, strftime

QUIT = "quit"
LEN_SIZE = 4
CLIENT_DICT = {}
ADMINS = ["admin"]
BLACKLISTED = []


def accept_client(server_sock):
    while True:
        client_socket, client_address = server_sock.accept()
        print("%s:%s has connected." % client_address)

        name = receive(client_socket)[1][0]
        while(name in CLIENT_DICT.keys() or name[0] == '@'):
            send(client_socket, "100")
            name = receive(client_socket)

        if name == QUIT:  # In case the client disconnected before entering a name
            disconnect_client(client_socket)
        else:
            send(client_socket, "200")
            CLIENT_DICT[name] = client_socket
            Thread(target=handle_client, args=(name,)).start()


def handle_command(name, command, data):
    admin_commands = {2: promote_user, 3: kick_user, 4: silence}
    general_commands = {0: get_help, 5: send_private_msg, 6: get_users}
    print(command)
    data.insert(1, name)
    print(data)
    if name in BLACKLISTED:
        send(CLIENT_DICT[name], format_msg("You cannot talk here!"))
    elif command in general_commands:
        general_commands[command](*data)
    elif command in admin_commands.keys() and name not in ADMINS:
        send(CLIENT_DICT[name], format_msg("You are not an admin!"))
    elif command in admin_commands.keys():
        if data[0] not in CLIENT_DICT.keys() or data[0] == name:
            send(CLIENT_DICT[name], format_msg("Error - invalid name"))
        elif data[0] in ADMINS:
            send(CLIENT_DICT[name], format_msg("Error - Target is an admin"))
        else:
            admin_commands[command](*data)
    else:
        broadcast(format_msg(*data))


def handle_client(name):
    send(CLIENT_DICT[name], format_msg("Welcome {}! To quit, type {}".format(name, QUIT)))
    broadcast(format_msg("{} joined the chat".format(name)))
    command, data = receive(CLIENT_DICT[name])
    while command != 10:
        handle_command(name, command, data)
        command, data = receive(CLIENT_DICT[name])
    broadcast(format_msg("{} left the chat".format(name)))
    disconnect_client(name)


def broadcast(msg, sender=""):
    """ Function sends a message to all active clients besides the sender"""
    print("Broadcasting to {} users: {}".format(len(CLIENT_DICT), msg))
    for client in CLIENT_DICT.keys():
            send(CLIENT_DICT[client], msg)


def promote_user(receiver, sender):
    """Admin rank function, promotes a user to an admin rank."""
    ADMINS.append(receiver)
    broadcast(format_msg("{} promoted {}!".format(sender, receiver)))


def kick_user(receiver, sender):
    """Admin rank function, enabling disconnecting other users."""
    broadcast(format_msg("{} kicked {}!".format(sender, receiver)))
    disconnect_client(receiver)


def silence(receiver, sender):
    """Admin rank function, enabling/disabling other users from sending messages"""
    if receiver in BLACKLISTED:
        BLACKLISTED.remove(receiver)
        broadcast(format_msg("{} un-muted {}!".format(sender, receiver)))
    else:
        BLACKLISTED.append(receiver)
        broadcast(format_msg("{} muted {}!".format(sender, receiver)))


def send_private_msg(receiver, sender, msg):
    """Sends a private message, visible only to the sender and receiver."""
    send(CLIENT_DICT[receiver], "<!> " + format_msg(msg, sender + " -> " + "YOU"))
    send(CLIENT_DICT[sender], "<!> " + format_msg(msg, "YOU" + " -> " + receiver))


def send(sock, msg):
    """Sends the message to the client.
        sock = client socket which the data will be sent through
        msg = a string to be sent to the client"""
    sock.send(struct.pack("!I", len(msg)))
    sock.send(bytes(msg, "utf8"))


def disconnect_client(name):
    """ Function disconnects a client and closes the active socket"""
    send(CLIENT_DICT[name], QUIT)
    CLIENT_DICT[name].close()
    del CLIENT_DICT[name]
    print("Client {} disconnected".format(name))


def format_msg(msg, name="CONSOLE"):
    """ Edits a message to be sent according the chat message format.
        msg =   a string to be formatted
        name =  message sender name. Notice the default value, which indicates the message is from
                the server itself"""
    if name in ADMINS:
        name = '@' + name
    return "[{}] [{}]: {}".format(strftime("%H:%M", gmtime()), name, msg)


def receive(sock):
    """Gathers the complete message sent by a client, using a helper function
        sock = origin socket representing the client."""
    data_len = struct.unpack("!I", sock.recv(LEN_SIZE))[0]
    code = int(sock.recv(LEN_SIZE).decode("utf8"))
    data_len -= LEN_SIZE
    data = []
    while data_len > 0:
        len = struct.unpack("!I", sock.recv(LEN_SIZE))[0]
        data.append(sock.recv(len).decode("utf8"))
        data_len -= len
    return [code, data]


def get_help(name):
    send(CLIENT_DICT[name], format_msg("List of available commands for {}:".format(name)))
    send(CLIENT_DICT[name], format_msg("--msg [username] [message] = private message another user"))
    send(CLIENT_DICT[name], format_msg("--users = view all online users"))
    if name in ADMINS:
        send(CLIENT_DICT[name], format_msg("--kick [user] = disconnect a user"))
        send(CLIENT_DICT[name], format_msg("--mute [user] = disable a user from sending texts"))
        send(CLIENT_DICT[name], format_msg("--unmute [user] = enable a muted user to send text"))
        send(CLIENT_DICT[name], format_msg("--promote_user [user] = promote a user to an Admin"))


def get_users(name):
    send(CLIENT_DICT[name], format_msg("List of users online:"))
    send(CLIENT_DICT[name], format_msg(', '.join(CLIENT_DICT.keys())))


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("localhost", 12345))
    server_sock.listen(5)
    print("Server is active ...")
    listener_thread = Thread(target=accept_client, args=(server_sock,))
    listener_thread.start()
    listener_thread.join()
    server_sock.close()


if __name__ == '__main__':
    main()
