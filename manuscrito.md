# Pilot flight experience and accident severity in Brazilian general aviation: a register-based analysis of CENIPA final reports (2007–2024)

**Authors:** Daniel Marques¹*

¹ [Affiliation — institution, city, country]
\* Corresponding author. E-mail: Admin@danielmarques.org

---

## Highlights
- 824 Brazilian general-aviation airplane accidents (2007–2024) were analysed.
- Pilot total flight hours were not associated with accident fatality.
- Experience specific to the aircraft type was protective (OR 0.81 per ln-hour).
- Flight phase and type of operation were the dominant severity predictors.
- Accidents with human contributing factors were four times as lethal.

---

## Abstract

**Background and objective.** Pilot flight experience is widely assumed to protect against aviation accidents, an idea popularised as the general-aviation (GA) "killing zone". Most evidence is rate-based and drawn from high-income countries, and Brazilian research has been predominantly qualitative. We examined whether the flight experience of the pilot-in-command (PIC) is associated with the **severity** of GA accidents in Brazil.

**Methods.** We assembled a register-based cross-sectional dataset of fixed-wing GA accidents investigated by the Brazilian Aeronautical Accident Investigation and Prevention Center (CENIPA) between 2007 and 2024. PIC flight hours (total, in-type and recent) were extracted from 3,075 final reports and linked to CENIPA open data on occurrences, aircraft and contributing factors. The outcome was a fatal accident (≥1 on-board fatality). Multivariable logistic regression estimated the adjusted association of log-transformed PIC hours with fatality, controlling for type of operation, flight phase, engine type and number, and year; nonlinearity was assessed with natural cubic splines. Robustness was tested with multiple imputation, an alternative outcome (aircraft destroyed), and an in-type-experience model.

**Results.** Of 824 accidents, 197 (23.9%) were fatal. PIC total flight hours were identical between fatal and non-fatal accidents (median 1,300 vs 1,300 h; p=0.99) and were not associated with fatality after adjustment (odds ratio [OR] per natural-log hour 0.91, 95% CI 0.82–1.02; p=0.10), with no nonlinear "killing-zone" signature (likelihood-ratio p=0.09). In contrast, experience **specific to the accident aircraft type** was protective: each natural-log increase in in-type hours lowered the odds of a fatal outcome by 19% (OR 0.81, 95% CI 0.72–0.92; p=0.001). Severity was dominated by flight phase (cruise OR 4.7, manoeuvre OR 6.5, other OR 8.5 vs approach/landing) and by operation (agricultural OR 0.49, instruction OR 0.32 vs private). Accidents in which human contributing factors were identified were four times as lethal as those without (40% vs 10%). Findings were stable across sensitivity analyses (AUC 0.72; good calibration).

**Conclusions.** In Brazilian GA, the PIC's **total** logged experience did not predict whether an accident was fatal, whereas experience **in the accident aircraft type** did. Severity was governed by the energy state implied by flight phase and by operational context, and was strongly associated with human contributing factors. Prevention should prioritise type currency over raw logbook totals and target high-energy phases and human-factor pathways. Because the analysis conditions on accidents (severity), it does not address accident occurrence, which requires exposure data unavailable in the registry.

**Keywords:** general aviation; accident severity; pilot experience; flight hours; logistic regression; CENIPA

---

## 1. Introduction

General aviation (GA) accounts for the overwhelming majority of civil aviation accidents and fatalities worldwide [4,16] and comprises the bulk of the civil aircraft fleet [21], even as commercial aviation safety is closely monitored and comparatively strong worldwide [22]. A long-standing tenet of flight safety holds that risk is highest early in a pilot's career and declines as experience accrues — an idea popularised as the "killing zone" and formalised in rate-based analyses linking accident frequency to total flight hours [1,2]. Subsequent work has questioned both the location and the shape of this relationship, suggesting that elevated individual risk may extend well beyond the early hundreds of hours and that the hours–risk function is markedly nonlinear [1]. Importantly, some large studies have found that greater pilot experience and older age are associated with *higher*, not lower, odds of a **fatal** outcome once an accident has occurred [3], and pilot qualification and recency — rather than raw totals — have been shown to differentiate GA accident profiles [17], underscoring that accident *occurrence* and accident *severity* are distinct phenomena that need not share the same relationship with experience.

