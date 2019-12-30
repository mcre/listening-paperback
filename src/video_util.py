from moviepy.editor import AudioClip


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def write_video(path, video_clip, fps=30):
    video_clip.write_videofile(path, fps=fps, codec='libx264', audio_codec='libfdk_aac', audio_bitrate='384k')


def write_raw_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='utvideo', audio_codec='pcm_s32le')
