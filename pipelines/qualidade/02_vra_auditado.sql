-- ---------------------------------------------------------------------------
-- Passo 2 — o contrato de dados, escrito como codigo.
--
-- TODAS as expectations aqui sao "warn" (nenhuma tem ON VIOLATION). Isso e
-- arquitetura, nao preguica: a silver nao pode perder registro. As expectations
-- MEDEM a qualidade e publicam a metrica no event log; a linha continua viva.
--
-- Quem decide excluir e a gold, porque excluir e decisao de negocio.
--
-- Por que LIVE VIEW e nao TEMPORARY VIEW: CREATE TEMPORARY VIEW nao aceita
-- clausula CONSTRAINT. LIVE VIEW e a forma retida exatamente para o caso
-- "view intermediaria com expectations" — nada e materializado em UC aqui,
-- so as metricas do contrato saem para o event log.
--
-- Cuidado com NULL: numa expectation, NULL conta como REPROVADO. Por isso as
-- regras que podem receber NULL legitimamente (voo cancelado nao tem
-- chegada real) escrevem o NULL como aprovado, explicitamente.
--
-- Versao expandida (base: gabarito oficial do marco-06) com 3 constraints a
-- mais, que o gabarito original nao cobria e a auditoria de governanca achou:
--   - codigo_di_catalogado_na_anac
--   - codigo_tipo_linha_catalogado_na_anac
--   - linha_nao_duplicada
-- ---------------------------------------------------------------------------
CREATE LIVE VIEW vra_auditado (
  -- === completude ===
  CONSTRAINT horarios_previstos_presentes
    EXPECT (partida_prevista IS NOT NULL AND chegada_prevista IS NOT NULL),

  CONSTRAINT situacao_voo_conhecida
    EXPECT (situacao_voo IN ('REALIZADO', 'CANCELADO')),

  -- === coerencia temporal (NULL aprovado explicitamente) ===
  CONSTRAINT chegada_prevista_depois_da_partida_prevista
    EXPECT (partida_prevista IS NULL OR chegada_prevista IS NULL
            OR chegada_prevista > partida_prevista),

  CONSTRAINT chegada_real_depois_da_partida_real
    EXPECT (partida_real IS NULL OR chegada_real IS NULL
            OR chegada_real > partida_real),

  -- === faixa plausivel: -2h de antecipacao a 24h de atraso ===
  CONSTRAINT atraso_partida_plausivel
    EXPECT (atraso_partida_min IS NULL
            OR atraso_partida_min BETWEEN -120 AND 1440),

  CONSTRAINT atraso_chegada_plausivel
    EXPECT (atraso_chegada_min IS NULL
            OR atraso_chegada_min BETWEEN -120 AND 1440),

  -- === integridade referencial (as flags vem do passo 1) ===
  CONSTRAINT empresa_no_cadastro_anac
    EXPECT (empresa_no_cadastro),

  CONSTRAINT aeroporto_origem_no_cadastro_anac
    EXPECT (origem_no_cadastro),

  CONSTRAINT aeroporto_destino_no_cadastro_anac
    EXPECT (destino_no_cadastro),

  -- === dominio de codigos (seed table) ===
  CONSTRAINT codigo_di_catalogado_na_anac
    EXPECT (codigo_di_catalogado),

  CONSTRAINT codigo_tipo_linha_catalogado_na_anac
    EXPECT (codigo_tipo_linha_catalogado),

  -- === unicidade (diagnostico; decisao de remover e da gold) ===
  CONSTRAINT linha_nao_duplicada
    EXPECT (NOT linha_duplicada)
)
COMMENT 'Contrato de dados de silver.vra. Doze expectations, todas em modo warn:
 medem qualidade sem descartar linha. A silver segue com a contagem original.'
AS SELECT * FROM vra_marcado;
