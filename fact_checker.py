#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fact Checker — поиск статей через прямой API Wikipedia (без библиотеки-обёртки).
"""

import requests

def search_wikipedia(query, lang='ru', limit=5):
    """Ищет статьи в Wikipedia по ключевым словам. Возвращает список словарей."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
    }
    headers = {
        'User-Agent': 'MyFactChecker/1.0 (contact@example.com)'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('query', {}).get('search', [])
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []


def get_summary(title, lang='ru'):
    """Получает краткое содержание статьи по её точному названию."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": title,
        "format": "json",
    }
    headers = {
        'User-Agent': 'MyFactChecker/1.0 (contact@example.com)'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if page_id != '-1':
                return page_data.get('extract', 'Нет содержания.')
        return "Статья не найдена."
    except Exception as e:
        return f"Ошибка получения содержания: {e}"


def main():
    print("Fact Checker — поиск по Wikipedia")
    print("Введите 'выход' для завершения.\n")

    while True:
        query = input("Что искать? ").strip()
        if query.lower() in ('выход', 'exit', 'quit'):
            print("До встречи!")
            break
        if not query:
            continue

        results = search_wikipedia(query)

        if not results:
            print("Ничего не найдено. Попробуйте другой запрос.\n")
            continue

        print(f"\nНайдено статей: {len(results)}")
        for i, r in enumerate(results, 1):
            snippet = r.get('snippet', '')
            # Убираем HTML-теги из сниппета
            import re
            snippet = re.sub('<[^>]+>', '', snippet)
            print(f"{i}. {r['title']}")
            print(f"   {snippet[:150]}...")

        choice = input("\nВведите номер статьи для просмотра (или Enter для пропуска): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                title = results[idx]['title']
                print(f"\n--- {title} ---")
                summary = get_summary(title)
                print(summary[:800])
                print(f"\nСсылка: https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}\n")
        else:
            print()


if __name__ == '__main__':
    main()
