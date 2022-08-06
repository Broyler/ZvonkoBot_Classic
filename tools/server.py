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
                            user.update({'campus': 1})
                            user.stage('setup_select_grade', override_screen=get_auto_screen(
                                list(File('../files/grades.json').read().keys())
                            ))

                        elif t == self.screens.get('setup_select_campus')[0][1][0]:
                            user.update({'campus': 7})
                            user.stage('select_notifications')

                        else:
                            user.msg(self.messages.get('setup_select_campus_error'))

                    elif user.get('stage') == 'setup_select_grade':
                        if t in list(File('../files/grades.json').read().keys()):
                            user.update({'grade': int(t)})
                            user.stage('setup_select_type', override_screen=get_auto_screen(
                                File('../files/grades.json').get(t)
                            ))

                        else:
                            user.msg(self.messages.get('setup_select_grade_error'))

                    elif user.get('stage') == 'setup_select_type':
                        if t in File('../files/grades.json').get(str(user.get('grade'))):
                            user.update({'type': t})
                            user.stage('select_notifications')

                        else:
                            user.msg(self.messages.get('setup_select_type_error'))

                    elif user.get('stage') == 'select_notifications':
                        correct_input = True

                        if t == self.screens.get('select_notifications')[0][0][0]:
                            user.update({"notifications_preferences": {
                                "lesson_start": True,
                                "lesson_end": True
                            }})

                        elif t == self.screens.get('select_notifications')[0][1][0]:
                            user.update({"notifications_preferences": {
                                "lesson_start": False,
                                "lesson_end": False
                            }})

                        elif t == self.screens.get('select_notifications')[1][0][0]:
                            user.update({"notifications_preferences": {
                                "lesson_start": True,
                                "lesson_end": False
                            }})

                        elif t == self.screens.get('select_notifications')[1][1][0]:
                            user.update({"notifications_preferences": {
                                "lesson_start": False,
                                "lesson_end": True
                            }})

                        else:
                            correct_input = False
                            user.msg(self.messages.get('select_notifications_error'))

                        if correct_input:
                            user.stage('main_screen', 'setup_finish')

                else:
                    user = self.database.new_user(uid, self.vk_api)

                    user.msg(self.messages.get('setup_welcome'))
                    user.stage('setup_select_campus')


server = Server()
server.start()
