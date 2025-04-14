import os
import sys
import uuid
from flask import current_app
from moviepy import *
from vosk import Model, KaldiRecognizer
import wave
import json
import urllib.request
import zipfile

os.makedirs("model", exist_ok=True)
model_path = "model/vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    print("Downloading Vosk model...")
    zip_path = "model/vosk-model-small-en-us-0.15.zip"
    urllib.request.urlretrieve(
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        zip_path
    )
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("model")
    
   
    os.remove(zip_path)
    print("Model downloaded and extracted.")

class RecordingTranscriber:
    @staticmethod
    def convert_video_to_wav(video_path):
    
        try:
            print(f"Converting video to WAV: {video_path}")
            video = VideoFileClip(video_path)
            audio_filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.abspath(audio_filename)  # Get absolute path
            # Export as WAV with proper settings for Vosk
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
        
            model_path = os.path.abspath("model/vosk-model-small-en-us-0.15")
            print(f"Loading Vosk model from: {model_path}")
           
            if not os.path.exists(model_path):
                current_app.logger.error(f"Model not found at: {model_path}")
                print(f"Model not found at: {model_path}")
                return None
                
        
            model = Model(model_path)
        
            wf = wave.open(audio_path, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                current_app.logger.error("Audio file must be WAV format mono PCM")
                print("Audio file must be WAV format mono PCM")
                return None
            
            print(f"Audio sample rate: {wf.getframerate()}")
            recognizer = KaldiRecognizer(model, wf.getframerate())
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    part_result = json.loads(recognizer.Result())
                    results.append(part_result.get("text", ""))
            
            part_result = json.loads(recognizer.FinalResult())
            results.append(part_result.get("text", ""))
            
            transcription = " ".join([r for r in results if r])
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
            audio_path = RecordingTranscriber.convert_video_to_wav(video_path)
            if not audio_path:
                return None

            current_app.logger.info(f"Converted video to audio: {audio_path}")

            transcription = RecordingTranscriber.transcribe_audio(audio_path)
            if not transcription:
                return None

            current_app.logger.info(f"Transcription result: {transcription}")

            formatted_transcription = RecordingTranscriber.format_transcription(transcription)
            current_app.logger.info(f"Formatted transcription result: {formatted_transcription}")

            print(f"Cleaning up audio file: {audio_path}")
            os.remove(audio_path)

            print(f"Returning transcription: {formatted_transcription}")
            return formatted_transcription

        except Exception as e:
            current_app.logger.error(f"Error processing video: {str(e)}")
            print(f"Error processing video: {str(e)}")
            return None