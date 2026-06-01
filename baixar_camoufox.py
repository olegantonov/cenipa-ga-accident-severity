"""
Baixa os Relatórios Finais (PDF) da CENIPA usando Camoufox (Firefox anti-detect).

O site fica atrás do Cloudflare Turnstile. O Camoufox (humanize + geoip) tende a
passar o desafio sozinho num IP residencial; se aparecer o checkbox, basta clicar.
Depois de liberar o cf_clearance, os PDFs são baixados pelo próprio contexto do
navegador (mesmos cookies/fingerprint), então o Cloudflare não rebloqueia.

Uso:
    python baixar_camoufox.py --limite 3     # teste rápido
    python baixar_camoufox.py                # baixa tudo de alvos.json
"""
import argparse, csv, json, random, sys, time
from pathlib import Path
from camoufox.sync_api import Camoufox

BASE = Path(__file__).parent
ALVOS = BASE / "alvos.json"
OUTDIR = BASE / "pdfs"
LOG = BASE / "resultado.csv"
URL_FORM = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php"

CHALLENGE_FRASES = [
    "just a moment", "um momento", "verifying you are human",
    "verificação de segurança", "checking your browser", "enable javascript",
    "verificando se você", "precisa analisar a segurança",
]


def passou_challenge(page) -> bool:
    try:
        title = (page.title() or "").lower()
        body = page.evaluate("document.body ? document.body.innerText.slice(0,400) : ''").lower()
    except Exception:
        return False
    txt = title + " " + body
    return bool(title.strip()) and not any(f in txt for f in CHALLENGE_FRASES)


def tentar_clicar_checkbox(page):
    """Se o widget do Turnstile estiver visível, clica nele (coordenada do iframe)."""
    for fr in page.frames:
        if "challenges.cloudflare.com" in (fr.url or ""):
            try:
                el = fr.frame_element()
                box = el.bounding_box()
                if box:
                    # o checkbox fica à esquerda do widget
                    page.mouse.click(box["x"] + 30, box["y"] + box["height"] / 2)
                    return True
            except Exception:
                pass
    return False


def resolver_turnstile(page, timeout_s=120) -> bool:
    page.goto(URL_FORM, wait_until="domcontentloaded", timeout=60000)
    t0 = time.time()
    tentou_click = False
    while time.time() - t0 < timeout_s:
        if passou_challenge(page):
            return True
        # depois de ~8s preso, tenta clicar no checkbox uma vez
        if not tentou_click and time.time() - t0 > 8:
            tentou_click = tentar_clicar_checkbox(page)
            if tentou_click:
                print("  [turnstile] cliquei no widget, aguardando...", flush=True)
        print(f"  [turnstile] aguardando... title={page.title()!r}", flush=True)
        page.wait_for_timeout(2500)
    return False


def parece_challenge(body: bytes) -> bool:
    head = body[:4000].lower()
    return b"<!doctype html" in head and (b"challenge" in head or b"just a moment" in head or b"cf-" in head)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--delay-min", type=float, default=1.5)
    ap.add_argument("--delay-max", type=float, default=3.5)
    args = ap.parse_args()

    alvos = json.load(open(ALVOS, encoding="utf-8"))
    if args.limite:
        alvos = alvos[: args.limite]
    OUTDIR.mkdir(exist_ok=True)

    novo = not LOG.exists()
    log = open(LOG, "a", encoding="utf-8", newline="")
    w = csv.writer(log)
    if novo:
        w.writerow(["codigo_ocorrencia", "relatorio", "arquivo", "status", "tamanho"])

    ok = falha = pulou = 0
    with Camoufox(headless=False, humanize=True, geoip=True, locale="pt-BR", os="linux") as browser:
        page = browser.new_page()

        print("[*] Abrindo CENIPA e resolvendo Turnstile (clique no checkbox se aparecer)...", flush=True)
        if not resolver_turnstile(page):
            print("[!] Não passou do Turnstile.", flush=True)
            log.close(); sys.exit(1)
        print("[+] Turnstile OK! Iniciando downloads.\n", flush=True)

        total = len(alvos)
        for i, a in enumerate(alvos, 1):
            dest = OUTDIR / a["arquivo"]
            if dest.exists() and dest.stat().st_size > 1000:
                pulou += 1
                continue

            def baixar():
                r = page.context.request.get(a["url"], timeout=60000)
                return r.status, r.body()

            try:
                status, body = baixar()
            except Exception as e:
                print(f"[{i}/{total}] ERRO  {a['arquivo']}: {e}", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], "erro", str(e)[:80]])
                falha += 1
                continue

            if status == 403 or parece_challenge(body):
                print(f"[{i}/{total}] challenge — re-resolvendo...", flush=True)
                if resolver_turnstile(page):
                    try:
                        status, body = baixar()
                    except Exception:
                        status, body = -1, b""

            if status == 200 and body[:5] == b"%PDF-":
                dest.write_bytes(body)
                ok += 1
                print(f"[{i}/{total}] OK    {a['arquivo']}  ({len(body)//1024} KB)  {a['relatorio']}", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], "ok", len(body)])
            else:
                tag = "404" if status == 404 else (f"http{status}" if status > 0 else "nao-pdf")
                print(f"[{i}/{total}] {tag:8s} {a['arquivo']}  ({len(body)}B)", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], tag, len(body)])
                falha += 1

            log.flush()
            time.sleep(random.uniform(args.delay_min, args.delay_max))

    log.close()
    print(f"\n==== FIM ====  baixados={ok}  falhas/404={falha}  já existiam={pulou}", flush=True)
    print(f"PDFs em: {OUTDIR}", flush=True)


if __name__ == "__main__":
    main()
