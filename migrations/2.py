import re

# Чтение содержимого файла
with open('1-9wordshsk.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Удаление текста в круглых, квадратных и китайских скобках, а также внутри вертикальных черт и самих этих символов
cleaned_content = re.sub(r'\[.*?\]|\(.*?\)|\（.*?\）|\|.*?\|', '', content)

# Удаление запятых
cleaned_content = cleaned_content.replace(',', '')

# Сохранение очищенного содержимого в файл
with open('output1.txt', 'w', encoding='utf-8') as file:
    file.write(cleaned_content)
