import glob

from moviepy.editor import afx, vfx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ImageClip

fade_time = 0.15

def main():
    video_clips = []
    for i, page in enumerate(sorted(glob.glob('pages/novel*.png'))):
        duration = 1
        clip = ImageClip(page).set_start(i * (duration - fade_time)).set_duration(duration).crossfadein(fade_time).crossfadeout(fade_time)
        video_clips.append(clip)
    video_clip = CompositeVideoClip(video_clips, bg_color=(255, 255, 255))

    music = AudioFileClip('music.mp3')
    music = afx.audio_loop(music, duration=video_clip.duration)
    music = afx.audio_fadeout(music, duration=5)
    video_clip = video_clip.set_audio(music)

    video_clip.write_videofile('novel.avi', fps=30, codec='libx264')

if __name__ == '__main__':
    main()
