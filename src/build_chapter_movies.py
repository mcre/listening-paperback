import gc
import os
import sys

import util as u
import video_util as vu
from moviepy.editor import (AudioFileClip, CompositeAudioClip,
                            CompositeVideoClip, ImageClip, VideoFileClip,
                            concatenate_videoclips)

config = u.load_config()
consts = u.load_consts()
timekeeper = u.load_timekeeper()


def generate_voice_clip(voices, video_clip_duration):
    voice_clips = [vu.silence_clip(video_clip_duration)]  # 無音を重ねないと雑音が入ることがある
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_duration(clip.duration - 0.05)  # 後ろに雑音が入ることがあるのでちょっと削る
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip


def main(part_id):
    os.makedirs('chapter_movies', exist_ok=True)

    cft = consts['cross_fade_time']
    ci = config['chapter_interval'] / 2 if 'chapter_interval' in config else consts['chapter_interval'] / 2
    chapters = timekeeper['parts'][part_id]['chapters']
    for chapter in chapters:
        first_page = chapter['pages'][0]
        last_page = chapter['pages'][-1]
        video_clips = [ImageClip(first_page['image_path']).set_duration(first_page['start'])]  # 最初一瞬真っ黒になるのを防ぐ
        for page in chapter['pages']:
            clip = VideoFileClip(page['movie_path']).set_start(page['start'])
            video_clips.append(clip)
            if page['page_id'] > 0:  # 1ページ目の入り以外はクロスフェードインする
                clip = ImageClip(page['image_path']).set_start(page['start'] - cft).set_duration(cft).crossfadein(cft)
                video_clips.append(clip)
        video_clip_tmp = CompositeVideoClip(video_clips)
        vu.write_raw_video('tmp.avi', video_clip_tmp, config.get('low_quarity_intermediate_video_file', False))  # メモリ不足回避のため一旦ファイル化する

        # おそうじ
        clip, video_clips, video_clip_tmp = None, None, None
        gc.collect()
        for page in chapter['pages']:
            os.remove(page['movie_path'])

        video_clip = VideoFileClip('tmp.avi')
        video_clip = video_clip.set_audio(generate_voice_clip(chapter['voices'], video_clip.duration))

        # 前後に chapter_interval 分の静止画を挟んでおく
        for i in range(10):
            ci_offset = ci + i / 100  # ci が特定の値の場合にwrite_raw_videoが落ちる場合があるため、その場合は数値を少し変えて書き出し直す
            first_clip = ImageClip(first_page['image_path']).set_duration(ci_offset).set_audio(vu.silence_clip(ci_offset))
            if len(last_page['words']) == 0:  # 最後が空ページの場合
                last_clip = ImageClip(last_page['image_path']).set_duration(ci_offset).set_audio(vu.silence_clip(ci_offset))
            else:
                last_clip = ImageClip(last_page['words'][-1]['animation_image_path']).set_duration(ci_offset).set_audio(vu.silence_clip(ci_offset))  # 無音を入れないと雑音がはいる
            write_video_clip = concatenate_videoclips([first_clip, video_clip, last_clip])
            try:
                vu.write_raw_video(chapter['movie_path'], write_video_clip, config.get('low_quarity_intermediate_video_file', False))
            except IndexError:
                continue
            break
        os.remove('tmp.avi')


if __name__ == '__main__':
    main(int(sys.argv[1]))
