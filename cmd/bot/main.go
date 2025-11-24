package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"

	"github.com/ezhigval/ai_bot_telegram/internal/agent"
	"github.com/ezhigval/ai_bot_telegram/internal/config"
	"github.com/ezhigval/ai_bot_telegram/internal/storage"
	"github.com/ezhigval/ai_bot_telegram/internal/telegram"
)

func main() {
	// Базовые настройки логгера: время + короткий файл/строка.
	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	_ = godotenv.Load() // не падаем, если файла нет, можно задать переменные окружения снаружи

	cfg := config.Load()

	// Память на файле — задел для обучения на взаимодействиях.
	mem := storage.NewFileMemory("data/dialogs.jsonl")

	// Простой агент без реального LLM и инструментов.
	ag := agent.NewSimpleAgent(nil, mem, nil)

	bot, err := telegram.NewBot(cfg.TelegramBotToken, ag)
	if err != nil {
		log.Fatalf("failed to create bot: %v", err)
	}

	// graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		if err := bot.StartPolling(); err != nil {
			log.Fatalf("bot stopped with error: %v", err)
		}
	}()

	log.Println("Bot started. Press Ctrl+C to stop.")
	<-stop

	log.Println("Shutting down bot...")
	bot.Stop()
}
