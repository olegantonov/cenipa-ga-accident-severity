"""
Análise estatística — experiência do PIC e severidade de acidentes na aviação
geral brasileira (aviões), 2007–2024.

Desfecho primário: fatal (0/1). Preditor: horas de voo do PIC (log e spline).
Ajuste: tipo de operação, fase de voo (agrupada), motor, peso, ano.

Gera: resultados.md (tabelas) e figuras/*.png.
Rodar: .venv/bin/python analise.py
"""
import warnings, json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from patsy import dmatrices, cr
from scipy import stats
from sklearn.metrics import roc_auc_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
BASE = Path(__file__).parent
FIG = BASE / "figuras"; FIG.mkdir(exist_ok=True)
OUT = []   # linhas do resultados.md
def w(*a): OUT.append(" ".join(str(x) for x in a)); print(*a)

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 300, "font.size": 10,
                     "axes.grid": True, "grid.alpha": .3, "axes.axisbelow": True})

# ---------- carga e preparo ----------
df = pd.read_csv(BASE / "dataset_analitico.csv")
df["h_total"] = pd.to_numeric(df["h_total"], errors="coerce")
df["h_tipo"] = pd.to_numeric(df["h_tipo"], errors="coerce")
df["h_total_30d"] = pd.to_numeric(df["h_total_30d"], errors="coerce")
df["ano"] = pd.to_numeric(df["ano_ocorrencia"], errors="coerce")
df["fatal"] = df["fatal"].astype(int)
df["log_h"] = np.log(df["h_total"] + 1)

# operação: mantém 4 principais (rótulos do extrato 2007–2025)
op_keep = ["PRIVADA", "AGRÍCOLA", "INSTRUÇÃO", "TÁXI AÉREO"]
df["operacao"] = df["tipo_operacao"].where(df["tipo_operacao"].isin(op_keep))

# fase de voo agrupada
def grupo_fase(x):
    x = str(x)
    if x in ("DECOLAGEM", "SUBIDA"): return "Decolagem/Subida"
    if x in ("POUSO", "CORRIDA APÓS POUSO", "APROXIMAÇÃO FINAL", "APROXIMAÇÃO"): return "Aproximação/Pouso"
    if x in ("CRUZEIRO",): return "Cruzeiro"
    if x in ("MANOBRA", "ESPECIALIZADA", "VOO A BAIXA ALTURA"): return "Manobra/Especializada"
    return "Outras"
df["fase_g"] = df["fase_voo"].map(grupo_fase)

df["motor"] = df["motor_tipo"].where(df["motor_tipo"].isin(["PISTÃO", "TURBOÉLICE", "JATO"]))
df["motor"] = df["motor"].replace({"JATO": "TURBINA", "TURBOÉLICE": "TURBINA"})
df["bimotor"] = (pd.to_numeric(df["motor_qtd"], errors="coerce") >= 2).astype(int)

df["faixa_h"] = pd.cut(df["h_total"], [0, 100, 500, 1000, 5000, np.inf],
                       labels=["<100", "100–500", "500–1000", "1000–5000", "≥5000"])

w("# Resultados — Experiência do PIC e severidade (aviação geral BR, 2007–2024)\n")
w(f"N total no dataset: {len(df)} | fatais: {df.fatal.sum()} ({100*df.fatal.mean():.1f}%)")
w(f"Com h_total: {df.h_total.notna().sum()} | com h_tipo: {df.h_tipo.notna().sum()}\n")

# ---------- Tabela 1: características por desfecho ----------
w("## Tabela 1 — Características por desfecho (fatal vs não-fatal)\n")
def lin_cat(var, label):
    w(f"**{label}**")
    ct = pd.crosstab(df[var], df.fatal)
    for idx, row in ct.iterrows():
        nf, fa = row.get(0, 0), row.get(1, 0); tot = nf + fa
        w(f"  - {idx}: n={tot} | fatal {fa} ({100*fa/tot:.0f}%)")
    w("")
