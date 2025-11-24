run-go:
	go run ./cmd/bot

dev-go:
	air

core-dev:
	cd core && uvicorn app:app --reload --host 0.0.0.0 --port 8000

tg-dev:
	cd tg_bot && python -m main

