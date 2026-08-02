// -------- Guarda de autenticação --------
if (!localStorage.getItem('erp_token')) {
  window.location.href = 'index.html';
}
const usuarioLogado = JSON.parse(localStorage.getItem('erp_usuario') || '{}');
document.getElementById('sidebarUser').textContent = usuarioLogado.nome || 'Usuário';
document.getElementById('btnLogout').addEventListener('click', () => {
  localStorage.removeItem('erp_token');
  localStorage.removeItem('erp_usuario');
  window.location.href = 'index.html';
});

// "Trocar servidor" só aparece quando rodando dentro do app desktop (Electron)
if (window.erpDesktop) {
  const btnReconf = document.getElementById('btnReconfigurar');
  btnReconf.style.display = 'inline-block';
  btnReconf.addEventListener('click', () => {
    if (confirm('Isso vai desconectar deste servidor e pedir um novo endereço. Continuar?')) {
      window.erpDesktop.reconfigurar();
    }
  });
}

const content = document.getElementById('content');
const topbarTitle = document.getElementById('topbarTitle');
const topbarCrumb = document.getElementById('topbarCrumb');

// -------- Helpers de opções para selects (carregadas sob demanda) --------
const optEmpresas = async () => (await API.get('/api/empresas')).map(e => ({ value: e.id, label: `${e.codigo} · ${e.nome_fantasia || e.razao_social}` }));
const optFornecedores = async () => (await API.get('/api/fornecedores')).map(f => ({ value: f.id, label: `${f.codigo} · ${f.razao_social}` }));
const optTransportadoras = async () => (await API.get('/api/transportadoras')).map(t => ({ value: t.id, label: `${t.codigo} · ${t.razao_social}` }));
const optClientes = async () => (await API.get('/api/clientes')).map(c => ({ value: c.id, label: `${c.codigo} · ${c.nome}` }));
const optProdutos = async () => (await API.get('/api/produtos')).map(p => ({ value: p.id, label: `${p.codigo} · ${p.descricao}` }));
const optCategorias = async () => (await API.get('/api/categorias-produto')).map(c => ({ value: c.id, label: c.descricao }));
const optPerfis = async () => [{ value: '', label: '(sem perfil)' }];
const optTiposOperacao = async () => (await API.get('/api/tipos-operacao')).map(t => ({ value: t.id, label: `${t.codigo} · CFOP ${t.cfop} · ${t.descricao}` }));

