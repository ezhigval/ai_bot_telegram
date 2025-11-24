#!/usr/bin/env python3
"""Скрипт проверки готовности окружения к запуску."""

import os
import sys
from pathlib import Path


def check_python_version():
    """Проверка версии Python."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ требуется")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Проверка установленных зависимостей."""
    required = ["starlette", "httpx", "aiogram"]
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} не установлен")
            missing.append(module)
    
    return len(missing) == 0


def check_env_file():
    """Проверка наличия файла с переменными окружения."""
    env_files = ["keys.env", ".env"]
    found = False
    
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"✅ {env_file} найден")
            found = True
            
            # Проверяем наличие обязательных переменных
            with open(env_file) as f:
                content = f.read()
                if "TELEGRAM_BOT_TOKEN" in content:
                    print("  ✅ TELEGRAM_BOT_TOKEN найден")
                else:
                    print("  ⚠️  TELEGRAM_BOT_TOKEN не найден")
        else:
            print(f"⚠️  {env_file} не найден")
    
    return found


def check_core_files():
    """Проверка наличия всех файлов ядра."""
    required_files = [
        "core/app.py",
        "core/models.py",
        "core/memory.py",
        "core/llm_client.py",
        "core/agent.py",
        "core/tools.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} отсутствует")
            all_exist = False
    
    return all_exist


def main():
    """Главная функция проверки."""
    print("🔍 Проверка готовности окружения...\n")
    
    checks = [
        ("Версия Python", check_python_version),
        ("Зависимости", check_dependencies),
        ("Файлы ядра", check_core_files),
        ("Переменные окружения", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ Все проверки пройдены! Можно запускать проект.")
        return 0
    else:
        print("⚠️  Некоторые проверки не пройдены. Исправь ошибки и попробуй снова.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
