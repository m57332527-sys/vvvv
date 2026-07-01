import os
import sys
import numpy as np
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def analyze_audio_for_hooks(audio_path, clip_duration=55, sample_interval_ms=1000):
    """
    Scans the audio track using RMS amplitude tracking to find the highest energy section.
    """
    audio = AudioSegment.from_wav(audio_path)
    duration_ms = len(audio)
    clip_ms = clip_duration * 1000
    
    if duration_ms <= clip_ms:
        return 0, duration_ms / 1000

    max_energy = -1
    best_start_ms = 0

    # Slide window across audio timeline
    for start_ms in range(0, duration_ms - clip_ms, sample_interval_ms):
        window = audio[start_ms:start_ms + clip_ms]
        if window.rms > max_energy:
            max_energy = window.rms
            best_start_ms = start_ms

    return best_start_ms / 1000, (best_start_ms + clip_ms) / 1000

def process_video_pipeline(video_source_path, output_dir="public/clips"):
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"short_{int(np.random.rand()*100000)}.mp4"
    final_output_path = os.path.join(output_dir, output_filename)
    
    print(f"Loading raw asset: {video_source_path}")
    video = VideoFileClip(video_source_path)
    
    # Extract temporary audio footprint for analysis
    temp_audio_path = "temp_audio.wav"
    video.audio.write_audiofile(temp_audio_path, fps=22050, nbytes=2, codec='pcm_s16le')
    
    print("Executing structural audio energy scan...")
    start_time, end_time = analyze_audio_for_hooks(temp_audio_path)
    print(f"Hook isolated from timestamp: {start_time}s to {end_time}s")
    
    # Subclip the main video matrix
    sub_clip = video.subclip(start_time, end_time)
    
    # Calculate geometric dimensions for true 9:16 center-cropping
    original_w, original_h = sub_clip.size
    target_h = original_h
    target_w = int(target_h * (9 / 16))
    x_center = int((original_w - target_w) / 2)
    
    cropped_clip = sub_clip.crop(x1=x_center, y1=0, width=target_w, height=target_h)
    
    # Generate an automated caption overlay framework
    # Note: Ensure ImageMagick is configured on the engine runner
    caption = TextClip(
        "CRITICAL WIRELESS BOTTLENECK", 
        fontsize=34, 
        color='yellow', 
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(target_w - 40, None)
    ).set_position(('center', target_h - 250)).set_duration(cropped_clip.duration)
    
    print("Compiling video file composition layers...")
    final_video = CompositeVideoClip([cropped_clip, caption])
    
    # Compile composition using fast presets for low-compute environments
    final_video.write_videofile(
        final_output_path, 
        codec="libx264", 
        audio_codec="aac", 
        preset="fast", 
        threads=2,
        logger=None
    )
    
    # Clean up file handles
    video.close()
    sub_clip.close()
    cropped_clip.close()
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
        
    print(f"Successfully rendered file: {final_output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing input path target source.")
        sys.exit(1)
    process_video_pipeline(sys.argv[1])