A parallel and rapidly growing strand of work applies machine learning and risk-scoring to predict accident severity or fatality from large registries [13,14,18], achieving useful discrimination but offering limited interpretability and resting almost entirely on North-American or multi-country data. Most of this evidence derives from the United States, where exposure denominators (active pilots and flight hours by experience band) support the calculation of accident rates. Evidence from Brazil — which has one of the largest GA fleets in the Global South — is comparatively scarce and predominantly qualitative or framework-based: studies have applied the Human Factors Analysis and Classification System (HFACS) [5,6] to individual CENIPA investigations [8] and have shown that Brazilian reports emphasise individual and operational factors while under-representing organisational ones [7]. Recent systematic reviews of GA safety likewise identify human factors, training deficiencies, pilot characteristics and flight phase as the dominant themes, but draw almost exclusively on high-income settings [4]. To our knowledge, no large-sample quantitative study has tested whether the flight experience of the pilot-in-command (PIC) is associated with the severity of GA accidents in Brazil.

We address this gap using the full archive of final reports published by CENIPA, linked to the national open-accident dataset. Because that dataset records investigated occurrences but not the underlying flying population, accident *rates* by experience level cannot be computed without an exposure denominator. We therefore frame the question in terms of **severity conditional on an accident**, a self-contained design that does not require exposure data: among GA airplane accidents, does the PIC's flight experience predict whether the accident is fatal? We further examine whether any association is linear or follows the nonlinear pattern implied by the killing-zone literature, whether aircraft-type-specific experience behaves differently from total logged time, and how severity relates to the contributing factors coded by investigators.

## 2. Material and methods

### 2.1. Data source
CENIPA investigates civil aviation occurrences in accordance with ICAO Annex 13 [11] and publishes the final report of each as a PDF, alongside a structured open-data extract (occurrence, aircraft, occurrence-type and contributing-factor tables) distributed through the Brazilian open-data portal. We retrieved the complete set of published final reports (n=3,075) and the open-data tables, which span occurrences from 2007 to 2025; the analytic period is 2007–2024 (complete years with linkable reports).

### 2.2. Study sample
The unit of analysis was the accident aircraft. We included fixed-wing airplanes involved in events classified by CENIPA as *accidents* and operating in general aviation — private, instructional, agricultural, experimental, or air-taxi operations. Rotorcraft, ultralights, gliders and scheduled air-transport operations were excluded to obtain an operationally homogeneous sample comparable to the international GA literature.

### 2.3. Extraction of pilot flight experience
PIC flight experience is reported in the narrative of CENIPA final reports rather than in the structured extract. We parsed the standardised "Flight Hours" table (section 1.5.1 of the report template), which records, for each crew member, total hours, hours in the accident aircraft type, and hours in the preceding 30 days and 24 hours. For multi-crew reports the PIC column was selected by a role-priority rule; where no table was present, total and in-type hours were recovered from free text. Values in HH:MM were converted to decimal hours and implausible zeroes treated as missing. Extraction accuracy was assessed by comparing parsed totals against an independent regular-expression reading on table-sourced records, yielding 98.6% concordance; residual discrepancies were concentrated in multi-crew reports, where the structured parser correctly resolved the PIC column.

### 2.4. Linkage and variables
Reports were linked to the structured records using a cascade of keys (final-report number; aircraft registration plus occurrence date; registration plus year; unique registration). The primary **outcome** was a fatal accident (≥1 on-board fatality); the secondary outcome was aircraft *destroyed*. The primary **exposure** was PIC total flight hours (natural-log transformed, ln[hours+1]); secondary exposures were in-type hours and 30-day recency. **Covariates**, selected a priori for their established relevance to accident severity [3,4], were type of operation, flight phase (grouped as approach/landing, take-off/climb, cruise, manoeuvre/specialised, and other/undetermined), engine type (piston vs turbine), engine number (single vs multi), and occurrence year. We additionally linked CENIPA's coded **contributing factors**, summarised as the presence of any human, operational, or material factor. The full variable dictionary is provided as a supplementary codebook.

