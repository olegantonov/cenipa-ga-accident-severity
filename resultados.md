# Resultados — Experiência do PIC e severidade (aviação geral BR, 2007–2024)

N total no dataset: 824 | fatais: 197 (23.9%)
Com h_total: 805 | com h_tipo: 553

## Tabela 1 — Características por desfecho (fatal vs não-fatal)

**Horas totais PIC** (mediana [IIQ]): fatal 1300 [445–3612] | não-fatal 1300 [343–4455] | Mann-Whitney p=0.987

**Horas no tipo** (mediana [IIQ]): fatal 210 [47–881] | não-fatal 400 [104–1275] | Mann-Whitney p=0.004

**Tipo de operação**
  - AGRÍCOLA: n=238 | fatal 54 (23%)
  - INSTRUÇÃO: n=145 | fatal 15 (10%)
  - PRIVADA: n=347 | fatal 101 (29%)
  - TÁXI AÉREO: n=91 | fatal 27 (30%)

**Fase de voo**
  - Aproximação/Pouso: n=263 | fatal 25 (10%)
  - Cruzeiro: n=92 | fatal 32 (35%)
  - Decolagem/Subida: n=203 | fatal 51 (25%)
  - Manobra/Especializada: n=165 | fatal 45 (27%)
  - Outras: n=101 | fatal 44 (44%)

**Tipo de motor**
  - PISTÃO: n=693 | fatal 159 (23%)
  - TURBINA: n=130 | fatal 38 (29%)

**Faixa de horas totais**
  - <100: n=87 | fatal 21 (24%)
  - 100–500: n=165 | fatal 35 (21%)
  - 500–1000: n=108 | fatal 31 (29%)
  - 1000–5000: n=276 | fatal 70 (25%)
  - ≥5000: n=169 | fatal 39 (23%)

## Paradoxo de Simpson — horas medianas por operação × desfecho

| Operação | n | %fatal | h_med FATAL | h_med NÃO-FATAL |
|---|---|---|---|---|
| PRIVADA | 347 | 29% | 1000 | 1200 |
| AGRÍCOLA | 238 | 23% | 1300 | 1700 |
| INSTRUÇÃO | 145 | 10% | 482 | 300 |
| TÁXI AÉREO | 91 | 30% | 5000 | 6706 |

## Modelo logístico multivariável (desfecho: fatal)

N complete-case: 801 | eventos: 196

### ORs ajustados
| Termo | OR | IC95% | p |
|---|---|---|---|
| C(operacao, Treatment('PRIVADA'))[T.AGRÍCOLA] | 0.49 | 0.29–0.83 | 0.008 |
| C(operacao, Treatment('PRIVADA'))[T.INSTRUÇÃO] | 0.32 | 0.17–0.61 | 0.001 |
| C(operacao, Treatment('PRIVADA'))[T.TÁXI AÉREO] | 0.92 | 0.51–1.66 | 0.782 |
| C(fase_g)[T.Cruzeiro] | 4.73 | 2.53–8.86 | 0.000 |
| C(fase_g)[T.Decolagem/Subida] | 3.73 | 2.15–6.46 | 0.000 |
| C(fase_g)[T.Manobra/Especializada] | 6.45 | 3.28–12.67 | 0.000 |
| C(fase_g)[T.Outras] | 8.54 | 4.66–15.65 | 0.000 |
| C(motor)[T.TURBINA] | 1.55 | 0.94–2.56 | 0.088 |
| log_h | 0.91 | 0.82–1.02 | 0.100 |
| bimotor | 1.51 | 0.92–2.49 | 0.103 |
| ano | 0.98 | 0.94–1.02 | 0.301 |

OR por aumento de 1 unidade em ln(horas) = 0.91 (IC95% 0.82–1.02)
→ OR por **duplicação** das horas de voo = 0.939

**Diagnósticos:** pseudo-R²(McFadden)=0.105 | AUC=0.722 | LLR p=3.2e-15 | Hosmer-Lemeshow p=0.411 (boa calibração)
VIF máx = 2.05 (sem colinearidade preocupante se <5)

## Não-linearidade (spline natural em log-horas)

Teste de não-linearidade (LR spline vs linear): χ²=4.73, df=2, p=0.094
→ sem evidência de não-linearidade (efeito ~log-linear)

## Modelo secundário — experiência NO TIPO de aeronave

N=552 | eventos=139
**OR por ln(horas no tipo) = 0.81 (IC95% 0.72–0.92), p=0.001**
→ OR por duplicação das horas no tipo = 0.866 (redução de 13% nas chances de fatalidade)
Ajustando AMBAS no mesmo modelo (N=552): OR total=0.84 (p=0.071) | OR no_tipo=0.87 (p=0.054)

## Fatores contribuintes (CENIPA) × experiência do PIC

N com fatores codificados: 750 | fator humano em 50% | fator operacional em 96% | fator material em 3%

% com FATOR HUMANO por faixa de horas totais:
  - <100: 54% (n=80)
  - 100–500: 51% (n=154)
  - 500–1000: 47% (n=99)
  - 1000–5000: 50% (n=255)
  - ≥5000: 51% (n=152)

OR(fator humano) por ln(horas totais) = 0.97 (0.88–1.06), p=0.499

Fatalidade quando há fator humano: 40% vs sem fator humano: 10%

## Análises de sensibilidade

(a) Excluindo instrução (N=801): OR log_h = 0.91 (0.82–1.02), p=0.100
(b) Desfecho 'destruída' (N=801): OR log_h = 0.93 (0.82–1.04), p=0.190
(c) Horas NO TIPO (N=552): OR log_h_tipo = 0.81 (0.72–0.92), p=0.001
(d) Imputação múltipla (10 imp., missing h_total=2.3%): OR log_h = 0.99 (0.93–1.05) — materialmente igual ao complete-case (OR 0.91)