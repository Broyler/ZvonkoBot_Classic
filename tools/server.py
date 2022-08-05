import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from file_system import *


class Server:
    def __init__(self):
        settings = File('../settings.json')

        self.vk = vk_api.VkApi(token=settings.get('vk_api_token'))
        self.long_poll = VkBotLongPoll(self.vk, settings.get('vk_group_id'))
        self.vk_api = self.vk.get_api()
        self.database = UsersDatabase('../files/users.json')
        self.messages = File('../files/messages.json')
        self.screens = File('../files/screens.json')

    @check
    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                data = event.object.get('message')
                uid = data['from_id']
                t = data['text']

                if self.database.check_user(uid):
                    user = self.database.user(uid, self.vk_api)

                    if user.get('stage') == 'setup_select_campus':
                        if t == self.screens.get('setup_select_campus')[0][0][0]:
                            user.msg('option 1')

                        elif t == self.screens.get('setup_select_campus')[0][1][0]:
                            user.msg('option 2')

                        else:
                            user.msg('unknown option')

                else:
                    user = self.database.new_user(uid, self.vk_api)

                    user.msg(self.messages.get('setup_welcome'))
                    user.stage('setup_select_campus')


server = Server()
server.start()
