from flask import Blueprint, jsonify, request, current_app
from app.services.recordingTranscriber import RecordingTranscriber
from app import limiter
import os

recordingTranscription_bp = Blueprint('recordingTranscription', __name__, url_prefix='/api/video')

@recordingTranscription_bp.route('/upload', methods=['POST'])
@limiter.limit("3 per day") 
@limiter.limit("3 per hour") 
@limiter.limit("1 per 10 minutes")  
def upload_video():
  
    try:
        print("Received request to upload video")
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        print(f"Received file: {file.filename}")
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        video_path = os.path.join(upload_folder, file.filename)
        print(f"Saving video to: {video_path}")
        file.save(video_path)
        print(f"Video saved to: {video_path}")

        print(f"Processing video file: {video_path}")
        result = RecordingTranscriber.process_video(video_path)
        print(f"Processing result: {result}")

       
        try:
            os.remove(video_path)
            print(f"Cleaned up uploaded file: {video_path}")
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up uploaded file: {cleanup_error}")

        if isinstance(result, dict):
            if result.get('rejected', False):
                return jsonify({
                    'success': False, 
                    'error': result.get('error'),
                    'rejected': True,
                    'message': 'Video rejected to protect GCP credits'
                }), 400
            elif result.get('success', False):
                return jsonify({
                    'success': True, 
                    'transcription': result.get('transcription')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown processing error'),
                    'rejected': False
                }), 500
        else:
            return jsonify({'error': 'Unexpected response format'}), 500

    except Exception as e:
        current_app.logger.error(f"Error uploading video: {str(e)}")
        print(f"Error uploading video: {str(e)}")
        return jsonify({'error': str(e)}), 500