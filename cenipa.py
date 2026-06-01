"""
Baixa os Relatórios Finais (PDF) da CENIPA — fluxo definitivo.

1. Camoufox (Firefox anti-detect) passa o Cloudflare Turnstile uma vez.
2. Pagina relatorios.php?pag=N e extrai os LINKS REAIS dos PDFs da tabela
   (sem adivinhar nome de arquivo — os nomes são irregulares).
3. Filtra pelo escopo (default: classificação ACIDENTE) e baixa os PDFs pelo
   próprio contexto do navegador (cookies/fingerprint que passam o Cloudflare).

Resume: pula PDFs já baixados e reusa links_reais.json se já coletado.

Uso:
    python cenipa.py --max-paginas 2          # teste: só 2 páginas
    python cenipa.py                          # coleta tudo + baixa ACIDENTE
    python cenipa.py --classificacao TODAS    # baixa todos os tipos
    python cenipa.py --idioma ambos           # baixa PT e EN (default: pt)
"""
import argparse, csv, html as htmllib, json, math, random, re, sys, time
from pathlib import Path
from camoufox.sync_api import Camoufox

BASE = Path(__file__).parent
RELBASE = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/"
URL_FORM = RELBASE + "relatorios.php"
LINKS = BASE / "links_reais.json"
OUTDIR = BASE / "pdfs"
LOG = BASE / "resultado.csv"
CHALLENGE = ["just a moment", "um momento", "verifying you are human",
             "verificação de segurança", "checking your browser", "enable javascript"]


def passou(page):
    try:
        t = (page.title() or "").lower()
        b = page.evaluate("document.body?document.body.innerText.slice(0,400):''").lower()
    except Exception:
        return False
    return bool(t.strip()) and not any(c in (t + " " + b) for c in CHALLENGE)


def click_widget(page):
    for fr in page.frames:
        if "challenges.cloudflare.com" in (fr.url or ""):
            try:
                box = fr.frame_element().bounding_box()
                if box:
                    page.mouse.click(box["x"] + 30, box["y"] + box["height"] / 2)
                    return True
            except Exception:
                pass
    return False


def resolver_turnstile(page, timeout_s=120):
    page.goto(URL_FORM, wait_until="domcontentloaded", timeout=60000)
    t0 = time.time(); clicou = False
    while time.time() - t0 < timeout_s:
        if passou(page):
            return True
        if not clicou and time.time() - t0 > 8:
            clicou = click_widget(page)
        print(f"  [turnstile] aguardando... title={page.title()!r}", flush=True)
        page.wait_for_timeout(2500)
    return False


EXTRAIR_JS = r"""() => {
    const rows = [];
    document.querySelectorAll('#lista tbody tr').forEach(tr => {
        const td = tr.querySelectorAll('td');
        if (td.length < 8) return;
        let pt = '', en = '';
        td[7].querySelectorAll('a[href]').forEach(a => {
            if (!/\.pdf/i.test(a.href)) return;
            if (/\/en\//i.test(a.href)) en = a.href; else pt = a.href;
        });
        if (!pt && !en) return;
        const t = n => (td[n] ? td[n].innerText.trim() : '');
        rows.push({numero: t(0), data: t(1), matricula: t(2), classificacao: t(3),
                   tipo: t(4), cidade: t(5), uf: t(6), pdf_pt: pt, pdf_en: en});
    });
    return rows;
}"""


