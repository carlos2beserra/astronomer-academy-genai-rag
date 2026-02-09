# ============================================
# 🚀 Academy GenAI - Makefile
# ============================================
# Comandos para gerenciar o ambiente Docker
# ============================================

.PHONY: help up down restart logs logs-airflow logs-weaviate logs-streamlit \
        shell-airflow shell-weaviate shell-streamlit ps clean status \
        build rebuild airflow-ui streamlit-ui weaviate-ui \
        astro-up astro-down astro-kill

# Cores para output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# ============================================
# HELP
# ============================================

help: ## 📖 Mostra esta mensagem de ajuda
	@echo ""
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║       🚀 Academy GenAI - Comandos Disponíveis              ║$(RESET)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# CONTROLE DO AMBIENTE (Docker Compose)
# ============================================

up: ## ▶️  Inicia todos os containers
	@echo "$(GREEN)🚀 Iniciando ambiente...$(RESET)"
	docker compose up -d

down: ## ⏹️  Para todos os containers
	@echo "$(YELLOW)🛑 Parando ambiente...$(RESET)"
	docker compose down

restart: down up ## 🔄 Reinicia todos os containers

kill: ## 💀 Força parada de todos os containers
	@echo "$(RED)💀 Forçando parada...$(RESET)"
	docker compose down -v --remove-orphans

build: ## 🔨 Build das imagens
	@echo "$(CYAN)🔨 Construindo imagens...$(RESET)"
	docker compose build

rebuild: ## 🔨 Rebuild forçado (sem cache)
	@echo "$(CYAN)🔨 Reconstruindo imagens (sem cache)...$(RESET)"
	docker compose build --no-cache

# ============================================
# ASTRO CLI (alternativo)
# ============================================

astro-up: ## ▶️  Inicia via Astro CLI (requer astro instalado)
	@echo "$(GREEN)🚀 Iniciando via Astro CLI...$(RESET)"
	astro dev start

astro-down: ## ⏹️  Para via Astro CLI
	@echo "$(YELLOW)🛑 Parando via Astro CLI...$(RESET)"
	astro dev stop

astro-kill: ## 💀 Força parada via Astro CLI
	@echo "$(RED)💀 Forçando parada...$(RESET)"
	astro dev kill

# ============================================
# LOGS
# ============================================

logs: ## 📋 Mostra logs de todos os containers
	docker compose logs -f

logs-airflow: ## 📋 Logs do Airflow (scheduler + webserver)
	docker compose logs -f scheduler webserver

logs-weaviate: ## 📋 Logs do Weaviate
	docker compose logs -f weaviate

logs-streamlit: ## 📋 Logs do Streamlit
	docker compose logs -f streamlit

# ============================================
# SHELL / ACESSO AOS CONTAINERS
# ============================================

shell-airflow: ## 🐚 Acessa shell do Airflow scheduler
	docker compose exec scheduler /bin/bash

shell-webserver: ## 🐚 Acessa shell do Airflow webserver
	docker compose exec webserver /bin/bash

shell-weaviate: ## 🐚 Acessa shell do Weaviate
	docker compose exec weaviate /bin/sh

shell-streamlit: ## 🐚 Acessa shell do Streamlit
	docker compose exec streamlit /bin/bash

# ============================================
# STATUS E INFORMAÇÕES
# ============================================

ps: ## 📊 Lista containers em execução
	@echo "$(CYAN)📊 Containers em execução:$(RESET)"
	@docker compose ps

status: ## 📊 Status detalhado do ambiente
	@echo ""
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║                    📊 Status do Ambiente                   ║$(RESET)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(GREEN)🌐 URLs de Acesso:$(RESET)"
	@echo "   • Airflow UI:    http://localhost:8080  (admin/admin)"
	@echo "   • Streamlit:     http://localhost:8501"
	@echo "   • Weaviate:      http://localhost:8081"
	@echo ""
	@echo "$(GREEN)🐳 Containers:$(RESET)"
	@docker compose ps --format "   • {{.Name}}: {{.Status}}"
	@echo ""

# ============================================
# LIMPEZA
# ============================================

clean: ## 🧹 Remove containers e volumes órfãos
	@echo "$(YELLOW)🧹 Limpando ambiente...$(RESET)"
	docker compose down -v --remove-orphans
	@echo "$(GREEN)✅ Limpeza concluída$(RESET)"

clean-all: ## 🧹 Limpeza completa (inclui imagens)
	@echo "$(RED)🧹 Limpeza completa...$(RESET)"
	docker compose down -v --remove-orphans --rmi local
	@echo "$(GREEN)✅ Limpeza completa concluída$(RESET)"

clean-weaviate: ## 🧹 Limpa dados do Weaviate
	@echo "$(YELLOW)🧹 Limpando dados do Weaviate...$(RESET)"
	rm -rf include/weaviate/backup/*
	@echo "$(GREEN)✅ Dados do Weaviate limpos$(RESET)"

# ============================================
# ATALHOS PARA ABRIR UIs
# ============================================

airflow-ui: ## 🌐 Abre Airflow UI no navegador
	@echo "$(GREEN)🌐 Abrindo Airflow UI...$(RESET)"
	@xdg-open http://localhost:8080 2>/dev/null || open http://localhost:8080 2>/dev/null || echo "Acesse: http://localhost:8080"

streamlit-ui: ## 🌐 Abre Streamlit no navegador
	@echo "$(GREEN)🌐 Abrindo Streamlit...$(RESET)"
	@xdg-open http://localhost:8501 2>/dev/null || open http://localhost:8501 2>/dev/null || echo "Acesse: http://localhost:8501"

weaviate-ui: ## 🌐 Abre Weaviate Console no navegador
	@echo "$(GREEN)🌐 Abrindo Weaviate Console...$(RESET)"
	@xdg-open http://localhost:8081 2>/dev/null || open http://localhost:8081 2>/dev/null || echo "Acesse: http://localhost:8081"

# ============================================
# DESENVOLVIMENTO
# ============================================

run-dag: ## ▶️  Trigger manual do DAG principal
	@echo "$(GREEN)▶️  Executando DAG...$(RESET)"
	docker compose exec scheduler airflow dags trigger my_first_rag_dag_solution

test-connection: ## 🔌 Testa conexão com Weaviate
	@echo "$(CYAN)🔌 Testando conexão com Weaviate...$(RESET)"
	@curl -s http://localhost:8081/v1/.well-known/ready | jq . 2>/dev/null || curl -s http://localhost:8081/v1/.well-known/ready || echo "$(RED)Weaviate não está respondendo$(RESET)"

install-deps: ## 📦 Instala dependências locais (para desenvolvimento)
	@echo "$(CYAN)📦 Instalando dependências...$(RESET)"
	pip install -r requirements.txt

# ============================================
# SETUP INICIAL
# ============================================

setup: ## 🛠️  Setup inicial do projeto
	@echo "$(CYAN)🛠️  Configurando projeto...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)📝 Criando arquivo .env...$(RESET)"; \
		cp .env_example .env 2>/dev/null || echo "OPENAI_API_KEY=sua-chave-aqui" > .env; \
		echo "$(RED)⚠️  Configure sua OPENAI_API_KEY no arquivo .env$(RESET)"; \
	else \
		echo "$(GREEN)✅ Arquivo .env já existe$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Setup concluído! Execute 'make up' para iniciar.$(RESET)"

