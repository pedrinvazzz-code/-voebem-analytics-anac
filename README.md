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
- `docs/` — fontes de dados, perguntas de negócio, roadmap e notas do processo

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

## Progresso

- [x] Bronze: `vra`, `aerodromos`, `empresas_nacionais`, `empresas_estrangeiras`,
      `codigos_operacao` (1.014.705 linhas em `vra`)
- [x] Silver: espelho completo, mesma contagem de linhas do Bronze
- [x] Pipeline de qualidade: 12 expectations (9 do gabarito + 3 adicionais:
      catalogação de `codigo_di`/`codigo_tipo_linha` e detecção de duplicata exata)
- [x] Gold: `dim_aeroporto`, `fato_voos`, `obt_voos` (1.014.664 linhas — 41
      duplicatas exatas removidas, única exclusão de linha do pipeline)
- [x] Governança: `COMMENT` em todas as colunas, tags, lineage automático via
      Unity Catalog
- [x] Genie Agent conectado à `obt_voos`, validado contra o gabarito de negócio
      (ex: atraso médio em Guarulhos = 13,42 min, idêntico ao gabarito oficial)

## Créditos

Contexto educacional: **Imersão Engenharia de Dados**, Alura, setembro/2026.
Fonte dos dados: ANAC (Agência Nacional de Aviação Civil), ver `docs/fontes.md`.

O gabarito de referência usado para validar cada camada deste projeto vem do
repositório colaborativo da turma:
[Alura-Imersao-Engenharia-de-dados-2026/projeto-aviacao-anac](https://github.com/Alura-Imersao-Engenharia-de-dados-2026/projeto-aviacao-anac).
