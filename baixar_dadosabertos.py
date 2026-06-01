"""
Descobre e baixa os dados abertos atualizados do CENIPA.

dados.gov.br é renderizado via JS e a API exige token; então usamos o Camoufox
(que já passa o Cloudflare do CENIPA) para: (1) renderizar a página do dataset e
extrair as URLs reais dos recursos; (2) baixar os CSV/ZIP pelo contexto do browser.

Modo descoberta (default): apenas lista os links encontrados.
Modo download: passe --baixar para gravar em dataset_new/.
"""
import sys, time, re, json
from pathlib import Path
from camoufox.sync_api import Camoufox

BASE = Path(__file__).parent
OUT = BASE / "dataset_new"
DATASET = "https://dados.gov.br/dados/conjuntos-dados/ocorrencias-aeronauticas-da-aviacao-civil-brasileira"
CHALLENGE = ["just a moment", "um momento", "verifying you are human",
             "verificação de segurança", "checking your browser", "enable javascript"]


def passou(page):
    try:
        t = (page.title() or "").lower()
        b = page.evaluate("document.body?document.body.innerText.slice(0,300):''").lower()
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


def abrir(page, url, espera_sel=None, t=90):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    t0 = time.time(); clicou = False
    while time.time() - t0 < t:
        if passou(page):
            break
        if not clicou and time.time() - t0 > 8:
            clicou = click_widget(page)
        page.wait_for_timeout(2000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    if espera_sel:
        try:
            page.wait_for_selector(espera_sel, timeout=20000)
        except Exception:
            pass
    page.wait_for_timeout(2500)


def coletar_links(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('a[href]')).map(a => ({
        href: a.href, text: (a.innerText||'').trim().slice(0,60)
    }))""")


def main():
    baixar = "--baixar" in sys.argv
    with Camoufox(headless=False, humanize=True, geoip=True, locale="pt-BR", os="linux") as br:
        page = br.new_page()
        print(f"[*] abrindo dataset no dados.gov.br ...", flush=True)
        abrir(page, DATASET, espera_sel="a[href*='recurso'], a[href$='.csv'], a[href$='.zip']")
        links = coletar_links(page)
        # filtra candidatos
        cand = [l for l in links if re.search(r"\.(csv|zip|xlsx)(\?|$)|recurso|download|cenipa|arquivo", l["href"], re.I)]
        print(f"[+] {len(links)} links na página | {len(cand)} candidatos:\n", flush=True)
        for l in cand[:40]:
            print(f"    {l['text'][:40]:40s} {l['href']}", flush=True)
        (BASE / "dadosabertos_links.json").write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8")

        if baixar:
            OUT.mkdir(exist_ok=True)
            arqs = [l for l in cand if re.search(r"\.(csv|zip|xlsx)(\?|$)", l["href"], re.I)]
            print(f"\n[*] baixando {len(arqs)} arquivos para {OUT.name}/ ...", flush=True)
            for l in arqs:
                nome = re.sub(r"\?.*$", "", l["href"].rsplit("/", 1)[-1]) or "arquivo"
                try:
                    r = page.context.request.get(l["href"], timeout=120000)
                    if r.status == 200 and len(r.body()) > 200:
                        (OUT / nome).write_bytes(r.body())
                        print(f"    OK {nome} ({len(r.body())//1024} KB)", flush=True)
                    else:
                        print(f"    FALHA http{r.status} {nome}", flush=True)
                except Exception as e:
                    print(f"    ERRO {nome}: {e}", flush=True)
        else:
            print("\n[i] modo descoberta — rode com --baixar para baixar.", flush=True)


if __name__ == "__main__":
    main()
