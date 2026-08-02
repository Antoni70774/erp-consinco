-- =====================================================================
-- ERP CONSINCO-STYLE  |  SCHEMA POSTGRESQL  |  MÓDULO FUNDAÇÃO
-- Cadastros, Compras, Financeiro, Usuários, Tipos de Operação (CFOP)
-- Preparado para receber os módulos futuros: Estoque, Inventário,
-- Consumo, Perdas, Avarias, Vendas, Relatórios.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS erp;
SET search_path TO erp;

-- ---------------------------------------------------------------------
-- 1. EMPRESAS / LOJAS  (multi-empresa — usado em TODOS os módulos
--    futuros para comparativos "por empresa")
-- ---------------------------------------------------------------------
CREATE TABLE empresas (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(10) UNIQUE NOT NULL,
    razao_social    VARCHAR(150) NOT NULL,
    nome_fantasia   VARCHAR(150),
    cnpj            VARCHAR(18) UNIQUE NOT NULL,
    inscricao_estadual VARCHAR(20),
    tipo            VARCHAR(20) NOT NULL DEFAULT 'LOJA', -- LOJA, CD, MATRIZ
    endereco        VARCHAR(200),
    cidade          VARCHAR(100),
    uf              CHAR(2),
    cep             VARCHAR(10),
    telefone        VARCHAR(20),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 2. USUÁRIOS E SENHAS (item 13) + PERFIS DE ACESSO
-- ---------------------------------------------------------------------
CREATE TABLE perfis_acesso (
    id              SERIAL PRIMARY KEY,
    descricao       VARCHAR(60) UNIQUE NOT NULL,   -- ADMIN, GERENTE, OPERADOR, ESTOQUISTA...
    permissoes      JSONB NOT NULL DEFAULT '{}'::jsonb -- {"estoque": "rw", "financeiro": "r", ...}
);

CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    login           VARCHAR(60) UNIQUE NOT NULL,
    email           VARCHAR(120),
    senha_hash      VARCHAR(255) NOT NULL,
    perfil_id       INTEGER REFERENCES perfis_acesso(id),
    empresa_id      INTEGER REFERENCES empresas(id),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_login    TIMESTAMP,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE usuarios_log (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER REFERENCES usuarios(id),
    acao            VARCHAR(30) NOT NULL,   -- LOGIN, LOGOUT, LOGIN_FALHO, ALTERACAO_SENHA
    ip_origem       VARCHAR(45),
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 3. TIPOS DE OPERAÇÃO (item 14) — CFOP por situação
--    Ex.: Venda CFOP 5.102, Perda/Quebra CFOP 5.927 (exemplo genérico),
--    Avaria, Transferência, Devolução, Bonificação, Consumo Interno...
-- ---------------------------------------------------------------------
CREATE TABLE tipos_operacao (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(10) UNIQUE NOT NULL,     -- código interno do sistema
    cfop            VARCHAR(6) NOT NULL,             -- ex: 5102, 5927, 5949
    descricao       VARCHAR(150) NOT NULL,
    categoria       VARCHAR(20) NOT NULL,            -- VENDA, COMPRA, PERDA, AVARIA,
                                                       -- TRANSFERENCIA, DEVOLUCAO,
                                                       -- CONSUMO, BONIFICACAO, INVENTARIO
    movimenta_estoque BOOLEAN NOT NULL DEFAULT TRUE,
    natureza        VARCHAR(10) NOT NULL,            -- ENTRADA / SAIDA
    gera_financeiro BOOLEAN NOT NULL DEFAULT FALSE,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    observacao      VARCHAR(255)
);

-- ---------------------------------------------------------------------
-- 4. CADASTROS GERAIS (item 8)
-- ---------------------------------------------------------------------
CREATE TABLE fornecedores (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    razao_social    VARCHAR(150) NOT NULL,
    nome_fantasia   VARCHAR(150),
    cnpj_cpf        VARCHAR(18) UNIQUE NOT NULL,
    inscricao_estadual VARCHAR(20),
    tipo_pessoa     CHAR(1) NOT NULL DEFAULT 'J',   -- F / J
    endereco        VARCHAR(200),
    cidade          VARCHAR(100),
    uf              CHAR(2),
    cep             VARCHAR(10),
    telefone        VARCHAR(20),
    email           VARCHAR(120),
    contato_nome    VARCHAR(100),
    prazo_entrega_dias INTEGER DEFAULT 0,
    condicao_pagamento VARCHAR(100),
    banco_dados     JSONB DEFAULT '{}'::jsonb,       -- banco/agencia/conta
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE transportadoras (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    razao_social    VARCHAR(150) NOT NULL,
    cnpj            VARCHAR(18) UNIQUE NOT NULL,
    inscricao_estadual VARCHAR(20),
    endereco        VARCHAR(200),
    cidade          VARCHAR(100),
    uf              CHAR(2),
    telefone        VARCHAR(20),
    email           VARCHAR(120),
    tipo_frete      VARCHAR(10) DEFAULT 'CIF',      -- CIF / FOB
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE funcionarios (
    id              SERIAL PRIMARY KEY,
    matricula       VARCHAR(20) UNIQUE NOT NULL,
    nome            VARCHAR(120) NOT NULL,
    cpf             VARCHAR(14) UNIQUE NOT NULL,
    cargo           VARCHAR(80),
    setor           VARCHAR(80),
    empresa_id      INTEGER REFERENCES empresas(id),
    data_admissao   DATE,
    data_demissao   DATE,
    telefone        VARCHAR(20),
    email           VARCHAR(120),
    usuario_id      INTEGER REFERENCES usuarios(id),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE clientes (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    nome            VARCHAR(150) NOT NULL,
    cnpj_cpf        VARCHAR(18) UNIQUE,
    tipo_pessoa     CHAR(1) NOT NULL DEFAULT 'F',
    inscricao_estadual VARCHAR(20),
    endereco        VARCHAR(200),
    cidade          VARCHAR(100),
    uf              CHAR(2),
    cep             VARCHAR(10),
    telefone        VARCHAR(20),
    email           VARCHAR(120),
    data_nascimento DATE,
    limite_credito  NUMERIC(14,2) DEFAULT 0,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 5. PRODUTOS (item 9) — cadastro completo com dados fiscais
-- ---------------------------------------------------------------------
CREATE TABLE categorias_produto (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    descricao       VARCHAR(100) NOT NULL,
    categoria_pai_id INTEGER REFERENCES categorias_produto(id) -- permite subcategoria/seção
);

CREATE TABLE produtos (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30) UNIQUE NOT NULL,
    codigo_barras   VARCHAR(30),         -- EAN/GTIN
    descricao       VARCHAR(200) NOT NULL,
    descricao_reduzida VARCHAR(60),
    categoria_id    INTEGER REFERENCES categorias_produto(id),
    unidade_compra  VARCHAR(10) NOT NULL DEFAULT 'UN',
    unidade_venda   VARCHAR(10) NOT NULL DEFAULT 'UN',
    fator_conversao NUMERIC(10,4) NOT NULL DEFAULT 1,
    fornecedor_principal_id INTEGER REFERENCES fornecedores(id),

    -- Dados fiscais
    ncm             VARCHAR(10),
    cest            VARCHAR(10),
    origem_mercadoria CHAR(1) DEFAULT '0',      -- tabela origem NF-e 0..8
    cfop_padrao_saida VARCHAR(6),
    cfop_padrao_entrada VARCHAR(6),
    cst_icms        VARCHAR(4),
    aliquota_icms   NUMERIC(5,2) DEFAULT 0,
    cst_pis         VARCHAR(4),
    aliquota_pis    NUMERIC(5,2) DEFAULT 0,
    cst_cofins      VARCHAR(4),
    aliquota_cofins NUMERIC(5,2) DEFAULT 0,
    cst_ipi         VARCHAR(4),
    aliquota_ipi    NUMERIC(5,2) DEFAULT 0,
    percentual_mva  NUMERIC(6,2) DEFAULT 0,      -- ICMS-ST
    peso_liquido_kg NUMERIC(10,3),
    peso_bruto_kg   NUMERIC(10,3),

    -- Dados comerciais / estoque (base p/ módulo de Estoque futuro)
    preco_custo     NUMERIC(14,4) DEFAULT 0,
    preco_venda     NUMERIC(14,4) DEFAULT 0,
    margem_lucro    NUMERIC(6,2) DEFAULT 0,
    estoque_minimo  NUMERIC(14,3) DEFAULT 0,
    estoque_maximo  NUMERIC(14,3) DEFAULT 0,
    estoque_atual   NUMERIC(14,3) DEFAULT 0,      -- consolidado; detalhado por empresa em estoque_saldo (módulo 2)
    validade_controlada BOOLEAN DEFAULT FALSE,
    curva_abc       CHAR(1),                      -- A / B / C — calculado pelo módulo de análise

    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX idx_produtos_codigo_barras ON produtos(codigo_barras);

-- ---------------------------------------------------------------------
-- 6. COMPRAS (item 10) — cabeçalho + itens
-- ---------------------------------------------------------------------
CREATE TABLE compras (
    id              SERIAL PRIMARY KEY,
    numero_pedido   VARCHAR(20) UNIQUE NOT NULL,
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    fornecedor_id   INTEGER NOT NULL REFERENCES fornecedores(id),
    transportadora_id INTEGER REFERENCES transportadoras(id),
    tipo_operacao_id INTEGER REFERENCES tipos_operacao(id),
    usuario_id      INTEGER REFERENCES usuarios(id),
    numero_nf       VARCHAR(20),
    serie_nf        VARCHAR(5),
    chave_nfe       VARCHAR(44),
    data_pedido     DATE NOT NULL DEFAULT CURRENT_DATE,
    data_entrega_prevista DATE,
    data_entrega_real DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'ABERTO', -- ABERTO, APROVADO, EM_TRANSITO, RECEBIDO_PARCIAL, RECEBIDO, CANCELADO
    valor_produtos  NUMERIC(14,2) DEFAULT 0,
    valor_frete     NUMERIC(14,2) DEFAULT 0,
    valor_desconto  NUMERIC(14,2) DEFAULT 0,
    valor_icms_st   NUMERIC(14,2) DEFAULT 0,
    valor_total     NUMERIC(14,2) DEFAULT 0,
    condicao_pagamento VARCHAR(100),
    observacao      TEXT,
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE compras_itens (
    id              SERIAL PRIMARY KEY,
    compra_id       INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    produto_id      INTEGER NOT NULL REFERENCES produtos(id),
    quantidade_pedida NUMERIC(14,3) NOT NULL,
    quantidade_recebida NUMERIC(14,3) DEFAULT 0,
    valor_unitario  NUMERIC(14,4) NOT NULL,
    valor_desconto  NUMERIC(14,2) DEFAULT 0,
    valor_total     NUMERIC(14,2) NOT NULL,
    cfop            VARCHAR(6),
    ncm             VARCHAR(10),
    lote            VARCHAR(30),
    data_validade   DATE
);

CREATE INDEX idx_compras_itens_compra ON compras_itens(compra_id);
CREATE INDEX idx_compras_fornecedor ON compras(fornecedor_id);
CREATE INDEX idx_compras_empresa ON compras(empresa_id);

-- ---------------------------------------------------------------------
-- 7. FINANCEIRO (item 12) — contas a pagar / receber
-- ---------------------------------------------------------------------
CREATE TABLE plano_contas (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,
    descricao       VARCHAR(120) NOT NULL,
    tipo            VARCHAR(10) NOT NULL   -- RECEITA / DESPESA
);

CREATE TABLE contas_pagar (
    id              SERIAL PRIMARY KEY,
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    fornecedor_id   INTEGER NOT NULL REFERENCES fornecedores(id),
    compra_id       INTEGER REFERENCES compras(id),
    plano_conta_id  INTEGER REFERENCES plano_contas(id),
    numero_documento VARCHAR(30),
    parcela         INTEGER DEFAULT 1,
    total_parcelas  INTEGER DEFAULT 1,
    valor_original  NUMERIC(14,2) NOT NULL,
    valor_juros     NUMERIC(14,2) DEFAULT 0,
    valor_desconto  NUMERIC(14,2) DEFAULT 0,
    valor_pago      NUMERIC(14,2) DEFAULT 0,
    data_emissao    DATE NOT NULL DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_pagamento  DATE,
    forma_pagamento VARCHAR(30),
    status          VARCHAR(20) NOT NULL DEFAULT 'ABERTO', -- ABERTO, PAGO, ATRASADO, CANCELADO
    observacao      VARCHAR(255),
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE contas_receber (
    id              SERIAL PRIMARY KEY,
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    venda_id        INTEGER,  -- referência futura ao módulo de Vendas
    plano_conta_id  INTEGER REFERENCES plano_contas(id),
    numero_documento VARCHAR(30),
    parcela         INTEGER DEFAULT 1,
    total_parcelas  INTEGER DEFAULT 1,
    valor_original  NUMERIC(14,2) NOT NULL,
    valor_juros     NUMERIC(14,2) DEFAULT 0,
    valor_desconto  NUMERIC(14,2) DEFAULT 0,
    valor_recebido  NUMERIC(14,2) DEFAULT 0,
    data_emissao    DATE NOT NULL DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_recebimento DATE,
    forma_recebimento VARCHAR(30),
    status          VARCHAR(20) NOT NULL DEFAULT 'ABERTO',
    observacao      VARCHAR(255),
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_cp_vencimento ON contas_pagar(data_vencimento);
CREATE INDEX idx_cr_vencimento ON contas_receber(data_vencimento);
CREATE INDEX idx_cp_status ON contas_pagar(status);
CREATE INDEX idx_cr_status ON contas_receber(status);

-- =====================================================================
-- TABELAS-ÂNCORA PARA OS PRÓXIMOS MÓDULOS (referenciadas pelo roadmap,
-- criadas vazias/mínimas aqui para não quebrar FKs futuras)
-- =====================================================================

-- Saldo de estoque por empresa/produto (módulo 2 - Estoque)
CREATE TABLE estoque_saldo (
    id              SERIAL PRIMARY KEY,
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    produto_id      INTEGER NOT NULL REFERENCES produtos(id),
    quantidade      NUMERIC(14,3) NOT NULL DEFAULT 0,
    valor_medio     NUMERIC(14,4) NOT NULL DEFAULT 0,
    atualizado_em   TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE(empresa_id, produto_id)
);

-- Movimentações de estoque (kardex) — todo módulo (venda/perda/avaria/
-- inventário/consumo/compra) grava aqui usando tipos_operacao
CREATE TABLE estoque_movimentos (
    id              SERIAL PRIMARY KEY,
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    produto_id      INTEGER NOT NULL REFERENCES produtos(id),
    tipo_operacao_id INTEGER NOT NULL REFERENCES tipos_operacao(id),
    documento_origem VARCHAR(30),          -- ex: NF, pedido, boletim de inventário
    quantidade      NUMERIC(14,3) NOT NULL,
    valor_unitario  NUMERIC(14,4) NOT NULL DEFAULT 0,
    saldo_apos      NUMERIC(14,3),
    usuario_id      INTEGER REFERENCES usuarios(id),
    criado_em       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_mov_produto ON estoque_movimentos(produto_id, empresa_id);
CREATE INDEX idx_mov_tipo ON estoque_movimentos(tipo_operacao_id);
CREATE INDEX idx_mov_data ON estoque_movimentos(criado_em);

COMMENT ON TABLE estoque_movimentos IS
'Kardex central. Módulos futuros de Estoque/Inventário/Consumo/Perdas/Avarias/Vendas
gravam e leem esta tabela filtrando por categoria em tipos_operacao.';
