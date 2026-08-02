const UI = {};

UI.toast = function (msg, type = 'ok') {
  let wrap = document.querySelector('.toast-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.className = 'toast-wrap';
    document.body.appendChild(wrap);
  }
  const el = document.createElement('div');
  el.className = `toast ${type === 'err' ? 'err' : type === 'ok' ? 'ok' : ''}`;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3800);
};

UI.fmtMoney = (v) => (Number(v) || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
UI.fmtDate = (v) => v ? new Date(v + (v.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('pt-BR') : '—';
UI.fmtNum = (v, dec = 2) => (Number(v) || 0).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });

UI.closeModal = function () {
  const ov = document.querySelector('.modal-overlay');
  if (ov) ov.remove();
};

UI.openModal = function ({ title, bodyHtml, onMount, footerHtml }) {
  UI.closeModal();
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div class="modal-title">${title}</div>
        <button class="icon-btn" data-close>✕</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
      <div class="modal-footer">${footerHtml || ''}</div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) UI.closeModal(); });
  overlay.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', UI.closeModal));
  if (onMount) onMount(overlay);
  return overlay;
};

/**
 * Motor genérico de CRUD (tabela + modal de formulário) dirigido por configuração.
 * config = {
 *   title, apiPath, idField: 'id',
 *   columns: [{ key, label, render? }],
 *   formFields: [{ key, label, type: 'text'|'number'|'date'|'select'|'checkbox'|'textarea',
 *                  options?: [{value,label}] | async fn, required?, span? }]
 *   searchable: bool
 * }
 */
UI.renderCrudView = async function (container, config) {
  container.innerHTML = `
    <div class="table-toolbar">
      <input class="search-input" placeholder="Buscar..." id="crud-search" ${config.searchable === false ? 'style="visibility:hidden"' : ''}>
      <button class="btn btn-primary" id="crud-new">+ Novo registro</button>
    </div>
    <div class="table-wrap"><table class="data-table">
      <thead><tr>${config.columns.map(c => `<th>${c.label}</th>`).join('')}<th style="width:90px">Ações</th></tr></thead>
      <tbody id="crud-tbody"><tr><td colspan="99" style="padding:20px;color:#9096a8">Carregando...</td></tr></tbody>
    </table></div>
  `;

  let items = [];

  async function load(q) {
    const qs = q ? `?q=${encodeURIComponent(q)}` : '';
    items = await API.get(`${config.apiPath}${qs}`);
    renderRows();
  }

  function renderRows() {
    const tbody = container.querySelector('#crud-tbody');
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="99"><div class="empty-state"><div class="empty-state-title">Nenhum registro encontrado</div>Cadastre o primeiro clicando em "Novo registro".</div></td></tr>`;
      return;
    }
    tbody.innerHTML = items.map(item => `
      <tr>
        ${config.columns.map(c => `<td>${c.render ? c.render(item) : (item[c.key] ?? '—')}</td>`).join('')}
        <td class="row-actions">
          <button class="icon-btn" data-edit="${item[config.idField || 'id']}">✎</button>
          <button class="icon-btn" data-del="${item[config.idField || 'id']}">🗑</button>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('[data-edit]').forEach(btn =>
      btn.addEventListener('click', () => openForm(items.find(i => String(i[config.idField || 'id']) === btn.dataset.edit))));
    tbody.querySelectorAll('[data-del]').forEach(btn =>
      btn.addEventListener('click', () => removeItem(btn.dataset.del)));
  }

  async function removeItem(id) {
    if (!confirm('Confirma a exclusão deste registro?')) return;
    try {
      await API.del(`${config.apiPath}/${id}`);
      UI.toast('Registro excluído.');
      load();
    } catch (e) { UI.toast(e.message, 'err'); }
  }

  async function resolveOptions(field) {
    if (typeof field.options === 'function') return await field.options();
    return field.options || [];
  }

  async function openForm(item) {
    const isEdit = !!item;
    const fieldsHtml = await Promise.all(config.formFields.map(async (f) => {
      const val = item ? (item[f.key] ?? '') : (f.default ?? '');
      if (f.type === 'select') {
        const opts = await resolveOptions(f);
        return `<label class="field" style="grid-column: span ${f.span || 1}">
          <span>${f.label}${f.required ? ' *' : ''}</span>
          <select name="${f.key}" ${f.required ? 'required' : ''}>
            <option value="">Selecione...</option>
            ${opts.map(o => `<option value="${o.value}" ${String(o.value) === String(val) ? 'selected' : ''}>${o.label}</option>`).join('')}
          </select></label>`;
      }
      if (f.type === 'checkbox') {
        return `<label class="field" style="grid-column: span ${f.span || 1}; flex-direction:row; align-items:center; gap:8px;">
          <input type="checkbox" name="${f.key}" ${val ? 'checked' : ''}> <span>${f.label}</span></label>`;
      }
      if (f.type === 'textarea') {
        return `<label class="field" style="grid-column: span ${f.span || 2}">
          <span>${f.label}</span><textarea name="${f.key}" rows="3">${val ?? ''}</textarea></label>`;
      }
      return `<label class="field" style="grid-column: span ${f.span || 1}">
        <span>${f.label}${f.required ? ' *' : ''}</span>
        <input type="${f.type || 'text'}" name="${f.key}" value="${val ?? ''}" ${f.required ? 'required' : ''} ${f.step ? `step="${f.step}"` : ''}>
      </label>`;
    }));

    UI.openModal({
      title: isEdit ? `Editar ${config.title}` : `Novo ${config.title}`,
      bodyHtml: `<form id="crud-form" class="field-row">${fieldsHtml.join('')}</form>`,
      footerHtml: `<button class="btn btn-secondary" data-close>Cancelar</button>
                   <button class="btn btn-primary" id="crud-save">Salvar</button>`,
      onMount: (overlay) => {
        overlay.querySelector('#crud-save').addEventListener('click', async () => {
          const form = overlay.querySelector('#crud-form');
          const payload = {};
          config.formFields.forEach(f => {
            const el = form.querySelector(`[name="${f.key}"]`);
            if (f.type === 'checkbox') payload[f.key] = el.checked;
            else if (f.type === 'number') payload[f.key] = el.value === '' ? 0 : Number(el.value);
            else payload[f.key] = el.value === '' ? null : el.value;
          });
          try {
            if (isEdit) await API.put(`${config.apiPath}/${item[config.idField || 'id']}`, payload);
            else await API.post(config.apiPath, payload);
            UI.toast(isEdit ? 'Registro atualizado.' : 'Registro criado.');
            UI.closeModal();
            load();
          } catch (e) { UI.toast(e.message, 'err'); }
        });
      },
    });
  }

  container.querySelector('#crud-new').addEventListener('click', () => openForm(null));
  let searchTimer;
  container.querySelector('#crud-search').addEventListener('input', (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => load(e.target.value), 300);
  });

  load();
};
