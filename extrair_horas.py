"""
Extrai a experiência de voo do piloto em comando (PIC) dos relatórios CENIPA.

Fonte: extraidos/*.json (texto já extraído dos PDFs).
A seção 1.5.1 ("Experiência de voo dos tripulantes") traz a tabela "Horas Voadas":

    Discriminação
    PIC                 (1 ou 2 colunas: PIC/SIC, PILOTO/COPILOTO, INSTRUTOR/ALUNO...)
    Totais                          -> horas totais
    Totais, nos últimos 30 dias     -> recência (30 dias)
    Totais, nas últimas 24 horas
    Neste tipo de aeronave          -> horas no tipo
    Neste tipo, nos últimos 30 dias
    Neste tipo, nas últimas 24 horas

A coluna do PIC é escolhida por prioridade de papel. Valores HH:MM viram horas
decimais; "Desconhecido"/"NULL"/"-" viram ausente. Fallback narrativo quando não
há tabela ("X horas totais de voo, sendo Y no modelo").

Também coleta, quando disponíveis: idade do PIC, licença, e condição
meteorológica (VMC/IMC) da seção 1.7.

Saída: horas_voo.json (lista, uma entrada por relatório com texto).
"""
import json, glob, re
from pathlib import Path

BASE = Path(__file__).parent
EXTR = BASE / "extraidos"
OUT = BASE / "horas_voo.json"

ROWS = [
    ("total", r"Totais"),
    ("total_30d", r"Totais,?\s*nos\s*[úu]ltimos\s*30\s*dias"),
    ("total_24h", r"Totais,?\s*nas\s*[úu]ltimas\s*24\s*horas"),
    ("tipo", r"Neste\s*tipo\s*de\s*aeronave"),
    ("tipo_30d", r"Neste\s*tipo,?\s*nos\s*[úu]ltimos\s*30\s*dias"),
    ("tipo_24h", r"Neste\s*tipo,?\s*nas\s*[úu]ltimas\s*24\s*horas"),
]
ROW_LABELS_RE = re.compile(r"^(Totais|Neste\s*tipo)", re.I)
# prioridade para identificar a coluna do PIC entre os cabeçalhos
PIC_PRIORITY = ["PIC", "PILOTO EM COMANDO", "COMANDANTE", "CMTE", "PILOTO", "PILOTA",
                "INSTRUTOR", "CONDUTOR", "PILOTO EM INSTRUÇÃO"]
MISSING_TOK = re.compile(r"desconhecid|ignorad|n[ãa]o\s*(informad|apurad|dispon)|NULL|^-+$|N/?D", re.I)


def hhmm_to_hours(tok):
    """'1.142:50' -> 1142.83 ; 'Desconhecido' -> None"""
    tok = tok.strip()
    if not tok or MISSING_TOK.search(tok):
        return None
    m = re.match(r"^([\d.]+)\s*:\s*(\d{1,2})$", tok)
    if m:
        h = int(m.group(1).replace(".", ""))
        return round(h + int(m.group(2)) / 60.0, 2)
    m = re.match(r"^([\d.]+)$", tok)  # às vezes só horas inteiras
    if m and tok not in (".",):
        try:
            return float(tok.replace(".", ""))
        except ValueError:
            return None
    return None


def parse_tabela(texto):
    """Tenta o layout vertical canônico. Retorna dict de papéis->medidas ou None."""
    m = re.search(r"Horas\s*Voadas(.{0,700})", texto, re.S | re.I)
    if not m:
        return None
    bloco = m.group(1)
    md = re.search(r"Discrimina[çc][ãa]o\s*\n(.*)", bloco, re.S | re.I)
    if not md:
        return None
    linhas = [l.strip() for l in md.group(1).split("\n")]
    # 1) cabeçalhos = linhas até a 1ª linha de rótulo de dados (Totais/Neste tipo)
    headers, i = [], 0
    while i < len(linhas) and linhas[i] != "":
        if ROW_LABELS_RE.match(linhas[i]):
            break
        if linhas[i]:
            headers.append(linhas[i])
        i += 1
    if not headers:
        headers = ["PIC"]
    ncol = len(headers)
    # 2) varre rótulos conhecidos e captura ncol valores após cada um
    dados = {h: {} for h in headers}
    j = i
    while j < len(linhas):
        lab = linhas[j]
        chave = None
        for nome, pat in ROWS:
            if re.fullmatch(pat, lab, re.I):
                chave = nome
                break
        if chave:
            vals = []
            k = j + 1
            while k < len(linhas) and len(vals) < ncol:
                if linhas[k] == "":
                    k += 1
                    continue
                if ROW_LABELS_RE.match(linhas[k]) or linhas[k].lower().startswith("obs"):
                    break
                vals.append(linhas[k])
                k += 1
            for ci, h in enumerate(headers):
                if ci < len(vals):
                    dados[h][chave] = hhmm_to_hours(vals[ci])
            j = k
            continue
        if lab.lower().startswith("obs") or lab.startswith("1.5") or lab.startswith("1.6"):
            break
        j += 1
    # se nenhuma medida foi capturada, falhou
    if not any(v for d in dados.values() for v in d.values()):
        return None
    return headers, dados