// -------- Configurações de CRUD por entidade --------
const CRUD_CONFIGS = {
  empresas: {
    title: 'Empresa/Loja', apiPath: '/api/empresas',
    columns: [
      { key: 'codigo', label: 'Código' },
      { key: 'razao_social', label: 'Razão Social' },
      { key: 'nome_fantasia', label: 'Fantasia' },
      { key: 'cnpj', label: 'CNPJ' },
      { key: 'tipo', label: 'Tipo' },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'razao_social', label: 'Razão Social', required: true, span: 2 },
      { key: 'nome_fantasia', label: 'Nome Fantasia', span: 2 },
      { key: 'cnpj', label: 'CNPJ', required: true },
      { key: 'inscricao_estadual', label: 'Inscrição Estadual' },
      { key: 'tipo', label: 'Tipo', type: 'select', options: [{ value: 'LOJA', label: 'Loja' }, { value: 'CD', label: 'Centro de Distribuição' }, { value: 'MATRIZ', label: 'Matriz' }] },
      { key: 'cidade', label: 'Cidade' },
      { key: 'uf', label: 'UF' },
      { key: 'telefone', label: 'Telefone' },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  clientes: {
    title: 'Cliente', apiPath: '/api/clientes',
    columns: [
      { key: 'codigo', label: 'Código' }, { key: 'nome', label: 'Nome' },
      { key: 'cnpj_cpf', label: 'CPF/CNPJ' }, { key: 'cidade', label: 'Cidade' },
      { key: 'limite_credito', label: 'Limite Crédito', render: i => UI.fmtMoney(i.limite_credito) },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'nome', label: 'Nome / Razão Social', required: true, span: 2 },
      { key: 'tipo_pessoa', label: 'Tipo Pessoa', type: 'select', options: [{ value: 'F', label: 'Física' }, { value: 'J', label: 'Jurídica' }] },
      { key: 'cnpj_cpf', label: 'CPF/CNPJ' },
      { key: 'inscricao_estadual', label: 'Inscrição Estadual' },
      { key: 'endereco', label: 'Endereço', span: 2 },
      { key: 'cidade', label: 'Cidade' }, { key: 'uf', label: 'UF' }, { key: 'cep', label: 'CEP' },
      { key: 'telefone', label: 'Telefone' }, { key: 'email', label: 'E-mail' },
      { key: 'data_nascimento', label: 'Data Nascimento', type: 'date' },
      { key: 'limite_credito', label: 'Limite de Crédito', type: 'number', step: '0.01' },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  fornecedores: {
    title: 'Fornecedor', apiPath: '/api/fornecedores',
    columns: [
      { key: 'codigo', label: 'Código' }, { key: 'razao_social', label: 'Razão Social' },
      { key: 'cnpj_cpf', label: 'CNPJ/CPF' }, { key: 'prazo_entrega_dias', label: 'Prazo (dias)' },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'razao_social', label: 'Razão Social', required: true, span: 2 },
      { key: 'nome_fantasia', label: 'Nome Fantasia', span: 2 },
      { key: 'tipo_pessoa', label: 'Tipo Pessoa', type: 'select', options: [{ value: 'F', label: 'Física' }, { value: 'J', label: 'Jurídica' }] },
      { key: 'cnpj_cpf', label: 'CNPJ/CPF', required: true },
      { key: 'inscricao_estadual', label: 'Inscrição Estadual' },
      { key: 'endereco', label: 'Endereço', span: 2 },
      { key: 'cidade', label: 'Cidade' }, { key: 'uf', label: 'UF' }, { key: 'cep', label: 'CEP' },
      { key: 'telefone', label: 'Telefone' }, { key: 'email', label: 'E-mail' },
      { key: 'contato_nome', label: 'Contato' },
      { key: 'prazo_entrega_dias', label: 'Prazo Entrega (dias)', type: 'number' },
      { key: 'condicao_pagamento', label: 'Condição de Pagamento', span: 2 },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  transportadoras: {
    title: 'Transportadora', apiPath: '/api/transportadoras',
    columns: [
      { key: 'codigo', label: 'Código' }, { key: 'razao_social', label: 'Razão Social' },
      { key: 'cnpj', label: 'CNPJ' }, { key: 'tipo_frete', label: 'Frete' },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'razao_social', label: 'Razão Social', required: true, span: 2 },
      { key: 'cnpj', label: 'CNPJ', required: true },
      { key: 'inscricao_estadual', label: 'Inscrição Estadual' },
      { key: 'endereco', label: 'Endereço', span: 2 },
      { key: 'cidade', label: 'Cidade' }, { key: 'uf', label: 'UF' },
      { key: 'telefone', label: 'Telefone' }, { key: 'email', label: 'E-mail' },
      { key: 'tipo_frete', label: 'Tipo de Frete', type: 'select', options: [{ value: 'CIF', label: 'CIF (remetente paga)' }, { value: 'FOB', label: 'FOB (destinatário paga)' }] },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  funcionarios: {
    title: 'Funcionário', apiPath: '/api/funcionarios',
    columns: [
      { key: 'matricula', label: 'Matrícula' }, { key: 'nome', label: 'Nome' },
      { key: 'cargo', label: 'Cargo' }, { key: 'setor', label: 'Setor' },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'matricula', label: 'Matrícula', required: true },
      { key: 'nome', label: 'Nome Completo', required: true, span: 2 },
      { key: 'cpf', label: 'CPF', required: true },
      { key: 'cargo', label: 'Cargo' }, { key: 'setor', label: 'Setor' },
      { key: 'empresa_id', label: 'Empresa', type: 'select', options: optEmpresas },
      { key: 'data_admissao', label: 'Data Admissão', type: 'date' },
      { key: 'data_demissao', label: 'Data Demissão', type: 'date' },
      { key: 'telefone', label: 'Telefone' }, { key: 'email', label: 'E-mail' },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  categorias: {
    title: 'Categoria de Produto', apiPath: '/api/categorias-produto',
    columns: [{ key: 'codigo', label: 'Código' }, { key: 'descricao', label: 'Descrição' }],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'descricao', label: 'Descrição', required: true, span: 2 },
    ],
  },

  produtos: {
    title: 'Produto', apiPath: '/api/produtos',
    columns: [
      { key: 'codigo', label: 'Código' }, { key: 'descricao', label: 'Descrição' },
      { key: 'ncm', label: 'NCM' },
      { key: 'preco_custo', label: 'Custo', render: i => UI.fmtMoney(i.preco_custo) },
      { key: 'preco_venda', label: 'Venda', render: i => UI.fmtMoney(i.preco_venda) },
      { key: 'estoque_atual', label: 'Estoque', render: i => UI.fmtNum(i.estoque_atual, 0) },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'codigo', label: 'Código', required: true },
      { key: 'codigo_barras', label: 'Código de Barras (EAN)' },
      { key: 'descricao', label: 'Descrição', required: true, span: 2 },
      { key: 'descricao_reduzida', label: 'Descrição Reduzida', span: 2 },
      { key: 'categoria_id', label: 'Categoria', type: 'select', options: optCategorias },
      { key: 'fornecedor_principal_id', label: 'Fornecedor Principal', type: 'select', options: optFornecedores },
      { key: 'unidade_compra', label: 'Unidade Compra' }, { key: 'unidade_venda', label: 'Unidade Venda' },
      { key: 'fator_conversao', label: 'Fator Conversão', type: 'number', step: '0.0001' },
      // Fiscais
      { key: 'ncm', label: 'NCM' }, { key: 'cest', label: 'CEST' },
      { key: 'origem_mercadoria', label: 'Origem Mercadoria (0-8)' },
      { key: 'cfop_padrao_entrada', label: 'CFOP Padrão Entrada' },
      { key: 'cfop_padrao_saida', label: 'CFOP Padrão Saída' },
      { key: 'cst_icms', label: 'CST ICMS' }, { key: 'aliquota_icms', label: 'Alíq. ICMS %', type: 'number', step: '0.01' },
      { key: 'cst_pis', label: 'CST PIS' }, { key: 'aliquota_pis', label: 'Alíq. PIS %', type: 'number', step: '0.01' },
      { key: 'cst_cofins', label: 'CST COFINS' }, { key: 'aliquota_cofins', label: 'Alíq. COFINS %', type: 'number', step: '0.01' },
      { key: 'cst_ipi', label: 'CST IPI' }, { key: 'aliquota_ipi', label: 'Alíq. IPI %', type: 'number', step: '0.01' },
      { key: 'percentual_mva', label: 'MVA (ICMS-ST) %', type: 'number', step: '0.01' },
      { key: 'peso_liquido_kg', label: 'Peso Líquido (kg)', type: 'number', step: '0.001' },
      { key: 'peso_bruto_kg', label: 'Peso Bruto (kg)', type: 'number', step: '0.001' },
      // Comercial / estoque
      { key: 'preco_custo', label: 'Preço de Custo', type: 'number', step: '0.0001' },
      { key: 'preco_venda', label: 'Preço de Venda', type: 'number', step: '0.0001' },
      { key: 'margem_lucro', label: 'Margem de Lucro %', type: 'number', step: '0.01' },
      { key: 'estoque_minimo', label: 'Estoque Mínimo', type: 'number', step: '0.001' },
      { key: 'estoque_maximo', label: 'Estoque Máximo', type: 'number', step: '0.001' },
      { key: 'validade_controlada', label: 'Controla Validade/Lote', type: 'checkbox' },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  'tipos-operacao': {
    title: 'Tipo de Operação', apiPath: '/api/tipos-operacao',
    columns: [
      { key: 'codigo', label: 'Código' }, { key: 'cfop', label: 'CFOP' },
      { key: 'descricao', label: 'Descrição' }, { key: 'categoria', label: 'Categoria' },
      { key: 'natureza', label: 'Natureza' },
      { key: 'gera_financeiro', label: 'Gera Financeiro', render: i => i.gera_financeiro ? '<span class="tag tag-green">Sim</span>' : '<span class="tag tag-gray">Não</span>' },
    ],
    formFields: [
      { key: 'codigo', label: 'Código Interno', required: true },
      { key: 'cfop', label: 'CFOP', required: true },
      { key: 'descricao', label: 'Descrição', required: true, span: 2 },
      { key: 'categoria', label: 'Categoria', type: 'select', required: true, options: [
        { value: 'VENDA', label: 'Venda' }, { value: 'COMPRA', label: 'Compra' },
        { value: 'PERDA', label: 'Perda / Quebra' }, { value: 'AVARIA', label: 'Avaria' },
        { value: 'TRANSFERENCIA', label: 'Transferência' }, { value: 'DEVOLUCAO', label: 'Devolução' },
        { value: 'CONSUMO', label: 'Consumo Interno' }, { value: 'BONIFICACAO', label: 'Bonificação' },
        { value: 'INVENTARIO', label: 'Ajuste de Inventário' },
      ] },
      { key: 'natureza', label: 'Natureza', type: 'select', required: true, options: [{ value: 'ENTRADA', label: 'Entrada' }, { value: 'SAIDA', label: 'Saída' }] },
      { key: 'movimenta_estoque', label: 'Movimenta Estoque', type: 'checkbox' },
      { key: 'gera_financeiro', label: 'Gera Título Financeiro', type: 'checkbox' },
      { key: 'observacao', label: 'Observação', type: 'textarea' },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },

  usuarios: {
    title: 'Usuário', apiPath: '/api/usuarios',
    columns: [
      { key: 'nome', label: 'Nome' }, { key: 'login', label: 'Login' }, { key: 'email', label: 'E-mail' },
      { key: 'ativo', label: 'Status', render: i => tagAtivo(i.ativo) },
    ],
    formFields: [
      { key: 'nome', label: 'Nome Completo', required: true, span: 2 },
      { key: 'login', label: 'Login', required: true },
      { key: 'email', label: 'E-mail' },
      { key: 'senha', label: 'Senha (deixe em branco para não alterar)', type: 'password' },
      { key: 'empresa_id', label: 'Empresa', type: 'select', options: optEmpresas },
      { key: 'ativo', label: 'Ativo', type: 'checkbox' },
    ],
  },
};

function tagAtivo(ativo) {
  return ativo ? '<span class="tag tag-green">Ativo</span>' : '<span class="tag tag-gray">Inativo</span>';
}

// -------- Roteador --------
const VIEW_TITLES = {
  dashboard: ['Dashboard', 'Gerencial'],
  empresas: ['Empresas / Lojas', 'Cadastros'],
  clientes: ['Clientes', 'Cadastros'],
  fornecedores: ['Fornecedores', 'Cadastros'],
  transportadoras: ['Transportadoras', 'Cadastros'],
  funcionarios: ['Funcionários', 'Cadastros'],
  categorias: ['Categorias de Produto', 'Cadastros'],
  produtos: ['Produtos', 'Cadastros · Cadastro Completo com Dados Fiscais'],
  compras: ['Compras', 'Operacional'],
  financeiro: ['Financeiro', 'Operacional · Contas a Pagar e a Receber'],
  'tipos-operacao': ['Tipos de Operação (CFOP)', 'Configurações'],
  usuarios: ['Usuários e Senhas', 'Configurações'],
};

async function navigate(view) {
  document.querySelectorAll('.nav-item[data-view]').forEach(el => el.classList.toggle('active', el.dataset.view === view));
  const [title, crumb] = VIEW_TITLES[view] || [view, ''];
  topbarTitle.textContent = title;
  topbarCrumb.textContent = crumb;
  content.innerHTML = '';

  try {
    if (view === 'dashboard') return renderDashboard();
    if (view === 'compras') return renderCompras();
    if (view === 'financeiro') return renderFinanceiro();
    if (CRUD_CONFIGS[view]) return UI.renderCrudView(content, CRUD_CONFIGS[view]);
  } catch (e) {
    content.innerHTML = `<div class="error-msg">${e.message}</div>`;
  }
}

document.querySelectorAll('.nav-item[data-view]').forEach(el => {
  el.addEventListener('click', () => navigate(el.dataset.view));
});

// -------- View: Dashboard Gerencial --------
async function renderDashboard() {
  content.innerHTML = `<div id="dashLoad" style="color:#9096a8">Carregando indicadores...</div>`;
  const d = await API.get('/api/gerencial/dashboard');
  content.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">Produtos Ativos</div><div class="kpi-value">${d.cadastros.produtos_ativos}</div></div>
      <div class="kpi-card"><div class="kpi-label">Fornecedores Ativos</div><div class="kpi-value">${d.cadastros.fornecedores_ativos}</div></div>
      <div class="kpi-card"><div class="kpi-label">Clientes Ativos</div><div class="kpi-value">${d.cadastros.clientes_ativos}</div></div>
      <div class="kpi-card"><div class="kpi-label">Empresas/Lojas</div><div class="kpi-value">${d.cadastros.empresas_ativas}</div></div>
    </div>
    <div class="grid-2" style="margin-bottom:22px">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">Financeiro</div></div>
        <div class="panel-body kpi-grid" style="margin:0">
          <div class="kpi-card"><div class="kpi-label">A Pagar (aberto)</div><div class="kpi-value neg">${UI.fmtMoney(d.financeiro.contas_a_pagar_aberto)}</div></div>
          <div class="kpi-card"><div class="kpi-label">A Receber (aberto)</div><div class="kpi-value pos">${UI.fmtMoney(d.financeiro.contas_a_receber_aberto)}</div></div>
          <div class="kpi-card"><div class="kpi-label">Saldo Projetado</div><div class="kpi-value ${d.financeiro.saldo_projetado >= 0 ? 'pos' : 'neg'}">${UI.fmtMoney(d.financeiro.saldo_projetado)}</div></div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">Compras &amp; Estoque</div></div>
        <div class="panel-body kpi-grid" style="margin:0">
          <div class="kpi-card"><div class="kpi-label">Pedidos em Aberto</div><div class="kpi-value">${d.compras.pedidos_em_aberto}</div></div>
          <div class="kpi-card"><div class="kpi-label">Comprado no Mês</div><div class="kpi-value">${UI.fmtMoney(d.compras.valor_comprado_mes_atual)}</div></div>
          <div class="kpi-card"><div class="kpi-label">Valor em Estoque</div><div class="kpi-value">${UI.fmtMoney(d.estoque.valor_total_estoque)}</div></div>
          <div class="kpi-card"><div class="kpi-label">Abaixo do Mínimo</div><div class="kpi-value ${d.estoque.produtos_abaixo_minimo > 0 ? 'neg' : ''}">${d.estoque.produtos_abaixo_minimo}</div></div>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><div class="panel-title">Roadmap · Módulos em construção</div></div>
      <div class="panel-body">
        <p style="color:var(--ink-soft); font-size:13px; margin-top:0">
          A fundação (cadastros, compras e financeiro) está pronta. Os módulos de análise abaixo usam a mesma base
          de dados (tabela <span class="mono">estoque_movimentos</span> / <span class="mono">tipos_operacao</span>) e serão construídos na sequência:
        </p>
        <div style="display:flex; flex-wrap:wrap; gap:8px">
          ${d.modulos_em_construcao.map(m => `<span class="tag tag-amber">${m}</span>`).join('')}
        </div>
      </div>
    </div>
  `;
}

// -------- View: Compras (master-detail) --------
async function renderCompras() {
  content.innerHTML = `
    <div class="table-toolbar">
      <input class="search-input" id="compraFiltroStatus" placeholder="Filtrar por status (ABERTO, RECEBIDO...)">
      <button class="btn btn-primary" id="btnNovaCompra">+ Novo Pedido de Compra</button>
    </div>
    <div class="table-wrap"><table class="data-table">
      <thead><tr>
        <th>Pedido</th><th>Fornecedor</th><th>Data</th><th>Status</th><th>Valor Total</th><th style="width:130px">Ações</th>
      </tr></thead>
      <tbody id="comprasTbody"><tr><td colspan="6" style="padding:20px;color:#9096a8">Carregando...</td></tr></tbody>
    </table></div>
  `;

  const [fornecedores, empresas] = await Promise.all([optFornecedores(), optEmpresas()]);
  const fornecedorMap = Object.fromEntries(fornecedores.map(f => [f.value, f.label]));

  async function load() {
    const status = document.getElementById('compraFiltroStatus').value.trim();
    const compras = await API.get(`/api/compras${status ? `?status=${encodeURIComponent(status)}` : ''}`);
    const tbody = document.getElementById('comprasTbody');
    if (!compras.length) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-title">Nenhum pedido de compra</div>Clique em "Novo Pedido de Compra" para começar.</div></td></tr>`;
      return;
    }
    tbody.innerHTML = compras.map(c => `
      <tr>
        <td class="mono">${c.numero_pedido}</td>
        <td>${fornecedorMap[c.fornecedor_id] || c.fornecedor_id}</td>
        <td>${UI.fmtDate(c.data_pedido)}</td>
        <td>${statusTag(c.status)}</td>
        <td class="mono">${UI.fmtMoney(c.valor_total)}</td>
        <td class="row-actions">
          <button class="icon-btn" data-view-compra="${c.id}">Abrir</button>
          ${c.status !== 'RECEBIDO' ? `<button class="icon-btn" data-receber="${c.id}">Receber</button>` : ''}
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('[data-view-compra]').forEach(btn => btn.addEventListener('click', () => abrirCompra(Number(btn.dataset.viewCompra))));
    tbody.querySelectorAll('[data-receber]').forEach(btn => btn.addEventListener('click', () => receberCompra(Number(btn.dataset.receber))));
  }

  function statusTag(status) {
    const map = { ABERTO: 'tag-amber', APROVADO: 'tag-gray', RECEBIDO: 'tag-green', RECEBIDO_PARCIAL: 'tag-amber', CANCELADO: 'tag-red', EM_TRANSITO: 'tag-gray' };
    return `<span class="tag ${map[status] || 'tag-gray'}">${status}</span>`;
  }

  async function receberCompra(id) {
    if (!confirm('Confirmar o recebimento total desta mercadoria? Isso irá atualizar o estoque.')) return;
    try {
      await API.post(`/api/compras/${id}/receber`);
      UI.toast('Recebimento confirmado. Estoque atualizado.');
      load();
    } catch (e) { UI.toast(e.message, 'err'); }
  }

  async function abrirCompra(id) {
    const compra = id ? await API.get(`/api/compras/${id}`) : null;
    const produtos = await optProdutos();
    const tiposOperacao = await optTiposOperacao();
    let itens = compra ? [...compra.itens] : [];

    function itensTableHtml() {
      if (!itens.length) return `<div class="empty-state" style="padding:16px">Nenhum item adicionado.</div>`;
      return `<table class="data-table"><thead><tr><th>Produto</th><th>Qtd</th><th>Vlr Unit.</th><th>Total</th><th></th></tr></thead><tbody>
        ${itens.map((it, idx) => {
          const prod = produtos.find(p => p.value === it.produto_id);
          return `<tr>
            <td>${prod ? prod.label : it.produto_id}</td>
            <td class="mono">${UI.fmtNum(it.quantidade_pedida, 3)}</td>
            <td class="mono">${UI.fmtMoney(it.valor_unitario)}</td>
            <td class="mono">${UI.fmtMoney(it.valor_total)}</td>
            <td><button type="button" class="icon-btn" data-rm-item="${idx}">🗑</button></td>
          </tr>`;
        }).join('')}
      </tbody></table>`;
    }

    const overlay = UI.openModal({
      title: compra ? `Pedido ${compra.numero_pedido}` : 'Novo Pedido de Compra',
      bodyHtml: `
        <form id="compraForm" class="field-row">
          <label class="field"><span>Número do Pedido *</span><input name="numero_pedido" required value="${compra ? compra.numero_pedido : 'PC-' + Date.now().toString().slice(-6)}"></label>
          <label class="field"><span>Empresa *</span><select name="empresa_id" required>${empresas.map(e => `<option value="${e.value}" ${compra && compra.empresa_id === e.value ? 'selected' : ''}>${e.label}</option>`).join('')}</select></label>
          <label class="field"><span>Fornecedor *</span><select name="fornecedor_id" required>${fornecedores.map(f => `<option value="${f.value}" ${compra && compra.fornecedor_id === f.value ? 'selected' : ''}>${f.label}</option>`).join('')}</select></label>
          <label class="field"><span>Tipo de Operação</span><select name="tipo_operacao_id">${tiposOperacao.map(t => `<option value="${t.value}" ${compra && compra.tipo_operacao_id === t.value ? 'selected' : ''}>${t.label}</option>`).join('')}</select></label>
          <label class="field"><span>NF Número</span><input name="numero_nf" value="${compra ? (compra.numero_nf || '') : ''}"></label>
          <label class="field"><span>Data do Pedido</span><input type="date" name="data_pedido" value="${compra && compra.data_pedido ? compra.data_pedido : new Date().toISOString().slice(0, 10)}"></label>
          <label class="field"><span>Frete (R$)</span><input type="number" step="0.01" name="valor_frete" value="${compra ? compra.valor_frete || 0 : 0}"></label>
          <label class="field"><span>Desconto (R$)</span><input type="number" step="0.01" name="valor_desconto" value="${compra ? compra.valor_desconto || 0 : 0}"></label>
        </form>

        <div class="panel" style="margin-top:4px">
          <div class="panel-header"><div class="panel-title">Itens do Pedido</div></div>
          <div class="panel-body">
            <div id="itensTableWrap">${itensTableHtml()}</div>
            <div class="field-row" style="margin-top:14px; align-items:flex-end">
              <label class="field"><span>Produto</span>
                <select id="itemProduto">${produtos.map(p => `<option value="${p.value}">${p.label}</option>`).join('')}</select>
              </label>
              <label class="field"><span>Quantidade</span><input type="number" step="0.001" id="itemQtd" value="1"></label>
              <label class="field"><span>Vlr. Unitário</span><input type="number" step="0.0001" id="itemValor" value="0"></label>
              <button type="button" class="btn btn-secondary" id="btnAddItem">+ Adicionar Item</button>
            </div>
          </div>
        </div>
      `,
      footerHtml: `<button class="btn btn-secondary" data-close>Cancelar</button>
                   <button class="btn btn-primary" id="btnSalvarCompra">Salvar Pedido</button>`,
      onMount: (ov) => {
        ov.querySelector('#btnAddItem').addEventListener('click', () => {
          const produtoId = Number(ov.querySelector('#itemProduto').value);
          const qtd = Number(ov.querySelector('#itemQtd').value) || 0;
          const valor = Number(ov.querySelector('#itemValor').value) || 0;
          if (!produtoId || qtd <= 0) { UI.toast('Informe produto e quantidade válidos.', 'err'); return; }
          itens.push({ produto_id: produtoId, quantidade_pedida: qtd, valor_unitario: valor, valor_total: qtd * valor });
          ov.querySelector('#itensTableWrap').innerHTML = itensTableHtml();
          ov.querySelectorAll('[data-rm-item]').forEach(btn => btn.addEventListener('click', () => {
            itens.splice(Number(btn.dataset.rmItem), 1);
            ov.querySelector('#itensTableWrap').innerHTML = itensTableHtml();
          }));
        });
        ov.querySelectorAll('[data-rm-item]').forEach(btn => btn.addEventListener('click', () => {
          itens.splice(Number(btn.dataset.rmItem), 1);
          ov.querySelector('#itensTableWrap').innerHTML = itensTableHtml();
        }));

        ov.querySelector('#btnSalvarCompra').addEventListener('click', async () => {
          const form = ov.querySelector('#compraForm');
          const fd = new FormData(form);
          if (!itens.length) { UI.toast('Adicione ao menos um item ao pedido.', 'err'); return; }
          const payload = {
            numero_pedido: fd.get('numero_pedido'),
            empresa_id: Number(fd.get('empresa_id')),
            fornecedor_id: Number(fd.get('fornecedor_id')),
            tipo_operacao_id: fd.get('tipo_operacao_id') ? Number(fd.get('tipo_operacao_id')) : null,
            numero_nf: fd.get('numero_nf') || null,
            data_pedido: fd.get('data_pedido') || null,
            valor_frete: Number(fd.get('valor_frete')) || 0,
            valor_desconto: Number(fd.get('valor_desconto')) || 0,
            itens: itens.map(it => ({
              produto_id: it.produto_id, quantidade_pedida: it.quantidade_pedida,
              valor_unitario: it.valor_unitario, valor_total: it.quantidade_pedida * it.valor_unitario,
            })),
          };
          try {
            if (compra) await API.put(`/api/compras/${compra.id}`, payload);
            else await API.post('/api/compras', payload);
            UI.toast('Pedido de compra salvo.');
            UI.closeModal();
            load();
          } catch (e) { UI.toast(e.message, 'err'); }
        });
      },
    });
  }

  document.getElementById('btnNovaCompra').addEventListener('click', () => abrirCompra(null));
  let t;
  document.getElementById('compraFiltroStatus').addEventListener('input', () => { clearTimeout(t); t = setTimeout(load, 300); });
  load();
}

// -------- View: Financeiro (contas a pagar / receber) --------
async function renderFinanceiro() {
  content.innerHTML = `
    <div class="kpi-grid" id="finKpis"></div>
    <div class="tabs">
      <div class="tab-btn active" data-tab="pagar">Contas a Pagar</div>
      <div class="tab-btn" data-tab="receber">Contas a Receber</div>
    </div>
    <div id="finContent"></div>
  `;

  const resumo = await API.get('/api/financeiro/resumo');
  document.getElementById('finKpis').innerHTML = `
    <div class="kpi-card"><div class="kpi-label">A Pagar em Aberto</div><div class="kpi-value neg">${UI.fmtMoney(resumo.a_pagar_em_aberto)}</div><div class="kpi-sub">Atrasado: ${UI.fmtMoney(resumo.a_pagar_atrasado)}</div></div>
    <div class="kpi-card"><div class="kpi-label">A Receber em Aberto</div><div class="kpi-value pos">${UI.fmtMoney(resumo.a_receber_em_aberto)}</div><div class="kpi-sub">Atrasado: ${UI.fmtMoney(resumo.a_receber_atrasado)}</div></div>
    <div class="kpi-card"><div class="kpi-label">Saldo Projetado</div><div class="kpi-value ${resumo.saldo_projetado >= 0 ? 'pos' : 'neg'}">${UI.fmtMoney(resumo.saldo_projetado)}</div></div>
  `;

  const finContent = document.getElementById('finContent');
  let currentTab = 'pagar';

  document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
    currentTab = btn.dataset.tab;
    renderTab();
  }));

  async function renderTab() {
    if (currentTab === 'pagar') return renderPagar();
    return renderReceber();
  }

  async function renderPagar() {
    finContent.innerHTML = `
      <div class="table-toolbar"><div></div><button class="btn btn-primary" id="btnNovoPagar">+ Novo Título a Pagar</button></div>
      <div class="table-wrap"><table class="data-table">
        <thead><tr><th>Fornecedor</th><th>Documento</th><th>Vencimento</th><th>Valor</th><th>Status</th><th style="width:100px">Ações</th></tr></thead>
        <tbody id="pagarTbody"><tr><td colspan="6" style="padding:20px;color:#9096a8">Carregando...</td></tr></tbody>
      </table></div>`;
    const [fornecedores, empresas] = await Promise.all([optFornecedores(), optEmpresas()]);
    const fMap = Object.fromEntries(fornecedores.map(f => [f.value, f.label]));
    const contas = await API.get('/api/financeiro/contas-pagar');
    const tbody = document.getElementById('pagarTbody');
    tbody.innerHTML = contas.length ? contas.map(c => `
      <tr>
        <td>${fMap[c.fornecedor_id] || c.fornecedor_id}</td>
        <td class="mono">${c.numero_documento || '—'}</td>
        <td>${UI.fmtDate(c.data_vencimento)}</td>
        <td class="mono">${UI.fmtMoney(c.valor_original)}</td>
        <td>${finStatusTag(c.status, c.data_vencimento)}</td>
        <td class="row-actions">${c.status !== 'PAGO' ? `<button class="icon-btn" data-baixar="${c.id}">Baixar</button>` : ''}
          <button class="icon-btn" data-del="${c.id}">🗑</button></td>
      </tr>`).join('') : `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-title">Nenhum título a pagar</div></div></td></tr>`;

    tbody.querySelectorAll('[data-baixar]').forEach(b => b.addEventListener('click', async () => {
      const conta = contas.find(c => c.id === Number(b.dataset.baixar));
      if (!confirm(`Confirmar pagamento de ${UI.fmtMoney(conta.valor_original)}?`)) return;
      await API.post(`/api/financeiro/contas-pagar/${conta.id}/baixar?valor_pago=${conta.valor_original}`);
      UI.toast('Título baixado.'); renderPagar();
    }));
    tbody.querySelectorAll('[data-del]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('Excluir este título?')) return;
      await API.del(`/api/financeiro/contas-pagar/${b.dataset.del}`);
      UI.toast('Título excluído.'); renderPagar();
    }));

    document.getElementById('btnNovoPagar').addEventListener('click', () => {
      UI.openModal({
        title: 'Novo Título a Pagar',
        bodyHtml: `<form id="fpForm" class="field-row">
          <label class="field"><span>Empresa *</span><select name="empresa_id" required>${empresas.map(e => `<option value="${e.value}">${e.label}</option>`).join('')}</select></label>
          <label class="field"><span>Fornecedor *</span><select name="fornecedor_id" required>${fornecedores.map(f => `<option value="${f.value}">${f.label}</option>`).join('')}</select></label>
          <label class="field"><span>Documento</span><input name="numero_documento"></label>
          <label class="field"><span>Valor *</span><input type="number" step="0.01" name="valor_original" required></label>
          <label class="field"><span>Vencimento *</span><input type="date" name="data_vencimento" required></label>
        </form>`,
        footerHtml: `<button class="btn btn-secondary" data-close>Cancelar</button><button class="btn btn-primary" id="fpSalvar">Salvar</button>`,
        onMount: (ov) => ov.querySelector('#fpSalvar').addEventListener('click', async () => {
          const fd = new FormData(ov.querySelector('#fpForm'));
          try {
            await API.post('/api/financeiro/contas-pagar', {
              empresa_id: Number(fd.get('empresa_id')), fornecedor_id: Number(fd.get('fornecedor_id')),
              numero_documento: fd.get('numero_documento') || null,
              valor_original: Number(fd.get('valor_original')), data_vencimento: fd.get('data_vencimento'),
            });
            UI.toast('Título criado.'); UI.closeModal(); renderPagar();
          } catch (e) { UI.toast(e.message, 'err'); }
        }),
      });
    });
  }

  async function renderReceber() {
    finContent.innerHTML = `
      <div class="table-toolbar"><div></div><button class="btn btn-primary" id="btnNovoReceber">+ Novo Título a Receber</button></div>
      <div class="table-wrap"><table class="data-table">
        <thead><tr><th>Cliente</th><th>Documento</th><th>Vencimento</th><th>Valor</th><th>Status</th><th style="width:100px">Ações</th></tr></thead>
        <tbody id="receberTbody"><tr><td colspan="6" style="padding:20px;color:#9096a8">Carregando...</td></tr></tbody>
      </table></div>`;
    const [clientes, empresas] = await Promise.all([optClientes(), optEmpresas()]);
    const cMap = Object.fromEntries(clientes.map(c => [c.value, c.label]));
    const contas = await API.get('/api/financeiro/contas-receber');
    const tbody = document.getElementById('receberTbody');
    tbody.innerHTML = contas.length ? contas.map(c => `
      <tr>
        <td>${cMap[c.cliente_id] || c.cliente_id}</td>
        <td class="mono">${c.numero_documento || '—'}</td>
        <td>${UI.fmtDate(c.data_vencimento)}</td>
        <td class="mono">${UI.fmtMoney(c.valor_original)}</td>
        <td>${finStatusTag(c.status, c.data_vencimento, 'RECEBIDO')}</td>
        <td class="row-actions">${c.status !== 'RECEBIDO' ? `<button class="icon-btn" data-baixar="${c.id}">Baixar</button>` : ''}
          <button class="icon-btn" data-del="${c.id}">🗑</button></td>
      </tr>`).join('') : `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-title">Nenhum título a receber</div></div></td></tr>`;

    tbody.querySelectorAll('[data-baixar]').forEach(b => b.addEventListener('click', async () => {
      const conta = contas.find(c => c.id === Number(b.dataset.baixar));
      if (!confirm(`Confirmar recebimento de ${UI.fmtMoney(conta.valor_original)}?`)) return;
      await API.post(`/api/financeiro/contas-receber/${conta.id}/baixar?valor_recebido=${conta.valor_original}`);
      UI.toast('Título baixado.'); renderReceber();
    }));
    tbody.querySelectorAll('[data-del]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('Excluir este título?')) return;
      await API.del(`/api/financeiro/contas-receber/${b.dataset.del}`);
      UI.toast('Título excluído.'); renderReceber();
    }));

    document.getElementById('btnNovoReceber').addEventListener('click', () => {
      UI.openModal({
        title: 'Novo Título a Receber',
        bodyHtml: `<form id="frForm" class="field-row">
          <label class="field"><span>Empresa *</span><select name="empresa_id" required>${empresas.map(e => `<option value="${e.value}">${e.label}</option>`).join('')}</select></label>
          <label class="field"><span>Cliente *</span><select name="cliente_id" required>${clientes.map(c => `<option value="${c.value}">${c.label}</option>`).join('')}</select></label>
          <label class="field"><span>Documento</span><input name="numero_documento"></label>
          <label class="field"><span>Valor *</span><input type="number" step="0.01" name="valor_original" required></label>
          <label class="field"><span>Vencimento *</span><input type="date" name="data_vencimento" required></label>
        </form>`,
        footerHtml: `<button class="btn btn-secondary" data-close>Cancelar</button><button class="btn btn-primary" id="frSalvar">Salvar</button>`,
        onMount: (ov) => ov.querySelector('#frSalvar').addEventListener('click', async () => {
          const fd = new FormData(ov.querySelector('#frForm'));
          try {
            await API.post('/api/financeiro/contas-receber', {
              empresa_id: Number(fd.get('empresa_id')), cliente_id: Number(fd.get('cliente_id')),
              numero_documento: fd.get('numero_documento') || null,
              valor_original: Number(fd.get('valor_original')), data_vencimento: fd.get('data_vencimento'),
            });
            UI.toast('Título criado.'); UI.closeModal(); renderReceber();
          } catch (e) { UI.toast(e.message, 'err'); }
        }),
      });
    });
  }

  function finStatusTag(status, vencimento, quitadoLabel = 'PAGO') {
    if (status === quitadoLabel || status === 'PAGO' || status === 'RECEBIDO') return '<span class="tag tag-green">Quitado</span>';
    const atrasado = new Date(vencimento) < new Date(new Date().toDateString());
    return atrasado ? '<span class="tag tag-red">Atrasado</span>' : '<span class="tag tag-amber">Em aberto</span>';
  }

  renderPagar();
}

// -------- Inicialização --------
navigate('dashboard');
