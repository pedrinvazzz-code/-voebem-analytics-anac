# Databricks notebook source
# MAGIC %md
# MAGIC ## BRONZE - VRA
# MAGIC Lê os 12 CSVs mensais do volume `voebem.bronze.arquivos/vra/` e materializa `voebem.bronze.vra`.
# MAGIC
# MAGIC Regras da camada Bronze:
# MAGIC
# MAGIC - **nada de tipagem** — tudo string, exatamente como veio do arquivo;__
# MAGIC - **nada de filtro** — nenhuma linha é descartada;
# MAGIC - **colunas de auditoria** — de qual arquivo veio e quando foi ingerido;
# MAGIC - **idempotente** — rodar duas vezes não duplica.

# COMMAND ----------

from pyspark.sql import functions as F

CAMINHO = "/Volumes/voebem/bronze/arquivos/Vra/*.csv"
TABELA = "voebem.bronze.vra"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Leitura
# MAGIC
# MAGIC Quatro opções carregam quatro problemas do arquivo:
# MAGIC
# MAGIC | opção | resolve |
# MAGIC |---|---|
# MAGIC | `sep=";"` | separador brasileiro, não vírgula |
# MAGIC | `skipRows=1` | a 1ª linha é `Atualizado em: <data>`, não o cabeçalho — e o BOM `EF BB BF` mora nela, some junto |
# MAGIC | `header=true` | a 2ª linha (a primeira que sobra) é o cabeçalho de verdade |
# MAGIC | `inferSchema` **desligado** (default) | bronze não tipa: tudo chega como `string` |

# COMMAND ----------

bruto = (
    spark.read.format("csv")
    .option("sep", ";")
    .option("header", "true")
    .option("skipRows", 1)          # descarta "Atualizado em: ..." (e o BOM junto)
    .option("quote", '"')
    .option("escape", '"')
    .option("encoding", "UTF-8")
    .option("mode", "PERMISSIVE")   # bronze nao descarta linha nenhuma
    .load(CAMINHO)
)

print("colunas lidas do arquivo:")
for c in bruto.columns:
    print(f"  {c!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Nomes de coluna: o Delta não aceita espaço
# MAGIC
# MAGIC `ICAO Empresa Aérea` é um nome de coluna válido em CSV e **inválido** em Delta —
# MAGIC espaço está na lista de caracteres proibidos ( `,;{}()\n\t=` ).
# MAGIC
# MAGIC Então normalizamos o *nome*. Repare que isso não fere a regra da bronze: o que a
# MAGIC bronze preserva é o *valor* e a *granularidade*, não a grafia do cabeçalho.
# MAGIC Nenhuma coluna é somada, removida, filtrada ou convertida.
# MAGIC
# MAGIC O mapa fica explícito no código — nada de `regexp_replace` mágico, para que a
# MAGIC correspondência com o arquivo original seja auditável.

# COMMAND ----------

RENOMEAR = {
    "ICAO Empresa Aérea": "icao_empresa",
    "Número Voo": "numero_voo",
    "Código Autorização (DI)": "codigo_di",
    "Código Tipo Linha": "codigo_tipo_linha",
    "ICAO Aeródromo Origem": "icao_origem",
    "ICAO Aeródromo Destino": "icao_destino",
    "Partida Prevista": "partida_prevista",
    "Partida Real": "partida_real",
    "Chegada Prevista": "chegada_prevista",
    "Chegada Real": "chegada_real",
    "Situação Voo": "situacao_voo",
    "Código Justificativa": "codigo_justificativa",
}

faltando = [c for c in RENOMEAR if c not in bruto.columns]
assert not faltando, f"Coluna esperada nao encontrada no CSV: {faltando}"

renomeado = bruto.select(
    *[F.col(f"`{origem}`").cast("string").alias(novo) for origem, novo in RENOMEAR.items()]
)

# COMMAND ----------

# MAGIC %md
# MAGIC # Auditoria
# MAGIC
# MAGIC Duas colunas que o arquivo não tem e a tabela precisa ter:
# MAGIC `_arquivo_origem` (de qual CSV a linha veio — `_metadata` é uma coluna
# MAGIC oculta que o Spark expõe em qualquer leitura de arquivo) e
# MAGIC `_ingerido_em`.

# COMMAND ----------

bronze = renomeado.withColumn(
    "_arquivo_origem", F.col("_metadata.file_name")
).withColumn(
    "_ingerido_em", F.current_timestamp()
)

# COMMAND ----------

# MAGIC %md
# MAGIC # Escrita idempotente
# MAGIC
# MAGIC Estratégia: **full refresh determinístico** — `mode("overwrite")` sobre o
# MAGIC conjunto inteiro de arquivos.
# MAGIC
# MAGIC Por que essa e não um `append` com deduplicação:
# MAGIC
# MAGIC 1. A fonte é **imutável e completa**: o volume tem os 12 arquivos do
# MAGIC    mês fechado, e a ANAC republica o mês inteiro quando corrige
# MAGIC    algo. A entrada define o estado final — logo o destino pode ser
# MAGIC    derivado inteiro dela.
# MAGIC 2. `append` exigiria uma chave de negócio para deduplicar. O VRA **não
# MAGIC    tem chave natural única** (o mesmo voo pode repetir
# MAGIC    legitimamente na mesma data — veja o código DI "Etapa de Voo
# MAGIC    Duplicada"). Deduplicar no bronze seria decidir regra de negócio
# MAGIC    na camada errada.
# MAGIC 3. `overwrite` no Delta é **atômico**: ou a versão nova aparece inteira,
# MAGIC    ou a antiga continua valendo. Ninguém lê tabela pela metade.
# MAGIC 4. O histórico não se perde: cada `overwrite` gera uma versão nova
# MAGIC    no log do Delta, e a anterior continua acessível por time travel
# MAGIC    (marco-04).
# MAGIC
# MAGIC O que muda entre duas execuções: só `_ingerido_em`. O **conjunto de
# MAGIC linhas** é idêntico — é isso que a validação prova.

# COMMAND ----------

(
    bronze.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TABELA)
)

print(f"{TABELA}: {spark.table(TABELA).count():,} linhas")

# COMMAND ----------

spark.sql(f"""
    COMMENT ON TABLE {TABELA} IS
    'Bronze - VRA (Voo Regular Ativo) da ANAC, 12 meses (ago/2025 a jul/2026).
    Dado bruto: todas as colunas string, nenhuma linha descartada.
    Carga full refresh idempotente a partir de /Volumes/voebem/bronze/arquivos/vra/.'
""")

# COMMAND ----------

display(
    spark.sql(f"""
        SELECT _arquivo_origem, COUNT(*) AS linhas, MAX(_ingerido_em) AS ingerido_em
        FROM {TABELA}
        GROUP BY _arquivo_origem
        ORDER BY _arquivo_origem
    """)
)
