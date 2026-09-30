#!/bin/bash
# Descarrega les liquidacions i pressuposts del Ministeri d'Hisenda (CONPREL) per un rang d'anys,
# filtra les entitats de les Illes Balears (codi d'entitat que comença per "07") i les guarda
# a balears_entities.csv / balears_liquidacio.csv / balears_pressupost_inicial.csv en aquesta carpeta.
# Els fitxers .accdb originals (grans, tot Espanya) NO es guarden: s'esborren després de processar cada any.
set -e

DOWNLOAD_DIR="${DOWNLOAD_DIR:-/tmp/hacienda-download}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$DOWNLOAD_DIR"

YEARS="${1:-2016 2017 2018 2019 2020 2021 2022 2023 2024}"

for YEAR in $YEARS; do
  echo "=== Any $YEAR ==="
  cd "$DOWNLOAD_DIR"

  echo "Descarregant liquidacions $YEAR..."
  curl -fsSL -o "Liquidaciones${YEAR}.zip" "https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero?CCAA=&TipoDato=Liquidaciones&Ejercicio=${YEAR}&TipoPublicacion=Access"
  unzip -o -q "Liquidaciones${YEAR}.zip"
  rm "Liquidaciones${YEAR}.zip"

  echo "Descarregant pressuposts $YEAR..."
  curl -fsSL -o "Presupuestos${YEAR}.zip" "https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero?CCAA=&TipoDato=Presupuestos&Ejercicio=${YEAR}&TipoPublicacion=Access" || echo "  (sense pressuposts per $YEAR)"
  if [ -f "Presupuestos${YEAR}.zip" ]; then
    unzip -o -q "Presupuestos${YEAR}.zip"
    rm "Presupuestos${YEAR}.zip"
  fi

  echo "Processant $YEAR..."
  python3 "$SCRIPT_DIR/process_year.py" "$YEAR" "$DOWNLOAD_DIR"

  rm -f "$DOWNLOAD_DIR/Liquidaciones${YEAR}.accdb" "$DOWNLOAD_DIR/Presupuestos${YEAR}.accdb" "$DOWNLOAD_DIR/Liquidaciones${YEAR}.mdb" "$DOWNLOAD_DIR/Presupuestos${YEAR}.mdb"
done

echo "Fet. Resultats a $SCRIPT_DIR/balears_*.csv"
