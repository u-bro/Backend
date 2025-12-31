#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы модерации чатов
"""

import sys
import os

# Добавляем корневую директорию проекта в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chat_service import chat_service

def test_moderation():
    """Тестирование модерации с разными примерами"""
    
    test_cases = [
        "Hello world",  # Нормальное сообщение
        "This is fucking bad",  # Английское ругательство
        "Это хуйня",  # Русское ругательство
        "D0n't b3 4n 4ssh0l3",  # Leet замены
        "You are 4 b1tch",  # Leet с цифрами
        "What the h3ll",  # Легкое ругательство
        "Good morning everyone!",  # Нормальное сообщение
        "suck my d1ck",  # Leet ругательство
    ]
    
    print("=== Тестирование модерации чатов ===\n")
    
    for i, text in enumerate(test_cases, 1):
        result = chat_service.test_profanity_detection(text)
        
        print(f"Тест #{i}: {result['original']}")
        print(f"  Has profanity: {result['has_profanity']}")
        print(f"  Custom check: {result['custom_check']}")
        print(f"  Found word: {result['found_word']}")
        print(f"  Censored: {result['censored']}")
        print(f"  Changed: {result['is_changed']}")
        print()
    
    print("=== Статистика модерации ===")
    stats = chat_service.get_stats()
    print(f"Кастомных слов: {stats['moderation']['custom_words_count']}")
    print(f"Leet замен: {stats['moderation']['leet_replacements_count']}")
    print(f"Использует better-profanity: {stats['moderation']['uses_better_profanity']}")

if __name__ == "__main__":
    test_moderation()
