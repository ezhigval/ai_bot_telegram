package config

import (
	"log"
	"os"
)

// Config содержит основные настройки бота, загружаемые из переменных окружения.
type Config struct {
	TelegramBotToken string

	// Необязательный SSH URL репозитория (для локальной автоматизации, подсказок и т.п.).
	// Пример: git@github.com:ezhigval/ai_bot_telegram.git
	GitRemoteSSH string
}

// Load загружает конфиг из переменных окружения и валидирует критичные поля.
func Load() Config {
	cfg := Config{
		TelegramBotToken: os.Getenv("TELEGRAM_BOT_TOKEN"),
		GitRemoteSSH:     os.Getenv("GIT_REMOTE_SSH"),
	}

	if cfg.TelegramBotToken == "" {
		log.Fatal("TELEGRAM_BOT_TOKEN is not set in environment")
	}

	if cfg.GitRemoteSSH == "" {
		log.Println("GIT_REMOTE_SSH is not set; git push URL is not configured in runtime config")
	}

	return cfg
}
