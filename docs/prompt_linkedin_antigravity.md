# Prompt para o Antigravity — contexto completo do projeto

Cole isso no Antigravity junto com os dois links:
- https://www.alura.com.br/imersao-engenharia-dados
- https://github.com/Alura-Imersao-Engenharia-de-dados-2026/projeto-aviacao-anac

---

## Prompt

Estou fazendo a **Imersão Engenharia de Dados 2026 da Alura**, um curso prático
onde a gente constrói, do zero, um pipeline de dados real usando **Databricks**
(Unity Catalog, Delta Lake, PySpark e SQL) sobre dados abertos da **ANAC**
(Agência Nacional de Aviação Civil) — voos, atrasos, aeródromos e empresas
aéreas. O projeto final se chama **VoeBem Analytics** e termina com um agente
conversacional (Genie) que responde perguntas em linguagem natural sobre
atrasos de voos no Brasil.

Quero que você me ajude a **escrever um post pro LinkedIn** contando essa
experiência de aprendizado. Abaixo está o relato detalhado de tudo que eu fiz
até agora numa sessão de trabalho com o Claude Code, que me ajudou como
"par de programação" enquanto eu acompanhava as aulas do curso. Use isso como
matéria-prima — não é pra copiar literalmente, é pra você entender o processo
real e me ajudar a transformar isso numa narrativa boa pra LinkedIn (que mostre
aprendizado prático, não só "fiz um curso").

### 1. Organização do projeto

Criei uma pasta local (`curso-databricks-voos/`) espelhando a estrutura que
uso no Databricks, com subpastas `dados/` (organizados em `vra/` e
`referencias/`), `notebooks/` (backup de cada notebook em formato fonte do
Databricks) e `docs/` (anotações). A ideia foi ter um histórico local de tudo
que ia sendo construído no workspace do Databricks, já que o curso é 100%
feito na nuvem.

### 2. Coleta dos dados brutos (ANAC)

Baixei os datasets diretamente do portal de dados abertos da ANAC
(`sistemas.anac.gov.br/dadosabertos`):

- **VRA (Voo Regular Ativo)**: 12 arquivos CSV mensais, um ano completo
  (agosto/2025 a julho/2026) — cada linha é uma etapa de voo, com horário
  previsto x real de partida/chegada, situação (realizado/cancelado) e código
  de justificativa de atraso. No meio do processo percebi que faltavam 3 meses
  (outubro, novembro e dezembro de 2025) porque o padrão de nome do arquivo
  muda de 5 para 6 dígitos nesses meses (`VRA_20259.csv` vs `VRA_202510.csv`)
  — fui direto na estrutura de pastas do portal da ANAC (que tem um índice
  tipo Apache diretório) pra confirmar e baixar os que faltavam.
- **Referências**: cadastro de aeródromos públicos, e dois cadastros
  separados de empresas aéreas (nacionais e estrangeiras) — cada um com
  schema, encoding e peculiaridades diferentes, mesmo vindo do mesmo órgão.

### 3. Subida pro Databricks (Unity Catalog Volumes)

Fiz upload de tudo pra um Volume do Unity Catalog
(`/Volumes/voebem/bronze/arquivos`) e organizei em subpastas (`vra/` e
`referencias/`) usando tanto a interface quanto `dbutils.fs.mv` direto num
notebook — a interface de Volumes do Databricks ainda não tem um botão de
"mover arquivo" nativo, então isso teve que ser feito via código.

### 4. Camada Bronze — ingestão crua e auditável

Construí, célula por célula, acompanhando o professor ao vivo, o notebook
`03_bronze_vra`, seguindo os princípios rígidos da camada Bronze na
arquitetura medallion:

- **nada de tipagem** — tudo entra como `string`, exatamente como veio do CSV;
- **nada de filtro** — nenhuma linha é descartada, mesmo linhas "estranhas";
- **colunas de auditoria** — `_arquivo_origem` (usando a coluna oculta
  `_metadata.file_name` que o Spark expõe automaticamente) e `_ingerido_em`;
- **carga idempotente** — usando `overwrite` determinístico em vez de
  `append` com deduplicação, porque a fonte (ANAC) é imutável e completa a
  cada mês, e o VRA não tem uma chave de negócio única confiável pra
  deduplicar.

Detalhes técnicos que aprendi na prática:
- Os CSVs da ANAC têm uma primeira linha de metadado (`Atualizado em: <data>`)
  antes do cabeçalho real — resolvido com `skipRows=1` no leitor de CSV do
  Spark, que também descarta o BOM (`EF BB BF`) que vinha grudado nela.
- Nomes de coluna com espaço (`"ICAO Empresa Aérea"`) são válidos em CSV mas
  **inválidos em Delta Lake** — tive que normalizar todos os nomes de coluna
  num dicionário explícito de renomeação (sem usar regex mágico, pra manter a
  correspondência auditável com o arquivo original).
