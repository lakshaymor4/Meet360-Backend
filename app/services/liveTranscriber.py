import requests
import time
import json
import redis
from flask import current_app
from flask_socketio import emit
import threading
import pusher

class LiveTranscriber:
    pusher_client = None
    
    @staticmethod
    def _get_pusher_client():
        """Lazy initialization of the Pusher client within application context"""
        if LiveTranscriber.pusher_client is None:
            LiveTranscriber.pusher_client = pusher.Pusher(
                app_id=current_app.config.get("APP_ID"),
                key=current_app.config.get("KEY_PUSHER"),
                secret=current_app.config.get("SECRET_PUSHER"),
                cluster='ap2',
                ssl=True
            )
        return LiveTranscriber.pusher_client
    
    @staticmethod
    def get_Bod_id(meet):
        url = "https://api.meetingbaas.com/bots/"
        json_data = {
            "automatic_leave": {
                "noone_joined_timeout": 600,
                "waiting_room_timeout": 600
            },
            "bot_name": "Transcriber",
            "entry_message": "Me the transcriber",
            "meeting_url": meet,
            "recording_mode": "audio_only",
            "reserved": False,
            "speech_to_text": {
                "provider": "Default"
            },
        }
        headers = {
            "x-meeting-baas-api-key": current_app.config.get("API_KEY")
        }
      
        response = requests.request("POST", url, json=json_data, headers=headers)
        response_data = response.json()
        return response_data.get("bot_id")

    @staticmethod
    def leave(uuid):
        url = f"https://api.meetingbaas.com/bots/{uuid}"
        headers = {
            "x-meeting-baas-api-key": current_app.config.get("API_KEY")
        }
        print(f"Making DELETE request to {url} with headers: {headers}")
        response = requests.request("DELETE", url, headers=headers)
        print(f"Response from DELETE request to {url}: {response.status_code} - {response.text}")
        return response

    @staticmethod
    def getTranscription(uuid):
        url2 = "https://api.meetingbaas.com/bots/retranscribe"
        json_data = {
            "bot_uuid": uuid,
            "speech_to_text": {
                "provider": "Default"
            },
        }
        headers = {
            "x-meeting-baas-api-key": current_app.config.get("API_KEY")
        }
        print(f"Making POST request to {url2} with data: {json_data} and headers: {headers}")
        response = requests.post(url2, json=json_data, headers=headers)

        if response.status_code == 202:
            url = f"https://api.meetingbaas.com/bots/meeting_data?bot_id={uuid}"
            print(f"Making GET request to {url} with headers: {headers}")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                transcripts = data.get("bot_data", {}).get("transcripts", [])
                new_transcripts = []

                redis_client = redis.Redis(
                        host=current_app.config.get("REDIS_URL"),
                        port=15230,
                        decode_responses=True,
                        username="default",
                        password=current_app.config.get("KEY_REDIS"),
                        )               
                redis_key = current_app.config.get("REDIS_KEY")

                for transcript in transcripts:
                    transcript_id = transcript["id"]
                    if not redis_client.sismember(redis_key, transcript_id):
                        new_transcripts.append(transcript)
                        redis_client.sadd(redis_key, transcript_id)

                return new_transcripts
        return []

    @staticmethod
    def listen_for_updates(uuid, session_id, stop_event=None):
        while True:
            if stop_event and stop_event.is_set():
                current_app.logger.info(f"Stopping transcription for bot {uuid} (Session: {session_id})")
                break

            try:
                print(f"Calling getTranscription for bot {uuid}")
                new_data = LiveTranscriber.getTranscription(uuid)
                if new_data:
                    formatted_data = []
                    for t in new_data:
                        speaker = t.get("speaker", "Unknown Speaker")
                        words = t.get("words", [])
                        text = " ".join(w.get("text", "") for w in words if "text" in w)
                        formatted_data.append({"speaker": speaker, "text": text})
                    
                    pusher_client = LiveTranscriber._get_pusher_client()
                    pusher_client.trigger(
                        f'transcription-channel-{uuid}', 
                        f'transcription-update-{session_id}', 
                        {'transcription': formatted_data}
                    )
                    
            except Exception as e:
                current_app.logger.error(f"Error in listen_for_updates (Bot: {uuid}, Session: {session_id}): {str(e)}")

            if stop_event and stop_event.is_set():
                break

            time.sleep(5)