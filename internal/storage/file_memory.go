package storage

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/ezhigval/ai_bot_telegram/internal/agent"
)

// FileMemory — простейшая реализация Memory, которая пишет диалоги в JSONL-файл.
// Это задел под дальнейшее обучение и анализ истории.
type FileMemory struct {
	path string
	mu   sync.Mutex
}

type interactionRecord struct {
	Timestamp  time.Time         `json:"ts"`
	UserID     int64             `json:"user_id"`
	ChatID     int64             `json:"chat_id"`
	Type       agent.MessageType `json:"type"`
	InputText  string            `json:"input_text"`
	OutputText string            `json:"output_text"`
}

func NewFileMemory(path string) *FileMemory {
	return &FileMemory{path: path}
}

func (m *FileMemory) AppendInteraction(_ context.Context, in agent.Input, out agent.Output) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if err := os.MkdirAll(filepath.Dir(m.path), 0o755); err != nil {
		return err
	}

	f, err := os.OpenFile(m.path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()

	rec := interactionRecord{
		Timestamp:  time.Now().UTC(),
		UserID:     in.UserID,
		ChatID:     in.ChatID,
		Type:       in.Type,
		InputText:  in.Text,
		OutputText: out.Text,
	}

	enc := json.NewEncoder(f)
	if err := enc.Encode(&rec); err != nil {
		return err
	}

	return nil
}

// GetLastInteractionsForUser возвращает последние limit взаимодействий для заданного пользователя.
// Реализация наивная: читает весь JSONL-файл и фильтрует по user_id.
func (m *FileMemory) GetLastInteractionsForUser(_ context.Context, userID int64, limit int) ([]interactionRecord, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	f, err := os.Open(m.path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	defer f.Close()

	dec := json.NewDecoder(f)
	var all []interactionRecord

	for {
		var rec interactionRecord
		if err := dec.Decode(&rec); err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return nil, err
		}
		if rec.UserID == userID {
			all = append(all, rec)
		}
	}

	if limit <= 0 || len(all) <= limit {
		return all, nil
	}

	return all[len(all)-limit:], nil
}
