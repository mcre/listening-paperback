import glob
import json
import os

from moviepy.editor import afx, vfx, AudioClip, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, concatenate_audioclips

with open('consts.json', 'r') as f:
    consts = json.load(f)
with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)

def write_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')

def silence_clip(duration):
    return AudioClip(lambda t: 2*[0], duration=duration)

def generate_voice_clip(voices, video_clip_duration):
    voice_clips = []
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_duration(clip.duration - 0.05) # 後ろに雑音が入ることがあるのでちょっと削る
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip
    #return concatenate_audioclips([voice_clip, silence_clip(video_clip_duration - voice_clip.duration)]) # 動画と音声の長さが違うと雑音になるっぽいので無音で埋めておく

def main():
    os.makedirs('chapter_movies', exist_ok=True)

    cft = consts['cross_fade_time']
    ci = consts['chapter_interval'] / 2
    for chapter in timekeeper['chapters']:
        first_page = chapter['pages'][0]
        last_page = chapter['pages'][-1]
        video_clips = [ImageClip(first_page['image_path']).set_duration(first_page['start'])] # 最初一瞬真っ黒になるのを防ぐ
        for page in chapter['pages']:
            clip = VideoFileClip(page['movie_path']).set_start(page['start'])
            video_clips.append(clip)
            if page['page_id'] > 0: # 1ページ目の入り以外はクロスフェードインする
                clip = ImageClip(page['image_path']).set_start(page['start'] - cft).set_duration(cft).crossfadein(cft)
                video_clips.append(clip)
        video_clip = CompositeVideoClip(video_clips)
        video_clip = video_clip.set_audio(generate_voice_clip(chapter['voices'], video_clip.duration))
        video_clip = concatenate_videoclips([ # 前後に chapter_interval 分の静止画を挟んでおく
            ImageClip(first_page['image_path']).set_duration(ci).set_audio(silence_clip(ci)),
            video_clip,
            ImageClip(last_page['words'][-1]['animation_image_path']).set_duration(ci).set_audio(silence_clip(ci)), # 無音を入れないと雑音がはいる
        ])
        write_video(chapter['movie_path'], video_clip)

if __name__ == '__main__':
    main()
