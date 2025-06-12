<?php
// Set the content type to application/json for the browser
header('Content-Type: application/json');

// --- Database Credentials ---
$db_host = 'localhost';
$db_name = 'sae24_simulation';
$db_user = 'root';
$db_password = '';

// --- Database Connection ---
try {
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8", $db_user, $db_password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit();
}

// --- Fetch Data ---
// MISE À JOUR : On sélectionne aussi les distances a, b, et c !
$sql = "SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c 
        FROM (
            SELECT pos_x_estimee, pos_y_estimee, dist_a, dist_b, dist_c, id 
            FROM enregistrements 
            ORDER BY id DESC 
            LIMIT 5
        ) AS sub
        ORDER BY sub.id ASC";

$stmt = $pdo->query($sql);
$positions = $stmt->fetchAll(PDO::FETCH_ASSOC);

// --- Return Data as JSON ---
echo json_encode($positions);

?>