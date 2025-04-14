from flask import Blueprint, jsonify, request, current_app
from app.services.recordingTranscriber import RecordingTranscriber
import os

recordingTranscription_bp = Blueprint('recordingTranscription', __name__, url_prefix='/api/video')

@recordingTranscription_bp.route('/upload', methods=['POST'])
def upload_video():
  
    try:
        print("Received request to upload video")
        file = request.files['file']
        print(f"Received file: {file.filename}")
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        video_path = os.path.join(upload_folder, file.filename)
        print(f"Saving video to: {video_path}")
        file.save(video_path)
        print(f"Video saved to: {video_path}")

        print(f"Processing video file: {video_path}")
        transcription = RecordingTranscriber.process_video(video_path)
        print(f"Transcription result: {transcription}")


        if transcription:
            print("Transcription successful")
            return jsonify({'success': True, 'transcription': transcription}), 200
        else:
            print("Error processing video")
            return jsonify({'error': 'Error processing video'}), 500

    except Exception as e:
        current_app.logger.error(f"Error uploading video: {str(e)}")
        print(f"Error uploading video: {str(e)}")
        return jsonify({'error': str(e)}), 500