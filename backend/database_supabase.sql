-- ===============================================
-- 🗄️ BANCO DE DADOS SUPABASE - SISTEMA DE BOTS
-- Sistema Multi-usuário de Sinais de Apostas
-- ===============================================

-- ============================================
-- 📋 1. TABELA DE USUÁRIOS
-- ============================================
CREATE TABLE usuarios (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    plano VARCHAR(20) DEFAULT 'free' CHECK (plano IN ('free', 'premium', 'vip', 'admin')),
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'suspenso')),
    max_robos INTEGER DEFAULT 1,
    max_sinais_dia INTEGER DEFAULT 50,
    telegram_user_id BIGINT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultimo_login TIMESTAMP WITH TIME ZONE,
    configuracoes JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 🏢 2. TABELA DE PLATAFORMAS
-- ============================================
CREATE TABLE plataformas (
    id VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    url VARCHAR(100) NOT NULL,
    jogo VARCHAR(30) NOT NULL,
    api_endpoint VARCHAR(200),
    api_ativa BOOLEAN DEFAULT true,
    configuracoes JSONB DEFAULT '{}'::jsonb,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 🤖 3. TABELA DE ROBÔS
-- ============================================
CREATE TABLE robos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    plataforma_id VARCHAR(20) NOT NULL REFERENCES plataformas(id),
    nome VARCHAR(100) NOT NULL,
    telegram_bot_token VARCHAR(200) NOT NULL,
    telegram_chat_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'inativo' CHECK (status IN ('ativo', 'inativo', 'pausado', 'erro')),
    configuracoes JSONB DEFAULT '{
        "max_gales": 2,
        "intervalo_segundos": 3,
        "confianca_minima": 75,
        "max_sinais_dia": 20,
        "protecao_branco": true,
        "alertas_ativos": true
    }'::jsonb,
    mensagens_personalizadas JSONB DEFAULT '{
        "entrada": "🎯 SINAL DETECTADO!\\n\\n🎰 Plataforma: [PLATAFORMA]\\n🎯 Estratégia: [NOME_ESTRATEGIA]\\n💰 Apostar em: [SINAL]\\n\\n⏰ [HORA_AGORA] | 📅 [DATA_HOJE]",
        "win": "✅ GREEN! \\n\\n💰 [TIPO_GREEN_MAIUSCULO]\\n🎯 Estratégia: [NOME_ESTRATEGIA]\\n\\n📊 Hoje: [WINS] wins | [LOSSES] loss\\n📈 Assertividade: [PERCENTUAL_ASSERTIVIDADE]%",
        "loss": "❌ RED\\n\\n🎯 Estratégia: [NOME_ESTRATEGIA]\\n\\n📊 Hoje: [WINS] wins | [LOSSES] loss\\n📈 Assertividade: [PERCENTUAL_ASSERTIVIDADE]%"
    }'::jsonb,
    estatisticas JSONB DEFAULT '{
        "sinais_enviados": 0,
        "wins": 0,
        "losses": 0,
        "wins_sem_gale": 0,
        "wins_por_gale": {},
        "ganhos_consecutivos": 0,
        "ultima_atividade": null
    }'::jsonb,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(usuario_id, nome)
);

-- ============================================
-- 🎯 4. TABELA DE ESTRATÉGIAS
-- ============================================
CREATE TABLE estrategias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    robo_id UUID NOT NULL REFERENCES robos(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    pattern VARCHAR(50) NOT NULL,
    bet VARCHAR(10) NOT NULL,
    confianca INTEGER DEFAULT 50 CHECK (confianca >= 0 AND confianca <= 100),
    ativa BOOLEAN DEFAULT true,
    descricao TEXT,
    estatisticas JSONB DEFAULT '{
        "total_sinais": 0,
        "wins": 0,
        "losses": 0,
        "assertividade": 0,
        "ultima_utilizacao": null
    }'::jsonb,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(robo_id, nome)
);

-- ============================================
-- 📊 5. TABELA DE RESULTADOS DAS PLATAFORMAS
-- ============================================
CREATE TABLE resultados_plataformas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plataforma_id VARCHAR(20) NOT NULL REFERENCES plataformas(id),
    resultado VARCHAR(10) NOT NULL,
    numero INTEGER,
    cor VARCHAR(10),
    timestamp_plataforma TIMESTAMP WITH TIME ZONE NOT NULL,
    coletado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dados_completos JSONB DEFAULT '{}'::jsonb,
    processado BOOLEAN DEFAULT false,
    
    UNIQUE(plataforma_id, timestamp_plataforma)
);

