import glob
import json

from moviepy.editor import afx, vfx, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip

with open('consts.json', 'r') as f:
    consts = json.load(f)

def main():
    with open(f'pagefeeds.json', 'r') as f:
        pagefeeds = json.load(f)
    with open(f'voice_durations.json', 'r') as f:
        voice_durations = json.load(f)

    video_clips = []
    pages = sorted(glob.glob('pages/novel*.png'))
    for i, page in enumerate(pages):
        cft = consts['cross_fade_time']
        pf = pagefeeds[i]
        clip = ImageClip(page).set_start(pf['start']).set_duration(pf['duration'])
        if i == 0: #start
            clip = clip.set_start(0).set_duration(pf['start'] + clip.duration + cft).crossfadeout(cft)
        elif i == len(pages) - 1: # end
            clip = clip.set_duration(clip.duration + cft).crossfadein(cft)
        else:
            clip = clip.set_duration(clip.duration + cft * 2).crossfadein(cft).crossfadeout(cft)

        video_clips.append(clip)
    video_clip = CompositeVideoClip(video_clips, bg_color=(255, 255, 255))

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
        .audio_loop(duration=video_clip.duration) \
        .audio_fadeout(duration=consts['music_fadeout_time']) \
        .volumex(consts['music_volume'])

    audio_clip = CompositeAudioClip([voice_clip, music_clip])

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile('novel.mp4', fps=30, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')

if __name__ == '__main__':
    main()
