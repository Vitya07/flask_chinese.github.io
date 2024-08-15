import json
import re

# Путь к исходному JSON-файлу
SOURCE_JSON_FILE_PATH = 'E:/flask_project/cedict_ts.json'
# Путь к файлу, в который будет сохранен результат
OUTPUT_JSON_FILE_PATH = 'E:/flask_project/cleaned_word_dict.json'

def is_chinese_char(ch):
    """Проверяет, является ли символ китайским иероглифом"""
    return '\u4e00' <= ch <= '\u9fff'

def clean_word_dict(file_path):
    """Удаляет все ненужные символы и оставляет только китайские иероглифы"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    result = {}
    
    for entry in data:
        chinese_word = entry['chinese']
        # Оставляем только китайские символы
        cleaned_characters = [ch for ch in chinese_word if is_chinese_char(ch)]
        if cleaned_characters:  # Только если остались иероглифы
            result[chinese_word] = cleaned_characters
    
    return result

def save_dict_to_json(dictionary, output_path):
    """Сохраняет словарь в JSON-файл"""
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=4)

# Преобразование JSON данных из файла и очистка
cleaned_word_dict = clean_word_dict(SOURCE_JSON_FILE_PATH)

# Сохранение очищенного словаря в новый JSON файл
save_dict_to_json(cleaned_word_dict, OUTPUT_JSON_FILE_PATH)

print("Очищенный словарь успешно сохранен в файл:", OUTPUT_JSON_FILE_PATH)
