#!/bin/bash
# Descarrega els fitxers anuals de licitacions (totes les entitats d'Espanya, format ATOM/XML CODICE)
# de la Plataforma de Contractació del Sector Públic. Es filtraran pel NIF de cada municipi després.
# Fa servir -C - (represa) perquè les connexions es tallen sovint abans d'acabar.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/raw"
mkdir -p "$DIR"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
MAX_TRIES=12

for YEAR in 2016 2017 2018 2019 2020 2021 2022 2023 2024; do
  OUT="$DIR/licitacions_${YEAR}.zip"
  if [ -f "$OUT" ] && unzip -l "$OUT" >/dev/null 2>&1; then
    echo "=== $YEAR: ja descarregat i vàlid, salto ==="
    continue
  fi
  echo "=== Descarregant $YEAR ==="
  TRY=0
  while [ $TRY -lt $MAX_TRIES ]; do
    TRY=$((TRY+1))
    curl -s -k --http1.1 -A "$UA" --max-time 1200 -C - \
      -o "$OUT" \
      "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_${YEAR}.zip"
    if unzip -l "$OUT" >/dev/null 2>&1; then
      echo "=== $YEAR: OK intent $TRY ($(du -h "$OUT" | cut -f1)) ==="
      break
    else
      SZ=$(du -h "$OUT" 2>/dev/null | cut -f1)
      echo "=== $YEAR: intent $TRY incomplet (${SZ:-0}), reintentant amb represa ==="
      sleep 5
    fi
  done
  if ! unzip -l "$OUT" >/dev/null 2>&1; then
    echo "=== $YEAR: FALLAT definitivament després de $MAX_TRIES intents ==="
  fi
done
echo "=== TOT FET ==="