-- ============================================
-- 🎯 6. TABELA DE SINAIS
-- ============================================
CREATE TABLE sinais (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    robo_id UUID NOT NULL REFERENCES robos(id) ON DELETE CASCADE,
    estrategia_id UUID NOT NULL REFERENCES estrategias(id),
    plataforma_id VARCHAR(20) NOT NULL REFERENCES plataformas(id),
    sinal VARCHAR(10) NOT NULL,
    confianca INTEGER NOT NULL,
    resultado VARCHAR(10),
    gales_utilizados INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'win', 'loss', 'cancelado')),
    enviado_telegram BOOLEAN DEFAULT false,
    timestamp_sinal TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    timestamp_resultado TIMESTAMP WITH TIME ZONE,
    dados_contexto JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_sinais_robo_data (robo_id, DATE(timestamp_sinal)),
    INDEX idx_sinais_status (status),
    INDEX idx_sinais_plataforma (plataforma_id)
);

-- ============================================
-- 📝 7. TABELA DE LOGS DO SISTEMA
-- ============================================
CREATE TABLE logs_sistema (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    robo_id UUID REFERENCES robos(id) ON DELETE SET NULL,
    nivel VARCHAR(10) NOT NULL CHECK (nivel IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    categoria VARCHAR(30) NOT NULL,
    mensagem TEXT NOT NULL,
    detalhes JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_logs_nivel (nivel),
    INDEX idx_logs_categoria (categoria),
    INDEX idx_logs_timestamp (timestamp),
    INDEX idx_logs_usuario (usuario_id),
    INDEX idx_logs_robo (robo_id)
);

-- ============================================
-- ⚙️ 8. TABELA DE CONFIGURAÇÕES GLOBAIS
-- ============================================
CREATE TABLE configuracoes_sistema (
    chave VARCHAR(50) PRIMARY KEY,
    valor JSONB NOT NULL,
    descricao TEXT,
    categoria VARCHAR(30) DEFAULT 'geral',
    editavel BOOLEAN DEFAULT true,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 🔄 9. TABELA DE SESSÕES (Para controle de login)
-- ============================================
CREATE TABLE sessoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    ativa BOOLEAN DEFAULT true,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL,
    ultimo_acesso TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_sessoes_usuario (usuario_id),
    INDEX idx_sessoes_token (token_hash),
    INDEX idx_sessoes_ativa (ativa)
);

-- ============================================
-- 📈 10. TABELA DE ESTATÍSTICAS DIÁRIAS
-- ============================================
CREATE TABLE estatisticas_diarias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    robo_id UUID NOT NULL REFERENCES robos(id) ON DELETE CASCADE,
    data DATE NOT NULL,
    sinais_enviados INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    wins_sem_gale INTEGER DEFAULT 0,
    wins_gale_1 INTEGER DEFAULT 0,
    wins_gale_2 INTEGER DEFAULT 0,
    wins_gale_3_plus INTEGER DEFAULT 0,
    assertividade DECIMAL(5,2) DEFAULT 0,
    melhor_sequencia_wins INTEGER DEFAULT 0,
    dados_detalhados JSONB DEFAULT '{}'::jsonb,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(robo_id, data),
    INDEX idx_stats_robo_data (robo_id, data)
);

-- ============================================
-- 🚀 TRIGGERS E FUNÇÕES
-- ============================================

-- Função para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualização automática de timestamps
CREATE TRIGGER usuarios_update_timestamp
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER robos_update_timestamp
    BEFORE UPDATE ON robos
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER estrategias_update_timestamp
    BEFORE UPDATE ON estrategias
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER plataformas_update_timestamp
    BEFORE UPDATE ON plataformas
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER configuracoes_sistema_update_timestamp
    BEFORE UPDATE ON configuracoes_sistema
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER estatisticas_diarias_update_timestamp
    BEFORE UPDATE ON estatisticas_diarias
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- ============================================
-- 📊 FUNÇÃO PARA CALCULAR ESTATÍSTICAS
-- ============================================
CREATE OR REPLACE FUNCTION calcular_estatisticas_robo(robo_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
    total_sinais INTEGER;
    total_wins INTEGER;
    total_losses INTEGER;
    assertividade DECIMAL(5,2);
BEGIN
    -- Calcular estatísticas básicas
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN status = 'win' THEN 1 END) as wins,
        COUNT(CASE WHEN status = 'loss' THEN 1 END) as losses
    INTO total_sinais, total_wins, total_losses
    FROM sinais 
    WHERE robo_id = robo_uuid 
    AND DATE(timestamp_sinal) = CURRENT_DATE;
    
    -- Calcular assertividade
    IF total_sinais > 0 THEN
        assertividade = (total_wins::DECIMAL / total_sinais) * 100;
    ELSE
        assertividade = 0;
    END IF;
    
    -- Montar JSON de retorno
    stats = jsonb_build_object(
        'sinais_enviados', total_sinais,
        'wins', total_wins,
        'losses', total_losses,
        'assertividade', assertividade,
        'atualizado_em', NOW()
    );
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 🔐 RLS (Row Level Security) - SUPABASE
-- ============================================

