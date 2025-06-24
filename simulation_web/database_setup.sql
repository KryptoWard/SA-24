-- SQL script that defines the table used to
-- store all simulation recordings. Run once to
-- prepare the MySQL database before launching
-- the simulator. Removes any old table and
-- recreates a new one with fields for distances,
-- raw values and estimated positions.
-- Supprime l'ancienne table si elle existe
DROP TABLE IF EXISTS enregistrements;

-- Crée la nouvelle structure de table
CREATE TABLE enregistrements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  source_type ENUM('ultrason', 'son') NOT NULL,
  dist_a DECIMAL(10, 4) NULL,
  dist_b DECIMAL(10, 4) NULL,
  dist_c DECIMAL(10, 4) NULL,
  valeur_brute_a DECIMAL(10, 4) NULL COMMENT 'Temps pour ultrason, Amplitude pour son',
  valeur_brute_b DECIMAL(10, 4) NULL COMMENT 'Temps pour ultrason, Amplitude pour son',
  valeur_brute_c DECIMAL(10, 4) NULL COMMENT 'Temps pour ultrason, Amplitude pour son',
  pos_x_estimee DECIMAL(10, 4) NOT NULL,
  pos_y_estimee DECIMAL(10, 4) NOT NULL
);