"""
Monta o dataset analítico a partir dos dados abertos ATUALIZADOS do CENIPA
(ocorrencia/aeronave/ocorrencia_tipo/fator_contribuinte, 2007–2025).

Diferenças do extrato antigo: delimitador ';', encoding latin-1, datas dd/mm/aaaa,
colunas renomeadas (aeronave_tipo_equipamento, anv_motor_qtd, aeronave_fatalidades_total),
tipo de ocorrência em arquivo separado, e labels de operação novos
(PRIVADA/INSTRUÇÃO/AGRÍCOLA/EXPERIMENTAL/TÁXI AÉREO).

Mantém o MESMO esquema de saída de montar_dataset.py (+ colunas de fator contribuinte),
para reaproveitar analise.py. Saídas: dataset_analitico.csv, codebook.md (atualizado).
"""
import json, glob, csv, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
DS = BASE / "dataset"
GA_OPS = {"PRIVADA", "INSTRUÇÃO", "AGRÍCOLA", "EXPERIMENTAL", "TÁXI AÉREO"}
MES = {'JAN':1,'FEV':2,'MAR':3,'ABR':4,'MAI':5,'MAIO':5,'JUN':6,'JUL':7,'AGO':8,'SET':9,'OUT':10,'NOV':11,'DEZ':12}


def load(f):
    return list(csv.DictReader(open(f, encoding="latin-1"), delimiter=";"))


def norm_num(n):
    n = (n or "").upper().replace(" ", "")
    m = re.search(r"([AI]G?)-?(\d{1,4})/CENIPA/(\d{4})", n)
    return f"{m.group(1)}-{int(m.group(2)):03d}/CENIPA/{m.group(3)}" if m else ""


def norm_mat(m):
    return re.sub(r"[^A-Z0-9]", "", (m or "").upper())


def iso_dia(s):
    """dd/mm/aaaa -> aaaa-mm-dd"""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s or "")
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""


def data_do_arquivo(nome):
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
    m = re.search(r"\b(19|20)(\d{2})\b", s)
    if m:
        return None, int(m.group(0))
    return None, None


