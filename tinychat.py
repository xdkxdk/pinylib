# -*- coding: utf-8 -*-
import time
import thread
import random
import traceback
from colorama import init, Fore, Style
from api import web_request, tinychat_api
from files import file_handler as fh
from rtmp import rtmp_protocol

# TODO: Error handling.

#  Basic settings.
SETTINGS = {
    'log': True,
    'debug_mode': True,
    'log_path': 'files/logs/'
}

#  Console colors.
COLOR = {
    'white': Fore.WHITE,
    'green': Fore.GREEN,
    'bright_green': Style.BRIGHT + Fore.GREEN,
    'yellow': Fore.YELLOW,
    'bright_yellow': Style.BRIGHT + Fore.YELLOW,
    'cyan': Fore.CYAN,
    'bright_cyan': Style.BRIGHT + Fore.CYAN,
    'red': Fore.RED,
    'bright_red': Style.BRIGHT + Fore.RED,
    'magenta': Fore.MAGENTA,
    'bright_magenta': Style.BRIGHT + Fore.MAGENTA
}

init(autoreset=True)


def create_random_string(min_length, max_length, upper=False):
    """
    Creates a random string of letters and numbers.
    :param min_length: int the minimum length of the string
    :param max_length: int the maximum length of the string
    :param upper: bool do we need upper letters
    :return: random str of letters and numbers
    """
    randlength = random.randint(min_length, max_length)
    junk = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if upper:
        junk += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join((random.choice(junk) for i in xrange(randlength)))


def console_write(info_list):
    """
    Writes to console.
    :param info_list: list of info.
    : info_list[0] = The console color.
    : info_list[1] = The message to write.
    : info_list[2] = The room name.
    """
    ts = time.strftime('%H:%M:%S')
    info = COLOR['white'] + '[' + ts + ']' + Style.RESET_ALL + ' ' + info_list[0] + info_list[1]
    try:
        # Colorama doesn't handle none english characters very well..
        print(info)
    except UnicodeEncodeError:
        pass

    #  Is logging enabled?
    if SETTINGS['log']:
        to_log = '[' + ts + '] ' + info_list[1]
        #  Pass the message and room name to write_to_log().
        write_to_log(to_log, info_list[2])


def write_to_log(msg, room_name):
    """
    Writes to log.
    The room name is used to construct a log file name from.
    :param msg: str the message to write to the log.
    :param room_name: str the room name.
    """
    d = time.strftime('%Y-%m-%d')
    file_name = d + '_' + room_name + '.log'
    fh.file_writer(SETTINGS['log_path'], file_name, msg.encode('ascii', 'ignore'))


def random_color():
    """
    Get a random tinychat color.
    :return: str random color
    """
    colors = ['#000000', '#7db257', '#a78901', '#9d5bb5', '#5c1a7a', '#c53332', '#821615', '#a08f23',
              '#487d21', '#c356a3', '#1d82eb', '#919104', '#b9807f', '#7bb224', '#1965b6', '#32a5d9']
    return random.choice(colors)


class RoomUser:
    """
    A object to hold info about a user.
    Each user will have a object associated with there username.
    The object is used to store information about the user.
    """
    def __init__(self, nick, uid=None, last_msg=None):
        self.nick = nick
        self.id = uid
        self.last_msg = last_msg
        self.is_owner = False
        self.is_mod = False
        self.has_power = False
        self.user_account = None
        self.tinychat_id = None
        self.last_login = None


