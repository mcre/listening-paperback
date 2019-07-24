import glob

from moviepy.editor import afx, vfx, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip


FADE_TIME = 0.15
START_VOICE_INTERVAL = 2
VOICE_INTERVAL = 1
MUSIC_VOLUME = 0.1

def main():
    voice_clips = []
    s = START_VOICE_INTERVAL
    for voice in sorted(glob.glob('voices/*.mp3')):
        clip = AudioFileClip(voice)
        clip = clip.set_start(s)
        voice_clips.append(clip)
        s += clip.duration + VOICE_INTERVAL
    voice_clip = CompositeAudioClip(voice_clips)

    video_clips = []
    for i, page in enumerate(sorted(glob.glob('pages/novel*.png'))):
        duration = 1
        clip = ImageClip(page).set_start(i * (duration - FADE_TIME)).set_duration(duration).crossfadein(FADE_TIME).crossfadeout(FADE_TIME)
        video_clips.append(clip)
    video_clip = CompositeVideoClip(video_clips, bg_color=(255, 255, 255))

    music_clip = AudioFileClip('music.mp3')\
        .audio_loop(duration=video_clip.duration)\
        .audio_fadeout(duration=5)

    audio_clip = CompositeAudioClip([voice_clip, music_clip.fx(afx.volumex, MUSIC_VOLUME)])

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile('novel.avi', fps=30, codec='libx264')

if __name__ == '__main__':
    main()
