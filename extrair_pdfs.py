"""
Extrai, de cada Relatório Final (PDF) da CENIPA, os metadados e o texto de
cada seção, de forma estruturada — para análise no paper.

Estratégia:
- Usa o TOC embutido (bookmarks) como lista canônica de seções; a página de
  cada entrada serve de âncora para pular o ÍNDICE (onde os títulos repetem).
- Remove cabeçalho/rodapé repetidos (nº do relatório, matrícula, data, "N de M").
- Enriquece com metadados de links_reais.json (cidade, UF, tipo, classificação).
- Idempotente/resumível: salva extraidos/<arquivo>.json e pula o que já existe.
  Pode rodar em paralelo aos downloads (só lê PDFs prontos).

Uso:
    python extrair_pdfs.py            # processa todos os pdfs/ pendentes
    python extrair_pdfs.py --limite 5 # teste
    python extrair_pdfs.py --reextrair
"""
import argparse, csv, json, re, unicodedata
from pathlib import Path
import fitz  # PyMuPDF

BASE = Path(__file__).parent
PDFDIR = BASE / "pdfs"
OUTDIR = BASE / "extraidos"
INDICE = OUTDIR / "_indice.csv"
LINKS = BASE / "links_reais.json"

RE_PAGNUM = re.compile(r"^\d{1,3}\s+de\s+\d{1,3}$")
RE_FORM = re.compile(r"^FORMRF", re.I)


def colapsa(s):
    return re.sub(r"[ \t ]+", " ", s)


def carregar_meta_links():
    if not LINKS.exists():
        return {}
    out = {}
    for r in json.loads(LINKS.read_text(encoding="utf-8")):
        nome = (r.get("pdf_pt") or r.get("pdf_en") or "").rsplit("/", 1)[-1]
        if nome:
            out[nome] = r
    return out


def extrair_cabecalho(primeira_pagina):
    """Lê os pares rótulo/valor do cabeçalho da capa."""
    txt = primeira_pagina
    meta = {}
    for chave, alvo in [("OCORRÊNCIA", "ocorrencia"), ("AERONAVE", "aeronave"),
                        ("MODELO", "modelo"), ("DATA", "data")]:
        m = re.search(rf"{chave}:\s*\n?\s*([^\n]+)", txt)
        if m:
            meta[alvo] = m.group(1).strip()
    m = re.search(r"\b([AI]G?-\d{2,4}/CENIPA/\d{4})\b", txt) or \
        re.search(r"\b(RF-[^\s]+/CENIPA/\d{4})\b", txt)
    if m:
        meta["numero"] = m.group(1)
    return meta


def limpar_paginas(doc, numero, matricula, data):
    lixo_exatos = {x for x in [numero, matricula, data] if x}
    paginas = []
    for p in range(doc.page_count):
        linhas = []
        for ln in doc[p].get_text().split("\n"):
            s = colapsa(ln).strip()
            if not s:
                continue
            if s in lixo_exatos or RE_PAGNUM.match(s) or RE_FORM.match(s):
                continue
            linhas.append(s)
        paginas.append("\n".join(linhas))
    return paginas


def segmentar(texto_full, offsets_pag, toc):
    """Localiza cada título do TOC no corpo (ancorado pela página) e fatia."""
    anchors = []
    for lvl, titulo, pg in toc:
        t = colapsa(re.sub(r"\.*\s*$", "", titulo)).strip()
        if not t:
            continue
        # número + nome separados por espaços variáveis -> regex tolerante
        partes = t.split(" ", 1)
        if re.match(r"^\d", partes[0]) and len(partes) == 2:
            pat = re.compile(re.escape(partes[0]) + r"\.?\s+" + re.escape(partes[1]), re.I)
        else:
            pat = re.compile(re.escape(t), re.I)
        ini_busca = offsets_pag[pg - 1] if 0 < pg <= len(offsets_pag) else 0
        m = pat.search(texto_full, max(0, ini_busca - 300))
        if not m:
            m = pat.search(texto_full)  # fallback global
        if m:
            anchors.append((m.start(), m.end(), lvl, titulo.strip().rstrip(".")))
    anchors.sort()
    secoes = []
    for i, (ini, fim_tit, lvl, titulo) in enumerate(anchors):
        prox = anchors[i + 1][0] if i + 1 < len(anchors) else len(texto_full)
        corpo = re.sub(r"^[.\s]+", "", texto_full[fim_tit:prox]).strip()
        num = ""
        mnum = re.match(r"^([\d.]+)\s+(.*)", titulo)
        if mnum:
            num, titulo_limpo = mnum.group(1).rstrip("."), mnum.group(2)
        else:
            titulo_limpo = titulo
        secoes.append({"numero": num, "titulo": titulo_limpo.strip(),
                       "nivel": lvl, "texto": corpo})
    return secoes