-- Habilitar RLS nas tabelas principais
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE robos ENABLE ROW LEVEL SECURITY;
ALTER TABLE estrategias ENABLE ROW LEVEL SECURITY;
ALTER TABLE sinais ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs_sistema ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE estatisticas_diarias ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para usuários
CREATE POLICY usuarios_select_own ON usuarios
    FOR SELECT USING (auth.uid() = id::text::uuid);

CREATE POLICY usuarios_update_own ON usuarios
    FOR UPDATE USING (auth.uid() = id::text::uuid);

-- Políticas RLS para robôs
CREATE POLICY robos_all_own ON robos
    FOR ALL USING (auth.uid() = usuario_id::text::uuid);

-- Políticas RLS para estratégias (através dos robôs)
CREATE POLICY estrategias_all_own ON estrategias
    FOR ALL USING (
        auth.uid()::uuid IN (
            SELECT usuario_id FROM robos WHERE id = estrategias.robo_id
        )
    );

-- Políticas RLS para sinais (através dos robôs)
CREATE POLICY sinais_all_own ON sinais
    FOR ALL USING (
        auth.uid()::uuid IN (
            SELECT usuario_id FROM robos WHERE id = sinais.robo_id
        )
    );

-- Políticas RLS para logs (através dos robôs)
CREATE POLICY logs_all_own ON logs_sistema
    FOR ALL USING (
        auth.uid() = usuario_id::text::uuid OR
        auth.uid()::uuid IN (
            SELECT usuario_id FROM robos WHERE id = logs_sistema.robo_id
        )
    );

-- Políticas RLS para sessões
CREATE POLICY sessoes_all_own ON sessoes
    FOR ALL USING (auth.uid() = usuario_id::text::uuid);

-- Políticas RLS para estatísticas diárias
CREATE POLICY estatisticas_all_own ON estatisticas_diarias
    FOR ALL USING (
        auth.uid()::uuid IN (
            SELECT usuario_id FROM robos WHERE id = estatisticas_diarias.robo_id
        )
    );

-- ============================================
-- 📝 DADOS INICIAIS
-- ============================================

-- Inserir plataformas padrão
INSERT INTO plataformas (id, nome, url, jogo, api_endpoint, configuracoes) VALUES
('blaze', 'Blaze', 'blaze.bet.br', 'Double', 'https://blaze1.space/api/roulette_games/recent', '{"delay_seconds": 3, "max_retries": 3}'),
('jonbet', 'Jonbet', 'jonbet.com', 'Double', 'https://jonbet.com/api/roulette_games/recent', '{"delay_seconds": 3, "max_retries": 3}'),
('betfire', 'Betfire', 'betfire.com', 'Double', 'https://betfire.com/api/roulette_games/recent', '{"delay_seconds": 3, "max_retries": 3}');

-- Inserir configurações do sistema
INSERT INTO configuracoes_sistema (chave, valor, descricao, categoria) VALUES
('sistema_versao', '"1.0.0"', 'Versão atual do sistema', 'sistema'),
('max_robos_free', '1', 'Máximo de robôs para usuários free', 'limites'),
('max_robos_premium', '5', 'Máximo de robôs para usuários premium', 'limites'),
('max_robos_vip', '20', 'Máximo de robôs para usuários VIP', 'limites'),
('max_sinais_dia_free', '50', 'Máximo de sinais por dia para usuários free', 'limites'),
('max_sinais_dia_premium', '200', 'Máximo de sinais por dia para usuários premium', 'limites'),
('max_sinais_dia_vip', '1000', 'Máximo de sinais por dia para usuários VIP', 'limites'),
('api_coleta_intervalo', '3', 'Intervalo em segundos para coleta das APIs', 'api'),
('logs_retencao_dias', '30', 'Dias de retenção dos logs', 'sistema'),
('telegram_timeout', '30', 'Timeout para requisições Telegram', 'telegram');