def main():
    oco = {r["codigo_ocorrencia"]: r for r in load(DS / "ocorrencia.csv")}
    anv = defaultdict(list)
    for a in load(DS / "aeronave.csv"):
        anv[a["codigo_ocorrencia2"]].append(a)
    tipo = defaultdict(list)
    for t in load(DS / "ocorrencia_tipo.csv"):
        tipo[t["codigo_ocorrencia1"]].append(t)
    fatores = defaultdict(list)
    for f in load(DS / "fator_contribuinte.csv"):
        fatores[f["codigo_ocorrencia3"]].append(f)

    # horas + metadados de capa por arquivo
    horas = {h["arquivo"]: h for h in json.load(open(BASE / "horas_voo.json", encoding="utf-8"))}
    meta = {}
    for f in glob.glob(str(BASE / "extraidos" / "*.json")):
        if f.endswith("_indice.csv"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        meta[d["arquivo"]] = d
    mat_links = {}
    for r in json.load(open(BASE / "links_reais.json", encoding="utf-8")):
        for url in (r.get("pdf_pt"), r.get("pdf_en")):
            if url:
                mat_links[url.rsplit("/", 1)[-1]] = norm_mat(r.get("matricula"))

    # índices de join
    by_num, by_mat_date, by_mat_year, mat_acc = {}, {}, defaultdict(list), defaultdict(list)
    for cod, o in oco.items():
        num = norm_num(o["divulgacao_relatorio_numero"])
        if num:
            by_num.setdefault(num, cod)
        dia = iso_dia(o["ocorrencia_dia"]); ano = dia[:4] if dia else None
        for a in anv[cod]:
            mt = norm_mat(a["aeronave_matricula"])
            if not mt:
                continue
            if dia:
                by_mat_date[(mt, dia)] = (cod, a)
            if ano:
                by_mat_year[(mt, ano)].append((cod, a))
            if o["ocorrencia_classificacao"] == "ACIDENTE":
                mat_acc[mt].append((cod, a))

    def achar(arq, rm):
        num = norm_num(rm.get("numero"))
        if num in by_num:
            cod = by_num[num]
            a = next((x for x in anv[cod] if norm_mat(x["aeronave_matricula"]) == norm_mat(rm["metadados"].get("aeronave"))),
                     anv[cod][0] if anv[cod] else None)
            if a: return cod, a, "numero"
        mat = mat_links.get(arq) or norm_mat(rm["metadados"].get("aeronave"))
        iso, ano = data_do_arquivo(arq)
        if mat and iso and (mat, iso) in by_mat_date:
            return (*by_mat_date[(mat, iso)], "mat+data")
        if mat and ano and len(by_mat_year.get((mat, str(ano)), [])) == 1:
            return (*by_mat_year[(mat, str(ano))][0], "mat+ano")
        if mat and len(mat_acc.get(mat, [])) == 1:
            return (*mat_acc[mat][0], "mat_unico")
        return None, None, "sem_match"

    linhas, metodos = [], defaultdict(int)
    fora = 0
    for arq, h in horas.items():
        if h["h_total"] is None:
            continue
        rm = meta.get(arq)
        if not rm:
            continue
        cod, a, metodo = achar(arq, rm)
        metodos[metodo] += 1
        if not cod:
            continue
        o = oco[cod]
        if (a["aeronave_tipo_equipamento"] != "AVIÃO" or
                a["aeronave_tipo_operacao"] not in GA_OPS or
                o["ocorrencia_classificacao"] != "ACIDENTE"):
            fora += 1
            continue
        fat = a["aeronave_fatalidades_total"]
        fatal = 1 if (fat.isdigit() and int(fat) > 0) else 0
        dia = iso_dia(o["ocorrencia_dia"])
        try:
            mqtd = int(a["anv_motor_qtd"])
        except (ValueError, TypeError):
            mqtd = ""
        tps = tipo.get(cod, [])
        fl = fatores.get(cod, [])
        areas = {x["fator_area"] for x in fl}

        def pos(x):
            return x if (x is not None and x > 0) else ""
        linhas.append({
            "arquivo": arq, "numero": rm.get("numero", ""), "codigo_ocorrencia": cod, "join": metodo,
            "fatal": fatal, "n_fatalidades": fat if fat.isdigit() else "",
            "nivel_dano": a["aeronave_nivel_dano"],
            "h_total": pos(h["h_total"]), "h_tipo": pos(h["h_tipo"]),
            "h_total_30d": h["h_total_30d"] if h["h_total_30d"] is not None else "",
            "h_total_24h": h["h_total_24h"] if h["h_total_24h"] is not None else "",
            "idade_pic": h["idade_pic"] if h["idade_pic"] else "", "fonte_horas": h["fonte_horas"],
            "tipo_operacao": a["aeronave_tipo_operacao"], "fase_voo": a["aeronave_fase_operacao"],
            "motor_tipo": a["aeronave_motor_tipo"], "motor_qtd": mqtd,
            "pmd": a["aeronave_pmd"], "assentos": a["aeronave_assentos"],
            "ano_fabricacao": a["aeronave_ano_fabricacao"],
            "fabricante": a["aeronave_fabricante"], "modelo": a["aeronave_modelo"],
            "tipo_ocorrencia": tps[0]["ocorrencia_tipo"] if tps else "",
            "tipo_icao": tps[0]["taxonomia_tipo_icao"] if tps else "",
            "uf": o["ocorrencia_uf"], "ano_ocorrencia": dia[:4],
            "meteo": h["meteo"], "total_recomendacoes": o["total_recomendacoes"],
            # fatores contribuintes (bônus)
            "fator_humano": int("FATOR HUMANO" in areas),
            "fator_operacional": int("FATOR OPERACIONAL" in areas),
            "fator_material": int("FATOR MATERIAL" in areas),
            "n_fatores": len(fl),
        })

    cols = list(linhas[0].keys())
    with open(BASE / "dataset_analitico.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(linhas)

    nfat = sum(l["fatal"] for l in linhas)
    anos = sorted(l["ano_ocorrencia"] for l in linhas if l["ano_ocorrencia"])
    print(f"Métodos de join: {dict(metodos)} | fora de escopo: {fora}")
    print(f">>> N analítico (GA aviões, acidente, com horas): {len(linhas)}")
    print(f"    fatais: {nfat} ({100*nfat//len(linhas)}%) | não-fatais: {len(linhas)-nfat}")
    print(f"    período: {anos[0]}–{anos[-1]}")
    print(f"    com h_tipo: {sum(1 for l in linhas if l['h_tipo']!='')} | "
          f"com fator contribuinte: {sum(1 for l in linhas if l['n_fatores']>0)}")
    print("→ dataset_analitico.csv")


if __name__ == "__main__":
    main()
