.PHONY: bootstrap seed backend frontend test evaluate

bootstrap:
	python scripts/bootstrap.py

seed:
	python scripts/seed_demo.py --reset

backend:
	cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	.venv/bin/python -m pytest backend/tests -q
	cd frontend && npm test

evaluate:
	.venv/bin/python scripts/evaluate.py
