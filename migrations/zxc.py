# Чтение файла и создание словаря
# Чтение файла и создание словаря
def create_word_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        words = file.read().splitlines()
        
    word_dict = {word: list(word) for word in words}
    return word_dict

# Запись словаря в файл
def save_word_dict_to_file(word_dict, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write("word_dict = {\n")
        for word, chars in word_dict.items():
            file.write(f'    "{word}": {chars},\n')
        file.write("}")

# Пример использования
input_file_path = 'output1.txt'  # Замените на путь к вашему файлу
output_file_path = 'denis_cherckash.json'

word_dict = create_word_dict(input_file_path)
save_word_dict_to_file(word_dict, output_file_path)
