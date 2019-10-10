# cp ./src/* ./work/ && docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_voice_movie.py"
import gc
import json
import os
import subprocess

from moviepy.editor import AudioClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ImageClip

BLANK = 0.1
FPS = 4

with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def write_video(path, video_clip):
    video_clip.write_videofile(path, fps=6, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')


def main():
    os.makedirs('voice_movie_tmp', exist_ok=True)
    with open(f'timekeeper.json', 'r') as f:
        timekeeper = json.load(f)

    already = set()
    for_concat_movies = []
    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                page_clip = ImageClip(page['image_path']).set_fps(FPS)
                for word in page['words']:
                    tv = f"{word['original_text']}{word['viseme']}"
                    if tv in already:  # textもvisemeも一致したものは再度作らない
                        continue
                    already.add(tv)
                    if word['includes_kanji'] and len(word['original_text']) >= 2:
                        d = word['duration']
                        fname = f"{chapter['chapter_id']:0>5}_{page['page_id']:0>5}_{word['word_id']:0>5}.png"
                        voice_id_clip = ImageClip(f'voice_text_images/voice_{word["voice_id"]:0>5}.png').set_fps(FPS).set_duration(d).set_pos((10, 10))
                        text_clip = ImageClip(f'voice_text_images/text_{fname}').set_fps(FPS).set_duration(d).set_pos(('center', 'center'))
                        viseme_clip = ImageClip(f'voice_text_images/viseme_{fname}').set_fps(FPS).set_duration(d).set_pos(('center', 230))
                        clip = CompositeVideoClip([page_clip.set_duration(d), text_clip, viseme_clip, voice_id_clip])
                        voice_path = chapter['voices'][str(word['voice_id'])]['voice_path']
                        audio_clip = AudioFileClip(voice_path)
                        st = word['start_in_voice']
                        en = min(word['start_in_voice'] + d, audio_clip.duration)
                        audio_clip = audio_clip.subclip(st, en)
                        clip = clip.set_audio(audio_clip)
                        s_clip = page_clip.set_duration(BLANK).set_audio(silence_clip(BLANK))
                        clip = concatenate_videoclips([clip, s_clip])
                        path = f'voice_movie_tmp/{chapter["chapter_id"]:0>5}_{page["page_id"]:0>5}_{word["word_id"]:0>5}.mp4'
                        write_video(path, clip)
                        for_concat_movies.append(f'file {path}\n')
                    clip, audio_clip, text_clip, s_clip = None, None, None, None
                    gc.collect()

    with open('concat_voice_movie_list.txt', 'w') as f:
        f.writelines(for_concat_movies)

    subprocess.call('ffmpeg -f concat -i concat_voice_movie_list.txt -c copy voice_movie.mp4', shell=True)


if __name__ == '__main__':
    main()