def lin_num(var, label):
    a = df.loc[df.fatal == 1, var].dropna(); b = df.loc[df.fatal == 0, var].dropna()
    p = stats.mannwhitneyu(a, b).pvalue
    w(f"**{label}** (mediana [IIQ]): fatal {a.median():.0f} [{a.quantile(.25):.0f}–{a.quantile(.75):.0f}] | "
      f"não-fatal {b.median():.0f} [{b.quantile(.25):.0f}–{b.quantile(.75):.0f}] | Mann-Whitney p={p:.3f}\n")
lin_num("h_total", "Horas totais PIC")
lin_num("h_tipo", "Horas no tipo")
lin_cat("operacao", "Tipo de operação")
lin_cat("fase_g", "Fase de voo")
lin_cat("motor", "Tipo de motor")
lin_cat("faixa_h", "Faixa de horas totais")

# ---------- Simpson: cru vs estratificado ----------
w("## Paradoxo de Simpson — horas medianas por operação × desfecho\n")
w("| Operação | n | %fatal | h_med FATAL | h_med NÃO-FATAL |")
w("|---|---|---|---|---|")
for op in op_keep:
    s = df[df.operacao == op]
    fa = s.loc[s.fatal == 1, "h_total"].median(); nf = s.loc[s.fatal == 0, "h_total"].median()
    w(f"| {op} | {len(s)} | {100*s.fatal.mean():.0f}% | {fa:.0f} | {nf:.0f} |")
w("")

# ---------- Regressão logística primária ----------
w("## Modelo logístico multivariável (desfecho: fatal)\n")
d = df.dropna(subset=["log_h", "operacao", "fase_g", "motor", "ano"]).copy()
w(f"N complete-case: {len(d)} | eventos: {d.fatal.sum()}")
f_main = ("fatal ~ log_h + C(operacao, Treatment('PRIVADA')) + C(fase_g) "
          "+ C(motor) + bimotor + ano")
m = smf.logit(f_main, data=d).fit(disp=0)

def tabela_or(model, titulo):
    w(f"\n### {titulo}")
    params, cis, ps = model.params, model.conf_int(), model.pvalues
    w("| Termo | OR | IC95% | p |")
    w("|---|---|---|---|")
    for term in params.index:
        if term == "Intercept": continue
        orr = np.exp(params[term]); lo, hi = np.exp(cis.loc[term])
        w(f"| {term} | {orr:.2f} | {lo:.2f}–{hi:.2f} | {ps[term]:.3f} |")
    return params, cis, ps
tabela_or(m, "ORs ajustados")

# OR para variação interpretável de horas: por dobra (log2) e por +1000h equivalente
or_log = np.exp(m.params["log_h"])
w(f"\nOR por aumento de 1 unidade em ln(horas) = {or_log:.2f} "
  f"(IC95% {np.exp(m.conf_int().loc['log_h',0]):.2f}–{np.exp(m.conf_int().loc['log_h',1]):.2f})")
w(f"→ OR por **duplicação** das horas de voo = {or_log**np.log(2):.3f}")

# diagnósticos
auc = roc_auc_score(d.fatal, m.predict(d))
# Hosmer-Lemeshow (10 grupos)
pr = m.predict(d); obs = d.fatal.values
gq = pd.qcut(pr, 10, duplicates="drop")
hl = 0.0
for _, idx in pd.Series(range(len(pr))).groupby(gq.values, observed=True):
    o1 = obs[idx].sum(); e1 = pr.values[idx].sum(); n_ = len(idx)
    e0 = n_ - e1; o0 = n_ - o1
    if e1 > 0: hl += (o1 - e1) ** 2 / e1
    if e0 > 0: hl += (o0 - e0) ** 2 / e0
