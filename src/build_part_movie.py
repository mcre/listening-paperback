import os
import sys

import util as u
import video_util as vu
from moviepy.editor import (AudioFileClip, CompositeAudioClip, ImageClip,
                            VideoFileClip, concatenate_audioclips,
                            concatenate_videoclips)

config = u.load_config()
consts = u.load_consts()
timekeeper = u.load_timekeeper()


cft = consts['cross_fade_time']
ci = config['chapter_interval'] / 2 if 'chapter_interval' in config else consts['chapter_interval'] / 2
vi = consts['voice_interval']
bg = u.hex_to_rgb(consts['background_color'])
end_adj_time = 0.1  # エンドカードをくっつけるときに原因不明で「clips[i].get_frame(t - tt[i]) list index out of range」が出るのを回避するために適当に足す


def build_cover_clip(part_id, parts_len):
    audio_clips = [
        vu.silence_clip(ci),
        AudioFileClip('voices/channel.mp3'), vu.silence_clip(vi),
        AudioFileClip('voices/title.mp3'), vu.silence_clip(vi),
    ]
    if parts_len > 1:
        audio_clips.append(AudioFileClip(f'voices/part{part_id:0>5}.mp3'))
    audio_clips.append(vu.silence_clip(ci))

    audio_clip = concatenate_audioclips(audio_clips)
    clip = ImageClip(f'cover_images/{part_id:0>5}.png') \
        .set_duration(audio_clip.duration) \
        .fadeout(cft, bg) \
        .set_audio(audio_clip)
    return clip


def build_end_clip(kind):
    audio_clip = concatenate_audioclips([
        vu.silence_clip(ci),
        AudioFileClip(f'voices/{kind}.mp3'), vu.silence_clip(vi),
        AudioFileClip('voices/please.mp3'),
    ])
    clip = ImageClip(f'cover_images/{kind}.png') \
        .set_duration(audio_clip.duration + end_adj_time) \
        .fadein(cft, bg).set_audio(audio_clip)
    return clip


def main(part_id):
    os.makedirs('part_movies', exist_ok=True)

    parts = timekeeper['parts']
    part = parts[part_id]

    os.makedirs(f'part_movies/{part_id:0>5}', exist_ok=True)
    video_clips = [build_cover_clip(part_id, len(parts))]
    for chapter in part['chapters']:
        video_clips.append(VideoFileClip(chapter['movie_path']).fadein(cft, bg).fadeout(cft, bg))
    video_clips.append(build_end_clip('next' if part_id < len(parts) - 1 else 'end'))
    video_clip = concatenate_videoclips(video_clips)

    if 'music' in config:
        music_clip = AudioFileClip('music.mp3') \
            .audio_loop(duration=video_clip.duration) \
            .audio_fadeout(duration=consts['music_fadeout_time']) \
            .volumex(consts['music_volume'])
        audio_clip = CompositeAudioClip([video_clip.audio, music_clip])
    else:
        audio_clip = CompositeAudioClip([video_clip.audio])
    video_clip = video_clip.set_audio(audio_clip)
    vu.write_video(f'part_movies/{part_id:0>5}/movie.mp4', video_clip)


if __name__ == '__main__':
    main(int(sys.argv[1]))
