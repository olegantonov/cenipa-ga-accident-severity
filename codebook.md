# Codebook — `dataset_analitico.csv`

Uma linha por **aeronave-acidente** da **aviação geral brasileira (aviões)**, período
**2007–2024** (dados abertos atualizados do CENIPA, 2007–2025).
N = 824 acidentes (197 fatais / 627 não-fatais).

Construído por `montar_dataset_v2.py` unindo `horas_voo.json` (experiência do PIC extraída
dos PDFs) às covariáveis estruturadas dos dados abertos atualizados:
`dataset/{ocorrencia,aeronave,ocorrencia_tipo,fator_contribuinte}.csv` (delimitador `;`,
encoding latin-1). Os arquivos antigos `oco.csv`/`anv.csv` (2009–2019) ficam preservados.

**Colunas adicionais (fatores contribuintes do CENIPA):** `fator_humano`, `fator_operacional`,
`fator_material` (0/1) e `n_fatores`. `motor_qtd` agora é numérico; `pmd` é numérico (kg).

## Identificação
| Campo | Descrição |
|---|---|
| `arquivo` | nome do PDF de origem |
| `numero` | número do Relatório Final (ex. A-105/CENIPA/2012) |
| `codigo_ocorrencia` | chave da ocorrência no CENIPA |
| `join` | método de pareamento PDF↔CSV (`numero`, `mat+data`, `mat+ano`) |

## Desfechos
| Campo | Tipo | Descrição |
|---|---|---|
| `fatal` | 0/1 | **desfecho primário**: 1 se houve ≥1 fatalidade a bordo |
| `n_fatalidades` | int | nº de fatalidades |
| `nivel_dano` | categórico | LEVE < SUBSTANCIAL < DESTRUÍDA (desfecho ordinal secundário) |

## Preditores — experiência do piloto em comando (PIC)
| Campo | Tipo | Preench. | Descrição |
|---|---|---|---|
| `h_total` | horas | 95% | **preditor principal**: horas totais de voo do PIC |
| `h_tipo` | horas | 66% | horas no tipo de aeronave acidentado |
| `h_total_30d` | horas | 52% | recência: horas nos últimos 30 dias |
| `h_total_24h` | horas | — | horas nas últimas 24 h |
| `idade_pic` | anos | <2% | idade do PIC (esparso → não usar) |
| `fonte_horas` | tabela/narrativa | 100% | origem da extração das horas |

Transformações para a análise: `log_h_total = ln(h_total+1)`; faixas categóricas
(<100, 100–500, 500–1000, 1000–5000, ≥5000 h) para a leitura tipo "killing zone".

## Covariáveis (ajuste)
| Campo | Preench. | Observação |
|---|---|---|
| `tipo_operacao` | 100% | VOO PRIVADO, OPERAÇÃO AGRÍCOLA, VOO DE INSTRUÇÃO, TÁXI AÉREO, VOO EXPERIMENTAL — **confundidor-chave** |
| `fase_voo` | 98% | fase da operação (decolagem, cruzeiro, pouso…) |
| `motor_tipo` | 99% | PISTÃO / TURBOÉLICE / JATO |
| `motor_qtd` | 99% | MONOMOTOR / BIMOTOR |
| `pmd_categoria` | 100% | faixa de peso máximo de decolagem |
| `ano_fabricacao` | 99% | ano de fabricação da aeronave |
| `fabricante`,`modelo` | 99% | — |
| `tipo_ocorrencia`,`tipo_icao` | 100% | tipo da ocorrência (taxonomia CENIPA/ICAO) |
| `uf`,`ano_ocorrencia` | 100% | localização e ano (ajuste temporal) |
| `meteo` | 11% | VMC/IMC — **esparso, não usar como covariável** |
| `total_recomendacoes` | 100% | nº de recomendações de segurança emitidas |

## Notas
- Horas iguais a 0 foram tratadas como ausentes (implausível para PIC).
- Janela 2009–2019: o CSV de dados abertos é a extração de 2019; PDFs de 2020–2024
  existem mas não têm covariáveis estruturadas equivalentes (extensão = trabalho futuro).
- Análise primária *complete-case* em `h_total`; imputação múltipla como sensibilidade.
