# VoeBem Analytics — Análise de Voos ANAC (Databricks)

Projeto construído durante a **Imersão Engenharia de Dados 2026 da Alura**: pipeline
completo de dados de voos no Brasil (ANAC), seguindo a arquitetura medallion
(Bronze → Silver → Gold) no Databricks, com Delta Lake, Unity Catalog, PySpark, SQL
e um agente Genie para consultas em linguagem natural.

A VoeBem Analytics é a consultoria fictícia do exercício: o objetivo é responder
**quais voos, companhias e rotas mais atrasam no Brasil, e por quê**.

## Estrutura

- `dados/` — 15 CSVs da ANAC: 12 meses de VRA (ago/2025–jul/2026) em `vra/`, e os
  cadastros de aeródromos e empresas aéreas em `referencias/`
- `notebooks/` — notebooks Databricks (formato `.py` fonte) das camadas Bronze e Silver
- `pipelines/qualidade/` — pipeline declarativo de qualidade de dados (expectations,
  modo warn, quarentena como diagnóstico)
- `sql/gold/` — camada Gold: dimensão de aeroporto, fato de voos, OBT (`obt_voos`)
- `genie/` — instruções do agente conversacional (Genie) sobre os dados
- `docs/` — fontes de dados, perguntas de negócio e critérios de aceitação

## Camadas

1. **Bronze** (`notebooks/03_bronze_vra.py`, `04_bronze_referencias.py`) — ingestão
   crua, sem tipagem nem filtro, com colunas de auditoria e carga idempotente.
2. **Silver** (`notebooks/05_silver_espelho.py`) — espelho tipado e documentado do
   Bronze, mesma contagem de linhas, sem regra de negócio.
3. **Qualidade** (`pipelines/qualidade/`) — contrato de dados declarativo (expectations
   em modo warn) + tabela de quarentena como diagnóstico, nunca filtro.
4. **Gold** (`sql/gold/`) — regras de negócio (pontualidade a 15 min, escopo
   doméstico/internacional, decisões sobre a quarentena) e a `obt_voos`, uma
   One Big Table desnormalizada desenhada para consumo por IA.
5. **Genie** (`genie/`) — agente conversacional sobre `voebem.gold.obt_voos`.

## Resultados

- **Bronze:** 5 tabelas (`vra`, `aerodromos`, `empresas_nacionais`, `empresas_estrangeiras`,
  `codigos_operacao`) — 1.014.705 linhas em `vra`, ingestão crua e idempotente
- **Silver:** espelho tipado e documentado, mesma contagem de linhas do Bronze
- **Qualidade:** pipeline declarativo com 12 expectations em modo warn (completude,
  coerência temporal, faixa plausível, integridade referencial, catalogação de
  código e detecção de duplicata), com quarentena como diagnóstico
- **Gold:** `dim_aeroporto`, `fato_voos` e `obt_voos` — 1.014.664 linhas (41
  duplicatas exatas removidas na única exclusão de linha do pipeline), com
  pontualidade, escopo doméstico/internacional e nomes resolvidos sem exigir join
- **Governança:** `COMMENT` em toda coluna, tags e lineage automático via Unity Catalog
- **Genie Agent** conectado à `obt_voos`, respondendo em linguagem natural às
  perguntas de negócio do projeto (ex: aeroportos com maiores atrasos, pontualidade
  por companhia, recuperação de atraso em voo)

## Créditos

Contexto educacional: **Imersão Engenharia de Dados**, Alura, setembro/2026.
Fonte dos dados: ANAC (Agência Nacional de Aviação Civil), ver `docs/fontes.md`.
