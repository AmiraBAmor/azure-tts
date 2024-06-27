import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

def initialize_speech_synthesizer():
    load_dotenv()
    api_key = os.getenv("api_key")
    region = os.getenv("region")
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    speech_config.speech_synthesis_voice_name = 'fr-FR-HenriNeural'
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    return speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

def synthesize_text_to_speech(text, synthesizer):
    synthesizer.speak_text_async(text).get() 