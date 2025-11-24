package telegram

import (
	"context"
	"log"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

	"github.com/ezhigval/ai_bot_telegram/internal/agent"
)

type Bot struct {
	api    *tgbotapi.BotAPI
	cancel context.CancelFunc
	agent  agent.Agent
}

func NewBot(token string, a agent.Agent) (*Bot, error) {
	api, err := tgbotapi.NewBotAPI(token)
	if err != nil {
		return nil, err
	}

	api.Debug = false
	return &Bot{
		api:   api,
		agent: a,
	}, nil
}

// StartPolling запускает простой лонг-поллинг и обрабатывает апдейты.
func (b *Bot) StartPolling() error {
	ctx, cancel := context.WithCancel(context.Background())
	b.cancel = cancel

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 30

	updates := b.api.GetUpdatesChan(u)

	for {
		select {
		case <-ctx.Done():
			return nil
		case update, ok := <-updates:
			if !ok {
				return nil
			}
			b.handleUpdate(ctx, update)
		}
	}
}

func (b *Bot) Stop() {
	if b.cancel != nil {
		b.cancel()
	}
	// Небольшая пауза, чтобы корректно завершить цикл
	time.Sleep(500 * time.Millisecond)
}

func (b *Bot) handleUpdate(ctx context.Context, update tgbotapi.Update) {
	if update.Message == nil { // игнорируем всё, что не сообщение
		return
	}

	if b.agent == nil {
		log.Printf("agent is not configured")
		return
	}

	in := agent.Input{
		ChatID: update.Message.Chat.ID,
		UserID: update.Message.From.ID,
		Type:   agent.MessageTypeText, // пока поддерживаем только текст
		Text:   update.Message.Text,
	}

	out, err := b.agent.Reply(ctx, in)
	if err != nil {
		log.Printf("agent reply error: %v", err)
		out.Text = "Произошла ошибка при обработке сообщения."
	}

	if out.Text == "" {
		return
	}

	msg := tgbotapi.NewMessage(update.Message.Chat.ID, out.Text)
	msg.ReplyToMessageID = update.Message.MessageID

	if _, err := b.api.Send(msg); err != nil {
		log.Printf("failed to send message: %v", err)
	}
}


