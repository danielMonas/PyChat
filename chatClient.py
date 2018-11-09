# Python Chat Client - April 2018
import socket
from threading import Thread
import struct
import wx

QUIT = "quit"
MSG_LEN_SIZE = 4
# Connecting to server
CLIENT_SOC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CLIENT_SOC.connect(("localhost", 12345))


def handleClientInput(msg):
    """Function checks what command the client chose. If no command was chosen,
        The default option is command 01 - send a public message"""
    commands = {"--help": 0, "--promote": 2, "--kick": 3, "--mute": 4,
                "--unmute": 4, "--msg": 5, "--users": 6, QUIT: 10}
    command = 1
    data = [msg]
    if msg.split(' ', 1)[0] in commands.keys():
        command = commands[msg.split(' ', 1)[0]]
        if command == commands["--msg"]:
            data = [msg.split(' ', 2)[1], msg.split(' ', 2)[2]]
        elif msg.split(' ', 1)[0] in ["--help", "--users", QUIT]:
            data = ""
        else:
            data = [msg.split(' ', 1)[1]]
    send(command, data)


def receive():
    try:
        msg_len = CLIENT_SOC.recv(MSG_LEN_SIZE)
        msg = CLIENT_SOC.recv(struct.unpack("!I", msg_len)[0]).decode("utf8")
    except socket.error:
        msg = QUIT
    if msg == QUIT:
        CLIENT_SOC.close()
    return msg


def send(command, data=[]):
    CLIENT_SOC.send(struct.pack("!I", sum(len(d) for d in data) + MSG_LEN_SIZE))
    CLIENT_SOC.send(bytes(str(command).rjust(MSG_LEN_SIZE, '0'), "utf8"))
    for msg in data:
        CLIENT_SOC.send(struct.pack("!I", len(msg)))
        CLIENT_SOC.send(bytes(msg, "utf8"))


class GraphicInterface(wx.Frame):
    def __init__(self, *args, **kw):
        super(GraphicInterface, self).__init__(*args, **kw)
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.msgDisplay = wx.ListBox(panel)
        vbox.Add(self.msgDisplay, 1,  wx.ALL | wx.EXPAND |
                 wx.ALIGN_CENTER_HORIZONTAL, 20)
        self.txtDisplay = wx.TextCtrl(panel, value="Enter text", style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.GetMessage, id=self.txtDisplay.GetId())
        self.Bind(wx.EVT_CLOSE, self.exit)
        vbox.Add(self.txtDisplay, 0, wx.EXPAND, 10)
        panel.SetSizer(vbox)
        self.login()
        Thread(target=self.listener).start()

    def login(self):
        name = wx.GetTextFromUser('Enter username:', 'Login')
        send("100", [name])
        while(int(receive()) != 200):
            name = wx.GetTextFromUser('Please choose a different username', 'Login')
            send("100", [name])

    def GetMessage(self, event):
        "Getting user dialog from button to be sent"
        text = self.txtDisplay.GetLineText(0)
        if text != '':
            self.txtDisplay.Clear()
            handleClientInput(text)

    def listener(self):
        """ Listener, updating the message list"""
        msg = receive()
        while msg != QUIT:
            self.msgDisplay.Append(msg)
            msg = receive()
        self.Destroy()

    def exit(self, event):
        send("10".rjust(MSG_LEN_SIZE, '0'))
        if(receive() == QUIT):
            self.Destroy()


def main():
    # Starting up GUI
    app = wx.App()
    ex = GraphicInterface(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
