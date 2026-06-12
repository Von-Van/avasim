.PHONY: test test-baseline test-all benchmark-analysis generate-fixtures help docker-up docker-down docker-logs docker-clean

help:
	@echo "AvaSim Development Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test-baseline     Run baseline regression tests (deterministic fixtures)"
	@echo "  make test-all          Run the full test suite"
	@echo "  make benchmark-analysis Run the canonical Python batch benchmark"
	@echo "  make generate-fixtures Regenerate baseline fixtures (BE CAREFUL!)"
	@echo ""
	@echo "Archived Docker stack (frozen next-gen experiment in archive/):"
	@echo "  make docker-up         Start all services with docker compose"
	@echo "  make docker-down       Stop all services"
	@echo "  make docker-logs       View logs from all services"
	@echo "  make docker-clean      Stop and remove all volumes (DESTRUCTIVE!)"
	@echo ""

test-baseline:
	@echo "Running baseline regression tests..."
	python3 -m unittest tests.test_baseline -v

test-all:
	@echo "Running all tests..."
	python3 -m unittest discover -s tests -t . -v

benchmark-analysis:
	@echo "Running canonical Python analysis benchmark..."
	python3 scripts/benchmark_analysis.py --runs 1000 --seed 12345 --parallelism 1

generate-fixtures:
	@echo "⚠️  Regenerating baseline fixtures - this will overwrite existing baselines!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] && python3 scripts/generate_fixtures.py || echo "Cancelled"

# Archived Docker stack (frozen next-gen experiment)
docker-up:
	@echo "🐳 Starting the archived AvaSim containerized stack..."
	docker compose -f archive/infra/docker/compose.yml up -d
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
	docker compose -f archive/infra/docker/compose.yml down

docker-logs:
	docker compose -f archive/infra/docker/compose.yml logs -f

docker-clean:
	@echo "⚠️  This will remove all containers AND volumes (data will be lost)!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] && \
		docker compose -f archive/infra/docker/compose.yml down -v || echo "Cancelled"