### 2.5. Statistical analysis
Characteristics were compared between fatal and non-fatal accidents using the Mann–Whitney U test for continuous variables and proportions for categorical variables. To illustrate confounding by operation, median PIC hours were tabulated by operation and outcome. The primary analysis was a multivariable logistic regression of fatality on log PIC total hours plus the covariates above; results are reported as odds ratios (OR) with 95% confidence intervals (CI). Nonlinearity was assessed by adding a natural cubic spline (4 degrees of freedom) and comparing models by likelihood-ratio test [9]. Model performance was summarised by McFadden's pseudo-R², the area under the ROC curve (AUC), and the Hosmer–Lemeshow test; multicollinearity was checked with variance inflation factors (VIF). Robustness was evaluated by (i) excluding instructional flights (where the PIC is the instructor under dual control), (ii) modelling the *destroyed* outcome, (iii) substituting in-type for total hours, and (iv) multiple imputation of missing hours (10 imputations, Rubin's rules) [10]. Analyses used Python 3.12 (statsmodels 0.14, scikit-learn 1.8).

### 2.6. Ethics
The study used publicly available, de-identified aggregate accident records published by CENIPA; no individually identifiable personal data were accessed, and no human participants were involved. Under Brazilian research-ethics norms, secondary analysis of such public records does not require institutional review board approval.

## 3. Results

### 3.1. Sample characteristics
After restriction to in-scope GA airplane accidents with extractable PIC hours and linkage to covariates, 824 accidents were analysed, of which 197 (23.9%) were fatal. PIC total hours were available for 805 (97.7%), in-type hours for 553 (67.1%), and coded contributing factors for 750 (91.0%). Private flying was the most common operation (347), followed by agricultural (238), instruction (145) and air-taxi (91). Table 1 summarises characteristics by outcome.

PIC total flight hours did **not** differ between fatal and non-fatal accidents (median 1,300 h in both; p=0.99), and fatality varied little across experience bands (24%, 21%, 29%, 25% and 23% from <100 to ≥5,000 h; Fig. 1). In contrast, in-type hours were markedly lower in fatal accidents (median 210 vs 400 h; p=0.004).

**Table 1.** Characteristics of 824 Brazilian general-aviation airplane accidents by outcome (2007–2024).

| Characteristic | Non-fatal (n=627) | Fatal (n=197) | p |
|---|---|---|---|
| PIC total hours, median [IQR] | 1,300 [343–4,455] | 1,300 [445–3,612] | 0.99 |
| PIC in-type hours, median [IQR] | 400 [104–1,275] | 210 [47–881] | 0.004 |
| Private flying, n (% fatal) | — | 101/347 (29%) | |
| Agricultural, n (% fatal) | — | 54/238 (23%) | |
| Instruction, n (% fatal) | — | 15/145 (10%) | |
| Air taxi, n (% fatal) | — | 27/91 (30%) | |
| Approach/landing, n (% fatal) | — | 25/263 (10%) | |
| Take-off/climb, n (% fatal) | — | 51/203 (25%) | |
| Cruise, n (% fatal) | — | 32/92 (35%) | |
| Manoeuvre/specialised, n (% fatal) | — | 45/165 (27%) | |
| Human contributing factor present, % fatal | 10% | 40% | <0.001 |

### 3.2. Confounding by operation
Median PIC hours and fatality moved in partly opposing directions across operations: air-taxi pilots were by far the most experienced (median ~5,000–6,700 h) yet had among the highest fatality (30%), whereas instructional flights involved the least-experienced PICs (median ~300–480 h) and the lowest fatality (10%). Within operations, more experienced PICs were generally involved in *less* severe accidents (e.g., private flying: median 1,000 h in fatal vs 1,200 h in non-fatal; agricultural: 1,300 vs 1,700 h). This pattern of opposing within- and between-group associations (Fig. 4) indicates confounding by operation that flattens the crude relationship, and motivates multivariable adjustment.

