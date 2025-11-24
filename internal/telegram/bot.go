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

	msg := update.Message

	if b.agent == nil {
		log.Printf("agent is not configured")
		return
	}

	// Определяем тип сообщения Telegram и маппим его на типы агента.
	msgType := agent.MessageTypeText
	var media *agent.Media

	switch {
	case msg.Voice != nil:
		msgType = agent.MessageTypeVoice
		v := msg.Voice
		media = &agent.Media{
			FileID:   v.FileID,
			MimeType: v.MimeType,
			FileSize: int64(v.FileSize),
		}
	case msg.Photo != nil:
		msgType = agent.MessageTypeImage
		// Обычно последняя фотография в срезе — наибольшего размера.
		if len(msg.Photo) > 0 {
			p := msg.Photo[len(msg.Photo)-1]
			media = &agent.Media{
				FileID:   p.FileID,
				FileSize: int64(p.FileSize),
			}
		}
	case msg.Video != nil || msg.VideoNote != nil:
		msgType = agent.MessageTypeVideo
		if msg.Video != nil {
			v := msg.Video
			media = &agent.Media{
				FileID:   v.FileID,
				MimeType: v.MimeType,
				FileSize: int64(v.FileSize),
			}
		} else if msg.VideoNote != nil {
			v := msg.VideoNote
			media = &agent.Media{
				FileID:   v.FileID,
				FileSize: int64(v.FileSize),
			}
		}
	case msg.Document != nil:
		msgType = agent.MessageTypeFile
		d := msg.Document
		media = &agent.Media{
			FileID:   d.FileID,
			FileName: d.FileName,
			MimeType: d.MimeType,
			FileSize: int64(d.FileSize),
		}
	}

	// Берём текст сообщения или подпись к медиа, если есть.
	text := msg.Text
	if text == "" && msg.Caption != "" {
		text = msg.Caption
	}

	in := agent.Input{
		ChatID: msg.Chat.ID,
		UserID: msg.From.ID,
		Type:   msgType,
		Text:   text,
		Media:  media,
	}

	out, err := b.agent.Reply(ctx, in)
	if err != nil {
		log.Printf("agent reply error: %v", err)
		out.Text = "Произошла ошибка при обработке сообщения."
	}

	if out.Text == "" {
		return
	}

	outMsg := tgbotapi.NewMessage(update.Message.Chat.ID, out.Text)
	outMsg.ReplyToMessageID = update.Message.MessageID

	if _, err := b.api.Send(outMsg); err != nil {
		log.Printf("failed to send message: %v", err)
	}
}
