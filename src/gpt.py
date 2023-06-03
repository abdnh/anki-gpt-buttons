from __future__ import annotations

from typing import Callable

import openai
import openai.error

from .errors import GPTButtonsException


class OpenAI:
    "This class integrates OpenAI's (chat) completion models via the .complete()/.chat_complete() methods given the settings set in the add-on config."

    _default_params = {"model": "gpt-3.5-turbo"}

    def __init__(self, options: dict) -> None:
        params = self._default_params.copy()
        params.update(options)
        self._params = params

    def _complete(self, callback: Callable[[str], str], prompt: str) -> str:
        try:
            return callback(prompt)
        except openai.error.OpenAIError as exc:
            raise GPTButtonsException(
                f"An OpenAI error has occurred. Make sure you set your API key and other OpenAI settings correctly in the config and that your OpenAI account is active.\n\nFull error message from the OpenAI module:\n{str(exc)}"
            ) from exc

    def complete(self, prompt: str) -> str:
        def callback(prompt: str) -> str:
            completion = openai.Completion.create(prompt=prompt, **self._params)
            return completion.choices[0].text.strip()

        return self._complete(callback, prompt)

    def chat_complete(self, prompt: str) -> str:
        def callback(prompt: str) -> str:
            completion = openai.ChatCompletion.create(
                messages=[{"role": "user", "content": prompt}], **self._params
            )
            return completion.choices[0].message.content.strip()

        return self._complete(callback, prompt)
