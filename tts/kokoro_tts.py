import logging
from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import torch

log = logging.getLogger(__name__)

lang_dict = {
    'en' :'a',
    'es': 'e',
    'fr' :'f',
    'zh' :'z',
}

def language_code(language):
    try:
        return lang_dict[language]
    except KeyError as e:
        raise Exception(f"Language {language} not supported by kokoro.")


def text_to_audio(text, file_path, language='en'):
    lang_code = language_code(language)
    pipeline = KPipeline(lang_code=lang_code)

    generator = pipeline(text, voice='af_heart')
    for i, (gs, ps, audio) in enumerate(generator):
        print(i, gs, ps)
        display(Audio(data=audio, rate=24000, autoplay=i==0))
        sf.write(file_path, audio, 24000)
    return file_path