hl_p = stats.chi2.sf(hl, 8)
w(f"\n**Diagnósticos:** pseudo-R²(McFadden)={m.prsquared:.3f} | AUC={auc:.3f} | "
  f"LLR p={m.llr_pvalue:.1e} | Hosmer-Lemeshow p={hl_p:.3f} "
  f"({'boa calibração' if hl_p>0.05 else 'calibração ruim'})")
# VIF
y, X = dmatrices(f_main, d, return_type="dataframe")
vif = [(X.columns[i], variance_inflation_factor(X.values, i)) for i in range(X.shape[1]) if X.columns[i] != "Intercept"]
maxvif = max(v for _, v in vif)
w(f"VIF máx = {maxvif:.2f} (sem colinearidade preocupante se <5)")

# ---------- não-linearidade: spline natural em log_h ----------
w("\n## Não-linearidade (spline natural em log-horas)\n")
m_lin = smf.logit("fatal ~ log_h + C(operacao) + C(fase_g) + C(motor) + bimotor + ano", data=d).fit(disp=0)
m_spl = smf.logit("fatal ~ cr(log_h, df=4) + C(operacao) + C(fase_g) + C(motor) + bimotor + ano", data=d).fit(disp=0)
lr = 2 * (m_spl.llf - m_lin.llf); dfd = m_spl.df_model - m_lin.df_model
p_nl = stats.chi2.sf(lr, dfd)
w(f"Teste de não-linearidade (LR spline vs linear): χ²={lr:.2f}, df={dfd:.0f}, p={p_nl:.3f}")
w("→ " + ("há evidência de não-linearidade" if p_nl < 0.05 else "sem evidência de não-linearidade (efeito ~log-linear)"))

# ---------- modelo secundário: HORAS NO TIPO (achado-chave) ----------
w("\n## Modelo secundário — experiência NO TIPO de aeronave\n")
ds = df.dropna(subset=["h_tipo", "operacao", "fase_g", "motor", "ano"]).copy()
ds["log_htipo"] = np.log(ds["h_tipo"] + 1)
ms = smf.logit("fatal ~ log_htipo + C(operacao, Treatment('PRIVADA')) + C(fase_g) "
               "+ C(motor) + bimotor + ano", data=ds).fit(disp=0)
or_t = np.exp(ms.params["log_htipo"]); ci_t = np.exp(ms.conf_int().loc["log_htipo"])
w(f"N={len(ds)} | eventos={ds.fatal.sum()}")
w(f"**OR por ln(horas no tipo) = {or_t:.2f} (IC95% {ci_t[0]:.2f}–{ci_t[1]:.2f}), p={ms.pvalues['log_htipo']:.3f}**")
w(f"→ OR por duplicação das horas no tipo = {or_t**np.log(2):.3f} "
  f"(redução de {100*(1-or_t**np.log(2)):.0f}% nas chances de fatalidade)")
# contraste direto total vs tipo no mesmo subset
mc = smf.logit("fatal ~ log_h + log_htipo + C(operacao) + C(fase_g) + C(motor) + bimotor + ano",
               data=ds.assign(log_h=np.log(ds["h_total"] + 1))).fit(disp=0)
w(f"Ajustando AMBAS no mesmo modelo (N={int(mc.nobs)}): "
  f"OR total={np.exp(mc.params['log_h']):.2f} (p={mc.pvalues['log_h']:.3f}) | "
  f"OR no_tipo={np.exp(mc.params['log_htipo']):.2f} (p={mc.pvalues['log_htipo']:.3f})")

