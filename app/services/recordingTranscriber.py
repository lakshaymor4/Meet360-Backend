import os
import sys
import uuid
from flask import current_app
from moviepy import *
import whisper

class RecordingTranscriber:
    
  
    MAX_VIDEO_DURATION_SECONDS = 30  
    MAX_FILE_SIZE_MB = 50 
    
    @staticmethod
    def validate_video_safety(video_path):
        """
        Validate video file for safety checks before processing
        Returns (is_valid, error_message)
        """
        try:
           
            if not os.path.exists(video_path):
                return False, "Video file not found"
            
            
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if file_size_mb > RecordingTranscriber.MAX_FILE_SIZE_MB:
                return False, f"File too large: {file_size_mb:.1f}MB. Maximum allowed: {RecordingTranscriber.MAX_FILE_SIZE_MB}MB"
            
          
            print(f"Checking video duration for: {video_path}")
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()  
            
            print(f"Video duration: {duration:.2f} seconds")
            
            if duration > RecordingTranscriber.MAX_VIDEO_DURATION_SECONDS:
                return False, f"Video too long: {duration:.1f}s. Maximum allowed: {RecordingTranscriber.MAX_VIDEO_DURATION_SECONDS}s"
            
            return True, "Video validation passed"
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"
    @staticmethod
    def convert_video_to_wav(video_path):
        try:
            print(f"Converting video to WAV: {video_path}")
            video = VideoFileClip(video_path)
            audio_filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.abspath(audio_filename)
            video.audio.write_audiofile(audio_path, codec='pcm_s16le', ffmpeg_params=['-ar', '16000', '-ac', '1'])
            print(f"Audio file created: {audio_path}")
            return audio_path
        except Exception as e:
            current_app.logger.error(f"Error converting video to WAV: {str(e)}")
            print(f"Error converting video to WAV: {str(e)}")
            return None

    @staticmethod
    def transcribe_audio(audio_path):
        try:
            print("Loading Whisper base model...")
            model = whisper.load_model("small.en")  
            print(f"Transcribing audio: {audio_path}")
            result = model.transcribe(audio_path)
            transcription = result.get("text", "")
            print(f"Transcription result: {transcription}")
            return transcription
        except Exception as e:
            current_app.logger.error(f"Error during transcription: {str(e)}")
            print(f"Error during transcription: {str(e)}")
            return None

    @staticmethod
    def format_transcription(transcription):
        return transcription

    @staticmethod
    def process_video(video_path):
        try:
            print(f"Processing video: {video_path}")
            
            is_valid, error_message = RecordingTranscriber.validate_video_safety(video_path)
            if not is_valid:
                current_app.logger.error(f"Video validation failed: {error_message}")
                print(f" Video rejected: {error_message}")
                return {"error": error_message, "rejected": True}
            
            print("Video passed safety checks, proceeding with processing...")
            
            audio_path = RecordingTranscriber.convert_video_to_wav(video_path)
            if not audio_path:
                return {"error": "Failed to convert video to audio", "rejected": False}

            current_app.logger.info(f"Converted video to audio: {audio_path}")

            transcription = RecordingTranscriber.transcribe_audio(audio_path)
            if not transcription:
                return {"error": "Failed to transcribe audio", "rejected": False}

            current_app.logger.info(f"Transcription result: {transcription}")

            formatted_transcription = RecordingTranscriber.format_transcription(transcription)
            current_app.logger.info(f"Formatted transcription result: {formatted_transcription}")

            print(f"Cleaning up audio file: {audio_path}")
            try:
                os.remove(audio_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up audio file: {cleanup_error}")

            print(f"Returning transcription: {formatted_transcription}")
            return {"transcription": formatted_transcription, "success": True}

        except Exception as e:
            current_app.logger.error(f"Error processing video: {str(e)}")
            print(f"Error processing video: {str(e)}")
            return {"error": str(e), "rejected": False}
