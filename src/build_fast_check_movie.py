import os
import subprocess

import mutagen.mp3
import numpy as np
import video_util as vu
from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, concatenate_videoclips

import util as u


consts = u.load_consts()
timekeeper = u.load_timekeeper()

FPS = 10


def generate_voice_clip(voices, video_clip_duration):
    voice_clips = [vu.silence_clip(video_clip_duration)]  # 無音を重ねないと雑音が入ることがある
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip


def main():
    os.makedirs('fast_check_movie_tmp', exist_ok=True)

    for_concat_movies = []

    vopath = 'voices/title.mp3'
    title_video_clip = ImageClip(np.zeros((360, 640))).set_fps(FPS).set_duration(mutagen.mp3.MP3(vopath).info.length)
    title_video_clip = title_video_clip.set_audio(AudioFileClip(vopath))
    path = 'fast_check_movie_tmp/title.mp4'
    vu.write_video(path, title_video_clip, fps=FPS, bitrate='16k', audio_bitrate='32k')
    for_concat_movies.append(f'file {path}\n')

    for part in timekeeper['parts']:
        chapter_video_clips = []
        for chapter in part['chapters']:
            page_video_clips = []
            for page in chapter['pages']:
                page_video_clips.append(ImageClip(page['image_path'].replace('page_images', 'page_images_mini')).set_fps(FPS).set_start(page['start']).set_duration(page['duration']))
            chapter_video_clip = CompositeVideoClip(page_video_clips)
            chapter_video_clip = chapter_video_clip.set_audio(generate_voice_clip(chapter['voices'], chapter_video_clip.duration))
            chapter_video_clips.append(chapter_video_clip)
        path_tmp = f'fast_check_movie_tmp/{part["part_id"]:0>5}_tmp.mp4'
        path = f'fast_check_movie_tmp/{part["part_id"]:0>5}.mp4'
        vu.write_video(path_tmp, concatenate_videoclips(chapter_video_clips), fps=FPS, bitrate='16k', audio_bitrate='32k')
        subprocess.call(f'ffmpeg -y -i {path_tmp} -vf setpts=PTS/2.5 -af atempo=2.5 {path}', shell=True)
        for_concat_movies.append(f'file {path}\n')
    with open('concat_fast_check_movie_list.txt', 'w') as f:
        f.writelines(for_concat_movies)
    subprocess.call('ffmpeg -f concat -i concat_fast_check_movie_list.txt -c copy fast_check_movie.mp4', shell=True)


if __name__ == '__main__':
    main()