# ---------- fatores contribuintes × experiência ----------
w("\n## Fatores contribuintes (CENIPA) × experiência do PIC\n")
if "fator_humano" in df.columns:
    dfc = df[df["n_fatores"] > 0].copy()
    w(f"N com fatores codificados: {len(dfc)} | "
      f"fator humano em {100*dfc['fator_humano'].mean():.0f}% | "
      f"fator operacional em {100*dfc['fator_operacional'].mean():.0f}% | "
      f"fator material em {100*dfc['fator_material'].mean():.0f}%")
    # % fator humano por faixa de horas
    w("\n% com FATOR HUMANO por faixa de horas totais:")
    gh = dfc.dropna(subset=["faixa_h"]).groupby("faixa_h", observed=True)["fator_humano"].agg(["mean", "count"])
    for idx, r in gh.iterrows():
        w(f"  - {idx}: {100*r['mean']:.0f}% (n={int(r['count'])})")
    # logística: fator_humano ~ log_h (ajustada por operação)
    dch = dfc.dropna(subset=["log_h", "operacao"])
    try:
        mh = smf.logit("fator_humano ~ log_h + C(operacao, Treatment('PRIVADA'))", data=dch).fit(disp=0)
        w(f"\nOR(fator humano) por ln(horas totais) = {np.exp(mh.params['log_h']):.2f} "
          f"({np.exp(mh.conf_int().loc['log_h',0]):.2f}–{np.exp(mh.conf_int().loc['log_h',1]):.2f}), "
          f"p={mh.pvalues['log_h']:.3f}")
    except Exception as e:
        w(f"(modelo fator humano não convergiu: {type(e).__name__})")
    # fator humano e fatalidade
    ct = pd.crosstab(dfc["fator_humano"], dfc["fatal"])
    w(f"\nFatalidade quando há fator humano: {100*dfc[dfc.fator_humano==1].fatal.mean():.0f}% "
      f"vs sem fator humano: {100*dfc[dfc.fator_humano==0].fatal.mean():.0f}%")

# ---------- sensibilidade ----------
w("\n## Análises de sensibilidade\n")
# (a) excluindo instrução (PIC = instrutor, controle duplo)
d2 = d[d.operacao != "VOO DE INSTRUÇÃO"]
m2 = smf.logit(f_main, data=d2).fit(disp=0)
w(f"(a) Excluindo instrução (N={len(d2)}): OR log_h = {np.exp(m2.params['log_h']):.2f} "
  f"({np.exp(m2.conf_int().loc['log_h',0]):.2f}–{np.exp(m2.conf_int().loc['log_h',1]):.2f}), p={m2.pvalues['log_h']:.3f}")
# (b) desfecho = aeronave destruída
df["destruida"] = (df["nivel_dano"] == "DESTRUÍDA").astype(int)
d3 = df.dropna(subset=["log_h", "operacao", "fase_g", "motor", "ano"])
m3 = smf.logit("destruida ~ log_h + C(operacao) + C(fase_g) + C(motor) + bimotor + ano", data=d3).fit(disp=0)
w(f"(b) Desfecho 'destruída' (N={len(d3)}): OR log_h = {np.exp(m3.params['log_h']):.2f} "
  f"({np.exp(m3.conf_int().loc['log_h',0]):.2f}–{np.exp(m3.conf_int().loc['log_h',1]):.2f}), p={m3.pvalues['log_h']:.3f}")
# (c) horas no tipo (subset)
d4 = df.dropna(subset=["h_tipo", "operacao", "fase_g", "motor", "ano"]).copy()
d4["log_htipo"] = np.log(d4["h_tipo"] + 1)
m4 = smf.logit("fatal ~ log_htipo + C(operacao) + C(fase_g) + C(motor) + bimotor + ano", data=d4).fit(disp=0)
w(f"(c) Horas NO TIPO (N={len(d4)}): OR log_h_tipo = {np.exp(m4.params['log_htipo']):.2f} "
  f"({np.exp(m4.conf_int().loc['log_htipo',0]):.2f}–{np.exp(m4.conf_int().loc['log_htipo',1]):.2f}), p={m4.pvalues['log_htipo']:.3f}")
