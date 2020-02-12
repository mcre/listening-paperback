import glob
import json
import re
import threading
import time

import japanize_kivy
import kivy.app
import kivy.config
import kivy.core.audio
import kivy.lang
import kivy.properties
import kivy.uix.button
import kivy.uix.treeview
import kivy.uix.widget

from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty

print(japanize_kivy)
kivy.lang.Builder.load_file('root.kv')
kivy.config.Config.set('graphics', 'width', '1280')
kivy.config.Config.set('graphics', 'height', '720')


def root():
    return kivy.app.App.get_running_app().root


class MainApp(kivy.app.App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Corrector'

    def build(self):
        self.root = RootWidget()
        return self.root


class W(kivy.uix.widget.Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init(self):
        pass


class RootWidget(W):
    markers_widget = ObjectProperty(None)
    pages_widget = ObjectProperty(None)
    voice_widget = ObjectProperty(None)
    controller_widget = ObjectProperty(None)
    texts_widget = ObjectProperty(None)
    sentences_widget = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def reload(self):
        self.markers_widget.init()
        self.pages_widget.init()
        self.voice_widget.init()
        self.controller_widget.init()
        self.texts_widget.init()
        self.sentences_widget.init()


class ImagesViewerWidget(W):
    image_path = StringProperty(None)
    label = StringProperty('')
    button_disabled_prev = BooleanProperty(False)
    button_disabled_next = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.images = None
        self.cursor = 0

    def set_images(self, images):
        self.images = images
        self.__update_image()

    def __update_image(self):
        self.button_disabled_prev, self.button_disabled_next = False, False
        if self.cursor <= 0:
            self.cursor = 0
            self.button_disabled_prev = True
        if self.cursor >= len(self.images) - 1:
            self.cursor = len(self.images) - 1
            self.button_disabled_next = True
        self.label = f'{self.cursor + 1} / {len(self.images)}'
        self.image_path = self.images[self.cursor]

    def on_press_prev_button(self):
        self.cursor -= 1
        self.__update_image()

    def on_press_next_button(self):
        self.cursor += 1
        self.__update_image()

    def jump(self, image_id):
        self.cursor = image_id
        self.__update_image()


class MarkersWidget(ImagesViewerWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.set_images(sorted(glob.glob('corrector/markers/*')))


class PagesWidget(ImagesViewerWidget):
    def __init__(self, **kwargs):
        super(PagesWidget, self).__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.set_images(sorted(glob.glob('work/page_images/novel-*.png')))
        self.__create_voice_id_page_map()

    def __create_voice_id_page_map(self):
        with open(f'work/timekeeper.json', 'r') as f:
            timekeeper = json.load(f)
        pages = []
        for part in timekeeper['parts']:
            for chapter in part['chapters']:
                for page in chapter['pages']:
                    voice_ids = [word['voice_id'] for word in page['words']]
                    pages.append({
                        'serial_page_id': page['serial_page_id'],
                        'voice_id_list': list(range(min(voice_ids), max(voice_ids) + 1)),
                    })
        self.voice_id_page_map = {}
        for i in range(pages[-1]['voice_id_list'][-1] + 1):
            for page in pages:
                if i in page['voice_id_list']:
                    self.voice_id_page_map[i] = page['serial_page_id']
                    break

    def jump_by_voice_id(self, voice_id):
        self.jump(self.voice_id_page_map[voice_id])


class SentencesWidget(W):
    tv = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.sentenses = None

        def init_worker():
            tag = re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>''')
            sentences = []
            for sentences_file in sorted(glob.glob(f'work/ssml/*.xml')):
                with open(sentences_file) as f:
                    ssml = f.readlines()[7].strip()
                    fn = sentences_file[10:-4]
                    if fn.startswith('text'):
                        name = str(int(fn[4:]))
                    sentences.append({
                        'name': name,
                        'voice_file_path': f'work/voices/{fn}.mp3',
                        'ssml': ssml,
                        'plain_text': tag.sub('', ssml),
                    })
            self.sentences = sentences
            while True:
                if self.tv is not None:
                    for node in self.tv.children:
                        self.tv.remove_node(node)
                    for s in sentences:
                        self.tv.add_node(kivy.uix.treeview.TreeViewLabel(text=f"{s['name']}:{s['plain_text'][:20]}"))
                    self.tv.deselect_node()
                    break
                time.sleep(0.1)
        threading.Thread(target=init_worker).start()

    def selected_voice_id(self):
        for node_id_inv, node in enumerate(self.tv.children):
            if self.tv.selected_node == node:
                return len(self.tv.children) - node_id_inv - 1

    def on_select(self):
        vid = self.selected_voice_id()
        root().pages_widget.jump_by_voice_id(vid)
        root().texts_widget.show(self.sentences[vid])
        root().voice_widget.set_voice(self.sentences[vid]['voice_file_path'])


class TextsWidget(W):
    plain_text_box = ObjectProperty(None)
    ssml_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        if self.plain_text_box:
            self.plain_text_box.text = ''
        if self.ssml_box:
            self.ssml_box.text = ''

    def show(self, texts):
        self.plain_text_box.text = texts['plain_text']
        self.plain_text_box.cursor = (0, 0)
        self.ssml_box.text = texts['ssml']
        self.ssml_box.cursor = (0, 0)


class VoiceWidget(W):
    play_button_text = StringProperty()
    slider_max = NumericProperty()
    slider_value = NumericProperty()
    voice = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        if self.voice:
            self.voice.stop()
        self.voice = None
        self.touch_slider = False
        self.slider_max = 0
        self.slider_value = 0
        self.play_button_text = '▷'

    def set_voice(self, file_path):
        if self.voice:
            self.voice.stop()
        self.voice = kivy.core.audio.SoundLoader.load(file_path)
        self.slider_max = self.voice.length
        self.voice.on_play = self.__on_play
        self.voice.on_stop = self.__on_stop
        self.__update_slider()
        self.__update_button_text()

    def __update_slider(self, value=None):
        if self.touch_slider:
            return
        if value:
            self.slider_value = value
        else:
            self.slider_value = self.voice.get_pos()

    def __update_button_text(self):
        if self.voice.state == 'play':
            self.play_button_text = 'Ⅱ'
        else:
            self.play_button_text = '▷'

    def __on_play(self):
        def playing_worker():
            while self.voice and self.voice.state == 'play':
                self.__update_slider()
                time.sleep(0.1)
        threading.Thread(target=playing_worker).start()

    def __on_stop(self):
        if self.voice.length - self.voice.get_pos() < 0.5:
            self.voice.seek(0)
        self.__update_slider(0)
        self.__update_button_text()

    def __seek(self, seconds):
        if self.voice:
            p = self.voice.get_pos() + seconds
            if p > self.voice.length:
                p = self.voice.length
            elif p < 0:
                p = 0
            self.voice.seek(p)
            self.__update_slider(p)

    def on_press_play_button(self):
        if self.voice:
            if self.voice.state == 'stop':
                self.voice.play()
            else:
                self.voice.stop()
            self.__update_slider()
            self.__update_button_text()

    def on_press_stop_button(self):
        if self.voice:
            self.voice.stop()
            self.voice.seek(0)
            self.__update_slider()
            self.__update_button_text()

    def on_press_back_button(self):
        self.__seek(-5)

    def on_press_forward_button(self):
        self.__seek(5)

    def on_touch_down_slider(self):
        self.touch_slider = True

    def on_touch_up_slider(self, value):
        if self.voice and self.touch_slider:
            self.voice.seek(value)
        self.touch_slider = False


class ControllerWidget(W):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def on_press_forward_button(self):
        root().reload()


if __name__ == '__main__':
    MainApp().run()
