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
	// Пока только текст поддерживаем.
	if in.Type != MessageTypeText {
		out := Output{
			Text: "Пока я понимаю только текстовые сообщения. Скоро научусь работать с голосом, файлами и изображениями.",
		}
		a.appendToMemory(ctx, in, out)
		return out, nil
	}

	// Если есть LLM — можно будет генерировать ответ через неё.
	var text string
	if a.llm != nil {
		resp, err := a.llm.Generate(ctx, in.Text)
		if err != nil {
			log.Printf("llm error: %v", err)
			text = "Произошла ошибка при генерации ответа. Попробуй ещё раз."
		} else {
			text = resp
		}
	} else {
		// Без LLM — простой эхо-ответ с небольшим префиксом.
		if in.Text == "" {
			text = "Отправь мне текст, а позже я смогу обрабатывать голос, файлы и картинки."
		} else {
			text = "Ты написал: " + in.Text
		}
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


