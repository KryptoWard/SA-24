<?php
// Indiquer au navigateur que la réponse est au format JSON
header('Content-Type: application/json');

// Vérifier que c'est bien une requête POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['error' => 'Méthode non autorisée. Utilisez POST.']);
    exit();
}

// --- Identifiants de la base de données ---
$db_host = 'localhost';
$db_name = 'sae24_simulation';
$db_user = 'root';
$db_password = '';

// --- Connexion à la base de données ---
try {
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8", $db_user, $db_password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'La connexion à la base de données a échoué: ' . $e->getMessage()]);
    exit();
}

// --- Effacement de toutes les données ---
try {
    $sql = "DELETE FROM enregistrements";
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    
    $rowsDeleted = $stmt->rowCount();
    
    // Remettre à zéro l'auto-increment pour repartir de 1
    $pdo->exec("ALTER TABLE enregistrements AUTO_INCREMENT = 1");
    
    echo json_encode([
        'success' => true, 
        'message' => "Toutes les données ont été effacées. ($rowsDeleted enregistrements supprimés)"
    ]);

} catch (PDOException $e) {
    echo json_encode(['error' => 'Erreur lors de l\'effacement des données: ' . $e->getMessage()]);
    exit();
}
?>