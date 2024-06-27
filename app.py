import grpc
import bot_pb2
import bot_pb2_grpc
import concurrent.futures
import os
from dotenv import load_dotenv
from azure_tts import initialize_speech_synthesizer, synthesize_text_to_speech
from azure_stt import speak_to_microphone
from groq import Groq
import time
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename='latency_log.txt', level=logging.INFO)

class CallBotServicer(bot_pb2_grpc.CallBotServicer):
    def __init__(self):
        self.client = Groq(api_key=os.getenv("groq_api"))
        self.speech_synthesizer = initialize_speech_synthesizer()

    def SendMessage(self, request, context):
        start_time = time.time()
        
        user_input = request.message
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_input,
                    "name": "FrenchUser",
                }
            ],
            model="Llama3-8b-8192",
        )
        
        response = chat_completion.choices[0].message.content
        
        # Synthesize speech (comment out if not needed)
        # synthesize_text_to_speech(response, self.speech_synthesizer)
        
        end_time = time.time()
        logging.info(f"Appel API Groq a pris {end_time - start_time:.2f} secondes")
        return bot_pb2.MessageResponse(response=response)

def serve():
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    bot_pb2_grpc.add_CallBotServicer_to_server(CallBotServicer(), server)
    server.add_insecure_port('[::]:50080')
    print("Server starting on port 50080...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve() 