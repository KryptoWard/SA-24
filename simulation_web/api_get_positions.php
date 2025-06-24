<?php
// API endpoint returning the last recorded positions
// stored in the database, optionally filtered by type.
// It exposes recent ultrason or sound data to the web
// interface and can return both lists at once.
// Results are encoded as JSON.
// Indiquer au navigateur que la réponse est au format JSON
header('Content-Type: application/json');

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

// --- Récupération du paramètre de type ---
$type_filter = isset($_GET['type']) ? $_GET['type'] : 'all';

// --- Construction de la requête selon le type demandé ---
if ($type_filter === 'ultrason') {
    $sql = "SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp
            FROM (
                SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp, id 
                FROM enregistrements 
                WHERE source_type = 'ultrason'
                ORDER BY id DESC 
                LIMIT 5
            ) AS sub
            ORDER BY sub.id ASC";
} elseif ($type_filter === 'son') {
    $sql = "SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp
            FROM (
                SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp, id 
                FROM enregistrements 
                WHERE source_type = 'son'
                ORDER BY id DESC 
                LIMIT 5
            ) AS sub
            ORDER BY sub.id ASC";
} else {
    // Retourner les deux types séparément
    $sql_ultrason = "SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp
                     FROM (
                         SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp, id 
                         FROM enregistrements 
                         WHERE source_type = 'ultrason'
                         ORDER BY id DESC 
                         LIMIT 5
                     ) AS sub
                     ORDER BY sub.id ASC";
    
    $sql_son = "SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp
                FROM (
                    SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, source_type, timestamp, id 
                    FROM enregistrements 
                    WHERE source_type = 'son'
                    ORDER BY id DESC 
                    LIMIT 5
                ) AS sub
                ORDER BY sub.id ASC";
}

try {
    if ($type_filter === 'all') {
        // Récupérer les deux types séparément
        $stmt_ultrason = $pdo->query($sql_ultrason);
        $positions_ultrason = $stmt_ultrason->fetchAll(PDO::FETCH_ASSOC);
        
        $stmt_son = $pdo->query($sql_son);
        $positions_son = $stmt_son->fetchAll(PDO::FETCH_ASSOC);
        
        // Retourner un objet avec les deux types
        echo json_encode([
            'ultrason' => $positions_ultrason,
            'son' => $positions_son
        ]);
    } else {
        // Retourner un seul type
        $stmt = $pdo->query($sql);
        $positions = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode($positions);
    }

} catch (PDOException $e) {
    echo json_encode(['error' => 'Erreur lors de la récupération des données: ' . $e->getMessage()]);
    exit();
}
?>