# PRD - Sistema de Gerenciamento de Salas de Sinais Telegram

## 1. Visão Geral do Produto

### 1.1 Objetivo
Desenvolver uma plataforma SaaS para gerenciar múltiplas salas de sinais do Telegram, permitindo que usuários criem, configurem e monitorem bots de sinais automatizados para jogos online (inicialmente Blaze Double).

### 1.2 Problema Atual
- Gerenciamento manual de bots solo
- Dificuldade para escalar múltiplas salas
- Configurações hardcoded no código
- Impossibilidade de personalização por usuário
- Falta de interface para gerenciar estratégias

### 1.3 Solução Proposta
Sistema web completo que permite:
- Criação e gerenciamento de múltiplas salas de sinais
- Interface intuitiva para configurar estratégias
- Personalização de mensagens e stickers
- Dashboard de monitoramento em tempo real
- Sistema multi-tenant para múltiplos usuários

## 2. Personas e Casos de Uso

### 2.1 Persona Principal: Operador de Sinais
- **Perfil**: Pessoa que opera salas de sinais do Telegram
- **Necessidades**: 
  - Gerenciar múltiplas salas simultaneamente
  - Personalizar estratégias e mensagens
  - Monitorar performance em tempo real
  - Escalar operação sem complexidade técnica

### 2.2 Casos de Uso Principais
1. **UC001**: Cadastrar nova sala de sinais
2. **UC002**: Configurar bot do Telegram para sala
3. **UC003**: Criar e editar estratégias personalizadas
4. **UC004**: Personalizar templates de mensagens
5. **UC005**: Monitorar resultados em tempo real
6. **UC006**: Gerenciar usuários e permissões
7. **UC007**: Exportar relatórios de performance

## 3. Funcionalidades Principais

### 3.1 Core Features - MVP

#### 3.1.1 Autenticação e Usuários
- Sistema de login/registro
- Autenticação JWT
- Perfis de usuário (Admin, Operador)
- Multi-tenancy (isolamento por usuário)

#### 3.1.2 Gerenciamento de Salas
- **CRUD de Salas**: Criar, listar, editar, deletar salas
- **Configuração de Bot**: 
  - Token do bot Telegram
  - Chat ID da sala
  - Status (ativo/inativo)
  - Configurações de proteção e gales
- **Templates de Sala**: Modelos pré-configurados

#### 3.1.3 Sistema de Estratégias
- **Interface Visual**: Criador de estratégias sem código
- **Lógica Flexível**: 
  - Condições baseadas em sequências (números/cores)
  - Wildcards (X = qualquer valor)
  - Operadores lógicos (AND/OR)
- **Import/Export**: Importar CSV existente e exportar estratégias
- **Versionamento**: Histórico de mudanças nas estratégias

#### 3.1.4 Personalização de Mensagens
- **Templates Customizáveis**:
  - Mensagem de sinal
  - Mensagem de alerta
  - Mensagem de gale
  - Mensagem de resultado
  - Placar diário
- **Variáveis Dinâmicas**: {cor}, {gale}, {assertividade}, etc.
- **Stickers Personalizados**: Upload e configuração de stickers

#### 3.1.5 Monitor de Dados
- **Integração API Blaze**: Monitoramento em tempo real
- **Múltiplas Fontes**: Preparado para outros jogos
- **Cache Inteligente**: Otimização de requests
- **Fallback**: Sistema de redundância

### 3.2 Features Avançadas - Fase 2

#### 3.2.1 Dashboard Analytics
- **Métricas em Tempo Real**:
  - Taxa de assertividade por sala
  - Número de sinais enviados
  - Performance por estratégia
  - Estatísticas de gales
- **Gráficos Interativos**: Charts de performance
- **Alertas**: Notificações de baixa performance

#### 3.2.2 Automação Avançada
- **Agendamento**: Horários específicos para operar
- **Condições de Parada**: Stop loss automático
- **Rotação de Estratégias**: Alternância automática
- **Machine Learning**: Otimização baseada em histórico

#### 3.2.3 Integração e APIs
- **Webhook System**: Notificações externas
- **API REST**: Integração com sistemas externos
- **Telegram Bot Manager**: Bot principal para gerenciar salas
- **Export de Dados**: Relatórios e backups

## 4. Arquitetura Técnica

### 4.1 Stack Tecnológico

#### 4.1.1 Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + Redis (cache)
- **ORM**: SQLAlchemy
- **Queue**: Celery + Redis
- **Auth**: JWT + bcrypt
- **Monitoring**: Prometheus + Grafana

