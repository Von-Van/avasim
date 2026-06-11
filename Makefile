.PHONY: test test-baseline test-all benchmark-analysis help docker-up docker-down docker-logs docker-clean

help:
	@echo "AvaSim Development Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test-baseline     Run Phase 0 baseline regression tests"
	@echo "  make test-all          Run all tests (baseline + feature tests)"
	@echo "  make benchmark-analysis Run the canonical Python batch benchmark"
	@echo "  make generate-fixtures Regenerate baseline fixtures (BE CAREFUL!)"
	@echo ""
	@echo "Docker Stack (Phase 1+):"
	@echo "  make docker-up         Start all services with docker compose"
	@echo "  make docker-down       Stop all services"
	@echo "  make docker-logs       View logs from all services"
	@echo "  make docker-clean      Stop and remove all volumes (DESTRUCTIVE!)"
	@echo ""

test-baseline:
	@echo "Running Phase 0 baseline regression tests..."
	python test_baseline.py

test-all:
	@echo "Running all tests..."
	python -m unittest discover -s . -p 'test_*.py' -v

benchmark-analysis:
	@echo "Running canonical Python analysis benchmark..."
	python scripts/benchmark_analysis.py --runs 1000 --seed 12345 --parallelism 1

generate-fixtures:
	@echo "⚠️  Regenerating baseline fixtures - this will overwrite existing baselines!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] && python scripts/generate_fixtures.py || echo "Cancelled"

# Docker stack management
docker-up:
	@echo "🐳 Starting AvaSim containerized stack..."
	docker compose -f infra/docker/compose.yml up -d
	@echo ""
	@echo "✅ Stack started! Services:"
	@echo "   Orchestrator: http://localhost:3000"
	@echo "   Rules Engine: http://localhost:8080"
	@echo "   PostgreSQL:   localhost:5432"
	@echo "   Redis:        localhost:6379"
	@echo "   MinIO:        http://localhost:9001 (console)"
	@echo ""
	@echo "Check health: make docker-logs"

docker-down:
	@echo "🛑 Stopping AvaSim stack..."
	docker compose -f infra/docker/compose.yml down

docker-logs:
	docker compose -f infra/docker/compose.yml logs -f

docker-clean:
	@echo "⚠️  This will remove all containers AND volumes (data will be lost)!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] && \
		docker compose -f infra/docker/compose.yml down -v || echo "Cancelled"
