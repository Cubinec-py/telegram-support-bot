import json
from pathlib import Path
from typing import Dict, Any


class I18n:
    def __init__(self, locales_dir: str = "bot/locales", default_language: str = "ru"):
        self.locales_dir = Path(locales_dir)
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files"""
        for locale_file in self.locales_dir.glob("*.json"):
            language = locale_file.stem
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.translations[language] = json.load(f)

    def get(self, key: str, language: str = None, **kwargs) -> str:
        """Get translation by key"""
        if language is None:
            language = self.default_language

        # Get translation dict for language
        lang_dict = self.translations.get(language, self.translations.get(self.default_language, {}))

        # Navigate through nested keys (e.g., "start.welcome")
        keys = key.split(".")
        value = lang_dict

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                return key

        # Format with kwargs if provided
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return value if isinstance(value, str) else key

    def get_available_languages(self) -> list[str]:
        """Get list of available languages"""
        return list(self.translations.keys())


# Global i18n instance
i18n = I18n()

