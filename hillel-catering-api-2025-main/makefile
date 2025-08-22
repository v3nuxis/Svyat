install:
	pipenv lock && pipenv sync

installdev:
	pipenv lock && pipenv sync --dev

build:
	docker build -t catering-api .

run:
	docker run --rm -p 8000:8000 catering-api

clean:
	docker image prune -f

migrate:
	pipenv run python manage.py migrate

runserver:
	pipenv run python manage.py runserver 0.0.0.0:8000

worker_default:
	watchmedo auto-restart --recursive --pattern='*.py' -- celery -A config worker -l INFO -Q default

worker_high:
	watchmedo auto-restart --recursive --pattern='*.py' -- celery -A config worker -l INFO -Q high_priority

silpo_mock:
	python -m uvicorn tests.providers.silpo:app --port 8001 --reload

kfc_mock:
	python -m uvicorn tests.providers.kfc:app --port 8002 --reload

uklon_mock:
	python -m uvicorn tests.providers.uklon:app --port 8003 --reload

uber_mock:
	python -m uvicorn tests.providers.uber:app --port 8004 --reload

# При обновлении, мейкфайл сразу коммититься
update-makefile:
	@echo "# Auto-update: $$(data)" >> makefile

commit:
	git add makefile
	git commit -m "Auto update Makefile [ci skip]" || echo "No changes to commit"

push:
	git push

auto-update: update-makefile commit push

dev: installdev runserver worker_default

