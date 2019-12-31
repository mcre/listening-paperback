from moviepy.editor import AudioClip


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def write_video(path, video_clip, fps=30, bitrate=None, audio_bitrate='384k'):
    video_clip.write_videofile(path, codec='libx264', fps=fps, bitrate=bitrate, audio_codec='libfdk_aac', audio_bitrate=audio_bitrate)


def write_raw_video(path, video_clip):
    video_clip.write_videofile(path, codec='utvideo', fps=30, audio_codec='pcm_s32le')