class TinychatRTMPClient:
    """ Manages a single room connection to a given room. """
    def __init__(self, room, tcurl=None, app=None, room_type=None, nick=None, account=None,
                 password=None, room_pass=None, ip=None, port=None, proxy=None):
        self.roomname = room
        self.tc_url = tcurl
        self.app = app
        self.roomtype = room_type
        self.client_nick = nick
        self.account = account
        self.password = password
        self.room_pass = room_pass
        self.ip = ip
        self.port = port
        self.proxy = proxy
        self.greenroom = False
        self.prefix = u'tinychat'
        self.swf_url = u'http://tinychat.com/embed/Tinychat-11.1-1.0.0.0650.swf?version=1.0.0.0650/[[DYNAMIC]]/8'
        self.desktop_version = u'Desktop 1.0.0.0650'
        self.embed_url = u'http://tinychat.com/' + self.roomname
        self.client_id = None
        self.is_connected = False
        self.is_client_mod = False
        self.room_users = {}
        self.is_reconnected = False
        self.uptime = 0

    def prepare_connect(self):
        """ Gather necessary connection parameters before attempting to connect. """
        if self.account and self.password:
            web_request.delete_login_cookies()
            if len(self.account) > 3:
                login = web_request.post_login(self.account, self.password)
                if 'pass' in login['cookies']:
                    console_write([COLOR['green'], 'Logged in as: ' + login['cookies']['user'], self.roomname])
                else:
                    console_write([COLOR['red'], 'Log in Failed', self.roomname])
                    self.account = raw_input('Enter account: (optional)')
                    if self.account:
                        self.password = raw_input('Enter password: ')
                    self.prepare_connect()
            else:
                console_write([COLOR['red'], 'Account name is to short.', self.roomname])
                self.account = raw_input('Enter account: ')
                self.password = raw_input('Enter password: ')
                self.prepare_connect()

        console_write([COLOR['white'], 'Parsing room config xml...', self.roomname])
        config = tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
        while config == 'PW':
            self.room_pass = raw_input('The room is password protected. Enter room password: ')
            if not self.room_pass:
                self.roomname = raw_input('Enter room name: ')
                self.room_pass = raw_input('Enter room pass: (optional)')
                self.account = raw_input('Enter account: (optional)')
                self.password = raw_input('Enter password: (optional)')
                self.prepare_connect()
            else:
                config = tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
                if config != 'PW':
                    break
                else:
                    console_write([COLOR['red'], 'Password Failed.', self.roomname])

        self.ip = config['ip']
        self.port = config['port']
        self.tc_url = config['tcurl']
        self.app = config['app']
        self.roomtype = config['roomtype']
        self.greenroom = config['greenroom']

        console_write([COLOR['white'],
                       'TC Url: ' + self.tc_url + '\n' +
                       'Application: ' + self.app + '\n' +
                       'Room type: ' + self.roomtype + '\n' +
                       'Greenroom: ' + str(self.greenroom) + '\n\n' +
                       '============ CONNECTING ============\n', self.roomname])
        self.connect()

    def connect(self):
        """ Attempts to make a RTMP connection with the given connection parameters. """
        if not self.is_connected:
            try:
                tinychat_api.recaptcha(proxy=self.proxy)
                cauth_cookie = tinychat_api.get_cauth_cookie(self.roomname, proxy=self.proxy)
                # if self.greenroom:
                #    self.prefix = u'greenroom'
                self.connection = rtmp_protocol.RtmpClient(self.ip, self.port, self.tc_url, self.embed_url,
                                                           self.swf_url, self.app, self.roomtype, self.prefix,
                                                           self.roomname, self.desktop_version, cauth_cookie,
                                                           self.account, self.proxy)
                self.connection.connect([])
                self.is_connected = True
                self.callback()
            except Exception as e:
                self.is_connected = False
                if SETTINGS['debug_mode']:
                    traceback.print_exc()

    def disconnect(self):
        """ Closes the RTMP connection with the remote server. """
        if self.is_connected:
            try:
                self.is_connected = False
                self.is_client_mod = False
                self.room_users.clear()
                self.uptime = 0
                self.connection.shutdown()
            except Exception as e:
                if SETTINGS['debug_mode']:
                    traceback.print_exc()

    def reconnect(self):
        """ Reconnect to a room with the connection parameters already set. """
        console_write([COLOR['bright_cyan'], '============ RECONNECTING IN 15 SECONDS ============', self.roomname])
        self.is_reconnected = True
        self.disconnect()
        time.sleep(15)
        if self.account and self.password:
            self.prepare_connect()
        else:
            self.connect()

    def callback(self):
        """ Callback loop that reads from the RTMP stream. """
        failures = 0
        t = time.time()
        while self.is_connected:
            self.uptime = time.time() - t
            try:
                amf0_data = self.connection.reader.next()
                # amf0_data_format = self.amf0_data['msg']
            except:
                failures += 1
                if failures == 3:
                    self.reconnect()
                    break
            else:
                failures = 0
            try:
                amf0_cmd = amf0_data['command']
                cmd = amf0_cmd[0]
                iparam0 = 0

                if cmd == '_result':
                    print(amf0_data)

                elif cmd == '_error':
                    print(amf0_data)

                elif cmd == 'onBWDone':
                    self.on_bwdone()

                elif cmd == 'onStatus':
                    self.on_status()

                elif cmd == 'registered':
                    client_info_dict = amf0_cmd[3]
                    self.on_registered(client_info_dict)

                elif cmd == 'join':
                    usr_join_info_dict = amf0_cmd[3]
                    thread.start_new_thread(self.on_join, (usr_join_info_dict, ))

                elif cmd == 'joins':
                    current_room_users_info_list = amf0_cmd[3:]
                    if len(current_room_users_info_list) is not 0:
                        while iparam0 < len(current_room_users_info_list):
                            self.on_joins(current_room_users_info_list[iparam0])
                            iparam0 += 1

                elif cmd == 'joinsdone':
                    self.on_joinsdone()

                elif cmd == 'oper':
                    oper_id_name = amf0_cmd[3:]
                    while iparam0 < len(oper_id_name):
                        oper_id = str(oper_id_name[iparam0]).split('.0')
                        oper_name = oper_id_name[iparam0 + 1]
                        if len(oper_id) == 1:
                            self.on_oper(oper_id[0], oper_name)
                        iparam0 += 2

                elif cmd == 'deop':
                    deop_id = amf0_cmd[3]
                    deop_nick = amf0_cmd[4]
                    self.on_deop(deop_id, deop_nick)

                elif cmd == 'owner':
                    self.on_owner()

                elif cmd == 'avons':
                    avons_id_name = amf0_cmd[4:]
                    if len(avons_id_name) is not 0:
                        while iparam0 < len(avons_id_name):
                            avons_id = avons_id_name[iparam0]
                            avons_name = avons_id_name[iparam0 + 1]
                            self.on_avon(avons_id, avons_name)
                            iparam0 += 2

                elif cmd == 'pros':
                    pro_ids = amf0_cmd[4:]
                    if len(pro_ids) is not 0:
                        for pro_id in pro_ids:
                            pro_id = str(pro_id).replace('.0', '')
                            self.on_pro(pro_id)

                elif cmd == 'nick':
                    old_nick = amf0_cmd[3]
                    new_nick = amf0_cmd[4]
                    nick_id = int(amf0_cmd[5])
                    self.on_nick(old_nick, new_nick, nick_id)

                elif cmd == 'nickinuse':
                    self.on_nickinuse()

                elif cmd == 'quit':
                    quit_name = amf0_cmd[3]
                    quit_id = amf0_cmd[4]
                    self.on_quit(quit_id, quit_name)

                elif cmd == 'kick':
                    kick_id = amf0_cmd[3]
                    kick_name = amf0_cmd[4]
                    self.on_kick(kick_id, kick_name)

                elif cmd == 'banned':
                    self.on_banned()

                elif cmd == 'banlist':
                    banlist_id_nick = amf0_cmd[3:]
                    if len(banlist_id_nick) is not 0:
                        while iparam0 < len(banlist_id_nick):
                            banned_id = banlist_id_nick[iparam0]
                            banned_nick = banlist_id_nick[iparam0 + 1]
                            self.on_banlist(banned_id, banned_nick)
                            iparam0 += 2

                elif cmd == 'startbanlist':
                    # print(amf0_data)
                    pass

                elif cmd == 'topic':
                    topic = amf0_cmd[3]
                    self.on_topic(topic)

                elif cmd == 'from_owner':
                    owner_msg = amf0_cmd[3]
                    self.on_from_owner(owner_msg)

                elif cmd == 'doublesignon':
                    self.on_doublesignon()

                elif cmd == 'privmsg':
                    msg_text = self._decode_msg(u'' + amf0_cmd[4])
                    msg_sender = amf0_cmd[6]
                    self.on_privmsg(msg_text, msg_sender)

                elif cmd == 'notice':
                    notice_msg = amf0_cmd[3]
                    notice_msg_id = amf0_cmd[4]
                    if notice_msg == 'avon':
                        avon_name = amf0_cmd[5]
                        self.on_avon(notice_msg_id, avon_name)
                    elif notice_msg == 'pro':
                        self.on_pro(notice_msg_id)



                else:
                    console_write([COLOR['bright_red'], 'Unknown command:' + cmd, self.roomname])

            except Exception as e:
                if SETTINGS['debug_mode']:
                    traceback.print_exc()

    # Callback Event Methods.
    def on_result(self, result_info):
        pass

    def on_error(self, error_info):
        pass

    def on_status(self):
        pass

    def on_bwdone(self):
        if not self.is_reconnected:
            thread.start_new_thread(self.start_auto_job_timer, ())

    def on_registered(self, client_info):
        self.client_id = client_info['id']
        self.is_client_mod = client_info['mod']
        user = self.add_user_info(client_info['nick'])
        user.id = client_info['id']
        user.nick = client_info['nick']
        user.is_owner = client_info['own']
        user.is_mod = self.is_client_mod
        # self.is_client_pro = client_info['pro']

        console_write([COLOR['bright_green'], 'registered with ID: ' + str(self.client_id) +
                       '. Trying to parse captcha key.', self.roomname])

        key = tinychat_api.get_captcha_key(self.roomname, str(self.client_id), proxy=self.proxy)
        if key is None:
            console_write([COLOR['bright_red'], 'There was a problem parsing the captcha key. Key=' +
                           str(key), self.roomname])
        else:
            console_write([COLOR['bright_green'], 'Captcha key found: ' + key, self.roomname])
            self.send_cauth_msg(key)
            self.set_nick()

    def on_join(self, join_info_dict):
        user = self.add_user_info(join_info_dict['nick'])
        user.nick = join_info_dict['nick']
        user.user_account = join_info_dict['account']
        user.id = join_info_dict['id']
        user.is_mod = join_info_dict['mod']
        user.is_owner = join_info_dict['own']

        if join_info_dict['account']:
            tc_info = tinychat_api.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']
            if join_info_dict['own']:
                console_write([COLOR['red'], 'Room Owner ' + join_info_dict['nick'] +
                               ':' + str(join_info_dict['id']) + ':' + join_info_dict['account'], self.roomname])
            elif join_info_dict['mod']:
                console_write([COLOR['bright_red'], 'Moderator ' + join_info_dict['nick'] +
                               ':' + str(join_info_dict['id']) + ':' + join_info_dict['account'], self.roomname])
            else:
                console_write([COLOR['bright_yellow'], join_info_dict['nick'] + ':' + str(join_info_dict['id']) +
                               'Has account: ' + join_info_dict['account'], self.roomname])
        else:
            if join_info_dict['id'] is not self.client_id:
                console_write([COLOR['bright_cyan'], join_info_dict['nick'] + ':' + str(join_info_dict['id']) +
                               ' joined the room.', self.roomname])

    def on_joins(self, joins_info_dict):
        user = self.add_user_info(joins_info_dict['nick'])
        user.nick = joins_info_dict['nick']
        user.user_account = joins_info_dict['account']
        user.id = joins_info_dict['id']
        user.is_mod = joins_info_dict['mod']
        user.is_owner = joins_info_dict['own']

        if joins_info_dict['account']:
            if joins_info_dict['own']:
                console_write([COLOR['red'], 'Joins Room Owner ' + joins_info_dict['nick'] +
                               ':' + str(joins_info_dict['id']) + ':' + joins_info_dict['account'], self.roomname])
            elif joins_info_dict['mod']:
                console_write([COLOR['bright_red'], 'Joins Moderator ' + joins_info_dict['nick'] +
                               ':' + str(joins_info_dict['id']) + ':' + joins_info_dict['account'], self.roomname])
            else:
                console_write([COLOR['bright_yellow'], 'Joins: ' + joins_info_dict['nick'] +
                               ':' + str(joins_info_dict['id']) + ':' + joins_info_dict['account'], self.roomname])
        else:
            if joins_info_dict['id'] is not self.client_id:
                console_write([COLOR['bright_cyan'], 'Joins: ' + joins_info_dict['nick'] +
                               ':' + str(joins_info_dict['id']), self.roomname])

    def on_joinsdone(self):
        if self.is_client_mod:
            self.send_banlist_msg()

    def on_oper(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = True
        if uid != self.client_id:
            console_write([COLOR['bright_red'], nick + ':' + uid + ' is moderator.', self.roomname])

    def on_deop(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = False
        console_write([COLOR['red'], nick + ':' + uid + ' was deoped.', self.roomname])

    def on_owner(self):
        # self.is_client_mod = True
        # self.send_banlist_msg()
        pass

    def on_avon(self, uid, name):
        console_write([COLOR['cyan'], name + ':' + uid + ' is broadcasting.', self.roomname])

    def on_pro(self, uid):
        console_write([COLOR['cyan'], uid + ' is pro.', self.roomname])

    def on_nick(self, old, new, uid):
        if uid != self.client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self.room_users.keys():
                del self.room_users[old]
                self.room_users[new] = old_info
            console_write([COLOR['cyan'], old + ':' + str(uid) + ' changed nick to: ' + new, self.roomname])

    def on_nickinuse(self):
        self.nick_inuse()

    def on_quit(self, uid, name):
        if name in self.room_users.keys():
            del self.room_users[name]
        console_write([COLOR['cyan'], name + ':' + uid + ' left the room.', self.roomname])

    def on_kick(self, uid, name):
        console_write([COLOR['bright_red'], name + ':' + uid + ' was banned.', self.roomname])
        self.send_banlist_msg()

    def on_banned(self):
        console_write([COLOR['red'], 'You are banned from this room.', self.roomname])

    def on_banlist(self, uid, nick):
        console_write([COLOR['bright_red'], 'Banned user: ' + nick + ':' + uid, self.roomname])

    def on_topic(self, topic):
        topic_msg = topic.encode('utf-8', 'replace')
        console_write([COLOR['cyan'], 'room topic: ' + topic_msg, self.roomname])

    def on_from_owner(self, owner_msg):
        msg = str(owner_msg).replace('notice', '').replace('%20', ' ')
        console_write([COLOR['bright_red'], msg, self.roomname])

    def on_doublesignon(self):
        console_write([COLOR['bright_red'], 'This account is already in this room. Aborting!', self.roomname])
        self.is_connected = False

    def on_privmsg(self, msg, msg_sender):
        """
        Message command controller.
        :param msg: str message.
        :param msg_sender: str the sender of the message.
        """
        if msg.startswith('/'):
            msg_cmd = msg.split(' ')
            if msg_cmd[0] == '/msg':
                private_msg = ' '.join(msg_cmd[2:])
                self.private_message_handler(msg_sender, private_msg)

            elif msg_cmd[0] == '/mbs':
                media_type = msg_cmd[1]
                media_id = msg_cmd[2]
                thread.start_new_thread(self.media_broadcast_start, (media_type, media_id, msg_sender,))

            elif msg_cmd[0] == '/mbc':
                media_type = msg_cmd[1]
                self.media_broadcast_close(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpa':
                media_type = msg_cmd[1]
                self.media_broadcast_paused(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpl':
                media_type = msg_cmd[1]
                time_point = int(msg_cmd[2])
                # start in new thread
                self.media_broadcast_resumed(media_type, time_point, msg_sender)

            elif msg_cmd[0] == '/mbsk':
                media_type = msg_cmd[1]
                time_point = int(msg_cmd[2])
                # start in new thread
                self.media_broadcast_skip(media_type, time_point, msg_sender)
        else:
            self.message_handler(msg_sender, msg)

    # Message Handler.
    def message_handler(self, msg_sender, msg):
        """
        Message handler.
        :param msg_sender: str the user sending a message
        :param msg: str the message
        """
        console_write([COLOR['green'], msg_sender + ':' + msg, self.roomname])

    # Private message Handler.
    def private_message_handler(self, msg_sender, private_msg):
        """
        A user private message us.
        :param msg_sender: str the user sending the private message.
        :param private_msg: str the private message.
        """
        console_write([COLOR['white'], 'Private message from ' + msg_sender + ':' + private_msg, self.roomname])

    # Media Events.
    def media_broadcast_start(self, media_type, video_id, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param video_id: str the youtube ID or souncloud trackID.
        :param usr_nick: str the user name of the user playing media.
        """
        console_write([COLOR['bright_magenta'], usr_nick + ' is playing ' + media_type + ' ' + video_id, self.roomname])

    def media_broadcast_close(self, media_type, usr_nick):
        """
        A user closed a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param usr_nick: str the user name of the user closing the media.
        """
        console_write([COLOR['bright_magenta'], usr_nick + ' closed the ' + media_type, self.roomname])

    def media_broadcast_paused(self, media_type, usr_nick):
        """
        A user paused the media broadcast.
        :param media_type: str the type of media being paused. youTube or soundCloud.
        :param usr_nick: str the user name of the user pausing the media.
        """
        console_write([COLOR['bright_magenta'], usr_nick + ' paused the ' + media_type, self.roomname])

    def media_broadcast_resumed(self, media_type, time_point, usr_nick):
        """
        A user resumed playing a media broadcast.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user resuming the tune.
        """
        console_write([COLOR['bright_magenta'], usr_nick +
                       ' resumed the ' + media_type + ' at: ' + str(time_point), self.roomname])

    def media_broadcast_skip(self, media_type, time_point, usr_nick):
        """
        A user time searched a tune.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user time searching the tune.
        """
        console_write([COLOR['bright_magenta'], usr_nick + ' time searched the ' + media_type +
                       ' at: ' + str(time_point), self.roomname])

    # User Related
    def add_user_info(self, usr_nick):
        """
        Find the user object for a given user name and add to it.
        We use this methode to add info to our user info object.
.
        :param usr_nick: str the user name of the user we want to find info for.
        :return: object a user object containing user info.
        """
        if usr_nick not in self.room_users.keys():
            self.room_users[usr_nick] = RoomUser(usr_nick)
        return self.room_users[usr_nick]

    def find_user_info(self, usr_nick):
        """
        Find the user object for a given user name.
        Instead of adding to the user info object, we return None if the user name is NOT in the room_users dict.
        We use this method when we are getting user input to look up.

        :param usr_nick: str the user name to find info for.
        :return: object or None if no user name is in the room_users dict.
        """
        if usr_nick in self.room_users.keys():
            return self.room_users[usr_nick]
        return None

    # Message Functions
    def send_bauth_msg(self):
        """ Get and send the bauth key needed before we can start a broadcast. """
        bauth_key = tinychat_api.get_bauth_token(self.roomname, self.client_nick, self.client_id,
                                                 self.greenroom, proxy=self.proxy)
        if bauth_key != 'PW':
            self._sendCommand('bauth', [u'' + bauth_key])

    def send_cauth_msg(self, cauthkey):
        """
        Send the cauth key message with a working cauth key, we need to send this before we can chat.
        :param cauthkey: str a working cauth key.
        """
        self._sendCommand('cauth', [u'' + cauthkey])

    def send_owner_run_msg(self, msg):
        """
        Send owner run message. The client has to be mod when sending this message.
        :param msg: the message str to send.
        """
        self._sendCommand('owner_run', [u'notice' + msg.replace(' ', '%20')])

    def send_bot_msg(self, msg, is_mod=False):
        """
        Send a message in the color black.
        :param msg: str the message to send.
        :param is_mod: bool if True we send owner run message, else we send a normal message in the color black.
        """
        if is_mod:
            self.send_owner_run_msg(msg)
        else:
            self._sendCommand('privmsg', [u'' + self._encode_msg(msg), u'#000000,en'])

    def send_private_bot_msg(self, msg, nick):
        """
        Send a private message to a user in the color black.
        :param msg: str the message to send.
        :param nick: str the user to receive the message.
        """
        self._sendCommand('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg), u'#000000,en'])

    def send_chat_msg(self, msg):
        """
        Send a chat room message with a random color.
        :param msg: str the message to send.
        """
        self._sendCommand('privmsg', [u'' + self._encode_msg(msg), u'' + random_color() + ',en'])

    def send_private_msg(self, msg, nick):
        """
        Send a private message to a user with a random color.
        :param msg: str the private message to send.
        :param nick: str the user name to receive the message.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self._sendCommand('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg),
                                          u'' + random_color() + ',en', u'n' + str(user.id) + '-' + nick])
            self._sendCommand('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg),
                                          u'' + random_color() + ',en', u'b' + str(user.id) + '-' + nick])

    def send_userinfo_request_msg(self, user_id):
        """
        Send user info request to a user.
        :param user_id: str user id of the user we want info from.
        :return:
        """
        self._sendCommand('account', [u'' + str(user_id)])

    def send_undercover_msg(self, nick, msg):
        """
        Send a 'undercover' message.
        This is a special message that appears in the main chat, but is only visible to the user it is sent to.
        It can also be used to play 'private' youtubes/soundclouds with.

        :param nick: str the user name to send the message to.
        :param msg: str the message to send.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self._sendCommand('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'b' + str(user.id) + '-' + nick])
            self._sendCommand('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'n' + str(user.id) + '-' + nick])

    def set_nick(self):
        """ Send the nick message. """
        if not self.client_nick:
            self.client_nick = create_random_string(5, 25)
        console_write([COLOR['white'], 'Setting nick: ' + self.client_nick, self.roomname])
        self._sendCommand('nick', [u'' + self.client_nick])

    def send_ban_msg(self, nick, uid):
        """
        Send ban message. The client has to be mod when sending this message.
        :param nick: str the user name of the user we want to ban.
        :param uid: str the ID of the user we want to ban.
        """
        self._sendCommand('kick', [u'' + nick, str(uid)])

    def send_forgive_msg(self, uid):
        """
        Send forgive message. The client has to be mod when sending this message.
        :param uid: str the ID of the user we want to forgive.
        """
        self._sendCommand('forgive', [u'' + str(uid)])
        self.send_banlist_msg()

    def send_banlist_msg(self):
        """
        Send banlist message. The client has to be mod when sending this message.
        :return:
        """
        self._sendCommand('banlist', [])

    def send_topic_msg(self, topic):
        """
        Send a room topic message. The client has to be mod when sending this message.
        :param topic: str the room topic.
        """
        self._sendCommand('topic', [u'' + topic])

    def send_close_user_msg(self, nick):
        """
        Send close user broadcast message. The client has to be mod when sending this message.
        :param nick: str the user name of the user we want to close.
        """
        self._sendCommand('owner_run', [u'_close' + nick])

    def play_youtube(self, video_id):
        """
        Start a youtube video.
        :param video_id: str the youtube video ID.
        """
        self.send_chat_msg('/mbs youTube ' + str(video_id) + ' 0')

    def stop_youtube(self):
        """ Stop/Close a youtube video. """
        self.send_chat_msg('/mbc youTube')

    def play_soundcloud(self, track_id):
        """
        Start a soundcloud video.
        :param track_id: str soundcloud track ID.
        """
        self.send_chat_msg('/mbs soundCloud ' + str(track_id) + ' 0')

    def stop_soundcloud(self):
        """  Stop/Close a soundcloud video. """
        self.send_chat_msg('/mbc soundCloud')

    def nick_inuse(self):
        """ Choose a different user name if the one we chose originally was being used. """
        self.client_nick += str(random.randint(0, 10))
        console_write([COLOR['white'], 'Nick already taken. Changing nick to: ' + self.client_nick, self.roomname])
        self.set_nick()

    # Message Cunstruction.
    def _sendCommand(self, cmd, params=[]):
        """
        Calls remote procedure calls (RPC) at the receiving end.
        :param cmd: str remote command.
        :param params: list command parameters.
        """
        msg = {
            'msg': rtmp_protocol.DataTypes.COMMAND,
            'command': [u'' + cmd, 0, None] + params
        }
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _sendCreateStream(self):
        """ Send createStream message. """
        msg = {
            'msg': rtmp_protocol.DataTypes.COMMAND,
            'command': [u'' + 'createStream', 12, None]
        }
        console_write([COLOR['white'], 'Sending createStream message.', self.roomname])
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _sendCloseStream(self):
        """ Send closeStream message. """
        msg = {
            'msg': rtmp_protocol.DataTypes.COMMAND,
            'command': [u'' + 'closeStream', 0, None]
        }
        console_write([COLOR['white'], 'Closing stream.', self.roomname])
        self.connection.writer.writepublish(msg)
        self.connection.writer.flush()

    def _sendPublish(self):
        """ Send publish message. """
        msg = {
            'msg': rtmp_protocol.DataTypes.COMMAND,
            'command': [u'' + 'publish', 0, None, u'' + str(self.client_id), u'' + 'live']
        }
        console_write([COLOR['white'], 'Sending publish message.', self.roomname])
        self.connection.writer.writepublish(msg)
        self.connection.writer.flush()

    def _sendPingRequest(self):
        # TODO: Make this method work!
        msg = {
            'msg': rtmp_protocol.DataTypes.USER_CONTROL,
            'event_type': rtmp_protocol.UserControlTypes.PING_REQUEST
        }
        self.connection.handle_simple_message(msg)
        self.connection.writer.flush()

    # Helper Methods
    def _decode_msg(self, msg):
        """
        Decode str from comma separated decimal to normal text str.
        :param msg: str the encoded message.
        :return: str normal text.
        """
        chars = msg.split(',')
        msg = ''
        for i in chars:
            msg += unichr(int(i))
        return msg

    def _encode_msg(self, msg):
        """
        Encode normal text str to comma separated decimal.
        :param msg: str the normal text to encode
        :return: comma separated decimal str.
        """
        return ','.join(str(ord(char)) for char in msg)

    # Timed Auto Method.
    def start_auto_job_timer(self):
        """
        Just like using tinychat with a browser, this method will
        fetch the room config from tinychat API every 5 minute.
        See line 228 at http://tinychat.com/embed/chat.js
        """
        ts_now = int(time.time())
        while True:
            counter = int(time.time())
            if counter == ts_now + 300:  # 300 seconds = 5 minutes
                if self.is_connected:
                    tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
                self.start_auto_job_timer()
                break


def main():
    room_name = raw_input('Enter room name: ')
    nickname = raw_input('Enter nick name: (optional) ')
    room_password = raw_input('Enter room password: (optional) ')
    login_account = raw_input('Login account: (optional)')
    login_password = raw_input('Login password: (optional)')

    client = TinychatRTMPClient(room_name, nick=nickname, account=login_account,
                                password=login_password, room_pass=room_password)

    thread.start_new_thread(client.prepare_connect, ())
    while not client.is_connected:
        time.sleep(1)
    while client.is_connected:
        chat_msg = raw_input()
        if chat_msg.lower() == 'q':
            client.disconnect()
        else:
            client.send_bot_msg(chat_msg, client.is_client_mod)

if __name__ == '__main__':
    main()