# Títulos canônicos do modelo FORMRF (fallback p/ PDFs sem TOC embutido)
CANON = [
    ("1", "INFORMAÇÕES FACTUAIS", r"INFORMA[ÇC][ÕO]ES FACTUAIS"),
    ("1.1", "Histórico do voo", r"Hist[óo]rico do voo"),
    ("1.2", "Lesões às pessoas", r"Les[õo]es [àa]s pessoas"),
    ("1.3", "Danos à aeronave", r"Danos [àa] aeronave"),
    ("1.4", "Outros danos", r"Outros danos"),
    ("1.5", "Informações acerca do pessoal envolvido", r"Informa[çc][õo]es acerca do pessoal"),
    ("1.5.1", "Experiência de voo dos tripulantes", r"Experi[êe]ncia de voo"),
    ("1.5.2", "Formação", r"Forma[çc][ãa]o"),
    ("1.5.3", "Categorias das licenças e validade dos certificados", r"Categorias das licen"),
    ("1.5.4", "Qualificação e experiência no tipo de voo", r"Qualifica[çc][ãa]o e experi"),
    ("1.5.5", "Validade da inspeção de saúde", r"Validade da inspe[çc][ãa]o"),
    ("1.6", "Informações acerca da aeronave", r"Informa[çc][õo]es acerca da aeronave"),
    ("1.7", "Informações meteorológicas", r"Informa[çc][õo]es meteorol[óo]gicas"),
    ("1.8", "Auxílios à navegação", r"Aux[íi]lios [àa] navega[çc][ãa]o"),
    ("1.9", "Comunicações", r"Comunica[çc][õo]es"),
    ("1.10", "Informações acerca do aeródromo", r"Informa[çc][õo]es acerca do aer[óo]dromo"),
    ("1.11", "Gravadores de voo", r"Gravadores de voo"),
    ("1.12", "Informações acerca do impacto e dos destroços", r"Informa[çc][õo]es acerca do impacto"),
    ("1.13", "Informações médicas, ergonômicas e psicológicas", r"Informa[çc][õo]es m[ée]dicas"),
    ("1.13.1", "Aspectos médicos", r"Aspectos m[ée]dicos"),
    ("1.13.2", "Informações ergonômicas", r"Informa[çc][õo]es ergon[ôo]micas"),
    ("1.13.3", "Aspectos Psicológicos", r"Aspectos [Pp]sicol[óo]gicos"),
    ("1.14", "Informações acerca de fogo", r"Informa[çc][õo]es acerca de fogo"),
    ("1.15", "Informações acerca de sobrevivência e/ou de abandono", r"Informa[çc][õo]es acerca de sobreviv"),
    ("1.16", "Exames, testes e pesquisas", r"Exames, testes e pesquisas"),
    ("1.17", "Informações organizacionais e de gerenciamento", r"Informa[çc][õo]es organizacionais"),
    ("1.18", "Informações operacionais", r"Informa[çc][õo]es operacionais"),
    ("1.19", "Informações adicionais", r"Informa[çc][õo]es adicionais"),
    ("1.20", "Utilização ou efetivação de outras técnicas de investigação", r"Utiliza[çc][ãa]o ou efetiva[çc][ãa]o"),
    ("2", "ANÁLISE", r"AN[ÁA]LISE"),
    ("3", "CONCLUSÕES", r"CONCLUS[ÕO]ES"),
    ("3.1", "Fatos", r"Fatos"),
    ("3.2", "Fatores contribuintes", r"Fatores [Cc]ontribuintes"),
    ("4", "RECOMENDAÇÕES DE SEGURANÇA", r"RECOMENDA[ÇC][ÕO]ES DE SEGURAN[ÇC]A"),
    ("5", "AÇÕES CORRETIVAS OU PREVENTIVAS ADOTADAS", r"A[ÇC][ÕO]ES CORRETIVAS"),
]


