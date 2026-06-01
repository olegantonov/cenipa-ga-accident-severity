"""
Monta o dataset analítico do estudo (uma linha por aeronave-acidente da aviação
geral / aviões), unindo:
  - horas_voo.json        (experiência do PIC, extraída dos PDFs)
  - extraidos/*.json       (metadados de capa: matrícula, número, data)
  - links_reais.json       (arquivo -> matrícula limpa)
  - dataset/oco.csv, anv.csv (covariáveis e desfechos estruturados)

Join em cascata por aeronave-ocorrência:
  1. número do relatório  (cover numero  <->  oco.divulgacao_relatorio_numero)
  2. matrícula + data     (data do nome do arquivo  <->  anv.matricula + oco.ocorrencia_dia)
  3. matrícula + ano       (quando único)

Escopo: aeronave_tipo_veiculo=AVIÃO ∧ tipo_operacao∈GA ∧ classificacao=ACIDENTE.

Saídas: dataset_analitico.csv  e  codebook.md
"""
import json, glob, csv, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
GA_OPS = {"VOO PRIVADO", "VOO DE INSTRUÇÃO", "OPERAÇÃO AGRÍCOLA", "VOO EXPERIMENTAL", "TÁXI AÉREO"}
MES = {'JAN':1,'FEV':2,'MAR':3,'ABR':4,'MAI':5,'MAIO':5,'JUN':6,'JUL':7,'AGO':8,'SET':9,'OUT':10,'NOV':11,'DEZ':12}


def norm_num(n):
    n = (n or "").upper().replace(" ", "")
    m = re.search(r"([AI]G?)-?(\d{1,4})/CENIPA/(\d{4})", n)
    return f"{m.group(1)}-{int(m.group(2)):03d}/CENIPA/{m.group(3)}" if m else ""


def norm_mat(m):
    return re.sub(r"[^A-Z0-9]", "", (m or "").upper())


