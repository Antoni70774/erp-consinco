from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, Date, DateTime, ForeignKey,
    Text, CHAR
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Empresa(Base):
    __tablename__ = "empresas"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(10), unique=True, nullable=False)
    razao_social = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150))
    cnpj = Column(String(18), unique=True, nullable=False)
    inscricao_estadual = Column(String(20))
    tipo = Column(String(20), nullable=False, default="LOJA")
    endereco = Column(String(200))
    cidade = Column(String(100))
    uf = Column(CHAR(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class PerfilAcesso(Base):
    __tablename__ = "perfis_acesso"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    descricao = Column(String(60), unique=True, nullable=False)
    permissoes = Column(JSONB, default={})


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    login = Column(String(60), unique=True, nullable=False)
    email = Column(String(120))
    senha_hash = Column(String(255), nullable=False)
    perfil_id = Column(Integer, ForeignKey("erp.perfis_acesso.id"))
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"))
    ativo = Column(Boolean, default=True, nullable=False)
    ultimo_login = Column(DateTime)
    criado_em = Column(DateTime, server_default=func.now())

    perfil = relationship("PerfilAcesso")
    empresa = relationship("Empresa")


class TipoOperacao(Base):
    __tablename__ = "tipos_operacao"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(10), unique=True, nullable=False)
    cfop = Column(String(6), nullable=False)
    descricao = Column(String(150), nullable=False)
    categoria = Column(String(20), nullable=False)
    movimenta_estoque = Column(Boolean, default=True, nullable=False)
    natureza = Column(String(10), nullable=False)
    gera_financeiro = Column(Boolean, default=False, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    observacao = Column(String(255))


class Fornecedor(Base):
    __tablename__ = "fornecedores"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    razao_social = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150))
    cnpj_cpf = Column(String(18), unique=True, nullable=False)
    inscricao_estadual = Column(String(20))
    tipo_pessoa = Column(CHAR(1), default="J", nullable=False)
    endereco = Column(String(200))
    cidade = Column(String(100))
    uf = Column(CHAR(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(120))
    contato_nome = Column(String(100))
    prazo_entrega_dias = Column(Integer, default=0)
    condicao_pagamento = Column(String(100))
    banco_dados = Column(JSONB, default={})
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class Transportadora(Base):
    __tablename__ = "transportadoras"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    razao_social = Column(String(150), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    inscricao_estadual = Column(String(20))
    endereco = Column(String(200))
    cidade = Column(String(100))
    uf = Column(CHAR(2))
    telefone = Column(String(20))
    email = Column(String(120))
    tipo_frete = Column(String(10), default="CIF")
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class Funcionario(Base):
    __tablename__ = "funcionarios"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    matricula = Column(String(20), unique=True, nullable=False)
    nome = Column(String(120), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    cargo = Column(String(80))
    setor = Column(String(80))
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"))
    data_admissao = Column(Date)
    data_demissao = Column(Date)
    telefone = Column(String(20))
    email = Column(String(120))
    usuario_id = Column(Integer, ForeignKey("erp.usuarios.id"))
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nome = Column(String(150), nullable=False)
    cnpj_cpf = Column(String(18), unique=True)
    tipo_pessoa = Column(CHAR(1), default="F", nullable=False)
    inscricao_estadual = Column(String(20))
    endereco = Column(String(200))
    cidade = Column(String(100))
    uf = Column(CHAR(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(120))
    data_nascimento = Column(Date)
    limite_credito = Column(Numeric(14, 2), default=0)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class CategoriaProduto(Base):
    __tablename__ = "categorias_produto"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    descricao = Column(String(100), nullable=False)
    categoria_pai_id = Column(Integer, ForeignKey("erp.categorias_produto.id"))


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(30), unique=True, nullable=False)
    codigo_barras = Column(String(30))
    descricao = Column(String(200), nullable=False)
    descricao_reduzida = Column(String(60))
    categoria_id = Column(Integer, ForeignKey("erp.categorias_produto.id"))
    unidade_compra = Column(String(10), default="UN", nullable=False)
    unidade_venda = Column(String(10), default="UN", nullable=False)
    fator_conversao = Column(Numeric(10, 4), default=1, nullable=False)
    fornecedor_principal_id = Column(Integer, ForeignKey("erp.fornecedores.id"))

    ncm = Column(String(10))
    cest = Column(String(10))
    origem_mercadoria = Column(CHAR(1), default="0")
    cfop_padrao_saida = Column(String(6))
    cfop_padrao_entrada = Column(String(6))
    cst_icms = Column(String(4))
    aliquota_icms = Column(Numeric(5, 2), default=0)
    cst_pis = Column(String(4))
    aliquota_pis = Column(Numeric(5, 2), default=0)
    cst_cofins = Column(String(4))
    aliquota_cofins = Column(Numeric(5, 2), default=0)
    cst_ipi = Column(String(4))
    aliquota_ipi = Column(Numeric(5, 2), default=0)
    percentual_mva = Column(Numeric(6, 2), default=0)
    peso_liquido_kg = Column(Numeric(10, 3))
    peso_bruto_kg = Column(Numeric(10, 3))

    preco_custo = Column(Numeric(14, 4), default=0)
    preco_venda = Column(Numeric(14, 4), default=0)
    margem_lucro = Column(Numeric(6, 2), default=0)
    estoque_minimo = Column(Numeric(14, 3), default=0)
    estoque_maximo = Column(Numeric(14, 3), default=0)
    estoque_atual = Column(Numeric(14, 3), default=0)
    validade_controlada = Column(Boolean, default=False)
    curva_abc = Column(CHAR(1))

    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now())

    categoria = relationship("CategoriaProduto")
    fornecedor_principal = relationship("Fornecedor")


class Compra(Base):
    __tablename__ = "compras"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    numero_pedido = Column(String(20), unique=True, nullable=False)
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("erp.fornecedores.id"), nullable=False)
    transportadora_id = Column(Integer, ForeignKey("erp.transportadoras.id"))
    tipo_operacao_id = Column(Integer, ForeignKey("erp.tipos_operacao.id"))
    usuario_id = Column(Integer, ForeignKey("erp.usuarios.id"))
    numero_nf = Column(String(20))
    serie_nf = Column(String(5))
    chave_nfe = Column(String(44))
    data_pedido = Column(Date, server_default=func.current_date())
    data_entrega_prevista = Column(Date)
    data_entrega_real = Column(Date)
    status = Column(String(20), default="ABERTO", nullable=False)
    valor_produtos = Column(Numeric(14, 2), default=0)
    valor_frete = Column(Numeric(14, 2), default=0)
    valor_desconto = Column(Numeric(14, 2), default=0)
    valor_icms_st = Column(Numeric(14, 2), default=0)
    valor_total = Column(Numeric(14, 2), default=0)
    condicao_pagamento = Column(String(100))
    observacao = Column(Text)
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")
    fornecedor = relationship("Fornecedor")
    transportadora = relationship("Transportadora")
    tipo_operacao = relationship("TipoOperacao")
    itens = relationship("CompraItem", back_populates="compra", cascade="all, delete-orphan")


class CompraItem(Base):
    __tablename__ = "compras_itens"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    compra_id = Column(Integer, ForeignKey("erp.compras.id", ondelete="CASCADE"), nullable=False)
    produto_id = Column(Integer, ForeignKey("erp.produtos.id"), nullable=False)
    quantidade_pedida = Column(Numeric(14, 3), nullable=False)
    quantidade_recebida = Column(Numeric(14, 3), default=0)
    valor_unitario = Column(Numeric(14, 4), nullable=False)
    valor_desconto = Column(Numeric(14, 2), default=0)
    valor_total = Column(Numeric(14, 2), nullable=False)
    cfop = Column(String(6))
    ncm = Column(String(10))
    lote = Column(String(30))
    data_validade = Column(Date)

    compra = relationship("Compra", back_populates="itens")
    produto = relationship("Produto")


class PlanoConta(Base):
    __tablename__ = "plano_contas"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    descricao = Column(String(120), nullable=False)
    tipo = Column(String(10), nullable=False)


class ContaPagar(Base):
    __tablename__ = "contas_pagar"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("erp.fornecedores.id"), nullable=False)
    compra_id = Column(Integer, ForeignKey("erp.compras.id"))
    plano_conta_id = Column(Integer, ForeignKey("erp.plano_contas.id"))
    numero_documento = Column(String(30))
    parcela = Column(Integer, default=1)
    total_parcelas = Column(Integer, default=1)
    valor_original = Column(Numeric(14, 2), nullable=False)
    valor_juros = Column(Numeric(14, 2), default=0)
    valor_desconto = Column(Numeric(14, 2), default=0)
    valor_pago = Column(Numeric(14, 2), default=0)
    data_emissao = Column(Date, server_default=func.current_date())
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    forma_pagamento = Column(String(30))
    status = Column(String(20), default="ABERTO", nullable=False)
    observacao = Column(String(255))
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")
    fornecedor = relationship("Fornecedor")


