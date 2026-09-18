# Roadmap do curso — workspace do professor

Print da pasta `voebem` do professor (workspace pessoal), capturado em 2026-09-17.
Serve de referência pra conferir se estamos seguindo a mesma estrutura/nomenclatura.

## Estrutura vista

```
voebem/
├── pipelines/                    (pasta)
├── 03_bronze_vra                 ✅ feito com a gente
├── 04_bronze_referencias         ✅ feito (gerado por mim, conferir se bate com o do prof)
├── 05_silver_espelho
├── 05_silver_voos
├── 09_governanca_gold
├── _validacao_camadas
└── VoeBem Analytics - Voos atrasos e... (Genie agent, nome cortado no print)
```

Obs: a lista continuava rolando pra baixo no print — pode ter mais itens entre
`09_governanca_gold` e o Genie agent (numeração pulou de 05 pra 09, então
provavelmente tem 06, 07, 08 no meio que não apareceram).

## Padrão de nomenclatura observado

- Prefixo numérico = ordem/camada (`03`, `04`, `05`, `09`...)
- Camada Bronze: `0X_bronze_<fonte>`
- Camada Silver: `0X_silver_<assunto>` (existem dois silver: `espelho` e `voos` —
  investigar a diferença quando chegarmos lá)
- Camada Gold: `0X_governanca_gold`
- Notebook com `_` na frente (`_validacao_camadas`) = utilitário/suporte, não
  faz parte do pipeline numerado principal
- No fim tem um **Genie agent** (assistente de dados conversacional) chamado
  algo como "VoeBem Analytics - Voos atrasos e ..." — provavelmente a entrega
  final do curso, uma interface de perguntas em linguagem natural sobre atrasos

## Progresso local (nosso projeto)

- [x] `03_bronze_vra` — feito célula a célula acompanhando o professor
- [x] `04_bronze_referencias` — **substituído pela versão oficial** do repo
      github.com/Alura-Imersao-Engenharia-de-dados-2026/projeto-aviacao-anac em
      2026-09-18 (minha primeira versão tinha schema errado — faltava
      `codigos_operacao`, `quote=chr(0)` nos aeródromos, e o mapeamento
      `Estrangeira→sigla_iata`/`Ativa→situacao`). Rodou ok depois do fix de
      pasta (`referencias/informativos` → `referencias`).
- [x] `05_silver_espelho` — rodado inteiro em 2026-09-18 (silver.vra, silver.empresas,
      silver.aerodromos, silver.codigos_operacao, comments + tags de governança)
- [ ] `06`, `07`, `08` — desconhecidos ainda
- [ ] `09_governanca_gold`
- [ ] `_validacao_camadas`
- [ ] Genie agent final
