import json
import os
import sys

from moviepy.editor import AudioClip, CompositeAudioClip, ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, concatenate_audioclips

with open('consts.json', 'r') as f:
    consts = json.load(f)
with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def write_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')


def hex_to_rgb(hex):
    return tuple(int(hex[i: i + 2], 16) for i in range(0, 6, 2))


cft = consts['cross_fade_time']
ci = consts['chapter_interval'] / 2
vi = consts['voice_interval']
bg = hex_to_rgb(consts['background_color'])
end_adj_time = 0.1  # エンドカードをくっつけるときに原因不明で「clips[i].get_frame(t - tt[i]) list index out of range」が出るのを回避するために適当に足す


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def build_cover_clip(part_id):
    audio_clip = concatenate_audioclips([
        silence_clip(ci),
        AudioFileClip('voices/channel.mp3'), silence_clip(vi),
        AudioFileClip('voices/title.mp3'), silence_clip(vi),
        AudioFileClip(f'voices/part{part_id:0>5}.mp3'),
        silence_clip(ci),
    ])
    clip = ImageClip(f'cover_images/{part_id:0>5}.png') \
        .set_duration(audio_clip.duration) \
        .fadeout(cft, bg) \
        .set_audio(audio_clip)
    return clip


def build_end_clip(kind):
    audio_clip = concatenate_audioclips([
        silence_clip(ci),
        AudioFileClip(f'voices/{kind}.mp3'), silence_clip(vi),
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
    video_clips = [build_cover_clip(part_id)]
    for chapter in part['chapters']:
        video_clips.append(VideoFileClip(chapter['movie_path']).fadein(cft, bg).fadeout(cft, bg))
    video_clips.append(build_end_clip('next' if part_id < len(parts) - 1 else 'end'))
    video_clip = concatenate_videoclips(video_clips)
    music_clip = AudioFileClip('music.mp3') \
        .audio_loop(duration=video_clip.duration) \
        .audio_fadeout(duration=consts['music_fadeout_time']) \
        .volumex(consts['music_volume'])
    audio_clip = CompositeAudioClip([video_clip.audio, music_clip])
    video_clip = video_clip.set_audio(audio_clip)
    write_video(f'part_movies/{part_id:0>5}/movie.mp4', video_clip)


if __name__ == '__main__':
    main(int(sys.argv[1]))
