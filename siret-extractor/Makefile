.PHONY: help build up down logs restart clean install dev test lint

# Variables
DOCKER_COMPOSE = docker-compose
BACKEND_DIR = backend
FRONTEND_DIR = frontend

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Docker Commands
# ============================================

build: ## Construit les images Docker
	$(DOCKER_COMPOSE) build

up: ## Demarre les conteneurs en arriere-plan
	$(DOCKER_COMPOSE) up -d

down: ## Arrete les conteneurs
	$(DOCKER_COMPOSE) down

restart: ## Redemarre les conteneurs
	$(DOCKER_COMPOSE) restart

logs: ## Affiche les logs des conteneurs
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Affiche les logs du backend
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Affiche les logs du frontend
	$(DOCKER_COMPOSE) logs -f frontend

ps: ## Affiche le statut des conteneurs
	$(DOCKER_COMPOSE) ps

clean: ## Supprime les conteneurs et volumes
	$(DOCKER_COMPOSE) down -v --rmi local

# ============================================
# Development Commands (sans Docker)
# ============================================

install: install-backend install-frontend ## Installe toutes les dependances

install-backend: ## Installe les dependances backend
	cd $(BACKEND_DIR) && pip install -r requirements.txt

install-frontend: ## Installe les dependances frontend
	cd $(FRONTEND_DIR) && npm install

dev: ## Demarre le backend et frontend en mode dev (2 terminaux)
	@echo "Lancez dans 2 terminaux:"
	@echo "  Terminal 1: make dev-backend"
	@echo "  Terminal 2: make dev-frontend"

dev-backend: ## Demarre le backend en mode dev
	cd $(BACKEND_DIR) && python main.py

dev-frontend: ## Demarre le frontend en mode dev
	cd $(FRONTEND_DIR) && npm run dev

# ============================================
# Test & Quality
# ============================================

test: ## Lance les tests backend
	cd $(BACKEND_DIR) && pytest tests/ -v

test-cov: ## Lance les tests avec couverture
	cd $(BACKEND_DIR) && pytest tests/ -v --cov=. --cov-report=html

lint: ## Verifie le code frontend
	cd $(FRONTEND_DIR) && npm run lint

# ============================================
# Build
# ============================================

build-frontend: ## Build le frontend pour production
	cd $(FRONTEND_DIR) && npm run build

# ============================================
# Utilities
# ============================================

shell-backend: ## Ouvre un shell dans le conteneur backend
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-frontend: ## Ouvre un shell dans le conteneur frontend
	$(DOCKER_COMPOSE) exec frontend /bin/sh

env: ## Copie le fichier .env.example vers .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env cree - editez-le avec vos cles API"; \
	else \
		echo ".env existe deja"; \
	fi
