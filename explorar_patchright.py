"""
Tenta abrir CENIPA com patchright (anti-detecção). Salva HTML, screenshot,
e descreve o estado da página.
"""
from patchright.sync_api import sync_playwright
from pathlib import Path
import json

URL = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php"
OUT = Path(__file__).parent

def main():
    with sync_playwright() as p:
        # patchright recomenda usar Chrome real, persistent context, channel="chrome"
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(OUT / ".browser_profile"),
            channel="chrome",
            headless=False,
            no_viewport=True,
            locale="pt-BR",
        )
        page = ctx.new_page()

        print(f"[*] Abrindo {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        for i in range(60):
            title = page.title()
            body_text = page.evaluate("document.body ? document.body.innerText.slice(0, 300) : ''")
            challenge_phrases = [
                "just a moment", "um momento", "verifying", "verificação de segurança",
                "checking your browser", "executando verificação"
            ]
            in_challenge = any(p in (title + " " + body_text).lower() for p in challenge_phrases)
            print(f"    [{i:02d}] title={title!r} challenge={in_challenge}")
            if not in_challenge and title.strip():
                print(f"    body[:300]={body_text[:300]!r}")
                break
            page.wait_for_timeout(2000)
        else:
            print("[!] Não passou do challenge em 120s")

        page.wait_for_timeout(2000)
        html = page.content()
        (OUT / "page.html").write_text(html, encoding="utf-8")
        page.screenshot(path=str(OUT / "page.png"), full_page=True)
        print(f"[+] HTML ({len(html)}B) e screenshot salvos")

        forms = page.evaluate("""() => {
            const out = {forms: [], selects: [], inputs: [], buttons: []};
            document.querySelectorAll('form').forEach(f => out.forms.push({action: f.action, method: f.method, id: f.id}));
            document.querySelectorAll('select').forEach(s => out.selects.push({
                name: s.name, id: s.id,
                options: Array.from(s.options).slice(0, 50).map(o => ({v: o.value, t: o.text.trim()}))
            }));
            document.querySelectorAll('input').forEach(i => out.inputs.push({type: i.type, name: i.name, id: i.id, placeholder: i.placeholder}));
            document.querySelectorAll('button, input[type=submit]').forEach(b => out.buttons.push({text: (b.innerText||b.value||'').trim(), onclick: b.getAttribute('onclick')}));
            return out;
        }""")
        (OUT / "form_dump.json").write_text(json.dumps(forms, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] Formulário: {len(forms['forms'])} forms, {len(forms['selects'])} selects, {len(forms['inputs'])} inputs, {len(forms['buttons'])} buttons")

        ctx.close()

if __name__ == "__main__":
    main()
