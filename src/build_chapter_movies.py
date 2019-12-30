import gc
import os
import sys

import util as u
import video_util as vu
from moviepy.editor import (AudioFileClip, CompositeAudioClip,
                            CompositeVideoClip, ImageClip, VideoFileClip,
                            concatenate_videoclips)

consts = u.load_consts()
timekeeper = u.load_timekeeper()


def generate_voice_clip(voices, video_clip_duration):
    voice_clips = [vu.silence_clip(video_clip_duration)]  # 無音を重ねないと雑音が入ることがある
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip


def main(part_id):
    os.makedirs('chapter_movies', exist_ok=True)

    cft = consts['cross_fade_time']
    ci = consts['chapter_interval'] / 2
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
        vu.write_raw_video('tmp.avi', video_clip_tmp)  # メモリ不足回避のため一旦ファイル化する

        # おそうじ
        clip, video_clips, video_clip_tmp = None, None, None
        gc.collect()
        for page in chapter['pages']:
            os.remove(page['movie_path'])

        video_clip = VideoFileClip('tmp.avi')
        video_clip = video_clip.set_audio(generate_voice_clip(chapter['voices'], video_clip.duration))

        # 前後に chapter_interval 分の静止画を挟んでおく
        first_clip = ImageClip(first_page['image_path']).set_duration(ci).set_audio(vu.silence_clip(ci))
        if len(last_page['words']) == 0:  # 最後が空ページの場合
            last_clip = ImageClip(last_page['image_path']).set_duration(ci).set_audio(vu.silence_clip(ci))
        else:
            last_clip = ImageClip(last_page['words'][-1]['animation_image_path']).set_duration(ci).set_audio(vu.silence_clip(ci))  # 無音を入れないと雑音がはいる
        video_clip = concatenate_videoclips([first_clip, video_clip, last_clip])
        vu.write_raw_video(chapter['movie_path'], video_clip)
        os.remove('tmp.avi')


if __name__ == '__main__':
    main(int(sys.argv[1]))
