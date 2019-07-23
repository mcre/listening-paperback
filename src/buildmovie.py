from moviepy.editor import concatenate_videoclips
from moviepy.video.VideoClip import ImageClip

def main():
    clips = []
    for i in range(1, 10):
        clips.append(ImageClip(f'pages/novel-{i:0>2}.png').set_duration(1))
    clip = concatenate_videoclips(clips)
    clip.write_videofile("novel.mp4", fps=30)

if __name__ == '__main__':
    main()
