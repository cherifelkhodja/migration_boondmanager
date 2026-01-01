#!/bin/bash

# Script de gestion du projet SIRET Extractor
# Usage: ./run.sh <command>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$1" in
    # Docker commands
    build)
        echo "Construction des images Docker..."
        docker-compose build
        ;;
    up)
        echo "Demarrage des conteneurs..."
        docker-compose up -d
        echo "Application disponible sur http://localhost"
        ;;
    down)
        echo "Arret des conteneurs..."
        docker-compose down
        ;;
    restart)
        echo "Redemarrage des conteneurs..."
        docker-compose restart
        ;;
    logs)
        docker-compose logs -f
        ;;
    ps)
        docker-compose ps
        ;;
    clean)
        echo "Nettoyage complet..."
        docker-compose down -v --rmi local
        ;;

    # Development commands
    install)
        echo "Installation des dependances..."
        cd backend && pip install -r requirements.txt
        cd ../frontend && npm install
        ;;
    dev-backend)
        echo "Demarrage du backend en mode dev..."
        cd backend && python main.py
        ;;
    dev-frontend)
        echo "Demarrage du frontend en mode dev..."
        cd frontend && npm run dev
        ;;
    test)
        echo "Execution des tests..."
        cd backend && pytest tests/ -v
        ;;

    # Setup
    env)
        if [ ! -f .env ]; then
            cp .env.example .env
            echo ".env cree - editez-le avec vos cles API"
        else
            echo ".env existe deja"
        fi
        ;;

    # Help
    help|*)
        echo "Usage: ./run.sh <command>"
        echo ""
        echo "Docker:"
        echo "  build       Construit les images Docker"
        echo "  up          Demarre les conteneurs"
        echo "  down        Arrete les conteneurs"
        echo "  restart     Redemarre les conteneurs"
        echo "  logs        Affiche les logs"
        echo "  ps          Affiche le statut"
        echo "  clean       Supprime tout"
        echo ""
        echo "Development:"
        echo "  install     Installe les dependances"
        echo "  dev-backend   Demarre le backend (port 8000)"
        echo "  dev-frontend  Demarre le frontend (port 5173)"
        echo "  test        Lance les tests"
        echo ""
        echo "Setup:"
        echo "  env         Cree le fichier .env"
        ;;
esac
