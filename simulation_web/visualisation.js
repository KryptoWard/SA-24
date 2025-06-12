document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('simulationCanvas');
    const ctx = canvas.getContext('2d');
    const roomGrid = document.getElementById('roomGrid');
    const statusPanel = document.getElementById('statusPanel');
    const clearDbButton = document.getElementById('clearDbButton');

    const roomWidthMeters = 8.0;
    const roomHeightMeters = 8.0;

    const sensors = [
        { name: 'A', x: 0.25, y: 0.25, color: '#00FFFF' }, // Cyan
        { name: 'B', x: 0.25, y: 7.75, color: '#FF00FF' }, // Magenta
        { name: 'C', x: 7.75, y: 7.75, color: '#FFFF00' }  // Yellow
    ];

    function resizeCanvas() {
        canvas.width = roomGrid.clientWidth;
        canvas.height = roomGrid.clientHeight;
    }

    function toCanvasCoords(x_m, y_m) {
        const x_px = (x_m / roomWidthMeters) * canvas.width;
        const y_px = (y_m / roomHeightMeters) * canvas.height;
        return { x: x_px, y: y_px };
    }

    function drawBase() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        sensors.forEach(sensor => {
            const pos = toCanvasCoords(sensor.x, sensor.y);
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
            ctx.fillStyle = sensor.color;
            ctx.fill();
            ctx.strokeStyle = '#000';
            ctx.stroke();
            ctx.font = 'bold 12px Arial';
            ctx.fillStyle = '#000';
            ctx.fillText(sensor.name, pos.x + 10, pos.y + 5);
        });
    }

    // NOUVELLE FONCTION pour dessiner les cercles et distances
    function drawTrilaterationVisuals(lastPosition) {
        if (!lastPosition) return;
        const lastPosPx = toCanvasCoords(lastPosition.pos_x_estimee, lastPosition.pos_y_estimee);

        const distances = {
            A: lastPosition.dist_a,
            B: lastPosition.dist_b,
            C: lastPosition.dist_c
        };

        sensors.forEach(sensor => {
            const sensorPosPx = toCanvasCoords(sensor.x, sensor.y);
            const radius = distances[sensor.name];
            if (radius === null) return;

            const radiusPx = (radius / roomWidthMeters) * canvas.width;

            // Dessiner le cercle de distance
            ctx.beginPath();
            ctx.arc(sensorPosPx.x, sensorPosPx.y, radiusPx, 0, 2 * Math.PI);
            ctx.strokeStyle = sensor.color;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]); // Ligne en pointillés
            ctx.stroke();
            ctx.setLineDash([]); // Rétablir les lignes pleines

            // Dessiner la ligne du capteur au point
            ctx.beginPath();
            ctx.moveTo(sensorPosPx.x, sensorPosPx.y);
            ctx.lineTo(lastPosPx.x, lastPosPx.y);
            ctx.strokeStyle = sensor.color;
            ctx.lineWidth = 1;
            ctx.stroke();
        });
    }

    function drawPath(positions) {
        // Dessiner le tracé des 5 derniers points
        ctx.beginPath();
        ctx.strokeStyle = '#3498db';
        ctx.lineWidth = 3;
        const firstPos = toCanvasCoords(positions[0].pos_x_estimee, positions[0].pos_y_estimee);
        ctx.moveTo(firstPos.x, firstPos.y);
        positions.forEach(p => {
            const pos = toCanvasCoords(p.pos_x_estimee, p.pos_y_estimee);
            ctx.lineTo(pos.x, pos.y);
        });
        ctx.stroke();

        // Dessiner le point actuel (le dernier)
        const lastPosData = positions[positions.length - 1];
        const lastPos = toCanvasCoords(lastPosData.pos_x_estimee, lastPosData.pos_y_estimee);
        ctx.beginPath();
        ctx.arc(lastPos.x, lastPos.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = '#2ecc71'; // Vert
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.stroke();

        statusPanel.textContent = `Dernière position estimée : (${parseFloat(lastPosData.pos_x_estimee).toFixed(2)}, ${parseFloat(lastPosData.pos_y_estimee).toFixed(2)})`;
    }

    async function updateVisualization() {
        try {
            const response = await fetch('api_get_positions.php');
            const positions = await response.json();

            if (positions.error) {
                statusPanel.textContent = `Erreur: ${positions.error}`;
                return;
            }

            drawBase();

            if (positions.length > 0) {
                // On passe le dernier point pour dessiner les cercles
                drawTrilaterationVisuals(positions[positions.length - 1]);
                // On passe tous les points pour dessiner le chemin
                drawPath(positions);
            } else {
                statusPanel.textContent = 'Aucune donnée de position dans la base de données.';
            }

        } catch (error) {
            console.error("Failed to fetch or process data:", error);
            statusPanel.textContent = 'Erreur: Impossible de charger les données de l\'API.';
        }
    }

    // Logique pour le bouton "Effacer"
    clearDbButton.addEventListener('click', async () => {
        if (confirm("Voulez-vous vraiment vider l'historique des positions ?")) {
            try {
                await fetch('api_clear_database.php');
                updateVisualization(); // Mettre à jour l'affichage immédiatement
            } catch (error) {
                alert("Erreur lors du vidage de la base de données.");
            }
        }
    });

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    updateVisualization();
    setInterval(updateVisualization, 1000);
});