#### 4.1.2 Frontend  
- **Framework**: React.js + TypeScript
- **UI Library**: Ant Design ou Material-UI
- **State Management**: Redux Toolkit
- **Charts**: Chart.js ou Recharts
- **WebSocket**: Socket.io para tempo real

#### 4.1.3 Infrastructure
- **Container**: Docker + Docker Compose
- **Deploy**: AWS/DigitalOcean
- **Proxy**: Nginx
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry + LogRocket

### 4.2 Arquitetura de Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web     │    │   API Gateway   │    │   FastAPI       │
│   Dashboard     │◄──►│   (Nginx)       │◄──►│   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │   PostgreSQL    │
                                               │   Database      │
                                               └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Celery        │    │   Redis         │
│   Bot Manager   │◄──►│   Workers       │◄──►│   Cache/Queue   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4.3 Database Schema (Principal)

#### 4.3.1 Tabelas Core
```sql
-- Users
users (id, email, password_hash, name, plan, created_at, updated_at)

-- Signal Rooms
signal_rooms (id, user_id, name, bot_token, chat_id, status, config, created_at)

-- Strategies  
strategies (id, user_id, name, conditions, bet_direction, active, created_at)

-- Room Strategies (Many-to-Many)
room_strategies (room_id, strategy_id, priority, active)

-- Message Templates
message_templates (id, user_id, room_id, type, template, variables)

-- Results History
results_history (id, room_id, strategy_id, result, bet_color, timestamp)

-- Statistics
room_statistics (id, room_id, date, wins, losses, brancos, assertiveness)
```

## 5. MVP - Roadmap de Desenvolvimento

### 5.1 Sprint 1 (2 semanas) - Backend Core
- [ ] Setup inicial do projeto (FastAPI + PostgreSQL)
- [ ] Sistema de autenticação JWT
- [ ] CRUD de usuários
- [ ] CRUD de salas de sinais
- [ ] Sistema de configuração básico

### 5.2 Sprint 2 (2 semanas) - Sistema de Estratégias
- [ ] CRUD de estratégias
- [ ] Parser de estratégias CSV
- [ ] Engine de execução de estratégias
- [ ] Integração com API Blaze
- [ ] Sistema de cache Redis

### 5.3 Sprint 3 (2 semanas) - Bot Manager
- [ ] Core do bot manager
- [ ] Sistema de templates de mensagens
- [ ] Envio de sinais via Telegram
- [ ] Controle de gales e resultados
- [ ] Logs e monitoramento básico

### 5.4 Sprint 4 (2 semanas) - Frontend MVP
- [ ] Setup React + TypeScript
- [ ] Sistema de login/registro
- [ ] Dashboard principal
- [ ] Gerenciamento de salas
- [ ] Configuração de estratégias
- [ ] Templates de mensagens

### 5.5 Sprint 5 (1 semana) - Integração e Testes
- [ ] Integração frontend/backend
- [ ] Testes end-to-end
- [ ] Deploy inicial
- [ ] Documentação básica

## 6. Métricas de Sucesso

### 6.1 Métricas Técnicas
- **Performance**: Latência < 200ms para 95% das requests
- **Disponibilidade**: 99.5% uptime
- **Escalabilidade**: Suportar 100+ salas simultâneas
- **Confiabilidade**: < 1% de sinais perdidos

### 6.2 Métricas de Produto
- **Adoção**: 50+ usuários cadastrados em 3 meses
- **Engajamento**: 80% dos usuários ativos mensalmente
- **Eficiência**: Redução de 70% no tempo de configuração vs método manual
- **Satisfação**: NPS > 50

## 7. Considerações de Segurança

### 7.1 Proteção de Dados
- Criptografia de tokens do Telegram
- Sanitização de inputs
- Rate limiting nas APIs
- Auditoria de ações sensíveis

### 7.2 Conformidade
- LGPD compliance
- Logs de auditoria
- Backup automático
- Políticas de retenção de dados

## 8. Limitações e Riscos

### 8.1 Riscos Técnicos
- **Dependência API Externa**: Blaze pode alterar API
- **Rate Limit Telegram**: Limitações de envio de mensagens
- **Escalabilidade**: Crescimento além da capacidade

### 8.2 Mitigações
- Sistema de fallback para APIs
- Queue system para gerenciar rate limits
- Arquitetura preparada para escala horizontal

## 9. Próximos Passos

1. **Aprovação do PRD** ✓
2. **Setup do ambiente de desenvolvimento**
3. **Início do Sprint 1 - Backend Core**
4. **Criação dos repositórios Git**
5. **Configuração do CI/CD básico**

---

*Este PRD será atualizado conforme o desenvolvimento progride e novos requisitos são identificados.* 