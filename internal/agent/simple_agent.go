package agent

import (
	"context"
	"log"
)

// SimpleAgent — базовая реализация агента без реального LLM.
// Сейчас он по сути умный эхо-бот с возможностью логировать диалоги в Memory.
type SimpleAgent struct {
	llm   LLMClient
	mem   Memory
	tools []Tool
}

func NewSimpleAgent(llm LLMClient, mem Memory, tools []Tool) *SimpleAgent {
	return &SimpleAgent{
		llm:   llm,
		mem:   mem,
		tools: tools,
	}
}

func (a *SimpleAgent) Reply(ctx context.Context, in Input) (Output, error) {
	var text string

	switch in.Type {
	case MessageTypeText:
		// Если есть LLM — можно будет генерировать ответ через неё.
		if a.llm != nil {
			resp, err := a.llm.Generate(ctx, in.Text)
			if err != nil {
				log.Printf("llm error: %v", err)
				text = "Произошла ошибка при генерации ответа. Попробуй ещё раз."
			} else {
				text = resp
			}
		} else {
			// Без LLM — немного более дружелюбный и полезный базовый ответ.
			if in.Text == "" {
				text = "Я — локальный ИИ-бот. Напиши мне вопрос или команду /help, а позже я научусь работать с голосом, файлами и картинками."
			} else {
				switch in.Text {
				case "/start":
					text = "Привет! Я локальный ИИ‑бот на Go. Пиши вопросы, а также скоро смогу обрабатывать голос, файлы и медиа.\n\nДоступные команды сейчас:\n/help — краткая справка."
				case "/help":
					text = "Я пока работаю как умный эхо-бот и запоминаю наши диалоги локально.\nСкоро появится поддержка голоса, файлов, картинок и локального ИИ без платных API."
				default:
					text = "Ты написал: " + in.Text
				}
			}
		}
	case MessageTypeVoice:
		text = "Ты прислал голосовое сообщение. Пока я не умею его распознавать, но в планах — добавить локальное распознавание речи без платных сервисов."
	case MessageTypeImage:
		text = "Крутое изображение! Чуть позже я смогу его анализировать локально, без платных API."
	case MessageTypeVideo:
		text = "Видео получено. В будущем я смогу извлекать из него текст и делать краткие конспекты."
	case MessageTypeFile:
		text = "Файл получен. В roadmap — анализ документов, таблиц и PDF локальными инструментами."
	default:
		text = "Я получил сообщение неизвестного типа. Попробуй отправить текст или воспользуйся командой /help."
	}

	out := Output{Text: text}
	a.appendToMemory(ctx, in, out)
	return out, nil
}

func (a *SimpleAgent) appendToMemory(ctx context.Context, in Input, out Output) {
	if a.mem == nil {
		return
	}
	if err := a.mem.AppendInteraction(ctx, in, out); err != nil {
		log.Printf("memory append error: %v", err)
	}
}