### 3.3. Primary model: total flight hours and fatality
In the complete-case model (n=801; 196 fatal events), log PIC total hours were not significantly associated with fatality (OR per natural-log hour 0.91, 95% CI 0.82–1.02, p=0.10; OR 0.94 per doubling of hours) (Table 2). Adding a natural cubic spline did not significantly improve fit (likelihood-ratio χ²=4.73, df=2, p=0.09), giving no clear "killing-zone" pattern for severity (Fig. 2). Severity was instead strongly associated with flight phase — relative to approach/landing, the odds of a fatal outcome were roughly four- to nine-fold higher in take-off/climb, cruise, manoeuvre and other phases — and with operation, agricultural and instructional flights having markedly lower odds of fatality than private flying. The model discriminated moderately (AUC 0.72), was well calibrated (Hosmer–Lemeshow p=0.41), and showed no problematic collinearity (maximum VIF 2.05).

**Table 2.** Adjusted odds ratios for a fatal accident (multivariable logistic regression; n=801).

| Predictor | OR | 95% CI | p |
|---|---|---|---|
| PIC total hours (per ln-hour) | 0.91 | 0.82–1.02 | 0.10 |
| Operation: agricultural (vs private) | 0.49 | 0.29–0.83 | 0.008 |
| Operation: instruction (vs private) | 0.32 | 0.17–0.61 | 0.001 |
| Operation: air taxi (vs private) | 0.92 | 0.51–1.66 | 0.78 |
| Phase: cruise (vs approach/landing) | 4.73 | 2.53–8.86 | <0.001 |
| Phase: take-off/climb | 3.73 | 2.15–6.46 | <0.001 |
| Phase: manoeuvre/specialised | 6.45 | 3.28–12.67 | <0.001 |
| Phase: other/undetermined | 8.54 | 4.66–15.65 | <0.001 |
| Turbine (vs piston) | 1.55 | 0.94–2.56 | 0.09 |
| Multi-engine | 1.51 | 0.92–2.49 | 0.10 |
| Year (per year) | 0.98 | 0.94–1.02 | 0.30 |

### 3.4. Type-specific experience
Using aircraft-type-specific experience (n=552; 139 events), each natural-log increase in in-type hours was associated with 19% lower odds of a fatal accident (OR 0.81, 95% CI 0.72–0.92, p=0.001; ≈13% lower odds per doubling) (Fig. 5). When total and in-type hours were entered together, both retained a protective direction of similar size (total OR 0.84, p=0.07; in-type OR 0.87, p=0.05), consistent with the two correlated measures sharing a protective signal that is carried more cleanly by in-type time.

### 3.5. Contributing factors
Among the 750 accidents with coded contributing factors, an operational factor was identified in 96% and a human factor in 50%; material factors were rare (3%). The probability of a human factor being coded did not vary with PIC total experience (OR 0.97 per ln-hour, p=0.50), i.e., experienced pilots were no less likely to have human-factor accidents. However, accidents in which a human factor was identified were four times as lethal as those without (40% vs 10% fatal), highlighting human-factor pathways — rather than experience level *per se* — as the more salient severity correlate.

### 3.6. Sensitivity analyses
Results were robust. Excluding instructional flights left the total-hours estimate unchanged (OR 0.91, 95% CI 0.82–1.02). Modelling aircraft *destroyed* gave a similar total-hours association (OR 0.93, 95% CI 0.82–1.04). Multiple imputation of missing hours (missingness 2.3%) reproduced the complete-case estimate (OR 0.99, 95% CI 0.93–1.05). The in-type protective association persisted throughout.

## 4. Discussion

In a national sample of 824 Brazilian GA airplane accidents spanning 2007–2024, the pilot-in-command's **total** logged flight experience did not predict whether an accident was fatal, and no nonlinear killing-zone pattern was evident. The protective signal lay instead with experience **specific to the accident aircraft type**, which lowered the odds of a fatal outcome by roughly a fifth per natural-log hour. Severity was governed chiefly by the energy state implied by flight phase — fatalities concentrated in cruise, manoeuvre and take-off/climb and were uncommon in approach/landing — and by operational context, with agricultural and instructional flying far less lethal than private flying. Accidents attributed in part to human factors were four times as lethal as those without, even though the likelihood of a human-factor attribution did not vary with experience.

