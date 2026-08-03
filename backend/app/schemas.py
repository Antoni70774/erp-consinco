from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -------- Auth --------
class LoginRequest(BaseModel):
    login: str
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: dict


# -------- Empresa --------
class EmpresaIn(BaseModel):
    codigo: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    inscricao_estadual: Optional[str] = None
    tipo: str = "LOJA"
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    ativo: bool = True


class EmpresaOut(EmpresaIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Usuario --------
class UsuarioIn(BaseModel):
    nome: str
    login: str
    email: Optional[str] = None
    senha: Optional[str] = None
    perfil_id: Optional[int] = None
    empresa_id: Optional[int] = None
    ativo: bool = True


class UsuarioOut(ORMBase):
    id: int
    nome: str
    login: str
    email: Optional[str] = None
    perfil_id: Optional[int] = None
    empresa_id: Optional[int] = None
    ativo: bool
    criado_em: Optional[datetime] = None


# -------- Tipo Operacao --------
class TipoOperacaoIn(BaseModel):
    codigo: str
    cfop: str
    descricao: str
    categoria: str
    movimenta_estoque: bool = True
    natureza: str
    gera_financeiro: bool = False
    ativo: bool = True
    observacao: Optional[str] = None


class TipoOperacaoOut(TipoOperacaoIn, ORMBase):
    id: int


# -------- Fornecedor --------
class FornecedorIn(BaseModel):
    codigo: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj_cpf: str
    inscricao_estadual: Optional[str] = None
    tipo_pessoa: str = "J"
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    contato_nome: Optional[str] = None
    prazo_entrega_dias: int = 0
    condicao_pagamento: Optional[str] = None
    ativo: bool = True


class FornecedorOut(FornecedorIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Transportadora --------
class TransportadoraIn(BaseModel):
    codigo: str
    razao_social: str
    cnpj: str
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    tipo_frete: str = "CIF"
    ativo: bool = True


class TransportadoraOut(TransportadoraIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Funcionario --------
class FuncionarioIn(BaseModel):
    matricula: str
    nome: str
    cpf: str
    cargo: Optional[str] = None
    setor: Optional[str] = None
    empresa_id: Optional[int] = None
    data_admissao: Optional[date] = None
    data_demissao: Optional[date] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    ativo: bool = True


class FuncionarioOut(FuncionarioIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Cliente --------
class ClienteIn(BaseModel):
    codigo: str
    nome: str
    cnpj_cpf: Optional[str] = None
    tipo_pessoa: str = "F"
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    data_nascimento: Optional[date] = None
    limite_credito: float = 0
    ativo: bool = True


class ClienteOut(ClienteIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Categoria Produto --------
class CategoriaProdutoIn(BaseModel):
    codigo: str
    descricao: str
    categoria_pai_id: Optional[int] = None


class CategoriaProdutoOut(CategoriaProdutoIn, ORMBase):
    id: int


# -------- Produto --------
class ProdutoIn(BaseModel):
    codigo: str
    codigo_barras: Optional[str] = None
    descricao: str
    descricao_reduzida: Optional[str] = None
    categoria_id: Optional[int] = None
    unidade_compra: str = "UN"
    unidade_venda: str = "UN"
    fator_conversao: float = 1
    fornecedor_principal_id: Optional[int] = None
    ncm: Optional[str] = None
    cest: Optional[str] = None
    origem_mercadoria: str = "0"
    cfop_padrao_saida: Optional[str] = None
    cfop_padrao_entrada: Optional[str] = None
    cst_icms: Optional[str] = None
    aliquota_icms: float = 0
    cst_pis: Optional[str] = None
    aliquota_pis: float = 0
    cst_cofins: Optional[str] = None
    aliquota_cofins: float = 0
    cst_ipi: Optional[str] = None
    aliquota_ipi: float = 0
    percentual_mva: float = 0
    peso_liquido_kg: Optional[float] = None
    peso_bruto_kg: Optional[float] = None
    preco_custo: float = 0
    preco_venda: float = 0
    margem_lucro: float = 0
    estoque_minimo: float = 0
    estoque_maximo: float = 0
    estoque_atual: float = 0
    validade_controlada: bool = False
    curva_abc: Optional[str] = None
    ativo: bool = True


class ProdutoOut(ProdutoIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None


# -------- Compras --------
class CompraItemIn(BaseModel):
    produto_id: int
    quantidade_pedida: float
    quantidade_recebida: float = 0
    valor_unitario: float
    valor_desconto: float = 0
    valor_total: float
    cfop: Optional[str] = None
    ncm: Optional[str] = None
    lote: Optional[str] = None
    data_validade: Optional[date] = None


class CompraItemOut(CompraItemIn, ORMBase):
    id: int


class CompraIn(BaseModel):
    numero_pedido: str
    empresa_id: int
    fornecedor_id: int
    transportadora_id: Optional[int] = None
    tipo_operacao_id: Optional[int] = None
    usuario_id: Optional[int] = None
    numero_nf: Optional[str] = None
    serie_nf: Optional[str] = None
    chave_nfe: Optional[str] = None
    data_pedido: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    data_entrega_real: Optional[date] = None
    status: str = "ABERTO"
    valor_frete: float = 0
    valor_desconto: float = 0
    valor_icms_st: float = 0
    condicao_pagamento: Optional[str] = None
    observacao: Optional[str] = None
    itens: List[CompraItemIn] = []


class CompraOut(ORMBase):
    id: int
    numero_pedido: str
    empresa_id: int
    fornecedor_id: int
    transportadora_id: Optional[int] = None
    tipo_operacao_id: Optional[int] = None
    numero_nf: Optional[str] = None
    serie_nf: Optional[str] = None
    status: str
    data_pedido: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    valor_produtos: Optional[float] = 0
    valor_frete: Optional[float] = 0
    valor_desconto: Optional[float] = 0
    valor_icms_st: Optional[float] = 0
    valor_total: Optional[float] = 0
    condicao_pagamento: Optional[str] = None
    observacao: Optional[str] = None
    itens: List[CompraItemOut] = []


# -------- Financeiro --------
class ContaPagarIn(BaseModel):
    empresa_id: int
    fornecedor_id: int
    compra_id: Optional[int] = None
    plano_conta_id: Optional[int] = None
    numero_documento: Optional[str] = None
    parcela: int = 1
    total_parcelas: int = 1
    valor_original: float
    valor_juros: float = 0
    valor_desconto: float = 0
    valor_pago: float = 0
    data_emissao: Optional[date] = None
    data_vencimento: date
    data_pagamento: Optional[date] = None
    forma_pagamento: Optional[str] = None
    status: str = "ABERTO"
    observacao: Optional[str] = None


class ContaPagarOut(ContaPagarIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


class ContaReceberIn(BaseModel):
    empresa_id: int
    cliente_id: int
    venda_id: Optional[int] = None
    plano_conta_id: Optional[int] = None
    numero_documento: Optional[str] = None
    parcela: int = 1
    total_parcelas: int = 1
    valor_original: float
    valor_juros: float = 0
    valor_desconto: float = 0
    valor_recebido: float = 0
    data_emissao: Optional[date] = None
    data_vencimento: date
    data_recebimento: Optional[date] = None
    forma_recebimento: Optional[str] = None
    status: str = "ABERTO"
    observacao: Optional[str] = None


class ContaReceberOut(ContaReceberIn, ORMBase):
    id: int
    criado_em: Optional[datetime] = None


# -------- Inventário --------
class InventarioAbrirIn(BaseModel):
    empresa_id: int
    descricao: str
    tipo_abertura: str = "GERAL"  # PRODUTO, SECAO, GERAL
    categoria_id: Optional[int] = None
    produto_ids: Optional[List[int]] = None  # usado quando tipo_abertura = PRODUTO
    tolerancia_critica_pct: float = 5
    usuario_atribuido_id: Optional[int] = None
    observacao: Optional[str] = None


class InventarioItemOut(ORMBase):
    id: int
    produto_id: int
    quantidade_sistema: float
    quantidade_contada: Optional[float] = None
    valor_unitario: Optional[float] = 0
    diferenca: Optional[float] = None
    valor_diferenca: Optional[float] = None
    critica: bool = False
    critica_motivo: Optional[str] = None
    contado_em: Optional[datetime] = None
    ajuste_aplicado: bool = False


class InventarioOut(ORMBase):
    id: int
    empresa_id: int
    descricao: str
    tipo_abertura: str
    categoria_id: Optional[int] = None
    status: str
    tolerancia_critica_pct: Optional[float] = 5
    usuario_atribuido_id: Optional[int] = None
    data_abertura: Optional[datetime] = None
    data_congelamento: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None
    observacao: Optional[str] = None
    itens: List[InventarioItemOut] = []


class InventarioAtribuirIn(BaseModel):
    usuario_id: Optional[int] = None  # None = remove atribuição


class InventarioBipagemIn(BaseModel):
    codigo_barras: Optional[str] = None
    codigo_produto: Optional[str] = None
    quantidade_contada: float


class InventarioContagemIn(BaseModel):
    quantidade_contada: float


# -------- Lançamentos operacionais (Consumo / Perda / Avaria) --------
class LancamentoOperacionalIn(BaseModel):
    empresa_id: int
    produto_id: int
    tipo_operacao_id: int
    quantidade: float
    motivo: Optional[str] = None
    documento_origem: Optional[str] = None
    fornecedor_id: Optional[int] = None  # relevante principalmente para avarias


# -------- Vendas --------
class VendaItemIn(BaseModel):
    produto_id: int
    quantidade: float
    valor_unitario: float
    valor_desconto: float = 0
    valor_total: float
    cfop: Optional[str] = None


class VendaItemOut(VendaItemIn, ORMBase):
    id: int
    quantidade_devolvida: float = 0


class VendaIn(BaseModel):
    numero_venda: str
    empresa_id: int
    cliente_id: Optional[int] = None
    tipo_operacao_id: Optional[int] = None
    data_venda: Optional[datetime] = None
    valor_desconto: float = 0
    observacao: Optional[str] = None
    itens: List[VendaItemIn] = []
    gerar_financeiro: bool = False
    dias_vencimento: int = 30


class VendaOut(ORMBase):
    id: int
    numero_venda: str
    empresa_id: int
    cliente_id: Optional[int] = None
    tipo_operacao_id: Optional[int] = None
    data_venda: Optional[datetime] = None
    status: str
    valor_produtos: Optional[float] = 0
    valor_desconto: Optional[float] = 0
    valor_total: Optional[float] = 0
    observacao: Optional[str] = None
    itens: List[VendaItemOut] = []


class VendaDevolucaoItemIn(BaseModel):
    item_id: int
    quantidade: float


class VendaDevolucaoIn(BaseModel):
    itens: List[VendaDevolucaoItemIn]
    motivo: Optional[str] = None
