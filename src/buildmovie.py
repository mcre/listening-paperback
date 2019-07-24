import glob

from moviepy.editor import concatenate_videoclips, afx, vfx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip

def main():
    video_clips = []
    for page in sorted(glob.glob('pages/novel*.png')):
        video_clips.append(ImageClip(page).set_duration(1))
    video_clip = concatenate_videoclips(video_clips, method='compose')

    music = AudioFileClip('music.mp3')
    music = afx.audio_loop(music, duration=video_clip.duration)
    music = afx.audio_fadeout(music, duration=5)
    video_clip = video_clip.set_audio(music)

    video_clip.write_videofile('novel.avi', fps=30, codec='libx264')

if __name__ == '__main__':
    main()
