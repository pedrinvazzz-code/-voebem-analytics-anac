-- ---------------------------------------------------------------------------
-- Passo 1 — marcar cada voo com o resultado dos testes de integridade.
--
-- Expectation NAO aceita subquery. E integridade referencial e, por definicao,
-- "existe na outra tabela?" — ou seja, uma subquery. A saida e resolver o join
-- AQUI, com LEFT JOIN + flag booleana, e deixar a expectation olhando so a flag.
--
-- Temporary view: e logica intermediaria do pipeline, nao dado publicado.
--
-- Versao expandida (base: gabarito oficial do marco-06) com duas flags a mais,
-- descobertas na auditoria de governanca do projeto:
--   - codigo_di / codigo_tipo_linha nao catalogados na seed table
--     (codigo_di = 1 aparece no VRA e nao tem descricao oficial da ANAC)
--   - linha duplicada (todas as colunas de negocio identicas a outra linha)
--
-- Repare no que continua sem estar aqui: nenhuma classificacao de negocio
-- (nacional/estrangeiro, dentro/fora da faixa etc). So fato verificavel.
-- ---------------------------------------------------------------------------
CREATE TEMPORARY VIEW vra_marcado AS
WITH aerodromo AS (
  SELECT DISTINCT icao FROM voebem.silver.aerodromos
  WHERE icao IS NOT NULL AND icao <> ''
),
empresa AS (
  SELECT DISTINCT icao FROM voebem.silver.empresas
  WHERE icao IS NOT NULL AND icao <> ''
),
di AS (
  SELECT DISTINCT codigo FROM voebem.silver.codigos_operacao WHERE dominio = 'codigo_di'
),
tipo_linha AS (
  SELECT DISTINCT codigo FROM voebem.silver.codigos_operacao WHERE dominio = 'codigo_tipo_linha'
)
SELECT
  v.*,
  (ao.icao   IS NOT NULL) AS origem_no_cadastro,
  (ad.icao   IS NOT NULL) AS destino_no_cadastro,
  (em.icao   IS NOT NULL) AS empresa_no_cadastro,
  (di.codigo IS NOT NULL) AS codigo_di_catalogado,
  (tl.codigo IS NOT NULL) AS codigo_tipo_linha_catalogado,
  -- diagnostico, nao decisao: so aponta se a linha se repete identica.
  -- remover duplicata (se for o caso) e decisao de negocio da camada gold.
  COUNT(*) OVER (
    PARTITION BY icao_empresa, numero_voo, codigo_di, codigo_tipo_linha,
                 icao_origem, icao_destino, partida_prevista, partida_real,
                 chegada_prevista, chegada_real, situacao_voo
  ) > 1                                                              AS linha_duplicada
FROM voebem.silver.vra v
LEFT JOIN aerodromo   ao ON v.icao_origem      = ao.icao
LEFT JOIN aerodromo   ad ON v.icao_destino     = ad.icao
LEFT JOIN empresa     em ON v.icao_empresa     = em.icao
LEFT JOIN di             ON v.codigo_di        = di.codigo
LEFT JOIN tipo_linha  tl ON v.codigo_tipo_linha = tl.codigo;
