from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

def speak_to_microphone(api_key, region):
    load_dotenv()
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    speech_config.speech_recognition_language = "fr-FR"
    
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    speech_recognizer.properties.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "40000")
    speech_recognizer.properties.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "20000")
    
    print("Parlez dans votre microphone. Dites 'au revoir' pour terminer.")
    
    try:
        speech_recognition_result = speech_recognizer.recognize_once_async().get()
        
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Reconnu: {}".format(speech_recognition_result.text))
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("Aucune parole reconnue: {}".format(speech_recognition_result.no_match_details))
            return ""
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Annulé: {}".format(cancellation_details.reason))
            return ""
    except Exception as e:
        print(f"Exception during speech recognition: {e}")
        return ""