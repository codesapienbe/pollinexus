.PHONY: train

train:
	# Build and run only the trainer service (rebuild images)
	docker-compose up --build --no-deps trainer

.PHONY: build

build:
	docker-compose build

.PHONY: up

up:
	docker-compose up --build 