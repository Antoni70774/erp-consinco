// ==========================================================================
// CONFIGURAÇÃO DE AMBIENTE — único arquivo que muda entre clientes/ambientes
// ==========================================================================
// Desenvolvimento local: deixe como está (http://localhost:8000)
// Produção na nuvem: troque API_BASE pela URL pública do backend, ex:
//   window.ERP_CONFIG = { API_BASE: "https://erp-clientex-backend.up.railway.app" };
//
// Cada cliente instalado terá sua própria cópia deste arquivo apontando
// para o backend/banco daquele cliente na nuvem.
// ==========================================================================
window.ERP_CONFIG = {
  API_BASE: "https://erp-consinco-backend.onrender.com",
  CLIENTE_NOME: "Minha Empresa",
};
