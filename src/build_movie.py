import glob
import json
import os

from moviepy.editor import afx, vfx, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip, VideoFileClip

with open('consts.json', 'r') as f:
    consts = json.load(f)
with open(f'pagefeeds.json', 'r') as f:
    pagefeeds = json.load(f)
with open(f'voice_durations.json', 'r') as f:
    voice_durations = json.load(f)

def write_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')

def generate_audio_clip(video_duration):
    voice_clips = []
    s = consts['start_voice_interval']
    voice_num = len(glob.glob('voices/*.mp3'))
    for i in range(voice_num):
        clip = AudioFileClip(f'voices/{i:0>5}.mp3')
        clip = clip.set_duration(clip.duration - 0.05) # 後ろに雑音が入ることがあるのでちょっと削る
        clip = clip.set_start(s)
        voice_clips.append(clip)
        s += voice_durations[i] + consts['voice_interval'] # clip.durationは若干精度が悪く、ページ切り替えはmutagen基準なので、mutagenの長さに合わせる
    voice_clip = CompositeAudioClip(voice_clips)

    music_clip = AudioFileClip('music.mp3') \
        .audio_loop(duration=video_duration) \
        .audio_fadeout(duration=consts['music_fadeout_time']) \
        .volumex(consts['music_volume'])

    return CompositeAudioClip([voice_clip, music_clip])

def generate_page_movie(page_id, page_path):
    pf = pagefeeds[page_id]
    st = pf['start']
    video_clips = [ImageClip(page_path).set_duration(pf['duration_to_next_page_start'])]
    for word_id, word in enumerate(pf['words']):
        # next_word_durationを足さないと次のwordのフェードインがちらつく
        clip = ImageClip(f'animation_images/novel_{page_id:0>5}_{word_id:0>5}-1.png') \
            .set_start(word['start'] - st) \
            .set_duration(word['duration_to_next_word_start'] + word['next_word_duration']) \
            .crossfadein(word['duration'])
        video_clips.append(clip)
    video_clip = CompositeVideoClip(video_clips)
    write_video(f'page_movies/{page_id:0>5}.mp4', video_clip)

    if page_id == 0:
        cover_clip = video_clips[0].set_duration(st)
        write_video('page_movies/cover.mp4', cover_clip)

def main():
    os.makedirs('page_movies', exist_ok=True)
    pages = sorted(glob.glob('pages/novel*.png'))
    pages_num = len(pages)
    for page_id in range(pages_num):
        generate_page_movie(page_id, pages[page_id])

    cft = consts['cross_fade_time']
    video_clips = [VideoFileClip('page_movies/cover.mp4')]
    # to_ImageClip
    for page_id in range(pages_num):
        pf = pagefeeds[page_id]
        st = pf['start']
        clip = VideoFileClip(f'page_movies/{page_id:0>5}.mp4').set_start(st)
        video_clips.append(clip)
        if page_id > 0: # start 以外はクロスフェードインする
            clip = ImageClip(pages[page_id]) \
                .set_start(st - cft).set_duration(cft).crossfadein(cft)
            video_clips.append(clip)
        if page_id < pages_num - 1: # end 以外はクロスフェードアウトする
            word_id = len(pf['words']) - 1
            clip = ImageClip(f'animation_images/novel_{page_id:0>5}_{word_id:0>5}-1.png') \
                .set_start(st + clip.duration).set_duration(cft).crossfadeout(cft)
            video_clips.append(clip)
            
    video_clip = CompositeVideoClip(video_clips)
    video_clip = video_clip.set_audio(generate_audio_clip(video_clip.duration))
    write_video('novel.mp4', video_clip)

if __name__ == '__main__':
    main()
