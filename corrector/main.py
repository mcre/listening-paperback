import glob
import json
import os
import threading
import time

import kivy.app
import kivy.config
import kivy.core.audio
import kivy.lang
import kivy.properties
import kivy.uix.button
import kivy.uix.popup
import kivy.uix.treeview
import kivy.uix.widget

from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty

import util as u

kivy.lang.Builder.load_file('root.kv')
kivy.config.Config.set('graphics', 'width', '1440')
kivy.config.Config.set('graphics', 'height', '900')


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
        print(f'init {self.__class__.__name__} ...')
        super().__init__(**kwargs)

    def init(self):
        pass


class RootWidget(W):
    markers_widget = ObjectProperty(None)
    pages_widget = ObjectProperty(None)
    voice_widget = ObjectProperty(None)
    controller_widget = ObjectProperty(None)
    ime_widget = ObjectProperty(None)
    texts_widget = ObjectProperty(None)
    ruby_widget = ObjectProperty(None)
    sentences_widget = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        with open('work/config.json') as f:
            settings = json.load(f)
            self.project_name = settings.get('project_name', None) or f"{settings['author']}/{settings['title']}"
            kivy.app.App.get_running_app().title = self.project_name

    def reload(self):
        self.init()
        self.markers_widget.init()
        self.pages_widget.init()
        self.voice_widget.init()
        self.controller_widget.init()
        self.ime_widget.init()
        self.texts_widget.init()
        self.ruby_widget.init()
        self.sentences_widget.init()


class ImagesViewerWidget(W):
    image = ObjectProperty(None)
    image_path = StringProperty(None)
    image_darker = BooleanProperty(False)
    label = StringProperty('')
    button_disabled_prev = BooleanProperty(False)
    button_disabled_next = BooleanProperty(False)
    sub_image_path = StringProperty(None)
    enable_sub = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.images = None
        self.cursor = 0
        self.darks = []

    def set_images(self, images):
        self.images = images
        self.update_image()

    def update_image(self):
        self.button_disabled_prev, self.button_disabled_next = False, False
        if self.cursor <= 0:
            self.cursor = 0
            self.button_disabled_prev = True
        if self.cursor >= len(self.images) - 1:
            self.cursor = len(self.images) - 1
            self.button_disabled_next = True
        self.label = f'{self.cursor + 1} / {len(self.images)}'
        if len(self.darks) > 0:
            self.label += f'   ({len(self.darks)})'
        self.image_path = self.images[self.cursor]
        self.image_darker = self.image_path in self.darks
        if self.enable_sub:
            self.sub_image_path = self.images[self.cursor + 1] if self.cursor + 1 < len(self.images) else ''

    def on_button(self, count):
        self.cursor += count
        self.update_image()

    def jump(self, image_id):
        self.cursor = image_id
        self.update_image()


class MarkersWidget(ImagesViewerWidget):
    __darks_path = 'corrector/markers/darks.json'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.set_images(sorted(glob.glob('corrector/markers/*[!json]')))
        if os.path.exists(self.__darks_path):
            with open(self.__darks_path) as f:
                self.darks = json.load(f)
            self.update_image()

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.image.collide_point(*touch.pos):
            if touch.is_double_tap:
                p = self.image_path
                if p not in self.darks:
                    self.darks.append(p)
                else:
                    self.darks.remove(p)
                self.update_image()
                with open(self.__darks_path, 'w') as f:
                    json.dump(self.darks, f, ensure_ascii=False, indent=4)


class PagesWidget(ImagesViewerWidget):
    def __init__(self, **kwargs):
        super(PagesWidget, self).__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        self.enable_sub = True
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


class SWTreeViewLabel(kivy.uix.treeview.TreeViewLabel):
    def on_label_touch_down(self, text):
        root().sentences_widget.on_select(text)