def escolher_pic(headers, dados):
    up = [h.upper() for h in headers]
    for pref in PIC_PRIORITY:
        for idx, h in enumerate(up):
            if pref in h:
                return headers[idx]
    return headers[0]


def parse_narrativa(texto):
    """Fallback: 'X horas totais de voo, sendo Y horas no modelo'."""
    out = {}
    m = re.search(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*horas?\s*(?:totais|de\s*voo)", texto, re.I)
    if m:
        out["total"] = float(m.group(1).replace(".", "").replace(",", ""))
    m = re.search(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*horas?\s*(?:no\s*modelo|neste\s*tipo|no\s*tipo)", texto, re.I)
    if m:
        out["tipo"] = float(m.group(1).replace(".", "").replace(",", ""))
    return out or None


def extrair_idade(texto):
    m = re.search(r"(\d{2})\s*anos\s*de\s*idade", texto, re.I)
    if m:
        return int(m.group(1))
    return None


def extrair_meteo(d):
    """VMC/IMC a partir da seção 1.7 (meteorológicas) ou texto."""
    txt = ""
    for s in d.get("secoes", []):
        if s.get("numero") == "1.7":
            txt = s["texto"]
            break
    alvo = txt or d["texto_completo"]
    if re.search(r"\bIMC\b|condi[çc][õo]es\s*instrumento", alvo):
        return "IMC"
    if re.search(r"\bVMC\b|condi[çc][õo]es\s*visuais|CAVOK", alvo):
        return "VMC"
    return ""


def sec_151(d):
    for s in d.get("secoes", []):
        if s.get("numero") == "1.5.1":
            return s["texto"]
    return ""


def main():
    arquivos = [a for a in glob.glob(str(EXTR / "*.json")) if not a.endswith("_indice.csv")]
    saida = []
    n_tab = n_narr = n_none = 0
    for f in sorted(arquivos):
        d = json.load(open(f, encoding="utf-8"))
        if d.get("precisa_ocr"):
            continue
        # foca o texto da seção 1.5.1 (se houver), senão o documento todo
        contexto = sec_151(d) or d["texto_completo"]
        rec = {
            "arquivo": d["arquivo"], "numero": d.get("numero", ""),
            "fonte_horas": None, "pic_role": None,
            "h_total": None, "h_total_30d": None, "h_total_24h": None,
            "h_tipo": None, "h_tipo_30d": None, "h_tipo_24h": None,
            "idade_pic": extrair_idade(contexto), "meteo": extrair_meteo(d),
        }
        tab = parse_tabela(contexto) or parse_tabela(d["texto_completo"])
        if tab:
            headers, dados = tab
            pic = escolher_pic(headers, dados)
            md = dados[pic]
            rec.update({
                "fonte_horas": "tabela", "pic_role": pic,
                "h_total": md.get("total"), "h_total_30d": md.get("total_30d"),
                "h_total_24h": md.get("total_24h"), "h_tipo": md.get("tipo"),
                "h_tipo_30d": md.get("tipo_30d"), "h_tipo_24h": md.get("tipo_24h"),
            })
            n_tab += 1
        else:
            narr = parse_narrativa(contexto) or parse_narrativa(d["texto_completo"])
            if narr:
                rec.update({"fonte_horas": "narrativa",
                            "h_total": narr.get("total"), "h_tipo": narr.get("tipo")})
                n_narr += 1
            else:
                n_none += 1
        saida.append(rec)

    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    com_total = sum(1 for r in saida if r["h_total"] is not None)
    print(f"Relatórios processados: {len(saida)}")
    print(f"  via tabela:     {n_tab}")
    print(f"  via narrativa:  {n_narr}")
    print(f"  sem horas:      {n_none}")
    print(f"  COM h_total:    {com_total}")
    print(f"→ {OUT.name}")


if __name__ == "__main__":
    main()