These findings are coherent with the distinction between accident *occurrence* and accident *severity*. The killing-zone literature concerns occurrence **rates**, which fall as low-time pilots accumulate hours [1,2]; our design conditions on the occurrence of an accident and asks a different question about outcome. Viewed this way, our results align with large US analyses reporting that, once an accident happens, greater **total** experience does not reduce the odds of a fatal outcome [3]. The novel and arguably more actionable contrast we add is between total and type-specific experience: familiarity with the accident aircraft — a proxy for the distinction between currency and proficiency long emphasised by the GA community [20] — was protective where raw logbook totals were not, consistent with evidence that recency and qualification differentiate GA accident outcomes [17]. The dominance of flight phase echoes the consistent identification of phase as a leading severity determinant in the GA literature [4,13], and loss of control in cruise and manoeuvring flight — the phases we found most lethal — remains the leading fatal GA scenario internationally [15]. The lethality of human-factor accidents is, in turn, consistent with the central role of human performance in Brazilian investigations [7,8].

The between- versus within-operation reversal we observed is a textbook instance of confounding (Simpson's paradox): air-taxi PICs are highly experienced yet fly higher-energy operations with worse outcomes, while instructional flights pair low-time PICs with low-energy, closely supervised profiles. Crude comparisons of experience and severity in GA are therefore liable to mislead unless operation and phase are controlled — a methodological caution for safety analysts working with accident registries.

For prevention, the results argue against treating logged hours as a proxy for survivability and in favour of type-specific and recency-based training requirements over raw hour thresholds — aligned with currency-oriented regulatory guidance such as flight reviews and proficiency checks [19] — together with targeting the conditions that make accidents lethal: loss of control in cruise and manoeuvring flight, take-off/climb performance management, and operation-specific hazards (notably agricultural and air-taxi exposure).

**Limitations.** First, the design addresses severity conditional on an accident, not accident occurrence; because the registry lacks an exposure denominator, we cannot estimate how experience affects the probability of having an accident. Second, flight hours were extracted from investigation narratives; although concordance with independent reading was high (98.6%) and missingness on total hours was low (2.3%), in-type and recency data were less complete. Third, the analysis is restricted to published, text-based final reports; reports lacking machine-readable text (largely older, scanned documents) were not covered, introducing potential selection. Fourth, contributing-factor coding reflects investigators' judgement and is more thorough for fatal events, so the human-factor–lethality association is descriptive and may be partly artefactual. Finally, residual confounding (e.g., weather, terrain, pilot age) is possible, and findings pertain to Brazilian fixed-wing GA.

## 5. Conclusions
Among Brazilian general-aviation airplane accidents from 2007 to 2024, the pilot-in-command's total flight experience was not associated with accident severity, and no killing-zone nonlinearity was evident; experience specific to the aircraft type, by contrast, was protective. Accident lethality was determined principally by flight phase and type of operation and was strongly associated with human contributing factors. Safety efforts in Brazilian GA should value type currency over raw logbook totals and concentrate on high-energy phases of flight and human-factor pathways. Extending the analysis with exposure data to estimate accident rates is a priority for future work.

---

## Authors' contribution (CRediT)
**Daniel Marques:** Conceptualization, Methodology, Software, Formal analysis, Data curation, Writing – original draft, Writing – review & editing, Visualization.

## Declaration of competing interest
The author declares no competing interests.

## Funding
This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Data availability
The underlying CENIPA final reports and open-data tables are publicly available [12]. The derived analytic dataset, variable codebook, and analysis code are available from the author and will be deposited in a public repository (e.g., Mendeley Data) upon acceptance.

## Declaration of generative AI use
During the preparation of this work the author used a large language model (Anthropic Claude) to assist with data-extraction code, statistical-analysis scripting, and language editing. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication.

## References
[1] Knecht WR. The "killing zone" revisited: serial nonlinearities predict general aviation accident rates from pilot total flight hours. Accid Anal Prev. 2013;60:50–56. doi:10.1016/j.aap.2013.08.012
[2] Knecht WR. Predicting accident rates from general aviation pilot total flight hours. DOT/FAA/AM-15/3. Washington, DC: FAA Office of Aerospace Medicine; 2015.
[3] Bazargan M, Guzhva VS. Impact of gender, age and experience of pilots on general aviation accidents. Accid Anal Prev. 2011;43(3):962–970. doi:10.1016/j.aap.2010.11.023
[4] Sheffield E, Lee S-Y, Zhang Y. A systematic review of general aviation accident factors, effects and prevention. J Air Transp Manag. 2025;128:102859. doi:10.1016/j.jairtraman.2025.102859
[5] Shappell SA, Wiegmann DA. The Human Factors Analysis and Classification System – HFACS. DOT/FAA/AM-00/7. Oklahoma City, OK: FAA Civil Aeromedical Institute; 2000.
[6] Wiegmann DA, Shappell SA. Human error analysis of commercial aviation accidents: application of the Human Factors Analysis and Classification System (HFACS). Aviat Space Environ Med. 2001;72(11):1006–1016.
[7] Fajer M, de Almeida IM, Fischer FM. Contributive factors to aviation accidents. Rev Saúde Pública. 2011;45(2):432–435. doi:10.1590/S0034-89102011005000003
[8] Mendonça FAC, Huang C, Carney TQ, Johnson ME. A case study using the Human Factors Analysis and Classification System (HFACS) to analyze an aircraft accident investigated by CENIPA. In: Proc. 19th Int. Symp. Aviation Psychology; 2017. p. 209–214.
[9] Harrell FE. Regression modeling strategies. 2nd ed. Cham: Springer; 2015. doi:10.1007/978-3-319-19425-7
[10] Sterne JAC, White IR, Carlin JB, et al. Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls. BMJ. 2009;338:b2393. doi:10.1136/bmj.b2393
[11] International Civil Aviation Organization. Annex 13 to the Convention on International Civil Aviation: Aircraft Accident and Incident Investigation. 12th ed. Montréal: ICAO; 2020.
[12] Centro de Investigação e Prevenção de Acidentes Aeronáuticos (CENIPA). Aeronautical occurrences in Brazilian civil aviation (open data) and final reports. https://dados.gov.br/dados/conjuntos-dados/ocorrencias-aeronauticas-da-aviacao-civil-brasileira (accessed 2026).
[13] Silagyi DV, Liu D. Prediction of severity of aviation landing accidents using support vector machine models. Accid Anal Prev. 2023;187:107043. doi:10.1016/j.aap.2023.107043
[14] Omrani F, Etemadfard H, Shad R. Assessment of aviation accident datasets in severity prediction through machine learning. J Air Transp Manag. 2024;115:102531. doi:10.1016/j.jairtraman.2023.102531
[15] Majumdar N, Marais K. Human factors in general aviation loss of control: survey of pilot experiences. J Air Transp. 2025;33(1):57–68. doi:10.2514/1.D0432
[16] Boyd DD, Jin L. Static rate of failed equipment-related fatal accidents in general aviation. Safety. 2025;11(4):109. doi:10.3390/safety11040109
[17] Boyd DD, Scharf M, Cross D. A comparison of general aviation accidents involving airline pilots and instrument-rated private pilots. J Safety Res. 2021;76:127–134. doi:10.1016/j.jsr.2020.11.009
[18] Hinkelbein J, Hippler C, Liebold F, Schmitz J, Rothschild M, Schick V. A new scoring system to predict fatal accidents in General Aviation and to facilitate emergency control centre response. Sci Rep. 2024;14:27969. doi:10.1038/s41598-024-77994-3
[19] Federal Aviation Administration. Currency requirements and guidance for the flight review and instrument proficiency check. Advisory Circular AC 61-98E. Washington, DC: U.S. Department of Transportation, FAA; 2024.
[20] AOPA Air Safety Institute. Currency vs. proficiency. Frederick, MD: Aircraft Owners and Pilots Association; accessed 2026.
[21] Federal Aviation Administration. General aviation safety fact sheet. Washington, DC: U.S. Department of Transportation, FAA; 2025.
[22] International Civil Aviation Organization. State of global aviation safety: ICAO safety report, 2025 edition. Montréal: ICAO; 2025.

---
*Figures: Fig. 1 — crude fatality by experience band; Fig. 2 — adjusted predicted probability of a fatal accident vs total hours (spline), by operation; Fig. 3 — forest plot of adjusted odds ratios; Fig. 4 — median PIC hours by operation and outcome (confounding); Fig. 5 — adjusted predicted probability vs in-type vs total hours. Figure files in `figuras/`.*
