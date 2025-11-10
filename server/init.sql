-- Suppression des tables si elles existent déjà (pour pouvoir relancer le script)
DROP TABLE IF EXISTS "Client";
DROP TABLE IF EXISTS "Pizza";
DROP TABLE IF EXISTS "Production";

-- Création de la table Client
CREATE TABLE "Client" (
    "ID" INT PRIMARY KEY,
    "Distance" INT
);

-- Création de la table Pizza
CREATE TABLE "Pizza" (
    "Nom" TEXT,
    "Taille" TEXT,
    "Composition" TEXT,
    "TPsProd" INT,
    "Prix" INT,
    PRIMARY KEY ("Nom", "Taille")
);

-- Création de la table Production
CREATE TABLE "Production" (
    "Poste" INT PRIMARY KEY,
    "Capacite" INT,
    "Disponibilite" BOOL,
    "Taille" TEXT,
    "Restriction" TEXT
);

-- Insertion des données Clients
INSERT INTO "Client" ("ID", "Distance") VALUES
(529997, 12),
(530143, 24),
(529996, 24),
(530111, 12),
(530080, 15); -- Ajouté depuis l'exemple UDP pour les tests

-- Insertion des données Pizzas
INSERT INTO "Pizza" ("Nom", "Taille", "Composition", "TPsProd", "Prix") VALUES
('Veggie', 'G', 'JVBJ,VBJV,VVJJ,JJVV,BBJJ,VVVB', 7, 9),
('Calzone', 'M', '----,-VJ-,JVRR,RJJV,-JJ-,----', 7, 6),
('Margarita', 'G', 'RRJJ,JJBB,JJBB,RJBR,RRBB,JJRR', 6, 9),
('Reine', 'G', 'RJJV,VJJR,RJJV,VJJR,RRJJ,VVJR', 6, 8),
('Carnivore', 'G', 'RJRV,VRRJ,RRJV,VJRR,JRRV,VRRJ', 8, 12),
('Orientale', 'G', 'RJVB,BJJR,RVVB,JJBV,RRBJ,JBVR', 7, 10),
('Andalouse', 'G', 'RVVB,RJVB,JJBV,RRBJ,BJJR,JBVR', 11, 11),
('4_Fromages', 'G', 'JJJB,BJJJ,BJJB,BJBB,JJJB,BJJJ', 9, 12),
('Chevre', 'G', 'JJVB,BJJJ,JJVJ,BVJJ,JBBJ,JJJV', 7, 11),
('Chorizo', 'G', 'RRJJ,JJVV,VJRV,JRRV,JRRV,JRVR', 7, 10),
('Calzone', 'G', 'JJRV,RVJJ,JVRR,RJJV,VJJR,RJJV', 6, 8),
('Veggie', 'M', '----,-VJ-,BVJV,BJJV,-VB-,----', 7, 7),
('Margarita', 'M', '----,-JB-,JJBB,RJBR,-RB-,----', 5, 7),
('Reine', 'M', '----,-JJ-,RJJV,VJJR,-RJ-,----', 5, 6),
('Carnivore', 'M', '----,-RR-,RRJV,VJRR,-RR-,----', 7, 10),
('Orientale', 'M', '----,-JJ-,RVVB,JJBV,-RB-,----', 6, 8),
('Andalouse', 'M', '----,-JV-,JJBV,RRBJ,-JJ-,----', 10, 10),
('4_Fromages', 'M', '----,-JJ-,BJJB,BJBB,-JJ-,----', 9, 10),
('Chevre', 'M', '----,-JJ-,JJVJ,BVJJ,-BB-,----', 7, 8),
('Chorizo', 'M', '----,-JV-,VJRV,JRRV,-RR-,----', 6, 8);

-- Insertion des données Production
INSERT INTO "Production" ("Poste", "Capacite", "Disponibilite", "Taille", "Restriction") VALUES
(1, 30, TRUE, '', 'Veggie, Chevre'),
(5, 27, FALSE, 'M', '---'),
(3, 18, TRUE, 'G', 'Chevre, 4 Fromages'),
(4, 15, FALSE, '', '');