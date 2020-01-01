import os
import subprocess

import util as u
import video_util as vu
from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, concatenate_videoclips

consts = u.load_consts()
timekeeper = u.load_timekeeper()

FPS = 10


def generate_voice_clip(voices, video_clip_duration):
    voice_clips = [vu.silence_clip(video_clip_duration)]  # 無音を重ねないと雑音が入ることがある
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_duration(clip.duration - 0.05)  # 後ろに雑音が入ることがあるのでちょっと削る
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip


def main():
    part_video_clips = []
    for part in timekeeper['parts']:
        chapter_video_clips = []
        for chapter in part['chapters']:
            page_video_clips = []
            for page in chapter['pages']:
                page_video_clips.append(ImageClip(page['image_path'].replace('page_images', 'page_images_mini')).set_fps(FPS).set_start(page['start']).set_duration(page['duration']))
            chapter_video_clip = CompositeVideoClip(page_video_clips)
            chapter_video_clip = chapter_video_clip.set_audio(generate_voice_clip(chapter['voices'], chapter_video_clip.duration))
            chapter_video_clips.append(chapter_video_clip)
        part_video_clips.append(concatenate_videoclips(chapter_video_clips))
    vu.write_video(f'fast_check_movie_tmp.mp4', concatenate_videoclips(part_video_clips), fps=FPS, bitrate='16k', audio_bitrate='32k')
    subprocess.call('ffmpeg -y -i fast_check_movie_tmp.mp4 -vf setpts=PTS/2.5 -af atempo=2.5 fast_check_movie.mp4', shell=True)
    os.remove('fast_check_movie_tmp.mp4')


if __name__ == '__main__':
    main()
