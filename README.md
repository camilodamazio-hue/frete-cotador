# Frete Cotador Web (FastAPI + SQLite)

Sistema web simples para **usuários diversos** realizarem **cotações de frete** com base na planilha:
`Tabela_Redespacho_MT_Cliente_Estrategico.xlsx`.

## Funcionalidades
- Cadastro e login de usuários (senha com hash).
- Tela de cotação com:
  - Origem / Destino (busca no banco)
  - Peso (kg)
  - Volume (m³) → cubagem conforme a tabela (ex.: 300 kg/m³)
  - Valor da mercadoria (R$) → Ad Valorem (% com mínimo)
- Cálculo do peso cubado e peso tarifável (maior entre real e cubado)
- Histórico de cotações por usuário
- Área admin (usuário com `is_admin=1`) para:
  - Importar/atualizar a tabela a partir do Excel

## Como rodar (local)
1. Crie um venv e instale dependências:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure variáveis (opcional):
- `APP_SECRET` (padrão: "dev-secret-change-me")
- `DATABASE_URL` (padrão: "sqlite:///./app.db")

3. Inicialize o banco e importe a planilha:
```bash
python import_table.py --excel ../Tabela_Redespacho_MT_Cliente_Estrategico.xlsx
```

4. Rode o servidor:
```bash
uvicorn main:app --reload
```

Acesse: http://127.0.0.1:8000

## Usuário admin
Você pode promover um usuário a admin diretamente no SQLite:
```sql
UPDATE users SET is_admin=1 WHERE email='seuemail@dominio.com';
```

## Observações do cálculo
- **Peso cubado** = `volume_m3 * cubagem_kg_por_m3` (da tabela do lane)
- **Peso tarifável** = `max(peso_real_kg, peso_cubado)`
- **Frete base**:
  - se `peso_tarifavel <= 10`: usa `min_ate_10kg`
  - senão: `min_ate_10kg + (peso_tarifavel - 10) * kg_excedente`
- **Ad Valorem** = `max(valor_mercadoria * (adval_percent/100), adval_min)`
- **Total** = `frete_base + advalorem`

ICMS na tabela consta como “Não destacado” (apenas informativo).