class SentencesWidget(W):
    tv_all = ObjectProperty(None)
    tv_new = ObjectProperty(None)
    new_count = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        with open(f'work/sentences.json') as f:
            self.sentences = json.load(f)
        with open(f'work/polly_tasks.json') as f:
            tasks = json.load(f)
        tasks = [task['name'] for task in tasks if task['format'] == 'json']
        self.new_count = len(tasks)

        for sentence in self.sentences:
            with open(f'work/marks/{sentence["filename"]}.json') as f:
                marks = json.load(f)
            marks = [{'text': u.remove_tag(mark['value']), 'time': mark['time'] / 1000} for mark in marks if mark['type'] == 'word']

            st_hist = []
            cursor = 0
            for mark in marks:
                st = {'cursor': sentence['plain'].find(mark['text'], cursor), 'time': mark['time']}
                st_hist.append(st)
                cursor = st['cursor'] + len(mark['text'])

            times_by_cursor = {}
            for vid, st in enumerate(st_hist):
                en = st_hist[vid + 1]['cursor'] if vid < len(st_hist) - 1 else len(sentence['plain'])
                for cursor in range(st['cursor'], en):
                    times_by_cursor[cursor] = st['time']
            sentence['times_by_cursor'] = times_by_cursor
            sentence['morphemes'] = [{'range': range(m['start'], m['end']), 'el': m['el']} for m in sentence['morphemes']]

        def init_worker():
            while True:
                if self.tv_all is not None:
                    for node in self.tv_all.children:
                        self.tv_all.remove_node(node)
                    for s in self.sentences:
                        self.tv_all.add_node(SWTreeViewLabel(text=f"{s['id']}:{s['plain'][:10]}"))
                    break
                time.sleep(0.1)
            while True:
                if self.tv_new is not None:
                    for node in self.tv_new.children:
                        self.tv_new.remove_node(node)
                    for s in self.sentences:
                        if s['filename'] in tasks:
                            self.tv_new.add_node(SWTreeViewLabel(text=f"{s['id']}:{s['plain'][:10]}"))
                    self.tv_new.deselect_node()
                    break
                time.sleep(0.1)
        threading.Thread(target=init_worker).start()

    def on_select(self, text):
        vid = int(text.split(':')[0])
        root().pages_widget.jump_by_voice_id(vid)
        root().texts_widget.show(self.sentences[vid])
        root().voice_widget.set_voice(f"work/voices/{self.sentences[vid]['filename']}.mp3")


class TextsWidget(W):
    plain_text_box = ObjectProperty(None)
    ssml_box = ObjectProperty(None)
    tab = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        super().init()
        if self.plain_text_box:
            self.plain_text_box.text = ''
        if self.ssml_box:
            self.ssml_box.text = ''
        self.touch_text_box = False
        self.times_by_cursor = None
        self.morphemes = None

    def show(self, texts):
        self.times_by_cursor = texts['times_by_cursor']
        self.plain_text_box.text = texts['plain']
        self.plain_text_box.cursor = (0, 0)
        self.plain_text_box.cancel_selection()
        self.morphemes = texts['morphemes']
        self.ssml_box.text = texts['ssml']
        self.ssml_box.cursor = (0, 0)
        self.ssml_box.cancel_selection()

    def find(self, prev=False):
        box = self.tab.current_tab.content
        f = box.selection_from or -1
        q = root().ime_widget.text
        if q == '':
            return
        if prev:
            index = box.text.rfind(q, 0, f)
        else:
            index = box.text.find(q, f + 1)
        if index == -1:
            box.cancel_selection()
            self.on_touch_up_box(0, 0, '', force=True)
        else:
            f, t = index, index + len(q)
            box.select_text(f, t)
            self.on_touch_up_box(f, t, q, force=True)

    def on_find_prev_button(self):
        self.find(prev=True)

    def on_find_next_button(self):
        self.find()

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.touch_text_box = True

    def on_touch_up_box(self, selection_from, selection_to, text, force=False):
        if force or (self.touch_text_box and selection_from is not None and selection_to is not None):
            f, t = min(selection_from, selection_to), max(selection_from, selection_to)
            if self.times_by_cursor:
                vw = root().voice_widget
                if f in self.times_by_cursor:
                    sec = self.times_by_cursor[f]
                else:
                    sec = vw.voice.length
                if vw.voice:
                    vw.voice.seek(sec)
                    vw.update_slider(sec)
            if self.morphemes:
                els = []
                st = None
                for m in self.morphemes:
                    for r in range(f, t):
                        if r in m['range']:
                            els.append(m['el'])
                            st = st if st is not None else m['range'][0]
                            break
                rw = root().ruby_widget
                if len(els) > 0:
                    rw.target = {
                        'kanji': text,
                        'ruby': '',
                        'offset_from_first_morpheme': f - st,
                        'morphemes': els
                    }
                else:
                    rw.target = None
                rw.update_ruby()
        self.touch_text_box = False


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
        print(f'load start: {file_path}')
        self.voice = kivy.core.audio.SoundLoader.load(file_path)
        print(f'load end: {file_path}')
        self.slider_max = self.voice.length
        self.voice.on_play = self.__on_play
        self.voice.on_stop = self.__on_stop
        self.update_slider()
        self.__update_button_text()

    def update_slider(self, value=None):
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
                self.update_slider()
                time.sleep(0.1)
        threading.Thread(target=playing_worker).start()

    def __on_stop(self):
        if self.voice.length - self.voice.get_pos() < 0.5:
            self.voice.seek(0)
        self.update_slider(0)
        self.__update_button_text()

    def __seek(self, seconds):
        if self.voice:
            p = self.voice.get_pos() + seconds
            if p > self.voice.length:
                p = self.voice.length
            elif p < 0:
                p = 0
            self.voice.seek(p)
            self.update_slider(p)

    def on_play_button(self):
        if self.voice:
            if self.voice.state == 'stop':
                print('voice play')
                self.voice.play()
            else:
                self.voice.stop()
            self.update_slider()
            self.__update_button_text()

    def on_stop_button(self):
        if self.voice:
            self.voice.stop()
            self.voice.seek(0)
            self.update_slider()
            self.__update_button_text()

    def on_back_button(self):
        self.__seek(-5)

    def on_forward_button(self):
        self.__seek(5)

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.touch_slider = True

    def on_touch_up_slider(self, value):
        if self.voice and self.touch_slider:
            self.voice.seek(value)
        self.touch_slider = False


