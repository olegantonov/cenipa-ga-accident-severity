"""
Baixa os Relatórios Finais (PDF) da CENIPA.

Estratégia: o site fica atrás do Cloudflare Turnstile, então um Chrome real
(patchright, headful) resolve o desafio UMA vez e os PDFs são baixados dentro
do contexto do navegador (context.request) — mesmos cookies/TLS, o Cloudflare
libera. As URLs vêm de alvos.json (geradas a partir dos CSVs: matrícula + data).

Uso:
    python baixar_relatorios.py                # baixa tudo de alvos.json
    python baixar_relatorios.py --limite 3     # só os 3 primeiros (teste)
"""
import argparse, csv, json, random, sys, time
from pathlib import Path
from patchright.sync_api import sync_playwright

BASE = Path(__file__).parent
ALVOS = BASE / "alvos.json"
OUTDIR = BASE / "pdfs"
LOG = BASE / "resultado.csv"
PROFILE = BASE / ".browser_profile"
URL_FORM = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php"

CHALLENGE_FRASES = [
    "just a moment", "um momento", "verifying you are human",
    "verificação de segurança", "checking your browser", "enable javascript",
]


def passou_challenge(page) -> bool:
    """True quando a página real carregou (não é mais a tela do Cloudflare)."""
    try:
        title = (page.title() or "").lower()
        body = page.evaluate("document.body ? document.body.innerText.slice(0,300) : ''").lower()
    except Exception:
        return False
    txt = title + " " + body
    return bool(title.strip()) and not any(f in txt for f in CHALLENGE_FRASES)


def resolver_turnstile(page, timeout_s=180) -> bool:
    """Abre o formulário e espera passar do Turnstile (clique manual se aparecer)."""
    page.goto(URL_FORM, wait_until="domcontentloaded", timeout=60000)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if passou_challenge(page):
            return True
        print(f"  [turnstile] aguardando... (resolva o checkbox se aparecer) title={page.title()!r}", flush=True)
        page.wait_for_timeout(2500)
    return False


def parece_challenge(body: bytes) -> bool:
    head = body[:4000].lower()
    return b"<!doctype html" in head and (b"challenge" in head or b"cf-" in head or b"just a moment" in head)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0, help="baixar só os N primeiros (0 = todos)")
    ap.add_argument("--delay-min", type=float, default=1.2)
    ap.add_argument("--delay-max", type=float, default=3.0)
    args = ap.parse_args()

    alvos = json.load(open(ALVOS, encoding="utf-8"))
    if args.limite:
        alvos = alvos[: args.limite]
    OUTDIR.mkdir(exist_ok=True)

    novo_log = not LOG.exists()
    log = open(LOG, "a", encoding="utf-8", newline="")
    w = csv.writer(log)
    if novo_log:
        w.writerow(["codigo_ocorrencia", "relatorio", "arquivo", "status", "tamanho"])

    ok = falha = pulou = 0
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            channel="chrome",
            headless=False,
            no_viewport=True,
            locale="pt-BR",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("[*] Resolvendo Cloudflare Turnstile...", flush=True)
        if not resolver_turnstile(page):
            print("[!] Não passou do Turnstile. Abortando.", flush=True)
            ctx.close(); log.close(); sys.exit(1)
        print("[+] Turnstile OK — cf_clearance obtido. Iniciando downloads.\n", flush=True)

        total = len(alvos)
        for i, a in enumerate(alvos, 1):
            dest = OUTDIR / a["arquivo"]
            if dest.exists() and dest.stat().st_size > 1000:
                pulou += 1
                continue

            def baixar():
                r = ctx.request.get(a["url"], timeout=60000)
                return r.status, r.body()

            try:
                status, body = baixar()
            except Exception as e:
                print(f"[{i}/{total}] ERRO  {a['arquivo']}: {e}", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], "erro", str(e)[:80]])
                falha += 1
                continue

            # Cloudflare re-desafiou no meio do caminho? re-resolve 1x e tenta de novo.
            if status == 403 or parece_challenge(body):
                print(f"[{i}/{total}] challenge — re-resolvendo Turnstile...", flush=True)
                if resolver_turnstile(page):
                    try:
                        status, body = baixar()
                    except Exception as e:
                        status, body = -1, b""

            if status == 200 and body[:5] == b"%PDF-":
                dest.write_bytes(body)
                ok += 1
                print(f"[{i}/{total}] OK    {a['arquivo']}  ({len(body)//1024} KB)  {a['relatorio']}", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], "ok", len(body)])
            else:
                tag = "404" if status == 404 else f"http{status}" if status > 0 else "nao-pdf"
                print(f"[{i}/{total}] {tag:8s} {a['arquivo']}  ({len(body)}B)", flush=True)
                w.writerow([a["codigo_ocorrencia"], a["relatorio"], a["arquivo"], tag, len(body)])
                falha += 1

            log.flush()
            time.sleep(random.uniform(args.delay_min, args.delay_max))

        ctx.close()

    log.close()
    print(f"\n==== FIM ====  baixados={ok}  falhas/404={falha}  já existiam={pulou}", flush=True)
    print(f"PDFs em: {OUTDIR}\nLog: {LOG}", flush=True)


if __name__ == "__main__":
    main()