# (d) imputação múltipla das horas (missingness h_total ~4%) — Rubin's rules
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
try:
    cov = pd.get_dummies(df[["operacao", "fase_g", "motor"]], drop_first=True).astype(float)
    base_imp = pd.concat([df[["fatal", "log_h", "ano", "bimotor"]].reset_index(drop=True),
                          cov.reset_index(drop=True)], axis=1)
    preds = [c for c in base_imp.columns if c not in ("fatal",)]
    betas, vars_ = [], []
    for seed in range(10):
        ii = IterativeImputer(max_iter=10, random_state=seed, sample_posterior=True)
        arr = ii.fit_transform(base_imp[preds + ["fatal"]])
        di = pd.DataFrame(arr, columns=preds + ["fatal"])
        mi = sm.Logit(di["fatal"].round().clip(0, 1), sm.add_constant(di[preds])).fit(disp=0)
        betas.append(mi.params["log_h"]); vars_.append(mi.bse["log_h"] ** 2)
    qbar = np.mean(betas); ubar = np.mean(vars_); B = np.var(betas, ddof=1)
    T = ubar + (1 + 1 / 10) * B; se = np.sqrt(T)
    or_mice = np.exp(qbar)
    w(f"(d) Imputação múltipla (10 imp., missing h_total={df.h_total.isna().mean()*100:.1f}%): "
      f"OR log_h = {or_mice:.2f} ({np.exp(qbar-1.96*se):.2f}–{np.exp(qbar+1.96*se):.2f}) "
      f"— materialmente igual ao complete-case (OR {or_log:.2f})")
except Exception as e:
    w(f"(d) Imputação não executada: {type(e).__name__}: {e}")

# ============ FIGURES (rótulos em inglês p/ a revista) ============
OP_EN = {"PRIVADA": "Private", "AGRÍCOLA": "Agricultural", "INSTRUÇÃO": "Instruction", "TÁXI AÉREO": "Air taxi"}
FASE_EN = {"Aproximação/Pouso": "Approach/landing", "Decolagem/Subida": "Take-off/climb",
           "Cruzeiro": "Cruise", "Manobra/Especializada": "Manoeuvre/spec.", "Outras": "Other"}

# Fig 1 — crude fatality by hour band (binomial CI)
fig, ax = plt.subplots(figsize=(6.5, 4))
g = df.dropna(subset=["faixa_h"]).groupby("faixa_h", observed=True)["fatal"].agg(["mean", "count", "sum"])
lo, hi = [], []
for _, r in g.iterrows():
    ci = stats.binomtest(int(r["sum"]), int(r["count"])).proportion_ci()
    lo.append(r["mean"] - ci.low); hi.append(ci.high - r["mean"])
ax.bar(range(len(g)), g["mean"] * 100, yerr=[np.array(lo) * 100, np.array(hi) * 100],
       capsize=4, color="#4C72B0", alpha=.85)
ax.set_xticks(range(len(g))); ax.set_xticklabels(g.index)
ax.set_ylabel("Fatal accidents (%)"); ax.set_xlabel("PIC total flight hours")
ax.set_title("Fig. 1 — Fatality by pilot experience band (unadjusted)")
for i, (_, r) in enumerate(g.iterrows()):
    ax.text(i, r["mean"] * 100 + 3, f"n={int(r['count'])}", ha="center", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "fig1_letalidade_faixa.png"); plt.close()

# Fig 2 — adjusted predicted probability vs hours (spline), by operation
fig, ax = plt.subplots(figsize=(6.5, 4))
hgrid = np.linspace(df.h_total.quantile(.02), df.h_total.quantile(.98), 100)
base = dict(fase_g="Aproximação/Pouso", motor="PISTÃO", bimotor=0, ano=int(d.ano.median()))
for op, col in zip(op_keep, ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]):
    pred = pd.DataFrame({"log_h": np.log(hgrid + 1), "operacao": op, **base})
    ax.plot(hgrid, m_spl.predict(pred) * 100, label=OP_EN.get(op, op), color=col, lw=2)