def segmentar_canonico(texto_full):
    """Fallback sem TOC: ancora nos títulos canônicos, ignorando o índice (dots)."""
    achados = []
    for num, titulo, nome_re in CANON:
        pat = re.compile(r"(?m)^\s*" + re.escape(num) + r"\.?\s+(?:" + nome_re + r")\b[^\n]*$", re.I)
        for m in pat.finditer(texto_full):
            linha = m.group(0)
            if "...." in linha or re.search(r"\.{3,}", linha):
                continue  # é entrada do ÍNDICE
            achados.append((m.start(), m.end(), num, titulo, num.count(".") + 1))
            break  # primeira ocorrência válida (no corpo)
    achados.sort()
    secoes = []
    for i, (ini, fim, num, titulo, nivel) in enumerate(achados):
        prox = achados[i + 1][0] if i + 1 < len(achados) else len(texto_full)
        corpo = re.sub(r"^[.\s]+", "", texto_full[fim:prox]).strip()
        secoes.append({"numero": num, "titulo": titulo, "nivel": nivel, "texto": corpo})
    return secoes


# Modelo ANTIGO (CENIPA-04, ~1990–2008): seções em algarismos romanos
CANON_ANTIGO = [
    ("HISTÓRICO DO ACIDENTE", r"HIST[ÓO0]RICO DO ACID[EO]NT[EC]"),
    ("DANOS CAUSADOS", r"DANOS CAUSADOS"),
    ("ELEMENTOS DE INVESTIGAÇÃO", r"ELEMENTOS [DP]E INVESTIGA[ÇC][ÃAÀ]O"),
    ("ANÁLISE", r"AN[ÁA]LISE"),
    ("CONCLUSÃO", r"CONCLUS[ÃA]O"),
    ("RECOMENDAÇÕES DE SEGURANÇA", r"RECOMENDA[ÇC][ÕO]ES"),
    ("DIVULGAÇÃO", r"DIVULGA[ÇC][ÃA]O"),
]


def segmentar_antigo(texto_full):
    """Fallback p/ modelo CENIPA-04: títulos romanos (I. HISTÓRICO, IV. ANÁLISE...)."""
    achados = []
    for titulo, nome_re in CANON_ANTIGO:
        pat = re.compile(r"(?m)^\s*([IVX]{1,4})\s*[-.)]\s*(?:" + nome_re + r")\b[^\n]*$", re.I)
        for m in pat.finditer(texto_full):
            if re.search(r"\.{3,}", m.group(0)):
                continue
            achados.append((m.start(), m.end(), m.group(1).upper(), titulo))
            break
    achados.sort()
    secoes = []
    for i, (ini, fim, num, titulo) in enumerate(achados):
        prox = achados[i + 1][0] if i + 1 < len(achados) else len(texto_full)
        corpo = re.sub(r"^[.\s]+", "", texto_full[fim:prox]).strip()
        secoes.append({"numero": num, "titulo": titulo, "nivel": 1, "texto": corpo})
    return secoes


def pegar_sinopse(texto_full):
    """Escolhe o bloco após 'SINOPSE' com conteúdo real (ignora entradas do índice)."""
    melhor = ""
    for m in re.finditer(r"\bSINOPSE\b\s*(.*?)(?:\b[ÍI]NDICE\b|\bGLOSS[ÁA]RIO\b|\n\s*1\.?\s+INFORMA[ÇC])",
                         texto_full, re.S):
        bloco = re.sub(r"^[.\s]+", "", m.group(1)).strip()
        if re.search(r"\.{4,}", bloco):  # dots leaders => é o índice
            continue
        letras = sum(c.isalpha() for c in bloco)
        if letras > 60 and letras > sum(c.isalpha() for c in melhor):
            melhor = bloco
    return melhor


