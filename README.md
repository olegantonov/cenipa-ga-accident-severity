# Pilot flight experience and accident severity in Brazilian general aviation

[![Code license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data & text: CC BY 4.0](https://img.shields.io/badge/data%20%26%20text-CC%20BY%204.0-lightgrey.svg)](CC-BY-4.0.md)

Reproducible research compendium for a register-based, cross-sectional study of
whether **pilot-in-command (PIC) flight experience** is associated with the
**severity** (fatal vs non-fatal) of **general-aviation airplane accidents in
Brazil (2007–2024)**. Data come from the final reports and open data of the
Brazilian Aeronautical Accident Investigation and Prevention Center (**CENIPA**).

This repository contains the full pipeline — web scraping, PDF text and
flight-hour extraction, dataset assembly, statistical analysis — together with
the de-identified analytic dataset, the figures, and the manuscript.

## Key findings

- Among **824** GA airplane accidents (197 fatal, 23.9%), **total** PIC flight
  hours were **not** associated with accident fatality (adjusted OR 0.91 per
  ln-hour, 95% CI 0.82–1.02), with **no "killing-zone" nonlinearity**.
- Experience **specific to the accident aircraft type** was protective
  (OR 0.81 per ln-hour, 95% CI 0.72–0.92, p = 0.001).
- Severity was dominated by **flight phase** (cruise/manoeuvre ≫ approach/landing)
  and **type of operation** (agricultural/instruction less lethal than private).
- Accidents with **human contributing factors** were ~4× as lethal (40% vs 10%).

> Design note: the study models severity **conditional on an accident**; it does
> not estimate accident *rates*, which would require exposure data absent from the
> registry. See the manuscript's Discussion for this limitation.

## Repository structure

```
.
├── cenipa.py               # scraper: CENIPA final reports (Camoufox bypasses Cloudflare Turnstile)
├── baixar_camoufox.py      # earlier scraper variant (Camoufox)
├── baixar_dadosabertos.py  # helper to locate/fetch the open-data CSVs
├── extrair_pdfs.py         # PDF → structured sections (PyMuPDF), per report
├── extrair_horas.py        # parse PIC flight hours from the reports
├── montar_dataset_v2.py    # join + build the analytic dataset (current open data, 2007–2025)
├── montar_dataset.py       # legacy builder (2009–2019 extract); kept for provenance
├── analise.py              # statistics (statsmodels) + figures
├── gerar_docx.py           # render the manuscript to .docx
├── dataset/                # CENIPA open-data CSVs (public; ';'-delimited, latin-1)
├── dataset_analitico.csv   # analytic dataset (one row per accident aircraft; de-identified)
├── codebook.md             # variable dictionary for the analytic dataset
├── horas_voo.json          # extracted PIC flight hours (intermediate)
├── links_reais.json        # report catalogue (number, registration, date, PDF links)
├── figuras/                # figures (PNG, 300 dpi)
├── manuscrito.md           # manuscript (Markdown source)
├── manuscrito.docx         # manuscript (formatted, submission-ready)
├── referencias.bib         # references (BibTeX)
├── requirements.txt
├── CITATION.cff
├── LICENSE                 # MIT (code)
└── CC-BY-4.0.md# CC BY 4.0 (data, figures, manuscript)
```

**Not included** (by design): the raw report PDFs (~3 GB; re-downloadable via
`cenipa.py`), the per-report extracted JSON (large; regenerable), and any
third-party copyrighted material (cited articles, the journal's author guide).

## Data sources

- **CENIPA open data** (occurrences, aircraft, occurrence types, contributing
  factors): https://dados.gov.br/dados/conjuntos-dados/ocorrencias-aeronauticas-da-aviacao-civil-brasileira
- **CENIPA final reports** (PDF): https://sistema.cenipa.fab.mil.br/cenipa/paginas/relatorios/relatorios.php
  (behind Cloudflare Turnstile; `cenipa.py` uses Camoufox to access them).

## Reproducing the study

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

### Re-run the analysis only (no large downloads)
The de-identified `dataset_analitico.csv` is included, so you can reproduce all
results, tables and figures directly:

```bash
python analise.py        # → resultados.md + figuras/*.png (300 dpi)
python gerar_docx.py     # → manuscrito.docx
```

### Full pipeline from scratch
Requires a graphical display (the scraper opens a real browser; click the
Cloudflare checkbox if prompted) and downloads ~3 GB of PDFs.

```bash
python -m camoufox fetch          # one-time: fetch the anti-detection browser
python cenipa.py                  # 1. scrape final reports (PDFs) + links_reais.json
python extrair_pdfs.py            # 2. PDF → extraidos/*.json (sectioned text)
python extrair_horas.py           # 3. parse PIC flight hours → horas_voo.json
python montar_dataset_v2.py       # 4. build dataset_analitico.csv (+ codebook.md)
python analise.py                 # 5. statistics + figures → resultados.md
python gerar_docx.py              # 6. manuscript → manuscrito.docx
```

Notes on method: the CENIPA site is protected by Cloudflare Turnstile; the
scraper uses **Camoufox** (an anti-detection Firefox). Earlier attempts with
Playwright/Patchright did not pass the challenge. Report-PDF URLs are irregular,
so links are scraped from the results table rather than guessed.

## How to cite

See [`CITATION.cff`](CITATION.cff). The manuscript bibliography is in
[`referencias.bib`](referencias.bib).

## License

- **Source code** (`*.py`): MIT — see [`LICENSE`](LICENSE).
- **Manuscript, figures, derived data**: CC BY 4.0 — see
  [`CC-BY-4.0.md`](CC-BY-4.0.md).
- **Underlying CENIPA CSVs**: Brazilian government open data (public).

## Use of generative AI

Code, data-extraction pipeline, statistical scripting and language editing were
developed with the assistance of a large language model (Anthropic Claude). All
outputs were reviewed and validated by the author, who takes full responsibility
for the content. This disclosure is also included in the manuscript.

## Author

**Daniel Marques** — Admin@danielmarques.org · GitHub [@olegantonov](https://github.com/olegantonov)
