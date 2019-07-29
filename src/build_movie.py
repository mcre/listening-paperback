import glob
import json

from moviepy.editor import afx, vfx, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip

with open('consts.json', 'r') as f:
    consts = json.load(f)

def main():
    with open(f'pagefeeds.json', 'r') as f:
        pagefeeds = json.load(f)

    video_clips = []
    pages = sorted(glob.glob('pages/novel*.png'))
    for i, page in enumerate(pages):
        cft = consts['cross_fade_time']
        pf = pagefeeds[i]
        clip = ImageClip(page).set_start(pf['start']).set_duration(pf['duration'])
        if i == 0: #start
            it = consts['start_voice_interval']
            clip = clip.set_start(clip.start - it).set_duration(it + clip.duration + cft).crossfadeout(cft)
        elif i == len(pages) - 1: # end
            clip = clip.set_duration(clip.duration + cft).crossfadein(cft)
        else:
            clip = clip.set_duration(clip.duration + cft * 2).crossfadein(cft).crossfadeout(cft)

        video_clips.append(clip)
    video_clip = CompositeVideoClip(video_clips, bg_color=(255, 255, 255))

    voice_clips = []
    s = consts['start_voice_interval']
    for voice in sorted(glob.glob('voices/*.mp3')):
        clip = AudioFileClip(voice)
        clip = clip.set_start(s)
        voice_clips.append(clip)
        s += clip.duration + consts['voice_interval']
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