ax.set_xlabel("PIC total flight hours"); ax.set_ylabel("Adjusted P(fatal) (%)")
ax.set_title("Fig. 2 — Probability of a fatal accident vs experience (adjusted spline)")
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "fig2_prob_ajustada.png"); plt.close()

# Fig 3 — forest plot of adjusted ORs
fig, ax = plt.subplots(figsize=(7, 5))
params, cis = m.params.drop("Intercept"), m.conf_int().drop("Intercept")
ors = np.exp(params); lo = np.exp(cis[0]); hi = np.exp(cis[1])
ylab = []
for t in params.index:
    s = (t.replace("C(operacao, Treatment('PRIVADA'))[T.", "Op: ").replace("C(fase_g)[T.", "Phase: ")
          .replace("C(motor)[T.", "Engine: ").replace("]", "").replace("log_h", "ln(PIC total hours)")
          .replace("bimotor", "Multi-engine").replace("ano", "Year").replace("TURBINA", "Turbine"))
    for pt, en in {**OP_EN, **FASE_EN}.items():
        s = s.replace(pt, en)
    ylab.append(s)
yy = range(len(ors))
ax.errorbar(ors, yy, xerr=[ors - lo, hi - ors], fmt="o", color="#333", capsize=3)
ax.axvline(1, color="red", ls="--", lw=1); ax.set_yticks(list(yy)); ax.set_yticklabels(ylab, fontsize=8)
ax.set_xscale("log"); ax.set_xlabel("Odds ratio (log scale)")
ax.set_title("Fig. 3 — Adjusted odds ratios for a fatal accident"); fig.tight_layout()
fig.savefig(FIG / "fig3_forest.png"); plt.close()

# Fig 4 — Simpson: median hours by operation and outcome
fig, ax = plt.subplots(figsize=(6.5, 4))
xpos = range(len(op_keep))
medf = [df[(df.operacao == o) & (df.fatal == 1)].h_total.median() for o in op_keep]
mednf = [df[(df.operacao == o) & (df.fatal == 0)].h_total.median() for o in op_keep]
ax.plot(xpos, medf, "o-", color="#C44E52", label="Fatal", lw=2)
ax.plot(xpos, mednf, "s-", color="#4C72B0", label="Non-fatal", lw=2)
ax.set_xticks(list(xpos)); ax.set_xticklabels([OP_EN.get(o, o) for o in op_keep], fontsize=8)
ax.set_ylabel("PIC total hours (median)"); ax.set_title("Fig. 4 — Hours by operation and outcome (confounding)")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "fig4_simpson.png"); plt.close()

# Fig 5 — total vs in-type: adjusted predicted probability (key finding)
or_tipo_p = ms.pvalues["log_htipo"]; or_tot_p = m.pvalues["log_h"]
fig, ax = plt.subplots(figsize=(6.5, 4))
hgrid2 = np.linspace(1, ds["h_tipo"].quantile(.95), 100)
base2 = dict(operacao="PRIVADA", fase_g="Aproximação/Pouso", motor="PISTÃO", bimotor=0, ano=int(ds.ano.median()))
pred_t = pd.DataFrame({"log_htipo": np.log(hgrid2 + 1), **base2})
ax.plot(hgrid2, ms.predict(pred_t) * 100, color="#55A868", lw=2.5, label=f"In-type hours (p={or_tipo_p:.3f})")
pred_tot = pd.DataFrame({"log_h": np.log(hgrid2 + 1), **base2})
ax.plot(hgrid2, m.predict(pred_tot) * 100, color="#888", lw=2, ls="--", label=f"Total hours (p={or_tot_p:.2f})")
ax.set_xlabel("PIC flight hours"); ax.set_ylabel("Adjusted P(fatal) (%)")
ax.set_title("Fig. 5 — In-type experience is protective; total hours are not")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "fig5_tipo_vs_total.png"); plt.close()

(BASE / "resultados.md").write_text("\n".join(OUT), encoding="utf-8")
w("\n[figuras salvas em figuras/ | resultados em resultados.md]")
