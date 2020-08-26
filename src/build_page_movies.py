import gc
import os
import sys

import util as u
import video_util as vu
from moviepy.editor import CompositeVideoClip, ImageClip

config = u.load_config()
consts = u.load_consts()
timekeeper = u.load_timekeeper()


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
            vu.write_raw_video(page['movie_path'], video_clip, config.get('low_quarity_intermediate_video_file', False))
            video_clip = None
            gc.collect()


if __name__ == '__main__':
    main(int(sys.argv[1]))
