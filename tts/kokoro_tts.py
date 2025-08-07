import logging
from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import torch

log = logging.getLogger(__name__)

languages = {
    'en': { 'code': 'a', 'voice': 'af_sarah' },
    'es': { 'code': 'e', 'voice': ''},
    'fr': { 'code':'f', 'voice': 'ff_siwis'},
    'zh': {'code': 'z', 'voice': 'zf_xiaoyi'},
}

def language_config(language):
    try:
        return languages[language]
    except KeyError as e:
        raise Exception(f"Language {language} not supported by kokoro.")


def text_to_audio(text, file_path, language='en'):
    voice_config = language_config(language)
    pipeline = KPipeline(lang_code=voice_config['code'])

    generator = pipeline(text, voice=voice_config['voice'])
    for i, (gs, ps, audio) in enumerate(generator):
        print(i, gs, ps)
        display(Audio(data=audio, rate=24000, autoplay=i==0))
        sf.write(file_path, audio, 24000)
    return file_path
