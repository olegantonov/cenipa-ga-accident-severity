"""
Mapeia o formulário do CENIPA: filtros disponíveis, requisição que dispara
e formato dos resultados. Salva HTML pós-challenge para inspeção.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php"
OUT = Path(__file__).parent

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1366, "height": 900},
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )
        # Remove webdriver flag
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        page = ctx.new_page()

        requests = []
        page.on("request", lambda req: requests.append((req.method, req.url, req.post_data)))

        print(f"[*] Abrindo {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Aguarda passar do desafio Cloudflare (até 90s)
        for i in range(45):
            title = page.title()
            body_text = page.evaluate("document.body ? document.body.innerText.slice(0, 300) : ''")
            challenge_phrases = [
                "just a moment", "um momento", "verifying", "verificação de segurança",
                "checking your browser", "executando verificação"
            ]
            in_challenge = any(p in (title + " " + body_text).lower() for p in challenge_phrases)
            print(f"    [{i}] title='{title}' challenge={in_challenge}")
            if not in_challenge and title.strip():
                break
            page.wait_for_timeout(2000)

        page.wait_for_timeout(2000)

        html = page.content()
        (OUT / "page.html").write_text(html, encoding="utf-8")
        print(f"[+] HTML salvo em page.html ({len(html)} bytes)")

        # Lista todos os <select>, <input>, <form>
        forms = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('form').forEach(f => {
                out.push({
                    tag: 'form',
                    action: f.action,
                    method: f.method,
                    id: f.id,
                    name: f.name,
                });
            });
            document.querySelectorAll('select').forEach(s => {
                const opts = Array.from(s.options).slice(0, 30).map(o => ({v: o.value, t: o.text.trim()}));
                out.push({
                    tag: 'select',
                    name: s.name,
                    id: s.id,
                    options_count: s.options.length,
                    options: opts,
                });
            });
            document.querySelectorAll('input').forEach(i => {
                out.push({
                    tag: 'input',
                    type: i.type,
                    name: i.name,
                    id: i.id,
                    value: i.value,
                    placeholder: i.placeholder,
                });
            });
            document.querySelectorAll('button, input[type=submit]').forEach(b => {
                out.push({
                    tag: 'button',
                    text: (b.innerText || b.value || '').trim(),
                    onclick: b.getAttribute('onclick'),
                });
            });
            return out;
        }""")
        import json
        (OUT / "form_dump.json").write_text(json.dumps(forms, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] {len(forms)} elementos do formulário salvos em form_dump.json")

        print(f"\n[*] {len(requests)} requisições durante o load:")
        for m, u, d in requests[-30:]:
            print(f"    {m} {u}")

        browser.close()

if __name__ == "__main__":
    main()
