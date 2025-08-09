import logging
from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import torch

log = logging.getLogger(__name__)

languages = {
    'en': { 'code': 'a', 'voice': 'af_sarah', 'pipeline': KPipeline(lang_code='a')},
    'es': { 'code': 'e', 'voice': '', 'pipeline': None},
    'fr': { 'code':'f', 'voice': 'ff_siwis', 'pipeline': None},
    'zh': { 'code': 'z', 'voice': 'zf_xiaoyi', 'pipeline': None},
}


def language_config(language):
    try:
        return languages[language]
    except KeyError as e:
        raise Exception(f"Language {language} not supported by kokoro.")


def text_to_audio(text, file_path, language='en'):
    voice_config = language_config(language)
    if not voice_config.get('pipeline'):
        languages[language]['pipeline'] = KPipeline(lang_code=voice_config['code'])
    pipeline = voice_config['pipeline']

    generator = pipeline(text, voice=voice_config['voice'])
    for i, (gs, ps, audio) in enumerate(generator):
        log.debug(i, gs, ps)
        display(Audio(data=audio, rate=24000, autoplay=i==0))
        sf.write(file_path, audio, 24000)
    return file_path
