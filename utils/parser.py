# -*- coding: utf-8 -*-
import yaml
import re


def del_page_number(f):
    lines = f.readlines()

    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
        prev_line = lines[i - 1].strip() if i - 1 >= 0 else ''

        is_number_line = re.fullmatch(r'\d+', line)
        is_separator = line == '* * *'

        if is_number_line and (next_line == '* * *' or prev_line == '* * *'):
            # пропускаем эту строку (не добавляем в cleaned_lines)
            i += 1
            continue

        cleaned_lines.append(lines[i])
        i += 1

    # Объединяем обратно в строку
    content = ''.join(cleaned_lines)
    return content


def convert_txt_to_yaml(input_file, output_file):
    # Читаем файл и разбиваем по разделителю * * *
    with open(input_file, 'r', encoding='utf-8') as f:

        content = del_page_number(f)

    # Убираем возможные пробелы и переводим разделитель к одному виду
    anekdots = [a.strip() for a in content.split('* * *') if a.strip()]

    # Создаем словарь с нужным форматированием
    result = {}
    for i, anekdot in enumerate(anekdots, start=1):
        # Убираем переносы строк с дефисом внутри слов (например, пере-\nнос → перенос)
        cleaned = []
        lines = anekdot.splitlines()
        buffer = ""
        for line in lines:
            line = line.rstrip()
            if line.endswith('-') and not line.endswith('--'):  # чтобы не склеивать тире
                buffer += line[:-1]
            else:
                buffer += line
                cleaned.append(buffer)
                buffer = ""
        result[i] = "\n".join(cleaned)

    # Пишем YAML вручную, чтобы сохранить | и отступы
    with open(output_file, 'w', encoding='utf-8') as f:
        for key, text in result.items():
            f.write(f"{key}: |\n")
            for line in text.splitlines():
                f.write(f"  {line.rstrip()}\n")


def main():
    input_file = "../anekdots.txt"
    output_file = "../anekdots.yaml"
    convert_txt_to_yaml(input_file, output_file)


if __name__ == "__main__":
    main()

