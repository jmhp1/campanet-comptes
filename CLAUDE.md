# Els comptes de Campanet

Quadre de comandaments ciutadà sobre l'economia de l'Ajuntament de Campanet (Mallorca), 2016–2025: què es pressuposta, què s'executa, quant estalvi queda i a qui s'adjudiquen els contractes. Tot a partir de dades públiques oficials.

## Com treballar amb en Joan

- En Joan **no és programador**. Anau passa a passa, una cosa cada vegada.
- **Abans de cada passa, explicau què fareu i per què, amb paraules senzilles.** Esperau que digui que sí.
- Després de cada passa, confirmau què ha canviat i com ho pot comprovar ell mateix (per exemple, obrint una URL).
- No instal·leu res ni creeu cap compte sense avisar. Els passos que requereixen el seu compte (GitHub, Cloudflare) els fa ell, amb les vostres instruccions.
- Idioma: **català**, en to directe i proper. Ell escriu en mallorquí.
- Mai no poseu contrasenyes, tokens ni claus API dins el codi ni als commits.

## Què hi ha en aquesta carpeta

| Fitxer | Què és |
| --- | --- |
| `index.html` | El dashboard actual, autocontingut (HTML + CSS + JS, Chart.js per CDN). Ara mateix les dades hi són incrustades al codi. |
| `data/*.csv` | Totes les dades verificades, una taula per tema (vegeu el diccionari més avall). |
| `docs/Sollicitud_informacio_Ajuntament_Campanet.docx` | Petició d'informació enviada o per enviar a l'Ajuntament. |

## Pla del projecte (en aquest ordre)

1. **Repositori a GitHub** amb aquesta carpeta. Primer commit tal com està.
2. **Cloudflare Pages** connectat al repositori: cada `git push` publica la web automàticament.
3. **Base de dades SQL a Cloudflare D1**: crear-ne l'esquema a partir dels CSV (una taula per CSV, amb claus i tipus correctes) i carregar-hi les dades.
4. **Arxiu de documents a Cloudflare R2**: PDF dels comptes anuals i dels pressuposts, i els zips de dades obertes de contractació, perquè cada xifra pugui enllaçar al seu document original.
5. **Connectar el dashboard a les dades**: que `index.html` llegeixi les dades (primer dels CSV o d'un JSON generat, després de D1 a través d'un Worker) en lloc de tenir-les incrustades.
6. **Automatitzar la ingesta** de noves dades de contractació (vegeu «Contractació» més avall).

## Diccionari de dades (`data/`)

- `liquidacio_capitols.csv`: per any (2017–2024), costat (despesa/ingrés) i capítol, amb la previsió **inicial**, la **definitiva** i l'**executat** (obligacions reconegudes netes en despesa, drets reconeguts nets en ingrés). El capítol d'ingrés `i8` és romanent incorporat: no genera drets.
- `pressupost_inicial_capitols.csv`: pressupost inicial aprovat per capítol, 2016–2024. Pot diferir lleugerament de l'inicial de la liquidació (reclassificacions; per exemple, el 2024 hi ha 8.000 € d'«Equipaments culturals» que el pressupost posa a inversió i la liquidació al capítol 2).
- `pressupost_inicial_per_finalitat.csv`: pressupost inicial per política de despesa (o per àrea quan no hi ha més detall). És previsió, no execució.
- `resultat_pressupostari.csv`: resultat pressupostari, resultat ajustat, despesa pagada amb romanent i caixa a 31/12.
- `romanent_tresoreria.csv`: estat 24.6 de la memòria, 2016–2024. `despeses_generals` és l'estalvi que es pot gastar lliurement.
- `procediments_adjudicacio.csv`: import adjudicat per procediment (memòria, apartat 22).
- `contractes_plataforma.csv`: expedients de l'Ajuntament a la Plataforma de Contractació del Sector Públic (2018–2021 revisats), amb l'adjudicatari quan està publicat i el lligam amb la partida dels comptes.
- `projectes_inversio.csv`: annex d'inversions de cada pressupost (projectes anunciats).
- `serveis_recurrents.csv`: partides que cobra un tercer cada any.
- `governs.csv`: mandats municipals. 2015–juny 2019: MÉS per Campanet (majoria absoluta), batlessa Magdalena Solivellas. Juny 2019–juny 2023: PSIB-PSOE en minoria, batlessa Rosa Maria Bestard. Des de juny 2023: MÉS per Campanet en minoria, batle Guillem Rosselló.

Imports en euros corrents, amb decimals amb punt.

## Com s'han verificat les dades (no ho trenqueu)

- La liquidació per capítols s'ha agregat partida per partida des dels PDF dels comptes anuals. Per a cada any, la suma dels capítols quadra al cèntim amb els totals oficials (inicial, definitiu, obligacions i drets).
- Drets reconeguts − obligacions reconegudes = resultat pressupostari publicat, al cèntim.
- Romanent: components = total; total − dubtós − afectat = despeses generals; la columna comparativa de cada any coincideix amb l'any anterior.
- Si carregau o transformau dades, **tornau a fer aquestes comprovacions automàticament** (un script de tests) i avisau si alguna falla.

## Regles de disseny del dashboard

- Quatre colors amb significat fix: **verd** = saldo positiu o estalvi; **vermell** = dèficit o deutes; **gris** = pressupostat; **blau** = executat. No n'afegiu d'altres per a les dades.
- **Neutralitat.** Etiquetes descriptives, mai valoratives. Sense colors de partit. Cada xifra ha de poder enllaçar a la seva font. El dashboard ha de ser igual d'útil i creïble per a qualsevol persona, governi qui governi.
- Pestanyes actuals: Resum (xifres clau, diagrama de fluxos, qui governava), Ingressos i despeses, Pressupostat vs fet, Salut financera, Contractació, Fonts i mètode.
- Ha de funcionar bé al mòbil i en mode fosc.

## Fonts

- Pressuposts: https://ajcampanet.net/ca/pressuposts
- Comptes anuals 2017–2024 (2024 provisionals): https://ajcampanet.net/ca/comptes-anuals
- Dades obertes de contractació (Ministeri d'Hisenda): https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/licitaciones_plataforma_contratacion.aspx
- Formularis de pressupost al Ministeri: codi d'entitat 04-07-012-AA-000.

## Contractació: com se cerca

- Identificadors de l'Ajuntament: NIF **P0701200H**, DIR3 **L01070125**, òrgans a la Plataforma **31126200156380** (Ple), **31126210156381** (Junta de Govern), **31322900176050** (Batlia).
- Conjunt útil: «licitacionesPerfilesContratanteCompleto3_AAAA.zip» (fitxers ATOM/XML, esquema CODICE). Filtrar les entrades que contenen el NIF o el DIR3 i quedar-se amb la versió més recent de cada `entry/id`. Adjudicatari a `cac:TenderResult/cac:WinningParty`.
- Revisats sense resultats: contractes menors 2018–2024, plataformes agregades 2016–2021 i 2023. La Mancomunitat des Raiguer (NIF P0700005B) sí que hi publica; si s'inclou, ha d'anar separada i etiquetada.

## Pendent

- Zips de contractació (conjunt de licitacions) del 2022, 2023, 2024 i 2025.
- Resposta de l'Ajuntament a la petició d'informació: detall dels pressuposts 2016 i 2022, comptes 2024 definitius, liquidació 2025, relació de contractes amb NIF i relació de factures per proveïdor.
- Afegir el pressupost 2025 (prorrogat del 2024).
