import gc
import json
import os
import sys

from moviepy.editor import CompositeVideoClip, ImageClip

with open('consts.json', 'r') as f:
    consts = json.load(f)
with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def write_raw_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='utvideo', audio_codec='pcm_s32le')


def main(part_id):
    os.makedirs('page_movies', exist_ok=True)

    chapters = timekeeper['parts'][part_id]['chapters']
    for chapter in chapters:
        for page in chapter['pages']:
            print(f'\npart_id: {part_id}, chapter_id: {chapter["chapter_id"]} / [{", ".join([str(c["chapter_id"]) for c in chapters])}], page_id: {page["page_id"]} / {len(chapter["pages"]) - 1}\n')
            video_clips = [ImageClip(page['image_path']).set_duration(page['duration'])]
            for word in page['words']:
                # next_word_durationを足さないと次のwordのフェードインがちらつく
                clip = ImageClip(word['animation_image_path']) \
                    .set_start(word['start'] - page['start']) \
                    .set_duration(word['duration_to_next_word_start'] + word['next_word_duration']) \
                    .crossfadein(word['duration'] * 0.5)  # durationそのままにすると、色の変化が声に対して若干遅く感じるので調整する
                video_clips.append(clip)
                clip = None
                gc.collect()
            video_clip = CompositeVideoClip(video_clips)
            write_raw_video(page['movie_path'], video_clip)
            video_clip = None
            gc.collect()


if __name__ == '__main__':
    main(int(sys.argv[1]))
