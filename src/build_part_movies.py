import json
import os

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


def divide_parts():
    parts = []
    part, duration = [], 0
    for chapter in timekeeper['chapters']:
        part.append(chapter)
        duration += chapter['duration']
        if duration > consts['part_duration']:
            parts.append(part)
            part, duration = [], 0
    if len(part) > 0:
        parts.append(part)
    # 最後のパートが min_part_durationにも達していない場合はその前に足し込む
    if len(parts) <= 1:  # 1個しかないときは戻る
        return parts
    last_part_duration = sum(x['duration'] for x in parts[-1])
    if last_part_duration < consts['min_part_duration']:
        parts[-2].extend(parts[-1])
        del parts[-1]
    return parts


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
        .set_duration(audio_clip.duration) \
        .fadein(cft, bg).set_audio(audio_clip)
    return clip


def main():
    os.makedirs('part_movies', exist_ok=True)
    parts = divide_parts()

    for part_id, part in enumerate(parts):
        video_clips = [build_cover_clip(part_id)]
        for chapter in part:
            video_clips.append(VideoFileClip(chapter['movie_path']).fadein(cft, bg).fadeout(cft, bg))
        video_clips.append(build_end_clip('next' if part_id < len(parts) - 1 else 'end'))
        video_clip = concatenate_videoclips(video_clips)
        music_clip = AudioFileClip('music.mp3') \
            .audio_loop(duration=video_clip.duration) \
            .audio_fadeout(duration=consts['music_fadeout_time']) \
            .volumex(consts['music_volume'])
        audio_clip = CompositeAudioClip([video_clip.audio, music_clip])
        video_clip = video_clip.set_audio(audio_clip)
        write_video(f'part_movies/{part_id:0>5}.mp4', video_clip)


if __name__ == '__main__':
    main()
