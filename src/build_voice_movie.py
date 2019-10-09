# cp ./src/* ./work/ && docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_voice_movie.py"
import gc
import json
import os

from moviepy.editor import AudioClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ImageClip, VideoFileClip

BLANK = 0.1
FPS = 4

with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def write_video(path, video_clip):
    video_clip.write_videofile(path, fps=6, codec='libx264', audio_bitrate='128k')


def main():
    os.makedirs('voice_movie_tmp', exist_ok=True)
    with open(f'timekeeper.json', 'r') as f:
        timekeeper = json.load(f)

    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                page_clip = ImageClip(page['image_path']).set_fps(FPS)
                for word in page['words']:
                    if word['includes_kanji'] and len(word['original_text']) >= 2:
                        text_path = word['animation_image_path'].replace('animation_images', 'voice_text_images')
                        text_clip = ImageClip(text_path).set_fps(FPS).set_duration(word['duration']).set_pos(lambda t: ('center', 'center'))
                        clip = CompositeVideoClip([page_clip.set_duration(word['duration']), text_clip])
                        voice_path = chapter['voices'][str(word['voice_id'])]['voice_path']
                        audio_clip = AudioFileClip(voice_path)
                        st = word['start_in_voice']
                        en = min(word['start_in_voice'] + word['duration'], audio_clip.duration)
                        audio_clip = audio_clip.subclip(st, en)
                        clip = clip.set_audio(audio_clip)
                        s_clip = page_clip.set_duration(BLANK).set_audio(silence_clip(BLANK))
                        clip = concatenate_videoclips([clip, s_clip])
                        path = f'voice_movie_tmp/{chapter["chapter_id"]:0>5}_{page["page_id"]:0>5}_{word["word_id"]:0>5}.mp4'
                        write_video(path, clip)

                        clip, audio_clip, text_clip, s_clip = None, None, None, None
                        gc.collect()

    clip, audio_clip, text_clip, s_clip, page_clip = None, None, None, None, None
    gc.collect()

    tmp_videos = []
    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                clips = []
                gc.collect()
                for word in page['words']:
                    if word['includes_kanji'] and len(word['original_text']) >= 2:
                        vc = VideoFileClip(f'voice_movie_tmp/{chapter["chapter_id"]:0>5}_{page["page_id"]:0>5}_{word["word_id"]:0>5}.mp4')
                        clips.append(vc)
                if len(clips) == 0:
                    continue
                path = f'voice_movie_tmp/{chapter["chapter_id"]:0>5}_{page["page_id"]:0>5}.mp4'
                write_video(path, concatenate_videoclips(clips))
                tmp_videos.append(path)

    clips, vc = None, None
    gc.collect()

    clips = [VideoFileClip(v) for v in tmp_videos]
    clip = concatenate_videoclips(clips)
    write_video('voice_movie.mp4', clip)


if __name__ == '__main__':
    main()
