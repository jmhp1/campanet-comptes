ALTER TABLE liquidacio_capitols ADD COLUMN codi_ine TEXT;
ALTER TABLE pressupost_inicial_capitols ADD COLUMN codi_ine TEXT;
UPDATE liquidacio_capitols SET codi_ine = '07012AA000' WHERE municipi = 'Campanet';
UPDATE pressupost_inicial_capitols SET codi_ine = '07012AA000' WHERE municipi = 'Campanet';
ALTER TABLE romanent_tresoreria ADD COLUMN codi_ine TEXT;
UPDATE romanent_tresoreria SET codi_ine = '07012AA000' WHERE municipi = 'Campanet';
CREATE TABLE municipis (
  codi_ine TEXT PRIMARY KEY,
  nom TEXT NOT NULL,
  illa TEXT NOT NULL DEFAULT 'Mallorca',
  poblacio INTEGER
);
