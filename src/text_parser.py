from PyQt5.QtWidgets import QApplication, QMessageBox
import re
import json
import os
import pytesseract
import numpy as np
import re

class TextParser:
    def __init__(self, config_path):
        """
        Инициализация парсера текста.
        :param config_path: Путь к файлу конфигурации JSON.
        """
        self.config = self.load_config(config_path)

    def load_config(self, config_path):
        """
        Загружает конфигурацию из JSON-файла.
        :param config_path: Путь к JSON-файлу.
        :return: Словарь с конфигурацией.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл {config_path} не найден.")
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def extract_text(self, image):
        """
        Извлекает текст из изображения с использованием Tesseract.
        :param image: Изображение для обработки (Pillow Image).
        :return: Извлеченный текст.
        """
        extracted_text = pytesseract.image_to_string(image, lang="eng+rus", config="--psm 6")
        return extracted_text

    def parse_text(self, text):
        """
        Парсит текст на основе конфигурации.
        :param text: Текст, который нужно распарсить.
        :return: Список найденных совпадений с их категориями.
        """
        parsed_results = []

        for category in self.config.get("result", []):
            label = category["label"]
            entries = category.get("entries", [label])
            for entry in entries:
                matches = re.findall(re.escape(entry), text, re.IGNORECASE)
                for match in matches:
                    parsed_results.append({
                        "id": category["id"]
                    })

        return parsed_results

    def show_text_popup(self, text):
        """
        Показать всплывающее окно с извлеченным текстом.
        :param text: Текст для отображения.
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Извлеченный текст")
        msg_box.setText(text if text.strip() else "Текст не найден.")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setFixedWidth(1200)
        msg_box.exec_()