class RWTreeViewLabel(kivy.uix.treeview.TreeViewLabel):
    pass


class RWPopup(kivy.uix.popup.Popup):
    text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = kwargs['text']


class RubyWidget(W):
    ruby_text_box = ObjectProperty(None)
    disable_buttons = BooleanProperty(True)
    disable_mekabu_yomi_button = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        self.target = None
        self.ruby = ''
        self.ruby_obj = None
        self.disable_buttons = True
        self.disable_mekabu_yomi_button = True
        self.update_ruby()

    def update_ruby(self):
        self.ruby = root().ime_widget.text if root() else ''
        if self.ruby_text_box is None:
            return

        dis = True
        dis_m = True
        if self.target is not None:
            tg = self.target
            tg['ruby'] = self.ruby
            self.ruby_obj = tg
            self.ruby_text_box.text = json.dumps(tg, ensure_ascii=False, indent=4)
            self.ruby_text_box.cursor = (0, 0)
            if len(self.ruby) > 0:
                dis = False
            if len(self.ruby_obj['morphemes']) == 1:
                dis_m = False
        else:
            self.ruby_obj = None
            self.ruby_text_box.text = ''
        self.disable_buttons = dis
        self.disable_mekabu_yomi_button = dis_m

    def on_append_ruby_button(self, file_type, ruby_type, message_text):
        if file_type == 'consts':
            file_name = 'src/consts.json'
        elif file_type == 'config':
            file_name = f'projects/{root().project_name}/config.json'

        with open(file_name) as f:
            settings = json.load(f)
        if ruby_type == 'primary':
            if 'primary_special_rubies' not in settings:
                settings['primary_special_rubies'] = []
            settings['primary_special_rubies'].append(self.ruby_obj)
        elif ruby_type == 'normal':
            settings['special_rubies'].append(self.ruby_obj)
        elif ruby_type == 'mekabu_yomi':
            settings['use_mecab_yomi_rubies'].append(self.ruby_obj['morphemes'][0])

        with open(file_name, 'w') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

        if ruby_type == 'mekabu_yomi':
            detail = f'{self.ruby_obj["kanji"]}'
        else:
            detail = f'{self.ruby_obj["kanji"]} -> {self.ruby_obj["ruby"]}'
        RWPopup(text=f'{message_text}\n\n{detail}\n{file_name}').open()


class CWPopup(kivy.uix.popup.Popup):
    pop = ObjectProperty(None)
    log = StringProperty()
    executing = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        self.log = ''
        self.executing = True
        self.sound = None

        def init_worker():
            self.sound = kivy.core.audio.SoundLoader.load('./corrector/done.mp3')
            self.batch = u.Batch(f'./batch_first_timekeeper.sh {root().project_name}')
            for line in self.batch.start():
                print(line)
                self.log += line
            self.sound.play()
            self.executing = False
            self.batch = None
            root().sentences_widget.init()
        threading.Thread(target=init_worker).start()

    def on_button(self):
        if self.batch:
            self.batch.terminate()
        if self.sound:
            self.sound.unload()
        self.pop.dismiss()


class ControllerWidget(W):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def on_batch_button(self):
        CWPopup().open()

    def on_refresh_button(self):
        root().reload()


class IWPopup(kivy.uix.popup.Popup):
    pop = ObjectProperty(None)
    tv = ObjectProperty(None)

    def on_enter(self, romaji):
        if len(romaji) > 0:
            ls = u.kkc(romaji.strip(), 20)
            for node in self.tv.children:
                self.tv.remove_node(node)
            for s in ls:
                self.tv.add_node(kivy.uix.treeview.TreeViewLabel(text=s))
            self.tv.deselect_node()

    def on_button(self):
        if self.tv.selected_node:
            text = self.tv.selected_node.text
        else:
            text = ''
        root().ime_widget.text = text
        root().ruby_widget.update_ruby()
        self.pop.dismiss()


class ImeWidget(W):
    text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init()

    def init(self):
        self.text = ''

    def on_button(self):
        IWPopup().open()


if __name__ == '__main__':
    MainApp().run()
