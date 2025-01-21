# kokoro
from .models import build_model
import torch
print(torch)
print(dir(torch))
from .kokoro import generate
from scipy.io.wavfile import write


MODEL = build_model('models/kokoro/kokoro-v0_19.pth', 'cuda')
VOICE_NAME = [
    'af', # Default voice is a 50-50 mix of Bella & Sarah
    'af_bella', 'af_sarah', 'am_adam', 'am_michael',
    'bf_emma', 'bf_isabella', 'bm_george', 'bm_lewis',
    'af_nicole', 'af_sky',
][0]
VOICEPACK = torch.load(f'voices/kokoro/{VOICE_NAME}.pt', weights_only=True).to('cuda')


def tts_to_file(text, file_path):
    audio, out_ps = generate(MODEL, text, VOICEPACK, lang=VOICE_NAME[0])
    write(file_path, 24000, audio)