def processar(pdf_path, meta_links):
    doc = fitz.open(pdf_path)
    n = doc.page_count
    primeira = doc[0].get_text() if n else ""
    cab = extrair_cabecalho(primeira)

    matricula = cab.get("aeronave", "")
    data = cab.get("data", "")
    numero = cab.get("numero", "")

    paginas = limpar_paginas(doc, numero, matricula, data)
    offsets, acc, parts = [], 0, []
    for pl in paginas:
        offsets.append(acc); parts.append(pl); acc += len(pl) + 1
    texto_full = "\n".join(paginas)

    toc = doc.get_toc()
    secoes = segmentar(texto_full, offsets, toc) if toc else []
    metodo = "toc"
    if len(secoes) < 3:  # sem TOC ou TOC pobre → fallback canônico (FORMRF moderno)
        alt = segmentar_canonico(texto_full)
        if len(alt) > len(secoes):
            secoes, metodo = alt, "canonico"
    if len(secoes) < 3:  # ainda nada → modelo antigo (CENIPA-04, romano)
        alt = segmentar_antigo(texto_full)
        if len(alt) > len(secoes):
            secoes, metodo = alt, "canonico_antigo"
    sinopse = pegar_sinopse(texto_full)
    tem_texto = len(texto_full.strip()) > 400

    enr = meta_links.get(pdf_path.name, {})
    return {
        "arquivo": pdf_path.name,
        "numero": numero or enr.get("numero", ""),
        "metadados": {
            "ocorrencia": cab.get("ocorrencia", "") or enr.get("classificacao", ""),
            "aeronave": matricula or enr.get("matricula", ""),
            "modelo": cab.get("modelo", ""),
            "data_capa": data,
            "classificacao": enr.get("classificacao", ""),
            "tipo": enr.get("tipo", ""),
            "data_ocorrencia": enr.get("data", ""),
            "cidade": enr.get("cidade", ""),
            "uf": enr.get("uf", ""),
        },
        "n_paginas": n,
        "tem_texto": tem_texto,
        "precisa_ocr": not tem_texto,
        "metodo_secoes": metodo if secoes else "nenhum",
        "n_secoes": len(secoes),
        "sinopse": sinopse,
        "secoes": secoes,
        "texto_completo": texto_full,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--reextrair", action="store_true")
    args = ap.parse_args()
    OUTDIR.mkdir(exist_ok=True)
    meta_links = carregar_meta_links()

    pdfs = sorted(PDFDIR.glob("*.pdf"))
    feitos = ocr = erros = 0
    linhas_idx = []
    for pdf in pdfs:
        dest = OUTDIR / (pdf.stem + ".json")
        if dest.exists() and not args.reextrair:
            try:
                d = json.loads(dest.read_text(encoding="utf-8"))
                linhas_idx.append(d)
            except Exception:
                pass
            continue
        try:
            d = processar(pdf, meta_links)
        except Exception as e:
            print(f"  ERRO {pdf.name}: {e}")
            erros += 1
            continue
        dest.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        linhas_idx.append(d)
        feitos += 1
        if d["precisa_ocr"]:
            ocr += 1
        flag = " [SEM TEXTO/OCR]" if d["precisa_ocr"] else ""
        print(f"  {pdf.name}: {d['n_secoes']} seções, {d['n_paginas']}p{flag}")
        if args.limite and feitos >= args.limite:
            break

    # índice consolidado
    if linhas_idx:
        with open(INDICE, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["arquivo", "numero", "classificacao", "aeronave", "modelo",
                        "data_ocorrencia", "cidade", "uf", "n_paginas", "n_secoes",
                        "tem_texto", "chars"])
            for d in linhas_idx:
                m = d["metadados"]
                w.writerow([d["arquivo"], d["numero"], m["classificacao"], m["aeronave"],
                            m["modelo"], m["data_ocorrencia"], m["cidade"], m["uf"],
                            d["n_paginas"], d["n_secoes"], d["tem_texto"], len(d["texto_completo"])])
    print(f"\nProcessados agora: {feitos} | sem texto (OCR): {ocr} | erros: {erros}")
    print(f"Total no índice: {len(linhas_idx)} → {INDICE}")
    print(f"JSONs em: {OUTDIR}")


if __name__ == "__main__":
    main()
