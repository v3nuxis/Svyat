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
	celery -A config worker -Q default -l INFO


worker_high:
	celery -A config worker -Q high_priority -l INFO

silpo:
	uvicorn tests.providers.silpo:app --reload --port 8001

kfc:
	uvicorn tests.providers.kfc:app --reload --port 8002

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