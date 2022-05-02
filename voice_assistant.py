from typing import Dict, NoReturn, Optional
from datetime import datetime as dt, timedelta
from json import load as _load
from os import remove
import re

from speech_worker import SpeechWorker
from my_logger import logger
from config import config


class VoiceAssistant(SpeechWorker):
    """
    Помимо реализации работы с речью и текстом,
    будет реализовывать работу голосового ассистента
    """
    name: str
    sex: str
    speech_language: str
    recognition_language: str
    over_hear_minutes: float
    scheme: Dict[str, str]

    started_over_hear: Optional[dt] = None
    is_over_hear: bool = False

    def __init__(self) -> None:
        with open('./assistant.json', 'rt', encoding='utf-8') as file:
            owner_obj: Dict[str, str] = _load(file)
            for key in owner_obj.keys():
                setattr(self, key, owner_obj[key])

        with open('./assistant-scheme.json', 'rt', encoding='utf-8') as file:
            self.scheme = _load(file)
        
        self.over_hear_delta = timedelta(minutes=self.over_hear_minutes)

    def execute_command(self, arguments: str) -> None:
        """
        Пробегает по схеме ассистента и ищет совпадение токен-фразы с ключом.
        Ключ является названием метода, который имеется в данном классе
        """
        for key in self.scheme.keys():
            if not arguments:
                break
            if arguments.lower() == self.name.lower():
                self.call()
                break
            if key == arguments or arguments.startswith(key) or key.startswith(arguments):
                self.__getattribute__(self.scheme[arguments])()
                break
    
    def start_hear(self) -> NoReturn:
        """
        Цикличное прослушивание окружающей среды,
        управление программой не возвращает
        """
        while True:
            try:
                if self.started_over_hear:
                    if dt.now() - self.started_over_hear >= self.over_hear_delta:
                        self.is_over_hear = False
                        self.started_over_hear = None
                owner_speech = self.record_and_recognize_audio().lower()
                logger.log(f'Произнесено:\n{owner_speech}')
                if not self.is_over_hear:
                    if not owner_speech.startswith(self.name.lower()):
                        continue
                    # owner_speech = owner_speech.replace(self.name.lower(), '', 1)
                    if owner_speech.lower() != self.name.lower():
                        owner_speech = re.sub(rf'{self.name.lower()} ?,?', '', owner_speech, 1)
                if re.match(rf'{self.name.lower()}.', owner_speech):
                    owner_speech = re.sub(rf'{self.name.lower()} ?,?', '', owner_speech, 1)
                # вариант с регексом
                remove('microphone-results.wav')
                words = owner_speech.split()
                # command, *arguments = words
                command = owner_speech
                self.execute_command(command)# , arguments)
            except Exception as e:
                msg = "Упс, возникла ошибка..."
                if config.say_errors:
                    self.speak(msg, "runtime-error")
                print(msg)
                print(e)
        
    def call(self, *args) -> None:
        if not self.is_over_hear:
            self.is_over_hear = True
            self.started_over_hear = dt.now()
            self.speak("да, хозяин, слушаю вас внимательно", self._get_sound_path('carefull-hear'))
        else:
            self.speak("хозяин, я вас уже внимательно слушаю", self._get_sound_path('already-carefull'))

    def hello(self, *args) -> None:
        self.speak("Привет, мой хозяин", self._get_sound_path("greeting/hello"))

    def good_morning(self, *args) -> None:
        self.speak("Доброго утра хозяин", self._get_sound_path("greeting/good_morning"))
