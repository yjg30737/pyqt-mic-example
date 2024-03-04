# Connect to microphone
import wave
from pathlib import Path

import pyaudio

from openai import OpenAI

MIC_RECORDING = False

def check_microphone_access():
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        stream.close()
        audio.terminate()
        return True
    except Exception as e:
        return False

# Microphone recording function
def record(FORMAT=pyaudio.paInt16, CHANNELS=1, RATE=44100, CHUNK=1024, RECORD_SECONDS=5, WAVE_OUTPUT_FILENAME="output.wav"):
    audio = pyaudio.PyAudio()

    MIC_RECORDING = True

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording start...")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        if MIC_RECORDING:
            data = stream.read(CHUNK)
            frames.append(data)
        else:
            break

    print("Recording complete.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save as WAV file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# SPEECH TO TEXT
client = OpenAI(api_key='API-KEY')

def get_stt(filename, model='whisper-1'):
    transcript = client.audio.transcriptions.create(
        model=model,
        file=Path(filename)
    )
    # Remove the file
    Path(filename).unlink()
    return transcript.text

def get_recorded_text():
    if not check_microphone_access():
        return Exception("Microphone access is not available.")
    record()
    return get_stt('output.wav')

class GPTWrapper:
    def __init__(self, api_key=None):
        super().__init__()
        # Initialize OpenAI client
        if api_key:
            self.__client = OpenAI(api_key=api_key)
        self.__messages = []
        self.load_messages_from_json()

    def load_messages_from_json(self, json_file='messages.json'):
        # Check the file exists
        if not os.path.exists(json_file):
            self.save_messages_to_json(json_file)
        # Load messages from json file
        with open(json_file, 'r') as f:
            self.__messages = json.load(f)

    def save_messages_to_json(self, json_file='messages.json'):
        # Save messages to json file
        with open(json_file, 'w') as f:
            json.dump(self.__messages, f)

    # def update_last_messages(self, messages):

    def set_api(self, api_key):
        self.__api_key = api_key
        self.__client = OpenAI(api_key=api_key)

    def get_image_url_from_local(self, image_path):
        # Function to encode the image
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_image = encode_image(image_path)
        return f'data:image/jpeg;base64,{base64_image}'

    def get_message_obj(self, role, content):
        return {"role": role, "content": content}

    def get_arguments(
        self,
        model="gpt-4-0125-preview",
        system="You are a very helpful assistant.",
        n=1,
        temperature=1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format="text",
        objective: dict = {},
        cur_text: str = '',
        use_max_tokens=False,
        max_tokens=128000,
        stream=False,
        images=[],
    ):
        system_obj = self.get_message_obj("system", system)
        previous_messages = [system_obj] + self.__messages

        if response_format == 'text':
            pass
        else:
            cur_text = objective["cur_text"] + " " + str(objective["json_format"])
        try:
            openai_arg = {
                "model": model,
                "messages": previous_messages,
                "n": n,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stream": stream,
                "response_format": {"type": response_format},
            }

            # If there is at least one image, it should add
            if len(images) > 0:
                multiple_images_content = []
                for image in images:
                    multiple_images_content.append(
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': self.get_image_url_from_local(image)
                            }
                        }
                    )

                multiple_images_content = [
                                              {
                                                  "type": "text",
                                                  "text": cur_text
                                              }
                                          ] + multiple_images_content[:]
                openai_arg['messages'].append({"role": "user", "content": multiple_images_content})
            else:
                self.__messages.append(self.get_message_obj("user", cur_text))
                openai_arg['messages'].append({"role": "user", "content": cur_text})
            # If current model is "vision", default max token set to very low number by openai,
            # so let's set this to 4096 which is relatively better.
            if is_gpt_vision(model):
                openai_arg['max_tokens'] = 4096
            if use_max_tokens:
                openai_arg['max_tokens'] = max_tokens

            return openai_arg
        except Exception as e:
            raise Exception(e)

    def get_text_response(self, openai_arg):
        try:
            response = self.__client.chat.completions.create(**openai_arg)
            response_content = response.choices[0].message.content

            self.__messages.append(self.get_message_obj("assistant", response_content))

            return response_content
        except Exception as e:
            raise Exception(e)

    def get_image_response(self, model='dall-e-3', prompt="""
        Photorealistic,
        Close-up portrait of a person for an ID card, neutral background, professional attire, clear facial features, eye-level shot, soft lighting to highlight details without harsh shadows, high resolution for print quality --ar 1:1
        """, n=1, style='vivid', size='1024x1024', response_format='b64_json'):
            image_data = ''
            try:
                response = self.__client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=n,
                    style=style,
                    size=size,
                    response_format=response_format,
                )
                for _ in response.data:
                    image_data = _.b64_json
                return image_data
            except Exception as e:
                print(e)
                raise Exception(e)