def abrir_pagina(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector("#lista tbody tr", timeout=30000)
    except Exception:
        pass


def coletar(page, max_paginas=0):
    print("[*] Coletando links reais (paginando relatorios.php?pag=N)...", flush=True)
    abrir_pagina(page, URL_FORM)
    total_txt = page.evaluate("document.body.innerText.match(/Total de registros:\\s*([\\d.]+)/)?.[1] || ''")
    total = int(total_txt.replace(".", "")) if total_txt else 0
    primeira = page.evaluate(EXTRAIR_JS)
    por_pag = len(primeira) or 120
    n_pag = math.ceil(total / por_pag) if total else 1
    if max_paginas:
        n_pag = min(n_pag, max_paginas)
    print(f"    total={total} registros | {por_pag}/página | {n_pag} páginas", flush=True)

    todos = list(primeira)
    for p in range(2, n_pag + 1):
        try:
            abrir_pagina(page, f"{URL_FORM}?pag={p}")
            linhas = page.evaluate(EXTRAIR_JS)
        except Exception as e:
            print(f"    pág {p}: ERRO {e}", flush=True); continue
        todos.extend(linhas)
        print(f"    pág {p}/{n_pag}: +{len(linhas)} (acum {len(todos)})", flush=True)
        time.sleep(random.uniform(0.4, 1.0))

    # dedup por numero+pdf_pt
    seen = set(); uniq = []
    for r in todos:
        k = (r["numero"], r["pdf_pt"], r["pdf_en"])
        if k in seen: continue
        seen.add(k); uniq.append(r)
    LINKS.write_text(json.dumps(uniq, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] {len(uniq)} relatórios coletados → {LINKS.name}\n", flush=True)
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classificacao", default="ACIDENTE",
                    help="ACIDENTE | INCIDENTE | 'INCIDENTE GRAVE' | TODAS")
    ap.add_argument("--idioma", default="pt", choices=["pt", "en", "ambos"])
    ap.add_argument("--max-paginas", type=int, default=0, help="limita coleta (teste)")
    ap.add_argument("--max-downloads", type=int, default=0, help="limita downloads (teste)")
    ap.add_argument("--recoletar", action="store_true")
    ap.add_argument("--delay-min", type=float, default=1.2)
    ap.add_argument("--delay-max", type=float, default=3.0)
    args = ap.parse_args()
    OUTDIR.mkdir(exist_ok=True)

    with Camoufox(headless=False, humanize=True, geoip=True, locale="pt-BR", os="linux") as browser:
        page = browser.new_page()
        print("[*] Resolvendo Turnstile (clique no checkbox se aparecer)...", flush=True)
        if not resolver_turnstile(page):
            print("[!] Não passou do Turnstile."); sys.exit(1)
        print("[+] Turnstile OK.\n", flush=True)

        if LINKS.exists() and not args.recoletar:
            rels = json.loads(LINKS.read_text(encoding="utf-8"))
            print(f"[i] reusando {LINKS.name} ({len(rels)} relatórios; use --recoletar p/ atualizar)\n", flush=True)
        else:
            rels = coletar(page, args.max_paginas)

        # filtro de escopo
        if args.classificacao.upper() != "TODAS":
            rels = [r for r in rels if r["classificacao"].upper() == args.classificacao.upper()]
        # monta fila de downloads (pt/en)
        fila = []
        for r in rels:
            if args.idioma in ("pt", "ambos") and r["pdf_pt"]:
                fila.append((r, r["pdf_pt"]))
            if args.idioma in ("en", "ambos") and r["pdf_en"]:
                fila.append((r, r["pdf_en"]))
        if args.max_downloads:
            fila = fila[: args.max_downloads]
        print(f"[*] Escopo='{args.classificacao}' idioma='{args.idioma}' → {len(fila)} PDFs a baixar\n", flush=True)

        novo = not LOG.exists()
        log = open(LOG, "a", encoding="utf-8", newline=""); w = csv.writer(log)
        if novo:
            w.writerow(["numero", "classificacao", "arquivo", "status", "tamanho"])

        def baixar_um(url):
            resp = page.context.request.get(url, timeout=90000)
            return resp.status, resp.body()

        ok = falha = pulou = 0
        total = len(fila)
        for i, (r, url) in enumerate(fila, 1):
            nome = url.rsplit("/", 1)[-1]
            dest = OUTDIR / nome
            if dest.exists() and dest.stat().st_size > 1000:
                pulou += 1; continue
            try:
                status, body = baixar_um(url)
            except Exception as e:
                print(f"[{i}/{total}] ERRO {nome}: {e}", flush=True)
                w.writerow([r["numero"], r["classificacao"], nome, "erro", str(e)[:60]]); falha += 1; continue

            # cf_clearance expirou? (403 ou HTML de challenge) → re-resolve e tenta de novo
            if status != 200 or body[:5] != b"%PDF-":
                eh_challenge = status == 403 or (b"<!doctype html" in body[:200].lower() and b"%PDF" not in body[:200])
                if eh_challenge:
                    print(f"[{i}/{total}] Cloudflare rebloqueou — re-resolvendo Turnstile...", flush=True)
                    if resolver_turnstile(page):
                        print("    [+] Turnstile OK, retomando.", flush=True)
                        try:
                            status, body = baixar_um(url)
                        except Exception:
                            status, body = -1, b""

            if status == 200 and body[:5] == b"%PDF-":
                dest.write_bytes(body); ok += 1
                print(f"[{i}/{total}] OK   {nome} ({len(body)//1024} KB) {r['numero']}", flush=True)
                w.writerow([r["numero"], r["classificacao"], nome, "ok", len(body)])
            else:
                print(f"[{i}/{total}] FALHA http{status} {nome} ({len(body)}B)", flush=True)
                w.writerow([r["numero"], r["classificacao"], nome, f"http{status}", len(body)]); falha += 1
            log.flush()
            time.sleep(random.uniform(args.delay_min, args.delay_max))
        log.close()
        print(f"\n==== FIM ==== baixados={ok} falhas={falha} já existiam={pulou}", flush=True)
        print(f"PDFs em: {OUTDIR} | Log: {LOG.name}", flush=True)


if __name__ == "__main__":
    main()