def data_do_arquivo(nome):
    """Extrai (iso, ano) da data embutida no nome do PDF."""
    s = nome.upper()
    m = re.search(r"(\d{1,2})[_\-](\d{1,2})[_\-](\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y}-{mo:02d}-{d:02d}", y
    m = re.search(r"(\d{1,2})[_\-](\d{1,2})[_\-](\d{2})\b", s)
    if m:
        d, mo, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            y = 2000 + yy if yy < 50 else 1900 + yy
            return f"{y}-{mo:02d}-{d:02d}", y
    m = re.search(r"(\d{1,2})([A-Z]{3,4})(\d{4})", s)
    if m and m.group(2) in MES:
        return f"{int(m.group(3))}-{MES[m.group(2)]:02d}-{int(m.group(1)):02d}", int(m.group(3))
    m = re.search(r"\b(19|20)(\d{2})\b", s)  # só ano
    if m:
        return None, int(m.group(0))
    return None, None


def main():
    # 1) horas por arquivo
    horas = {h["arquivo"]: h for h in json.load(open(BASE / "horas_voo.json", encoding="utf-8"))}
    # 2) metadados de capa por arquivo
    meta = {}
    for f in glob.glob(str(BASE / "extraidos" / "*.json")):
        if f.endswith("_indice.csv"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        meta[d["arquivo"]] = d
    # 3) matrícula limpa por arquivo (links_reais)
    mat_links = {}
    for r in json.load(open(BASE / "links_reais.json", encoding="utf-8")):
        for url in (r.get("pdf_pt"), r.get("pdf_en")):
            if url:
                mat_links[url.rsplit("/", 1)[-1]] = norm_mat(r.get("matricula"))

    # 4) CSVs
    oco = {}
    with open(BASE / "dataset/oco.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="~", quotechar='"'):
            oco[r["codigo_ocorrencia"]] = r
    anv = defaultdict(list)
    with open(BASE / "dataset/anv.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="~", quotechar='"'):
            anv[r["codigo_ocorrencia"]].append(r)

    # índices para o join
    by_num = {}
    by_mat_date = {}
    by_mat_year = defaultdict(list)
    for cod, o in oco.items():
        num = norm_num(o["divulgacao_relatorio_numero"])
        if num:
            by_num.setdefault(num, cod)
        dia = o["ocorrencia_dia"]
        ano = dia[:4] if dia and dia[0:2] in ("19", "20") else None
        for a in anv[cod]:
            mt = norm_mat(a["aeronave_matricula"])
            if mt:
                if dia and dia != "NULL":
                    by_mat_date[(mt, dia)] = (cod, a)
                if ano:
                    by_mat_year[(mt, ano)].append((cod, a))

    def achar(arq, rec_meta):
        # 1) número
        num = norm_num(rec_meta.get("numero"))
        if num in by_num:
            cod = by_num[num]
            a = next((x for x in anv[cod]
                      if norm_mat(x["aeronave_matricula"]) == norm_mat(rec_meta["metadados"].get("aeronave"))),
                     anv[cod][0])
            return cod, a, "numero"
        # 2/3) matrícula + data / ano
        mat = mat_links.get(arq) or norm_mat(rec_meta["metadados"].get("aeronave"))
        iso, ano = data_do_arquivo(arq)
        if mat and iso and (mat, iso) in by_mat_date:
            cod, a = by_mat_date[(mat, iso)]
            return cod, a, "mat+data"
        if mat and ano and len(by_mat_year.get((mat, str(ano)), [])) == 1:
            cod, a = by_mat_year[(mat, str(ano))][0]
            return cod, a, "mat+ano"
        return None, None, "sem_match"

    linhas = []
    metodos = defaultdict(int)
    fora_escopo = 0
    for arq, h in horas.items():
        if h["h_total"] is None:
            continue
        rec_meta = meta.get(arq)
        if not rec_meta:
            continue
        cod, a, metodo = achar(arq, rec_meta)
        metodos[metodo] += 1
        if not cod:
            continue
        o = oco[cod]
        if (a["aeronave_tipo_veiculo"] != "AVIÃO" or
                a["aeronave_tipo_operacao"] not in GA_OPS or
                o["ocorrencia_classificacao"] != "ACIDENTE"):
            fora_escopo += 1
            continue
        fat = a["total_fatalidades"]
        fatal = 1 if (fat.isdigit() and int(fat) > 0) else 0
        ano_oco = o["ocorrencia_dia"][:4] if o["ocorrencia_dia"] else ""
        # plausibilidade: horas 0 viram ausente
        def pos(x):
            return x if (x is not None and x > 0) else ""
        linhas.append({
            "arquivo": arq, "numero": rec_meta.get("numero", ""), "codigo_ocorrencia": cod,
            "join": metodo,
            # desfechos
            "fatal": fatal, "n_fatalidades": fat if fat.isdigit() else "",
            "nivel_dano": a["aeronave_nivel_dano"],
            # preditores (experiência PIC)
            "h_total": pos(h["h_total"]), "h_tipo": pos(h["h_tipo"]),
            "h_total_30d": h["h_total_30d"] if h["h_total_30d"] is not None else "",
            "h_total_24h": h["h_total_24h"] if h["h_total_24h"] is not None else "",
            "idade_pic": h["idade_pic"] if h["idade_pic"] else "",
            "fonte_horas": h["fonte_horas"],
            # covariáveis
            "tipo_operacao": a["aeronave_tipo_operacao"],
            "fase_voo": a["aeronave_fase_operacao"],
            "motor_tipo": a["aeronave_motor_tipo"], "motor_qtd": a["aeronave_motor_quantidade"],
            "pmd_categoria": a["aeronave_pmd_categoria"], "assentos": a["aeronave_assentos"],
            "ano_fabricacao": a["aeronave_ano_fabricacao"],
            "fabricante": a["aeronave_fabricante"], "modelo": a["aeronave_modelo"],
            "tipo_ocorrencia": o["ocorrencia_tipo"], "tipo_icao": o["ocorrencia_tipo_icao"],
            "uf": o["ocorrencia_uf"], "ano_ocorrencia": ano_oco,
            "meteo": h["meteo"],
            "total_recomendacoes": o["total_recomendacoes"],
        })

    # grava CSV
    cols = list(linhas[0].keys())
    with open(BASE / "dataset_analitico.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(linhas)

    nfat = sum(l["fatal"] for l in linhas)
    print(f"Relatórios c/ horas: {len(horas)}")
    print(f"Métodos de join: {dict(metodos)}")
    print(f"Fora de escopo (não GA/avião/acidente): {fora_escopo}")
    print(f"\n>>> N analítico (GA aviões, acidente, com horas): {len(linhas)}")
    print(f"    fatais: {nfat} | não-fatais: {len(linhas)-nfat}")
    com_tipo = sum(1 for l in linhas if l["h_tipo"] != "")
    print(f"    com h_tipo: {com_tipo} | com idade: {sum(1 for l in linhas if l['idade_pic']!='')}")
    print("→ dataset_analitico.csv")


if __name__ == "__main__":
    main()
