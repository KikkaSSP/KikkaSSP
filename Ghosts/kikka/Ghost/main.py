# coding=utf-8
import os
import sys
import time
import random
import logging
import datetime
import requests
from functools import partial

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QStackedLayout, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QGuiApplication, QImage

import kikka
from kikka.const import GhostEvent
from ghost.ghost import Ghost
from ghost.window_dialog import WindowDialog

KIKKA = 0
TOWA = 1


def createGhost(ghost_id, ghost_data, ghost_loader):
    return GhostKikka(ghost_id, ghost_data, ghost_loader)


class GhostKikka(Ghost):

    def __init__(self, gid, ghost_data, ghost_loader):
        Ghost.__init__(self, gid, ghost_data, ghost_loader)
        self._datetime = datetime.datetime.now()
        self._touch_count = {KIKKA: {}, TOWA: {}}

    def init(self):
        super().init()
        self.add_soul(KIKKA, 0)
        self.add_soul(TOWA, 10)

    def initialed(self):
        super().initialed()
        self._weather = self.get_weather()

        self.init_kikka_layout()
        self.init_towa_layout()
        self.init_talk()
        self.init_menu()
        self.on_first_boot()

    def init_kikka_layout(self):
        dlg = self.get_soul(KIKKA).get_dialog()
        self._kikka_widget = QWidget()
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._stacked_layout = QStackedLayout()
        self._stacked_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout = QVBoxLayout()
        self._footer_layout = QHBoxLayout()

        # 0 main Layout
        self._main_layout.addLayout(self._top_layout)
        self._main_layout.addLayout(self._stacked_layout)
        self._main_layout.addLayout(self._footer_layout)

        # 1.0 top layout
        self._toplabel = QLabel("Hello")
        self._toplabel.setObjectName('Hello')
        self._top_layout.addWidget(self._toplabel)

        # 1.2 tab layout
        self._tabLayout = QHBoxLayout()
        self._top_layout.addLayout(self._tabLayout)

        # 1.2.1 tab button
        p1 = QPushButton("常用")
        p2 = QPushButton("设置")
        p1.clicked.connect(lambda: self._stacked_layout.setCurrentIndex(0))
        p2.clicked.connect(lambda: self._stacked_layout.setCurrentIndex(1))
        self._tabLayout.addWidget(p1)
        self._tabLayout.addWidget(p2)
        self._tabLayout.addStretch()

        # 2.0 page
        page1 = QWidget(self._kikka_widget)
        page2 = QWidget(self._kikka_widget)
        self._stacked_layout.addWidget(page1)
        self._stacked_layout.addWidget(page2)
        page1_l = QWidget(page1)
        page1_r = QWidget(page1)
        page2_l = QWidget(page2)
        page2_r = QWidget(page2)

        # 2.1.1 page1_l
        pl1 = QVBoxLayout()
        pl1.setContentsMargins(0, 0, 0, 0)
        page1_l.setLayout(pl1)
        for i in range(len(QGuiApplication.screens())):
            bt1 = QPushButton("◇复制壁纸%d" % i)
            bt1.clicked.connect(partial(self.copy_wall_paper, i))
            pl1.addWidget(bt1)

        # 2.1.2 page1_r
        pl2 = QVBoxLayout()
        pl2.setContentsMargins(0, 0, 0, 0)

        page1_r.setLayout(pl2)
        pl2.addStretch()

        # 2.2.1 page2_l
        dialog = self.get_soul(KIKKA).get_dialog()

        def click1():
            dialog.show_input_box(
                "新的称呼: ",
                self.get_variable('username'),
                callback=self.callback_set_user_name
            )

        def click3():
            dialog.show_input_box(
                "请输入和风天气的APIkey:\n可以在 https://dev.heweather.com/ 免费申请哦~",
                self.memory_read('WeatherKey', ''),
                callback=self.callback_set_weather_api
            )

        pl3 = QVBoxLayout()
        pl3.setContentsMargins(0, 0, 0, 0)
        page2_l.setLayout(pl3)
        bt1 = QPushButton("◇更改称呼")
        bt2 = QPushButton("◇调整对话框")
        bt3 = QPushButton("◇设置天气APIkey")
        bt1.clicked.connect(click1)
        bt2.clicked.connect(lambda: self.emit_custom_event(KIKKA, 'ResizeWindow', {'bool': False}))
        bt3.clicked.connect(click3)
        pl3.addWidget(bt1)
        pl3.addWidget(bt2)
        pl3.addWidget(bt3)
        pl3.addStretch()

        # 2.2.2 page2_r
        pl4 = QVBoxLayout()
        pl4.setContentsMargins(0, 0, 0, 0)
        page2_r.setLayout(pl4)
        pl4.addStretch()

        # 3.0 footer layout
        self._footer_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(lambda: self.emit_custom_event(KIKKA, 'CloseDialog', {'bool': False}))
        self._footer_layout.addWidget(close_btn)

        self._kikka_widget.setLayout(self._main_layout)
        dlg.set_page(WindowDialog.DIALOG_MAIN_MENU, self._kikka_widget)

    def init_towa_layout(self):
        dlg = self.get_soul(TOWA).get_dialog()
        self._towa_widget = QWidget()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        bt1 = QPushButton("◇调整对话框")
        bt2 = QPushButton("◇关闭")
        bt1.clicked.connect(lambda: self.emit_custom_event(TOWA, 'ResizeWindow', {'bool': False}))
        bt2.clicked.connect(lambda: self.emit_custom_event(TOWA, 'CloseDialog', {'bool': False}))
        main_layout.addWidget(bt1)
        main_layout.addWidget(bt2)
        main_layout.addStretch()

        self._towa_widget.setLayout(main_layout)
        dlg.set_page(WindowDialog.DIALOG_MAIN_MENU, self._towa_widget)

    def init_menu(self):
        # main_menu = self.getMenu(KIKKA)
        # menu = Menu(main_menu.parent(), self.id, "kikka menu")
        # main_menu.insertMenu(main_menu.actions()[0], menu)
        #
        # def _test_callback(index=0, title=''):
        #     logging.info("GhostKikka_callback: click [%d] %s" % (index, title))
        #
        # act = menu.add_menu_item("111", _test_callback)
        # act.setShortcut(QKeySequence("Ctrl+T"))
        # act.setShortcutContext(Qt.ApplicationShortcut)
        # act.setShortcutVisibleInContextMenu(True)
        #
        #
        # w = self.getShellWindow(KIKKA)
        # w.addAction(act)
        pass

    def ghost_event(self, param):
        super().ghost_event(param)

        if param.event_type == GhostEvent.Dialog_Show:
            if self._weather is not None:
                text = "%s现在是%s℃哦，%s" % (
                    self._weather['basic']['location'],
                    self._weather['now']['tmp'],
                    self.get_variable('username')
                )
                self._toplabel.setText(text)
                self._stacked_layout.setCurrentIndex(0)
        elif param.event_type == GhostEvent.CustomEvent:
            if param.event_tag == 'ResizeWindow':
                self.resize_window(param)
            elif param.event_tag == 'CloseDialog':
                self.close_dlg(param)

    def emit_custom_event(self, soul_id, tag, data=None):
        param = kikka.helper.make_ghost_event_param(self.id, soul_id, GhostEvent.CustomEvent, tag, data)
        self.emit_ghost_event(param)

    def change_shell(self, shell_id):
        logging.debug("Please don't peek at me to change clothes!")
        super().change_shell(shell_id)

    # ########################################################################################################

    def on_first_boot(self):
        boot_last = datetime.datetime.fromtimestamp(self.memory_read('BootLast', time.time()))
        today = datetime.datetime.now()
        if boot_last.day == today.day:
            return
        self.daily_shell()

    def on_boot(self):
        self.talk(self.say_hello())

    def daily_shell(self):
        today = datetime.datetime.now()
        shell_name = None
        # feastival
        if today.month == 1 and today.day == 1:
            shell_name = 'normal-Yukata'
        elif today.month == 2 and today.day == 22:
            shell_name = 'normal-NekoMimi'
        elif today.month == 3 and today.day == 5:
            shell_name = 'cosplay-SilverFox'
        elif today.month == 3 and today.day == 9:
            shell_name = 'cosplay-HatsuneMiku'
        elif today.month == 3 and today.day == 28 \
                or today.month == 4 and today.day == 29:
            shell_name = 'cosplay-Momohime'
        elif today.month == 4 and today.day == 8:
            shell_name = 'cosplay-KonpakuYoumu'
        elif today.month == 5 and today.day == 2:
            shell_name = 'normal-Maid'
        elif today.month == 6 and today.day == 10 \
                or today.month == 8 and today.day == 11 \
                or today.month == 7 and today.day == 27:
            shell_name = 'cosplay-IzayoiSakuya'
        elif today.month == 8 and today.day == 17:
            shell_name = 'cosplay-InubashiriMomizi'
        elif today.month == 9 and today.day == 3:
            shell_name = 'cosplay-SetsukoOhara'
        elif today.month == 10 and today.day == 13:
            shell_name = 'private-Nurse'
        elif today.month == 10 and today.day == 22:
            shell_name = 'cosplay-Win7'
        elif today.month == 10 and today.day == 25:
            shell_name = 'cosplay-Taiwan'
        elif today.month == 10 and today.day == 31:
            shell_name = 'normal-Halloween'
        elif today.month == 12 and today.day == 25:
            shell_name = 'normal-Christmas'

        if shell_name is not None:
            self.set_shell(shell_name)
            return

        if self._weather:
            shell_name = random.choice(self.get_shell_by_weather(self._weather))
            if shell_name is not None:
                self.set_shell(shell_name)
                return

        # auto change shell every day!
        shell_list = []
        if today.month in [3, 4, 5]:
            shell_list = ['_Default_1',
                          '_Default_2',
                          'cosplay-Momohime',
                          'cosplay-SetsukoOhara',
                          'cosplay-WhiteBase',
                          'cosplay-Win7',
                          'cosplay-HatsuneMiku',
                          'cosplay-Taiwan',
                          'cosplay-InubashiriMomizi',
                          'cosplay-RemiliaScarlet',
                          'normal-Maid',
                          'normal-RedDress',
                          'normal-LongSkirt',
                          ]
        elif today.month in [6, 7, 8]:
            shell_list = ['private-HadaY',
                          'private-PolkaDots',
                          'private-China',
                          'private-Lingerie2',
                          'private-Lingerie1',
                          'normal-PinkDress',
                          'normal-ARN-5041W',
                          'normal-Swimsuit',
                          'normal-Sleeveless',
                          'normal-Camisole',
                          'normal-ZashikiChildren',
                          'normal-SummerDress1',
                          'normal-SummerDress2',
                          'normal-SummerDress3',
                          'normal-Yukata',
                          'normal-Taisou',
                          'cosplay-KonpakuYoumu',
                          'cosplay-SilverFox',
                          'cosplay-ZaregotoSeries',
                          'cosplay-LeberechtMaass',
                          ]
        elif today.month in [9, 10, 11]:
            shell_list = ['private-Nurse',
                          'private-BunnyGirl',
                          'normal-Sleeveless',
                          'normal-ZashikiChildren',
                          'cosplay-KonpakuYoumu',
                          'cosplay-SilverFox',
                          'cosplay-RemiliaScarlet',
                          'cosplay-InubashiriMomizi',
                          'cosplay-IzayoiSakuya',
                          'cosplay-HatsuneMiku',
                          'cosplay-Win7',
                          'cosplay-WhiteBase',
                          'cosplay-SetsukoOhara',
                          'cosplay-Momohime',
                          'cosplay-LeberechtMaass',
                          ]
        elif today.month in [12, 1, 2]:
            shell_list = ['_Default_1',
                          '_Default_2',
                          'normal-Winter',
                          'normal-Christmas',
                          'private-Sweater',
                          'private-Nurse',
                          'normal-LongSkirt',
                          'normal-RedDress',
                          'normal-NekoMimi',
                          'normal-DogEar',
                          'normal-Maid',
                          'cosplay-Maetel',
                          '201cosplay-Accessories',
                          ]

        shell_name = self._shell.name
        if shell_name in shell_list:
            shell_list.remove(shell_name)

        shell_name = random.choice(shell_list)
        self.set_shell(shell_name)

    def get_weather(self):
        """ Example data:
        {
            "basic": {
                "cid": "CN101010100",
                "location": "Beijing",
                "parent_city": "Beijing",
                "admin_area": "Beijing",
                "cnty": "China",
                "lat": "39.90498734",
                "lon": "116.4052887",
                "tz": "+8.00"
            },
            "update": {
                "loc": "2019-06-05 22:39",
                "utc": "2019-06-05 14:39"
            },
            "status": "ok",
            "now": {
                "cloud": "91",
                "cond_code": "104",
                "cond_txt": "阴",
                "fl": "24",
                "hum": "56",
                "pcpn": "0.0",
                "pres": "1005",
                "tmp": "23",
                "vis": "8",
                "wind_deg": "73",
                "wind_dir": "东北风",
                "wind_sc": "1",
                "wind_spd": "4"
            }
        }
        """

        try:
            # you can get a free weather API key from https://dev.heweather.com/
            key = self.memory_read('WeatherKey', '')
            if key == '':
                return None

            result = requests.get('https://free-api.heweather.net/s6/weather/now?location=auto_ip&key=' + key)
            if result.status_code != 200:
                logging.warning("getWeather FAIL")
                return None

            weather = result.json()

            # API version s6
            if 'HeWeather6' not in weather and len(weather['HeWeather6']) == 0:
                return None

            data = weather['HeWeather6'][0]
            if data['status'] != 'ok':
                logging.warning("getWeather API FAIL: %s" % data['status'])
                return None

            return data
        except Exception:
            logging.warning("getWeather FAIL")

        return None

    def resize_window(self, param):
        dlg = kikka.core.get_ghost(param.ghost_id).get_soul(param.soul_id).get_dialog()
        dlg.set_frameless_window_hint(param.data['bool'])

    def close_dlg(self, param):
        kikka.core.get_ghost(param.ghost_id).get_soul(param.soul_id).get_dialog().hide()

    def callback_set_user_name(self, text):
        if text is None or text == '':
            return
        self.set_variable('username', text)
        self.memory_write('UserName', text)
        self.talk(r"\0\s[0]『%(username)』是吗。\w9\w9\n\n[half]\0\s[6]那么再一次…\w9\s[26]\n\n[half]"
                  r"橘花和斗和、以后请多多指教。\1\s[10]多指教啦。\w9\0\s[30]\n\n[half]…终于开口了。")

    def callback_set_weather_api(self, text):
        if text is None or text == '':
            return
        self.memory_write('WeatherKey', text)
        weather = self.get_weather()
        if weather is None:
            self.talk(r"\0好像设置失败了呢\e")
        else:
            self._weather = weather
            self.talk(r"\0设置成功\n\w9\s[5]%s现在是%s℃哦" % (
                self._weather['basic']['location'],
                self._weather['now']['tmp']
            ))

    def copy_wall_paper(self, n):
        def find_image(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    file = os.path.join(root, f)
                    if QImage().load(file):
                        return file
            return None

        if sys.platform != 'win32':
            self.talk(r'现在只支持复制windows系统呢')
            return

        wallpaper_path = os.path.join(os.path.expanduser('~'), 'AppData/Roaming/Microsoft/Windows/Themes/CachedFiles')
        if os.path.exists(wallpaper_path):
            w, h = kikka.helper.get_screen_resolution()
            file = os.path.join(wallpaper_path, "CachedImage_%d_%d_POS2.jpg" % (w, h))
            wallpaper_file = file if os.path.exists(file) else find_image(wallpaper_path)
        else:
            # muti screen
            wallpaper_path = os.path.dirname(wallpaper_path)
            file = os.path.join(wallpaper_path, "Transcoded_%03d" % n)
            wallpaper_file = file if os.path.exists(file) and QImage().load(file) else find_image(wallpaper_path)

        if wallpaper_file is None:
            self.talk(r"\0\s[8]好像失败了呢")
        else:
            clipboard = QApplication.clipboard()
            clipboard.setImage(QImage(wallpaper_file))
            self.talk(r"\0\s[5]壁纸%d已经复制到剪贴板了哦~" % n)
        pass

    def on_update(self, update_time):
        super().on_update(update_time)
        self.on_datetime()

    def get_shell_by_weather(self, weather):
        if weather is None:
            return []

        tmp = int(weather['now']['tmp'])
        if tmp <= 5:
            shell_list = ['_Default_1',
                          '_Default_2',
                          'normal-Winter',
                          'normal-RedDress',
                          'normal-NekoMimi',
                          'normal-Maid',
                          'normal-LongSkirt',
                          'normal-Halloween',
                          'normal-DogEar',
                          'normal-Christmas',
                          'cosplay-Momohime',
                          'cosplay-Maetel',
                          'cosplay-Accessories'
                          ]
        elif tmp <= 16:
            shell_list = ['_Default_1',
                          '_Default_2',
                          'private-Sweater',
                          'normal-Christmas',
                          'cosplay-Win7',
                          'cosplay-WhiteBase',
                          'cosplay-Taiwan',
                          'cosplay-SilverFox',
                          'cosplay-SetsukoOhara',
                          'cosplay-LeberechtMaass',
                          'cosplay-IzayoiSakuya',
                          'cosplay-InubashiriMomizi'
                          ]
        elif tmp <= 27:
            shell_list = ['_Default_1',
                          '_Default_2',
                          'private-Nurse',
                          'private-HadaY',
                          'private-BunnyGirl',
                          'normal-ZashikiChildren',
                          'normal-Yukata',
                          'cosplay-ZaregotoSeries',
                          'cosplay-SilverFox',
                          'cosplay-RemiliaScarlet',
                          'cosplay-KonpakuYoumu',
                          'cosplay-HatsuneMiku'
                          ]
        else:
            shell_list = ['private-PolkaDots',
                          'private-Lingerie1',
                          'private-Lingerie2',
                          'private-China',
                          'normal-Taisou',
                          'normal-Swimsuit',
                          'normal-SummerDress1',
                          'normal-SummerDress2',
                          'normal-SummerDress3',
                          'normal-Sleeveless',
                          'normal-PinkDress',
                          'normal-Camisole',
                          'normal-ARN-5041W'
                          ]
        return shell_list

    def on_datetime(self):
        if self.is_talking():
            return

        now = datetime.datetime.now()
        if self._datetime.minute != now.minute:
            script = ''
            if now.hour == 7 and now.minute == 30:
                script = r"\0\s[5]早晨%(hour)点%(minute)分了，\w4该吃早餐了哦。\e"
            elif now.hour == 12 and now.minute == 10:
                script = r"\0\s[5]已经%(hour)点%(minute)分了，\w4该吃午餐了哦。\e"
            elif now.hour == 18 and now.minute == 10:
                script = r"\0\s[5]已经%(hour)点%(minute)分了，\w4该吃晚餐了哦。\e"
            elif now.hour == 23 and now.minute == 30:
                script = r"\0\s[5]现在是%(hour)点%(minute)分，\w9\w4要不要考虑吃个宵夜呢。\e"
            elif now.minute == 0:
                weather = self.get_weather()
                if weather is not None:
                    self._weather = weather
                    shell_list = self.get_shell_by_weather(weather)
                    if self._shell.name not in shell_list:
                        shell_name = random.choice(shell_list)
                        if shell_name is not None:
                            self.change_shell(shell_name)

                if now.hour == 0:
                    script = r"\0凌晨12点了呢.又是新的一天～\e"
                elif 1 <= now.hour <= 4:
                    script = random.choice([
                        r"\0%(hour)点了.%(username)还不睡吗\e",
                        r"\0%(hour)点了.%(username)不睡吗？熬夜会变笨的喔\e"
                    ])
                elif now.hour in [5, 6]:
                    script = random.choice([
                        r"\0%(hour)点了..要去看日出吗\e",
                        r"\0呼哈～唔..%(hour)点了\e",
                    ])
                elif now.hour in [7, 8]:
                    script = random.choice([
                        r"\0%(hour)点了.还沒清醒的话赶快打起精神喔\e"
                    ])
                elif now.hour in [9, 10, 11]:
                    script = random.choice([
                        r"\0%(hour)点了..据说是人一天中记忆能力最好的時段呢，要好好利用喔\e"
                    ])
                elif now.hour == 12:
                    script = random.choice([
                        r"12点了.午餐时间～\e"
                    ])
                elif now.hour in [13, 14]:
                    script = random.choice([
                        r"\0下午%(hour12)点了…總是很想睡的时间呢\e"
                    ])
                elif now.hour in [15, 16]:
                    script = random.choice([
                        r"\0%(hour)点了.要不要來杯下午茶呢\e"
                    ])
                elif now.hour in [17, 18]:
                    script = random.choice([
                        r"\0下午%(hour12)点.晚餐时间～\e"
                    ])
                elif 19 <= now.hour <= 23:
                    script = random.choice([
                        r"\0%(hour)点了..接下來该做什么事呢\e",
                        r"\0晚上%(hour12)点了呢..%(username)在做什么呢\e",
                        r"\0晚上%(hour12)点了呢..这个时间%(username)应该都在电脑前吧\e"
                    ])

            self._datetime = now
            self.talk(script)
        pass  # exit if

    def get_phase(self):
        return 2

    def touch_talk(self, param):
        sid = param.soul_id
        phase = self.get_phase()

        if param.event_tag not in self._touch_count[sid].keys():
            self._touch_count[sid][param.event_tag] = 0

        # touch_talk[soul_id][event_type][event_tag][phase][touch_count]
        if sid in self._touch_talk.keys() \
                and param.event_type in self._touch_talk[sid].keys() \
                and param.event_tag in self._touch_talk[sid][param.event_type].keys():
            talks = self._touch_talk[sid]
            type_talks = talks[param.event_type]

            if phase not in type_talks.keys():
                phase = 0

            if len(type_talks[param.event_tag]) <= 0 and len(type_talks[param.event_tag][phase]) <= 0:
                return False

            count = self._touch_count[sid][param.event_tag] % len(type_talks[param.event_tag][phase])
            if len(type_talks[param.event_tag][phase][count]) <= 0:
                return False

            script = random.choice(type_talks[param.event_tag][phase][count])
            self._touch_count[sid][param.event_tag] += 1
            self.talk(script)
            return True
        return False

    def init_talk(self):
        # touch_talk[soul_id][event_type][event_tag][phase][touch_count]
        self._touch_talk = {
            KIKKA: {
                GhostEvent.Shell_MouseTouch: {
                    'Head': {0: {}, 1: {}, 2: {}},
                    'Face': {0: {}},
                    'Bust': {0: {}, 1: {}, 2: {}},
                    'Hand': {0: {}},
                },
                GhostEvent.Shell_MouseDoubleClick: {
                    'Head': {0: {}, 1: {}, 2: {}},
                    'Face': {0: {}, 1: {}, 2: {}},
                    'Bust': {0: {}, 1: {}, 2: {}},
                    'Hand': {0: {}, 1: {}, 2: {}},
                },
                GhostEvent.Shell_WheelEvent: {
                    'Hand': {0: {}, 1: {}},
                }
            },
            TOWA: {
                GhostEvent.Shell_MouseTouch: {
                    'Head': {0: {}},
                    'Tail': {0: {}},
                },
                GhostEvent.Shell_MouseDoubleClick: {
                    'Head': {0: {}},
                    'Tail': {0: {}},
                },
                GhostEvent.Shell_WheelEvent: {
                    'Head': {0: {}},
                    'Tail': {0: {}},
                },
            }
        }

        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][0][0] = [
            r"\0\s[1]怎、\w9\w5怎么了吗？\e",
            r"\0\s[2]呀…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[2]啊…\w9\w9\s[1]这个…\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][0][1] = [
            r"\0\s[9]…\w9…\w9…\e",
            r"\0\s[33]…哎呀…\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][1][0] = [
            r"\0\s[1]怎、\w9\w5怎么了吗？\e",
            r"\0\s[2]呀…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[2]啊…\w9\w9\s[1]这个…\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][1][1] = [
            r"\0\s[1]…\w9嗯？\e",
            r"\0\s[1]那个…\w9\s[1]这个…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][1][2] = [
            r"\0\s[1]%(username)…\e",
            r"\0\s[1]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][1][3] = [
            r"\0\s[29]…\w9谢谢。\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][1][4] = [
            r"\0\s[1]那个…\w9已经可以了…\e",
            r"\0\s[1]那个…\w9我没关系的…\e",
            r"\0\s[1]…\w9…\w9…\e",
            r"\0\s[1]唔…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][2][0] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\e",
            r"\0\s[26]…\w9…\w9…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[2]啊…\w9\w9\s[1]那个…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][2][1] = [
            r"\0\s[1]谢…\w9谢谢…\e",
            r"\0\s[1]%(username)…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][2][2] = [
            r"\0\s[29]…\w9…\w9…\e",
            r"\0\s[1]这个…\w9\w9我的头发、\w9怎么了吗？\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][2][3] = [
            r"\0\s[29]…\w9那个。\w9\w9\s[1]\n啊…\w9没事…\e",
            r"\0\s[1]那、\w9那个…\w9\w9\n我会害羞的。\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Head'][2][4] = [
            r"\0\s[29]嗯…\e",
            r"\0\s[1]…\w9…\w9…\e",
            r"\0\s[1]那个…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\w9\w9唔…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Face'][0][0] = [
            r"\0\s[6]嗯。\w9\w9\s[0]\n怎么了？\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Face'][0][1] = [
            r"\0\s[6]嗯？\w9\w9\s[20]\n那个、\w9我脸上有什么东西吗？\e",
            r"\0\s[6]唔嗯…\w9\w9\s[2]那个、\w9怎么了？\e",
            r"\0\s[21]好痒喔。\e",
            r"\0\s[6]唔…\w9\w9\s[2]\n…\w9…\w9…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Bust'][0][0] = [
            r"\0\s[35]…\w9…\w9…\1\s[12]你就这么喜欢摸女生胸部吗……\0\e",
            r"\0\s[35]唔…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[35]啊…\e",
            r"\0\s[35]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Bust'][1][0] = [
            r"\0\s[1]呃…\w9\w9那、那个？\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Bust'][1][1] = [
            r"\0\s[1]嗯…\w9\w9啊…\e",
            r"\0\s[1]那、\w9那个…\e",
            r"\0\s[1]那个…\w9那个…\e",
            r"\0\s[1]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Bust'][2][0] = [
            r"\0\s[1]耶…\w9\w9那、那个？\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Bust'][2][1] = [
            r"\0\s[1]嗯…\w9\w9啊…\e",
            r"\0\s[1]那、\w9那个…\e",
            r"\0\s[1]…\w9…\w9…\e",
            r"\0\s[1]那个…\w9那个…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Hand'][0][0] = [
            r"\0\s[0]…\w9…\w9…\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseTouch]['Hand'][0][1] = [
            r"\0\s[29]…\w9…\w9…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[29]啊…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Head'][0][0] = [
            r"\0\![raise,OnPlay,se_03.wav]\s[3]呜…\e",
            r"\0\![raise,OnPlay,se_03.wav]\s[3]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Head'][1][0] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[33]啊…\w9\w9\w9\s[3]\n真过分…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[33]啊…\w9\w9\w9\s[7]\n为什么…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Head'][2][0] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[33]啊…\w9\w9\w9\s[9]\n呜呜…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[33]啊…\w9\w9\w9\nもう、\w9\w5\s[9]请不要故意欺负我…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Face'][0][0] = [
            r"\0\![raise,OnPlay,se_03.wav]\s[3]呜…\e",
            r"\0\![raise,OnPlay,se_03.wav]\s[3]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Face'][1][0] = [
            r"\0\![raise,OnPlay,se_02.wav]\s[1]呀啊…\e",
            r"\0\![raise,OnPlay,se_02.wav]\s[3]好痛…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Face'][2][0] = [
            r"\0\![raise,OnPlay,se_02.wav]\s[33]咿呀…\w9\w9\s[1]\n这…\e",
            r"\0\![raise,OnPlay,se_02.wav]\s[33]呜嗯…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][0][0] = [
            r"\0\s[23]…\w9\w9你到底要干什么…\e",
            r"\0\s[23]\w9\w9找死！！！\w9\w9\e",
            r"\0\![raise,OnPlay,se_03.wav]\s[35]呜…\e",
            r"\0\![raise,OnPlay,se_03.wav]\s[35]…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][1][0] = [
            r"\0\![raise,OnPlay,se_04.wav]\s[4]那…\w9\w9\w9那个…\e",
            r"\0\![raise,OnPlay,se_04.wav]\s[2]咿呀…\w9\w9\s[1]\n…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][1][1] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\w9\w9\w9\s[9]不、\w9不行啦…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][1][2] = [
            r"\0\![raise,OnPlay,se_03.wav]\s[3]呜！\e",
            r"\0\![raise,OnPlay,se_03.wav]\s[3]呜…\w9好痛…\e",
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\w9\w9讨厌…\e",
            r"\0\s[6]哼…\e",
            r"\0\s[23]…\w9\w9你到底要干什么…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][2][0] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\w9\w9\w9那个…\e",
            r"\0\![raise,OnPlay,se_02.wav]\s[2]咿呀…\w9\w9\s[1]\n…\w9…\w9…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][2][1] = [
            r"\0\![raise,OnPlay,se_01.wav]\s[1]啊…\w9\w9\w9\s[9]不、\w9不可以…\e",
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Bust'][2][2] = [
            r"\0\![raise,OnPlay,se_03.wav]\0\s[3]呜！\e",
            r"\0\![raise,OnPlay,se_03.wav]\0\s[3]呜…\w9好痛…\e",
            r"\0\![raise,OnPlay,se_01.wav]\0\s[1]啊…\w9\w9讨厌…\e",
            r"\0\s[22]%(username)想吃枪子儿吗？\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Hand'][0][0] = [
            # keep empty for show main menu
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Hand'][1][0] = [
            r"\0\s[26]？\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_MouseDoubleClick]['Hand'][2][0] = [
            r"\0\![raise,OnPlay,se_04.wav]\s[2]哇…\w9\w9\s[1]\n这…\e",
            r"\0\![raise,OnPlay,se_04.wav]\s[2]哇…\w9\w9\s[29]\n…\w9…\w9…\e",
        ]

        # ############################################################
        self._touch_talk[KIKKA][GhostEvent.Shell_WheelEvent]['Hand'][0][0] = [
            r"\0\s[3]…\w9…\w9…\e"
        ]
        self._touch_talk[KIKKA][GhostEvent.Shell_WheelEvent]['Hand'][0][1] = [
            r"\0\s[29]…\w9…\w9…\e",
            r"\0\s[29]\![raise,OnPlay,se_05.wav]行きます\w9…",
            r"\0\s[26]要带橘花去哪呢？\e",
        ]

        # ############################################################
        self._touch_talk[TOWA][GhostEvent.Shell_MouseDoubleClick]['Head'][0][0] = [

        ]
        self._touch_talk[TOWA][GhostEvent.Shell_MouseDoubleClick]['Tail'][0][0] = [
            r"\1\s[12]…\w9…\w9…\w9\s[10]\e",
            r"\1\s[12]动物保护团体的那些家伙会生气喔。\e",
            r"\1\s[12]\![move,-100,,500,me]\e",
        ]
        self._touch_talk[TOWA][GhostEvent.Shell_MouseTouch]['Head'][0][0] = \
            self._touch_talk[TOWA][GhostEvent.Shell_WheelEvent]['Head'][0][0] = [
            r"\1\s[12]…\w9…\w9…\w9\s[10]\e",
            r"\1\s[10]呣…\e",
            r"\1\s[10]嗯～。\w9\w9\n算了、\w9随你高兴吧。\e",
            r"\1\s[10]呼噜呼噜…………",
        ]
        self._touch_talk[TOWA][GhostEvent.Shell_MouseTouch]['Tail'][0][0] = \
            self._touch_talk[TOWA][GhostEvent.Shell_WheelEvent]['Tail'][0][0] = [
            r"\1\s[10]啊啊啊…\w9\s[12]\n给我停下来！\e",
            r"\1\s[10]呜～。\e",
            r"\1\s[12]咕嘎啊啊～！\w9\w9\n不准碰！\e",
            r"\1\s[12]喵了个咪的，你不知道猫很不喜欢被人摸尾巴吗？",
        ]

    def say_hello(self):
        today = datetime.datetime.now()
        if 4 <= today.time().hour < 6:
            # Early morning
            talk = [
                r"\1\s[10]\0\s[0]啊…\w9\w9\s[40]早安、\w9%(username)。\w9\w9\1\s[10]…\w9…\w9…\w9\w9\w9\0\s[0]\n\n[half]这么早是怎么了呢？\x",
                r"\1\s[10]\0\s[0]啊…\w9\w9\s[40]早安、\w9%(username)。\w9\w9\1\s[10]…\w9…\w9…\w9\w9\w9\0\s[26]\n\n[half]今天很早呢。\x",
            ]
        elif 6 <= today.time().hour < 10:
            # Morning
            talk = [
                r"\1\s[10]\0\s[26]早安、\w9%(username)。\x",
                r"\1\s[10]\0\s[40]早安、\w9%(username)。\w9\w9\w9\w9\s[26]\n今天一天也好好加油吧。\x",
                r"\1\s[10]\0\s[26]%(username)、\w9早安。\w9\w9\1\s[10]哟。\x",
                r"\1\s[10]\0\s[40]早安。\w9\w9\1\s[10]哟。\x",
            ]
        elif 10 <= today.time().hour < 16:
            # Day
            if today.date().weekday() in [5, 6]:
                talk = [r"\0\s[26]早安。\w9\w9\n…\w9嗯、\w9\s[8]已经中午了喔。\w9\w9\1\s[10]反正是周末嘛。\w9\w9\n有好好休息吗？"]
            else:
                talk = [
                    r"\1\s[10]\0\s[2]啊。\w9\w9\s[40]\n午安、\w9%(username)。\x",
                    r"\1\s[10]\0\s[40]午安、\w9%(username)。\1\s[10]哟。\x",
                    r"\1\s[10]\0\s[26]%(username)、\w9午安。\x",
                    r"\1\s[10]\0\s[26]午安。\1\s[10]哟。\x",
                ]
        elif 16 <= today.time().hour < 18:
            # Evening
            talk = [
                r"\1\s[10]\0\s[26]欢迎回来、\w9\w9%(username)。\x",
                r"\1\s[10]\0\s[26]欢迎回来、\w9\w9%(username)。\w9\w9\n没有被跟踪吧？\w9\w9\1\s[10]…\w9…\w9…\x",
            ]
        elif 18 <= today.time().hour < 23:
            # Evening
            talk = [
                r"\1\s[10]\0\s[26]晚好、\w9%(username)。\x",
                r"\1\s[10]\0\s[0]晚上好、\w9%(username)。\x",
                r"\1\s[10]\0\s[26]晚上好。\x",
                r"\1\s[10]\0\s[0]晚上好。\x",
                r"\1\s[10]\0\s[26]%(username)、\w9\w9\晚上好。\x",
            ]
        elif 23 <= today.time().hour or today.time().hour < 4:
            # Midnight
            if today.date().weekday() in [5, 6]:
                talk = [r"\1\s[10]\0\s[0]啊、\w9\w9\w9\s[26]晚上好、\w9%(username)。\w9\w9\w9\w9\n就算是假日、\w9\n也不要太晚睡喔。\x"]
            else:
                talk = [
                    r"\1\s[10]\0\s[0]晚安、\w9%(username)。\w9\w9\w9\w9\s[26]\n这么晚是怎么了呢？\x",
                    r"\1\s[10]\0\s[0]晚安、\w9%(username)。\w9\w9\w9\w9\n半夜了呢。\x",
                ]
        else:
            talk = [""]
        return random.choice(talk)

    def get_auto_talk_interval(self):
        return 1000*60*10

    def get_auto_talk(self):
        auto_talk = [
            # kikka
            r"\0\s[6]充满鼻腔的生腥血味。\w9\w9\n赤红的水面。\w9\w9\w9\n\s[0]我最初的记忆。\e",

            # 食物
            r"\0\s[0]食用动物的肉会另动物比较痛苦，\w9\w9那么食用植物的茎和叶植物就没痛苦了吗？\w9\w9\w9\1\s[10]众生平等只是统制者掩人耳目的说法吧？\w9\w9\w9\0\s[23]\n所以要一起吃掉？\w9\w9\w9\1\s[10]\n……",
            r"\0\s[0]杀死家畜的时候、\w9\n必须注意要杀的没有痛苦。\w9\w9\1\s[10]怎么、\w9是想表现慈悲吗？\w9\w9\0\s[6]\n\n[half]不然、\w9味道会变差。\w9\w9\w9\1\s[13]\n\n[half]…\w9可恶的人类。\e",

            # 情感
            r"\0\s[0]%(username),\w9\w9这些日子以来,\w9\w9多谢你对橘花和斗和的照顾，\w9\w9\1\s[11]小公主，你说这话%(username)会误解哦\0\s[32]\n\n[half]不要插话。听我把话说完\w9\w9\1\s[12]\n\n[half]……\w9\w9\0\s[3]\n\n[half]橘花知道，\w9\w9长期的寄宿在%(username)家中，\w9\w9给%(username)带来了很多麻烦，\w9\w9橘花不想因为自己的关系，\w9\w9给%(username)造成困绕\w9\w9\1\s[12]\n\n[half]小公主，\w9\w9你到底想要说什么……\w9\w9\0\s[1]\n\n[half]橘花希望，\w9\w9能陪%(username)度过快乐的每一天，\w9\w9但是，\w9\w9橘花心中也有些隐隐不安，\w9\w9觉得，\w9觉得有一天我会和%(username)分开\w9\w9\1\s[10]\n\n[half]小公主，\w9你是不是多虑了？\w9\w9\0\s[7]\n\n[half]世上没有不散的宴席，\w9\w9也许有一天，\w9\w9%(username)对我们的热情减退，\w9\w9就不再理我们了\w9\w9\1\n\n[half]唉，你什么时候变得多愁善感起来了。\e",
            r"\0\s[6]『想要谈像电视剧般的恋爱』\w9\s[0]说这种话的、\w9\n算是、分不清现实和虚构…\w9\w5\s[20]\n是这样吗？\w9\w9\1\s[10]电视剧般的恋爱？\w9\n现实也做得到吧。\w9\w9\0\s[2]\n\n[half]可以做到吗？\w9\w9\1\s[10]\n\n[half]该付的付的起的话。\w9\w9\0\s[8]\n\n[half]…\w9…\w9…\e",
            r"\0\s[6]虽然现在有家庭主夫的想法、\w9\s[0]\n我觉得家事\w5应该还是由母亲来做。\w9\w9\1\s[10]还真是意外的保守啊。\w9\w9\0\s[7]\n\n[half]有些东西不想让父亲来洗不是吗。\w9\w9\1\s[13]\n\n[half]呜～哇…\e",

            # 宗教
            r"\0\s[6]地球是蓝的。\w9\w9\n而且、\w9在这天空下并没有上帝。\e",

            # 军事
            r"\0\s[6]请把毒刺飞弹拿过来。\w9\1\s[10]啊？\w9\w9\0\s[0]\n\n[half]要击落。\w9\1\s[10]\n\n[half]击落什么啊？\e",
            r"\0\s[0]不可以随便握住门把。\w9\1\s[10]啊？\w9\w9\0\s[0]\n\n[half]不知道会被装上什么机关喔。\w9\w9\1\s[10]\n\n[half]…\w9…\w9…\e",
            r"\0\s[0]不管累积了多少训练\w9\s[6]\n面对轰炸都是无能为力的。\w9\w9\n\s[3]真难受…\w9\w9\1\s[10]你到底做过什么…\e",
            r"\0\s[0]买了新的工具、\w9\s[26]\n就算用不到也会很想用用看呢。\w9\w9\1\s[10]可能吧。\w9\w9\0\s[0]\n\n[half]新兵器也会很想用用看吧？\w9\w9\1\s[13]\n\n[half]啊…\e",
            r"\0\s[26]话说回来、%(username)喜欢怎么样的铁丝网设计呢？\w9\w9\1\s[10]突然、在问什么啊…\e",
            r"\0\s[26]在外面用餐的时候、\w9\n请尽量不要坐靠窗的位置喔。\w9\w9\1\s[10]…\w9…\w9…\w9\w9\0\s[0]\n\n[half]窗外或许会有爆炸也说不定。\w9\w9\w9\1\s[13]\n\n[half]希望这个玩笑题材、\w9\n能永远只是个玩笑啊…\e",
            r"\0\s[0]在看不见狙击手的情况下、\w9绝对不可以回应射击。\w9\w9\1\s[10]…\w9…\w9…\w9\w9\0\s[6]\n\n[half]首先、趴下、\w9\n之后、\w9请由声音来判断狙击手的位置。\w9\w9\s[26]\n\n[half]等移动到觉得安全的场所、\w9\n再来考虑对策也不会太迟。\w9\w9\1\s[13]\n\n[half]…\w9真是一辈子都不想派上用场的知识啊。\e",
            r"\0\s[6]敌人、\w5在寻找同调者。\w9\w9\n敌人、\w5企图衰弱我们的防卫力。\w9\w9\n敌人、\w5想让我们沉眠。\w9\w9\n敌人、\w5威胁着我们。\w9\w9\n敌人、\w5企图衰弱我们的经济力。\w9\w9\1\s[10]我们、\w9永远感谢自己的祖国、\w9\n以及享有自由。\w9\w9\n国家的独立、\w9我们国民人人有责。\w9\w9\0\s[30]\n\n[half]…\w9\e",
            r"\0\s[26]啊、\w9我稍微离席一下喔。\w9\w9\s[99]\w9\w9\1\s[10]…\w9…\w9…\w9\w9\0\s[26]\n\n[half]好了、\w9让您久等了。\w9\w9\1\s[10]\n\n[half]怎么、\w9厕所吗？\w9\w9\0\s[7]\n\n[half]才不是。\w9\w9\n…\w9还有那些话、\w9请说的有气质一点。\w9\w9\1\n\n[half]好啦…\w9\w9\0\s[6]\n\n[half]『去埋地雷吗？』\w9\w9像这样说。\w9\w9\1\n…\w9气质？\e",
            r"\1\s[10]虽然战争是没了…\w9\w9\n弱肉强食算和平吗？\e",
            r"\0\s[0]要用空手杀人时、\w9身体的哪部位是弱点\n必须牢牢记在心里。\w9\w9\1\s[10]别记啊。\w9\w9\0\s[0]\n\n[half]不过、\w9若情况允许请尽量使用道具。\w9\1\s[10]\n\n[half]好好听人说话。\e",
            r"\0\s[10]要讨厌人的话、\w9\n就要做好同样程度的觉悟。\w9\w9\w9\0\s[21]想进行大逃杀(Battle Royale)。\w9\1\s[10]\n\n[half]你一个人玩吧。\w9\0\s[7]\n\n[half]玩不起来啊。\e",
            r"\0\s[0]就算狙击胸前的口袋、\w9\n也打不中心脏喔。\w9\w9\s[26]\n\n[half]要再往左下一点才行。\w9\w9\1\s[10]你想让人做什么啊…\e",

            # 社会
            r"\0\s[0]刚开始被欺负时、\w9\n不对的是欺负人的那边…\w9\1\s[10]喔、\w9这样啊？\w9\w9\0\s[30]\n\n[half]是的。\w9\w9\s[0]\n不过、\w9之所以继续被欺负、\w9\n是被欺负的那边不对。\w9\w9\n因为没有努力去让自己不再被欺负。\w9\w9\1\s[10]\n\n[half]也不是谁都有办法的。\w9\w9\w9\0\s[0]\n\n[half]能满足于现状的话\n倒是没有什么关系。\e",
            r"\0\s[0]经常见到、\w5\n凶杀案被害者的家人\w5在怨恨诅咒凶手…\w9\w9\1\s[10]唔、\w5这没什么不对吧？\w9\w9\0\s[0]\n\n[half]责怪自己没能保护好家人的人、\w5\n不太见的到呢。\w9\e",
            r"\0\s[0]觉悟到死亡的人、\w9\n理解力会变的优秀。\w9\w9\s[6]\n\n[half]既然接受了最糟糕的事态、\w9\n能判断该如何行动就变的很重要。\w9\w9\w9\1\s[10]真稀奇\w9你也会说正经话啊。\w9\w9\0\s[0]\n\n[half]…\w9\s[32]你的发言、\w9是已经觉悟到死亡了吗？\e",
            r"\1\s[10]不管动物爱护法再怎么修正、\w9\n法律上、动物还是算『物』吧。\w9\w9\0\s[6]用了『爱护』这字眼就表示\w9\n不是对等的呢。\w9\w9\1\s[10]\n\n[half]等用了『保护』的话就表示已经快绝种了吧…\e",
            r"\0\s[0]生命的价值、\w9\w9和金钱一样、\w9\n是会随着时代而改变的。 \w9\w9\1\s[10]也会随地点而改变吧、\w5果然。\e",
            r"\0\s[0]人类、\w9\w5必然有死亡的时刻。\w9\w9\n\n[half]只是、\w9\s[6]到此之前的时间\w9是长…\w9还是短…\w9\w9\s[0]\n\n[half]如此而已。\e",
            r"\1\s[10]非要去找出他人的缺点…\w9\n来确认自己比较优秀\w9\n不这样做就无法安心吗？\w9\w9\0\s[8]在对谁说话啊？\e",
            r"\1\s[10]所谓历史、\w9是人类的血汇集成的河。\w9\w9\w9\n正义与心理…\w9\n不过是被那条河所附加的名词。\w9\w9\w5\0\s[0]所谓『正义必胜』\w9、\w9\n只是胜利的人、\w9\n自称为正义而已。\e",

            # 应急逃生
            r"\0\s[26]虽然问的很突然、\w9\w9\s[0]\n%(username)有手电筒吗？\w9\w9\n万一的时候很有用的、\w9\n如果没有\n去买一个如何呢？\w9\w9\1\s[10]还有、\w5收音机和打火机也是。\w9\w9\n就算不吸烟\n带着打火机也不会没用喔。",
            r"\0\s[26]如果说%(username)、\w9\n是住在公寓的二楼之类高的地方的话、\w9\w9\s[0]\n准备好坚固的绳子\w9\n万一的时候或许会有用。\w9\w9\1\s[10]然后、因为被谁发现的话可能会被误解…\w9。\w9\w9\s[12]\n要好好藏起来啊。\w9\w9\0\s[8]\n\n[half]如果紧急时不能马上拿出来用\w5那就没有意义了…\e"
        ]
        return random.choice(auto_talk)
