"""
Passa o Turnstile com Camoufox e mapeia o formulário REAL de relatorios.php:
salva o HTML liberado, lista selects/inputs/botões e TODOS os links de PDF
que já aparecem na página. Base para extrair os links reais (sem adivinhar URL).
"""
import json, time
from pathlib import Path
from camoufox.sync_api import Camoufox

BASE = Path(__file__).parent
URL = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php"
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


def main():
    with Camoufox(headless=False, humanize=True, geoip=True, locale="pt-BR", os="linux") as browser:
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        t0 = time.time(); clicou = False
        while time.time() - t0 < 120:
            if passou(page):
                break
            if not clicou and time.time() - t0 > 8:
                clicou = click_widget(page)
            print(f"  aguardando turnstile... title={page.title()!r}", flush=True)
            page.wait_for_timeout(2500)
        else:
            print("[!] não passou"); return

        print("[+] passou! aguardando conteúdo renderizar...\n", flush=True)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        try:
            page.wait_for_selector("select, input[type=text], table, form", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        (BASE / "form_real.html").write_text(page.content(), encoding="utf-8")

        info = page.evaluate("""() => {
            const out = {forms: [], selects: [], inputs: [], buttons: [], pdf_links: [], all_links_sample: []};
            document.querySelectorAll('form').forEach(f => out.forms.push({action: f.action, method: f.method, id: f.id, name: f.name}));
            document.querySelectorAll('select').forEach(s => out.selects.push({
                name: s.name, id: s.id, options_count: s.options.length,
                options: Array.from(s.options).slice(0,12).map(o => ({v: o.value, t: o.text.trim()}))
            }));
            document.querySelectorAll('input').forEach(i => out.inputs.push({type: i.type, name: i.name, id: i.id, value: i.value, placeholder: i.placeholder}));
            document.querySelectorAll('button, input[type=submit], a.btn, [onclick]').forEach(b => out.buttons.push({tag: b.tagName, text: (b.innerText||b.value||'').trim().slice(0,40), onclick: (b.getAttribute('onclick')||'').slice(0,120)}));
            const links = Array.from(document.querySelectorAll('a[href]'));
            out.pdf_links = links.filter(a => /\\.pdf/i.test(a.href)).map(a => a.href);
            out.all_links_sample = links.slice(0, 40).map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,40)}));
            out.body_preview = document.body.innerText.slice(0, 800);
            return out;
        }""")
        (BASE / "form_real.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"forms={len(info['forms'])} selects={len(info['selects'])} inputs={len(info['inputs'])} buttons={len(info['buttons'])}")
        print(f"PDF links já visíveis: {len(info['pdf_links'])}")
        print("\n--- FORMS ---")
        for f in info["forms"]: print("  ", f)
        print("\n--- SELECTS ---")
        for s in info["selects"]: print("  ", s["name"], s.get("id"), f"({s['options_count']} opts)", [o['t'] for o in s['options'][:6]])
        print("\n--- INPUTS ---")
        for i in info["inputs"]:
            if i["type"] not in ("hidden",): print("  ", i)
        print("\n--- BUTTONS/onclick ---")
        for b in info["buttons"][:25]: print("  ", b)
        print("\n--- BODY PREVIEW ---")
        print(info["body_preview"][:600])
        print("\n[i] HTML salvo em form_real.html | detalhes em form_real.json")
        page.wait_for_timeout(1000)


if __name__ == "__main__":
    main()
