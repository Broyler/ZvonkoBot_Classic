from json import loads, dumps
from datetime import datetime
import inspect
import vk_api.vk_api
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

colors = {
    "blue": VkKeyboardColor.PRIMARY,
    "green": VkKeyboardColor.POSITIVE,
    "red": VkKeyboardColor.NEGATIVE,
    "white": VkKeyboardColor.SECONDARY
}


def f(x: int) -> str:
    return str(x) if len(str(x)) == 2 else f"0{x}"


def timestamp() -> str:
    return (lambda x: f"[{f(x.hour)}:{f(x.minute)}:{f(x.second)}]")(datetime.now())


def log(s: str):
    print(f"{timestamp()} {s}")


def get_screen(screen_id: str):
    keyboard = VkKeyboard(one_time=False)
    data = File('../files/screens.json').get(screen_id)

    for i in data:
        for j in i:
            keyboard.add_button(j[0], colors[j[1]])

        keyboard.add_line() if data[-1] != i else None

    return keyboard.get_keyboard()


def get_auto_screen(data: list, buttons_per_row: int = 3, color: str = "white", cancel_button: str = ""):
    keyboard = VkKeyboard(one_time=False)
    buttons_on_current_row = 0

    for i in data:
        keyboard.add_button(i, colors[color])
        buttons_on_current_row += 1

        if buttons_on_current_row >= buttons_per_row and data[-1] != i:
            keyboard.add_line()
            buttons_on_current_row = 0

    if cancel_button != "":
        keyboard.add_line()
        keyboard.add_button(cancel_button, 'red')

    return keyboard.get_keyboard()


def check(func):
    def check_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            func_args = inspect.signature(func).bind(*args, **kwargs).arguments
            func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))

            log(f"Ошибка {e} в {func.__name__}, при {func_args_str}")

    return check_wrapper


class File:
    @check
    def reload(self):
        with open(self.path, "r", encoding="utf-8") as file:
            self.contents = (lambda x: loads(x) if self.path.endswith('.json') else x)(file.read())

    @check
    def read(self) -> str | dict:
        self.reload()
        return self.contents

    @check
    def get(self, field: str):
        self.reload()
        return self.contents.get(field)

    @check
    def update(self, contents: str | dict):
        self.read()
        with open(self.path, "w", encoding="utf-8") as file:
            if type(contents) == str:
                self.contents += contents
                file.write(self.contents)

            else:
                self.contents.update(contents)
                file.write(dumps(self.contents, indent=4))

    def __init__(self, path: str):
        self.path = path
        self.contents = None
        self.reload()


class User:
    def __init__(self, uid: int, users, vk):
        self.uid = uid
        self.database = users
        self.data = self.database.user_raw(self.uid)
        self.vk = vk

    @check
    def reload(self):
        self.data = self.database.user_raw(self.uid)

    @check
    def get(self, field: str):
        self.reload()
        return self.data.get(field)

    @check
    def update(self, payload: dict):
        self.database.update_user(self.uid, payload)

    @check
    def msg(self, msg: str):
        self.vk.messages.send(
            peer_id=self.uid,
            message=msg,
            random_id=get_random_id()
        )

    @check
    def screen(self, msg: str, screen_id: str):
        screen = get_screen(screen_id)

        self.vk.messages.send(
            peer_id=self.uid,
            message=msg,
            keyboard=screen,
            random_id=get_random_id()
        )

    @check
    def msg_and_clear_screen(self, msg: str):
        self.vk.messages.send(
            peer_id=self.uid,
            message=msg,
            keyboard=VkKeyboard.get_empty_keyboard(),
            random_id=get_random_id()
        )

    @check
    def stage(self, stage: str, override_msg: str = "", override_screen=None):
        self.vk.messages.send(
            peer_id=self.uid,
            message=File('../files/messages.json').get(stage if override_msg == "" else override_msg),
            keyboard=get_screen(stage) if override_screen is None else override_screen,
            random_id=get_random_id()
        )
        self.update({"stage": stage})


class UsersDatabase(File):
    @check
    def update_user(self, uid: int, payload: dict):
        user = self.contents.get(str(uid))
        user.update(payload)
        # self.contents[str(uid)] = user
        self.update({str(uid): user})

    @check
    def user(self, uid: int, vk: vk_api):
        return User(uid, self, vk)

    @check
    def user_raw(self, uid: int):
        return self.read().get(str(uid))

    @check
    def check_user(self, uid: int):
        self.reload()
        return str(uid) in self.contents

    @check
    def new_user(self, uid: int, vk: vk_api):
        self.update({str(uid): File('../files/standards.json').get('user')})
        return self.user(uid, vk)
