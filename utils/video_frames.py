import cv2
import os
import tempfile
import io
from PIL import Image
from typing import List, Union

def extract_key_frames(video_input: Union[str, bytes], interval_seconds: int = 2, max_frames: int = 8) -> List[bytes]:
    """
    Extracts key frames from a video file path or raw bytes.
    Returns a list of image bytes (PNG).
    
    Args:
        video_input: Path to the video file or bytes content.
        interval_seconds: How many seconds between each extracted frame.
        max_frames: Maximum number of frames to extract.
    """
    temp_path = None
    if isinstance(video_input, bytes):
        if not video_input:
             return []
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(video_input)
            temp_path = f.name
        video_path = temp_path
    else:
        video_path = video_input
        if not video_path or not os.path.exists(video_path):
            return []

    frames_bytes = []
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # Error will be caught by the caller or returned as empty list
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0 # Fallback
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps
        
        # Calculate frame indices to extract
        frame_indices = []
        for i in range(max_frames):
            time_at = i * interval_seconds
            if time_at >= duration_seconds:
                # If the video is shorter than interval_seconds, we still want at least the first frame
                if i == 0 and total_frames > 0:
                    frame_indices.append(0)
                break
            frame_indices.append(int(time_at * fps))

        # Always try to get at least the first frame if we didn't get any but there are frames
        if not frame_indices and total_frames > 0:
            frame_indices.append(0)

        for idx in frame_indices:
            if idx >= total_frames:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert BGR to RGB for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            # Save to bytes (PNG for quality/compatibility)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            frames_bytes.append(buf.getvalue())
            
        cap.release()
    except Exception:
        # Silently fail and return whatever we got
        pass
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
            
    return frames_bytes