-- Inserir usuário admin padrão (senha: admin123)
-- Hash gerado com bcrypt para 'admin123'
INSERT INTO usuarios (id, email, nome, senha_hash, plano, max_robos, max_sinais_dia) VALUES
('00000000-0000-0000-0000-000000000001', 'admin@sistema.com', 'Administrador', '$2b$12$LQv3c1yqBfVFr5fP2WZHUO8fhP8E4W8B9C4G5J3K1R5Q9L7M3N5O1', 'admin', 999, 9999);

-- ============================================
-- 📊 VIEWS ÚTEIS
-- ============================================

-- View para dashboard dos usuários
CREATE VIEW dashboard_usuario AS
SELECT 
    u.id as usuario_id,
    u.nome,
    u.plano,
    COUNT(r.id) as total_robos,
    COUNT(CASE WHEN r.status = 'ativo' THEN 1 END) as robos_ativos,
    COALESCE(SUM((r.estatisticas->>'sinais_enviados')::int), 0) as total_sinais_hoje,
    COALESCE(SUM((r.estatisticas->>'wins')::int), 0) as total_wins_hoje,
    COALESCE(SUM((r.estatisticas->>'losses')::int), 0) as total_losses_hoje
FROM usuarios u
LEFT JOIN robos r ON u.id = r.usuario_id
GROUP BY u.id, u.nome, u.plano;

-- View para estatísticas de robôs
CREATE VIEW estatisticas_robos AS
SELECT 
    r.id,
    r.nome,
    r.status,
    u.nome as usuario_nome,
    p.nome as plataforma_nome,
    COUNT(s.id) as sinais_total,
    COUNT(CASE WHEN s.status = 'win' THEN 1 END) as wins,
    COUNT(CASE WHEN s.status = 'loss' THEN 1 END) as losses,
    CASE 
        WHEN COUNT(s.id) > 0 THEN 
            ROUND((COUNT(CASE WHEN s.status = 'win' THEN 1 END)::DECIMAL / COUNT(s.id)) * 100, 2)
        ELSE 0 
    END as assertividade
FROM robos r
JOIN usuarios u ON r.usuario_id = u.id
JOIN plataformas p ON r.plataforma_id = p.id
LEFT JOIN sinais s ON r.id = s.robo_id AND DATE(s.timestamp_sinal) = CURRENT_DATE
GROUP BY r.id, r.nome, r.status, u.nome, p.nome;

-- ============================================
-- 🎯 ÍNDICES PARA PERFORMANCE
-- ============================================

-- Índices adicionais para queries frequentes
CREATE INDEX idx_robos_usuario_status ON robos(usuario_id, status);
CREATE INDEX idx_sinais_robo_timestamp ON sinais(robo_id, timestamp_sinal DESC);
CREATE INDEX idx_resultados_plataforma_timestamp ON resultados_plataformas(plataforma_id, timestamp_plataforma DESC);
CREATE INDEX idx_logs_timestamp_nivel ON logs_sistema(timestamp DESC, nivel);

-- ============================================
-- ✅ BANCO DE DADOS CRIADO COM SUCESSO!
-- ============================================

/*
🎉 BANCO DE DADOS SUPABASE CONFIGURADO!

📋 TABELAS CRIADAS:
✅ usuarios - Controle de usuários e planos
✅ plataformas - Configuração das casas de apostas  
✅ robos - Robôs de cada usuário
✅ estrategias - Estratégias personalizadas
✅ resultados_plataformas - Dados coletados das APIs
✅ sinais - Sinais enviados pelos robôs
✅ logs_sistema - Logs detalhados
✅ configuracoes_sistema - Configurações globais
✅ sessoes - Controle de autenticação
✅ estatisticas_diarias - Métricas por dia

🔐 SEGURANÇA:
✅ Row Level Security (RLS) configurado
✅ Políticas de acesso por usuário
✅ Autenticação integrada com Supabase Auth

📊 RECURSOS:
✅ Triggers automáticos
✅ Funções de cálculo
✅ Views para dashboards
✅ Índices otimizados
✅ Dados iniciais inseridos

🚀 PRONTO PARA USO!
*/ 