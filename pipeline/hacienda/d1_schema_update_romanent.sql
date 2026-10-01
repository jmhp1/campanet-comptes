ALTER TABLE romanent_tresoreria ADD COLUMN codi_ine TEXT;
UPDATE romanent_tresoreria SET codi_ine = '07012AA000' WHERE municipi = 'Campanet';
