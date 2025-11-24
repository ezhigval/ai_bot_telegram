package agent

import "context"

// MessageType описывает тип входящего/исходящего сообщения.
type MessageType string

const (
	MessageTypeText  MessageType = "text"
	MessageTypeVoice MessageType = "voice"
	MessageTypeImage MessageType = "image"
	MessageTypeVideo MessageType = "video"
	MessageTypeFile  MessageType = "file"
)

// Media — метаданные о медиа/файле из Telegram.
type Media struct {
	FileID   string
	FileName string
	MimeType string
	FileSize int64
}

// Input — то, что агент получает для обработки.
type Input struct {
	ChatID int64
	UserID int64

	Type MessageType

	Text string

	// Media — необязательные данные о файле/медиа-сообщении.
	// Для текстовых сообщений обычно nil.
	Media *Media
}

// Output — базовый ответ агента.
// Позже сюда можно добавить голос, файлы, изображения и т.д.
type Output struct {
	Text string
}

// Agent — основной интерфейс ИИ-агента.
type Agent interface {
	Reply(ctx context.Context, in Input) (Output, error)
}

// LLMClient — абстракция над любым LLM (локальная модель или внешний бесплатный API).
type LLMClient interface {
	Generate(ctx context.Context, prompt string) (string, error)
}

// Memory — интерфейс для хранения взаимодействий (обучение на истории диалогов).
type Memory interface {
	AppendInteraction(ctx context.Context, in Input, out Output) error
}

// Tool — любой инструмент агента (веб-поиск, анализ файлов, мультимедиа и т.п.).
type Tool interface {
	Name() string
	Execute(ctx context.Context, in Input) (string, error)
}