- Resultado: **1.014.705 linhas** carregadas na tabela `voebem.bronze.vra`.

### 5. Debugging real (a parte que mais ensina)

Passei por vários erros reais de engenharia de dados cloud, não só teoria:
- **Case sensitivity em Volumes**: criei uma pasta `Vra` (V maiúsculo) mas
  escrevi `vra` minúsculo no código — Volumes do Databricks são baseados em
  object storage (S3/ADLS/GCS), que é case-sensitive. Erro de
  "path not found" silencioso até eu perceber a diferença de capitalização.
- **Pastas aninhadas por engano**: ao organizar os arquivos de referência,
  acabei criando uma subpasta a mais sem querer (`referencias/informativos/`
  em vez de só `referencias/`), quebrando o caminho que o notebook esperava.
- **NameError / execução fora de ordem**: describir como células de notebook
  Databricks dependem de execução sequencial — rodar uma célula isolada sem
  rodar as anteriores quebra porque variáveis não existem ainda no kernel.

### 6. Camada Bronze das referências — onde os dados "mentem"

Ao tentar construir a camada Silver de empresas aéreas
(`voebem.silver.empresas`), bati num erro de coluna inexistente
(`sigla_iata`). Isso me levou a **descobrir o repositório oficial do curso no
GitHub** (que o professor documenta publicamente) e usar ele pra validar e
corrigir minha própria implementação da camada Bronze de referências. Isso
revelou pegadinhas reais dos dados abertos da ANAC:

- A coluna que a ANAC nomeia **`"Estrangeira"`** no cadastro de empresas
  aéreas **não é um flag booleano** — na verdade contém o **código IATA**
  (2 letras) da empresa. Um nome de coluna completamente enganoso na fonte
  oficial do governo.
- O arquivo de aeródromos usa caracteres `"` (aspas) dentro dos próprios
  dados pra representar **segundos de coordenada geográfica**
  (`09°52'06"S`), o que engana o parser de CSV padrão do Spark — ele acha que
  é início de um campo entre aspas e "engole" várias linhas seguintes sem
  dar erro nenhum, corrompendo os dados silenciosamente. A correção foi
  desligar o "quoting" do leitor de CSV completamente
  (`quote = chr(0)`, um caractere que não existe no arquivo).
- Esse mesmo arquivo de aeródromos vem em **encoding Latin-1**, enquanto os
  outros CSVs da mesma ANAC vêm em UTF-8 — inconsistência dentro do mesmo
  portal de dados abertos do governo.
- A ANAC publica empresas aéreas em **dois cadastros administrativos
  separados** (nacionais e estrangeiras) com o **mesmo schema exato** — a
  tentação óbvia seria unir os dois já na Bronze com um `UNION`, mas a regra
  da camada é "um arquivo de origem, uma tabela": a unificação é decisão de
  modelagem e só pode acontecer na Silver, preservando de qual cadastro cada
  registro veio (`origem_cadastro`).

### 7. Onde estou agora: camada Silver

Entrando na camada Silver (`05_silver_espelho`), cuja regra central é: **a
Silver é o espelho do Bronze com governança aplicada** — mesmo nome de
tabela, mesmo grão, **mesma contagem de linhas**. É permitido tipar
(`string` → `TIMESTAMP`/`DATE`), documentar (`COMMENT` em cada coluna, porque
o consumidor final do pipeline vai ser um **agente de IA via Genie**, que lê
os comentários pra decidir qual coluna usar), unificar cadastros do mesmo
assunto (sem perder linha), e fazer aritmética pura entre colunas da própria
linha (`atraso = horário_real - horário_previsto`). É **proibido** filtrar,
agregar ou aplicar qualquer limiar/regra de negócio — isso é trabalho da
camada Gold, que ainda não cheguei.

### O que eu quero que o post transmita

- Aprendizado hands-on de um pipeline de dados real de ponta a ponta, não só
  teoria de curso.
- A disciplina da arquitetura medallion (Bronze/Silver/Gold) como conceito —
  por que cada regra existe, não só "o que" fazer.
- Que dados abertos governamentais têm problemas reais (encoding, nomes de
  coluna enganosos, arquivos corrompidos, inconsistência entre arquivos do
  mesmo órgão) e que parte do trabalho de engenharia de dados é justamente
  caçar essas armadilhas antes que elas virem erro silencioso em produção.
- Que usei IA (Claude Code) como par de programação pra debugar erros,
  validar meu código contra o gabarito oficial do curso e manter um backup
  organizado do progresso — sem substituir o aprendizado ativo de digitar e
  entender cada célula junto com o professor.
