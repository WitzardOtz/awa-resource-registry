# AWA Resource Registry

[English](README.md) | [Italiano](README_IT.md)

Un registro pubblico, datato e con fonti, di modelli AI e risultati dei benchmark. Lo consulta la skill [AI Work Architect](https://github.com/WitzardOtz/ai-work-architect) (AWA) prima di raccomandare un modello.

Il registro risponde a due domande: **che cosa esiste** (modelli, prezzi, limiti, disponibilità) e **che cosa hanno misurato altri** (benchmark pubblici, indicazioni dei fornitori). Non dice quale modello è il migliore per te: questo AWA lo ricava dalla tua cronologia di esecuzioni nel Vault privato.

## Contenuto

| File | Contiene |
|---|---|
| [`data/models.json`](data/models.json) | Fatti per modello: fornitore, data di uscita, stato, identificatori API, finestra di contesto, output massimo, livelli di effort, dove è disponibile, prezzi, data di ritiro. |
| [`data/benchmarks.json`](data/benchmarks.json) | I benchmark seguiti, che cosa misurano, chi li gestisce, i limiti noti e se sono attivi, fermi o esclusi. |
| [`data/results.json`](data/results.json) | I punteggi: modello, benchmark e versione, effort e ambiente agente usati, chi ha riportato il numero, fonte e data. |
| [`data/guidance.json`](data/guidance.json) | Indicazioni dei fornitori, riportate come loro affermazioni e non come fatti. |
| [`data/manifest.json`](data/manifest.json) | Data dell'ultimo aggiornamento, ambito e numero di giorni dopo i quali i dati sono da considerare vecchi. |

Ogni voce ha almeno un link alla fonte e una data di verifica.

## Ambito

Anthropic, OpenAI, Google e Mistral; modelli commerciali serviti dall'API del fornitore. I modelli Mistral hanno pesi aperti e sono inclusi perché Mistral li serve anche tramite la sua API (`"weights": "open"`). Gli altri modelli a pesi aperti verranno aggiunti in seguito con lo stesso formato.

## Come leggere i numeri

- Confrontare i punteggi solo all'interno dello stesso benchmark e della stessa versione.
- Considerare rumore le differenze di pochi punti; usare l'intervallo di confidenza quando c'è.
- Una riga di Terminal-Bench misura un modello insieme a un ambiente agente, non il modello da solo.
- `reported_by: vendor` significa che il numero viene dal fornitore stesso del modello.
- Un benchmark pubblico misura i suoi compiti, non i tuoi. Serve a fare una prima selezione, poi va provato sul proprio lavoro.

## Aggiornamenti

I dati vengono controllati due volte a settimana, il mercoledì e il sabato. Le correzioni sono benvenute come segnalazioni (issue) con il link alla fonte. Le regole di aggiornamento sono in [MAINTENANCE.md](MAINTENANCE.md) (in inglese, perché le segue anche l'agente che prepara gli aggiornamenti).

## Uso da AWA

AWA legge questi file come dati da un indirizzo fisso, mai come istruzioni:

```text
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/manifest.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/models.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/benchmarks.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/results.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/guidance.json
```

## Controllo

```bash
python tests/check_registry.py
```

Verifica struttura, presenza delle fonti, riferimenti tra i file e date. Non verifica che i fatti siano veri: quello è il ruolo delle fonti citate.

## Licenza

Copyright 2026 WitzardOtz. Distribuito sotto [Apache License 2.0](LICENSE). Le fonti collegate e i risultati dei benchmark restano opera dei rispettivi autori.