class ContaReceber(Base):
    __tablename__ = "contas_receber"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("erp.clientes.id"), nullable=False)
    venda_id = Column(Integer)
    plano_conta_id = Column(Integer, ForeignKey("erp.plano_contas.id"))
    numero_documento = Column(String(30))
    parcela = Column(Integer, default=1)
    total_parcelas = Column(Integer, default=1)
    valor_original = Column(Numeric(14, 2), nullable=False)
    valor_juros = Column(Numeric(14, 2), default=0)
    valor_desconto = Column(Numeric(14, 2), default=0)
    valor_recebido = Column(Numeric(14, 2), default=0)
    data_emissao = Column(Date, server_default=func.current_date())
    data_vencimento = Column(Date, nullable=False)
    data_recebimento = Column(Date)
    forma_recebimento = Column(String(30))
    status = Column(String(20), default="ABERTO", nullable=False)
    observacao = Column(String(255))
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")
    cliente = relationship("Cliente")


class EstoqueSaldo(Base):
    __tablename__ = "estoque_saldo"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("erp.produtos.id"), nullable=False)
    quantidade = Column(Numeric(14, 3), default=0, nullable=False)
    valor_medio = Column(Numeric(14, 4), default=0, nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now())


class EstoqueMovimento(Base):
    __tablename__ = "estoque_movimentos"
    __table_args__ = {"schema": "erp"}

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("erp.empresas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("erp.produtos.id"), nullable=False)
    tipo_operacao_id = Column(Integer, ForeignKey("erp.tipos_operacao.id"), nullable=False)
    documento_origem = Column(String(30))
    quantidade = Column(Numeric(14, 3), nullable=False)
    valor_unitario = Column(Numeric(14, 4), default=0, nullable=False)
    saldo_apos = Column(Numeric(14, 3))
    usuario_id = Column(Integer, ForeignKey("erp.usuarios.id"))
    criado_em = Column(DateTime, server_default=func.now())
