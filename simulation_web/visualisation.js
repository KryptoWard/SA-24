// Front-end script driving the live visualisations on the
// main page: draws grids, positions and interacts with the API.
// Contains a visualization class for each sensor mode and
// helper methods to scale coordinates and poll new data.
document.addEventListener('DOMContentLoaded', () => {
    const roomWidthMeters = 8.0;
    const roomHeightMeters = 8.0;
    const sensors = [
        { name: 'A', x: 0.25, y: 0.25, color: '#00FFFF' },
        { name: 'B', x: 0.25, y: 7.75, color: '#FF00FF' },
        { name: 'C', x: 7.75, y: 7.75, color: '#FFFF00' }
    ];

    class VisualizationManager {
        constructor(canvasId, gridId, statusId, type) {
            this.canvas = document.getElementById(canvasId);
            this.ctx = this.canvas.getContext('2d');
            this.roomGrid = document.getElementById(gridId);
            this.statusPanel = document.getElementById(statusId);
            this.type = type;
            
            this.resizeCanvas();
            window.addEventListener('resize', () => this.resizeCanvas());
        }

        resizeCanvas() {
            this.canvas.width = this.roomGrid.clientWidth;
            this.canvas.height = this.roomGrid.clientHeight;
            this.drawBase();
        }

        toCanvasCoords(x_m, y_m) {
            const x_px = (x_m / roomWidthMeters) * this.canvas.width;
            const y_px = (y_m / roomHeightMeters) * this.canvas.height;
            return { x: x_px, y: y_px };
        }

        drawGrid() {
            const gridSpacing = 1.0;
            const numLines = Math.floor(roomWidthMeters / gridSpacing) + 1;
            
            this.ctx.strokeStyle = '#ddd';
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([]);

            for (let i = 0; i < numLines; i++) {
                const x_m = i * gridSpacing;
                const y_m = i * gridSpacing;
                
                if (x_m <= roomWidthMeters) {
                    const x_px = (x_m / roomWidthMeters) * this.canvas.width;
                    this.ctx.beginPath();
                    this.ctx.moveTo(x_px, 0);
                    this.ctx.lineTo(x_px, this.canvas.height);
                    this.ctx.stroke();
                }
                
                if (y_m <= roomHeightMeters) {
                    const y_px = (y_m / roomHeightMeters) * this.canvas.height;
                    this.ctx.beginPath();
                    this.ctx.moveTo(0, y_px);
                    this.ctx.lineTo(this.canvas.width, y_px);
                    this.ctx.stroke();
                }
            }

            this.ctx.strokeStyle = '#999';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.rect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.stroke();
        }

        drawCoordinateLabels() {
            this.ctx.font = '10px Arial';
            this.ctx.fillStyle = '#666';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'top';

            for (let i = 0; i <= roomWidthMeters; i++) {
                const x_px = (i / roomWidthMeters) * this.canvas.width;
                this.ctx.fillText(i.toString(), x_px, this.canvas.height + 5);
            }

            this.ctx.textAlign = 'right';
            this.ctx.textBaseline = 'middle';
            for (let i = 0; i <= roomHeightMeters; i++) {
                const y_px = this.canvas.height - (i / roomHeightMeters) * this.canvas.height;
                this.ctx.fillText(i.toString(), -5, y_px);
            }
        }

        drawBase() {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.drawGrid();
            this.drawCoordinateLabels();
            
            sensors.forEach(sensor => {
                const pos = this.toCanvasCoords(sensor.x, sensor.y);
                this.ctx.beginPath();
                this.ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
                this.ctx.fillStyle = sensor.color;
                this.ctx.fill();
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
                
                this.ctx.font = 'bold 12px Arial';
                this.ctx.fillStyle = '#000';
                this.ctx.textAlign = 'left';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(sensor.name, pos.x + 10, pos.y + 5);
            });
        }

        drawTrilaterationVisuals(lastPosition) {
            if (!lastPosition) return;
            
            const lastPosPx = this.toCanvasCoords(lastPosition.pos_x_estimee, lastPosition.pos_y_estimee);
            const distances = { 
                A: parseFloat(lastPosition.dist_a), 
                B: parseFloat(lastPosition.dist_b), 
                C: parseFloat(lastPosition.dist_c) 
            };

            sensors.forEach(sensor => {
                const sensorPosPx = this.toCanvasCoords(sensor.x, sensor.y);
                const radius = distances[sensor.name];
                if (radius === null || isNaN(radius)) return;
                
                const radiusPx = (radius / roomWidthMeters) * this.canvas.width;

                this.ctx.beginPath();
                this.ctx.arc(sensorPosPx.x, sensorPosPx.y, radiusPx, 0, 2 * Math.PI);
                this.ctx.strokeStyle = sensor.color;
                this.ctx.lineWidth = 2;
                this.ctx.setLineDash([5, 5]);
                this.ctx.stroke();
                this.ctx.setLineDash([]);

                this.ctx.beginPath();
                this.ctx.moveTo(sensorPosPx.x, sensorPosPx.y);
                this.ctx.lineTo(lastPosPx.x, lastPosPx.y);
                this.ctx.strokeStyle = sensor.color;
                this.ctx.lineWidth = 1;
                this.ctx.stroke();
                
                const midX = (sensorPosPx.x + lastPosPx.x) / 2;
                const midY = (sensorPosPx.y + lastPosPx.y) / 2;
                const text = `${radius.toFixed(2)}m`;
                
                this.ctx.font = 'bold 10px Arial';
                const textWidth = this.ctx.measureText(text).width;

                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                this.ctx.fillRect(midX - (textWidth / 2) - 2, midY - 10, textWidth + 4, 14);

                this.ctx.fillStyle = '#000000';
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(text, midX, midY - 3);
            });
        }

        drawPath(positions) {
            if (!positions || positions.length === 0) return;

            const trailColor = this.type === 'ultrason' ? '52, 152, 219' : '39, 174, 96';
            
            positions.slice(0, -1).forEach((p, index) => {
                const pos = this.toCanvasCoords(p.pos_x_estimee, p.pos_y_estimee);
                const opacity = (index + 1) / positions.length; 
                this.ctx.beginPath();
                this.ctx.arc(pos.x, pos.y, 6, 0, 2 * Math.PI);
                this.ctx.fillStyle = `rgba(${trailColor}, ${opacity})`;
                this.ctx.fill();
            });

            const lastPosData = positions[positions.length - 1];
            const lastPos = this.toCanvasCoords(lastPosData.pos_x_estimee, lastPosData.pos_y_estimee);
            
            this.ctx.beginPath();
            this.ctx.arc(lastPos.x, lastPos.y, 10, 0, 2 * Math.PI);
            this.ctx.fillStyle = this.type === 'ultrason' ? '#3498db' : '#27ae60';
            this.ctx.fill();
            this.ctx.strokeStyle = '#fff';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();

            const typeLabel = this.type === 'ultrason' ? 'Ultrason' : 'Son';
            this.statusPanel.textContent = `${typeLabel} : Position (${parseFloat(lastPosData.pos_x_estimee).toFixed(2)}, ${parseFloat(lastPosData.pos_y_estimee).toFixed(2)}) - ${new Date(lastPosData.timestamp).toLocaleTimeString()}`;
        }

        updateVisualization(positions) {
            this.drawBase();
            
            if (positions && positions.length > 0) {
                this.drawTrilaterationVisuals(positions[positions.length - 1]);
                this.drawPath(positions);
            } else {
                const typeLabel = this.type === 'ultrason' ? 'Ultrason' : 'Son';
                this.statusPanel.textContent = `${typeLabel} : Aucune donnée disponible`;
            }
        }
    }

    const ultrasonViz = new VisualizationManager(
        'simulationCanvasUltrason', 
        'roomGridUltrason', 
        'statusPanelUltrason', 
        'ultrason'
    );
    
    const sonViz = new VisualizationManager(
        'simulationCanvasSon', 
        'roomGridSon', 
        'statusPanelSon', 
        'son'
    );

    async function updateAllVisualizations() {
        try {
            const response = await fetch('api_get_positions.php?type=all');
            if (!response.ok) {
                throw new Error(`Erreur HTTP! Statut: ${response.status}`);
            }
            const data = await response.json();

            if (data.error) {
                ultrasonViz.statusPanel.textContent = `Erreur API: ${data.error}`;
                sonViz.statusPanel.textContent = `Erreur API: ${data.error}`;
                return;
            }

            ultrasonViz.updateVisualization(data.ultrason || []);
            sonViz.updateVisualization(data.son || []);

        } catch (error) {
            console.error("Échec du chargement des données:", error);
            ultrasonViz.statusPanel.textContent = `Erreur: ${error.message}`;
            sonViz.statusPanel.textContent = `Erreur: ${error.message}`;
        }
    }

    const clearDbButton = document.getElementById('clearDbButton');
    clearDbButton.addEventListener('click', async () => {
        if (confirm('Êtes-vous sûr de vouloir effacer tout l\'historique ?')) {
            try {
                const response = await fetch('api_clear_db.php', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    ultrasonViz.drawBase();
                    sonViz.drawBase();
                    ultrasonViz.statusPanel.textContent = 'Ultrason : Historique effacé';
                    sonViz.statusPanel.textContent = 'Son : Historique effacé';
                } else {
                    alert('Erreur lors de l\'effacement: ' + result.error);
                }
            } catch (error) {
                alert('Erreur de connexion: ' + error.message);
            }
        }
    });

    const modeSelector = document.getElementById('simulatorMode');
    const switchModeButton = document.getElementById('switchModeButton');
    
    switchModeButton.addEventListener('click', () => {
        const selectedMode = modeSelector.value;
        alert(`Mode sélectionné: ${selectedMode}\n\nNote: Pour changer réellement le mode, modifiez la variable SIMULATION_MODE dans simulateur.py et relancez le script.`);
    });

    updateAllVisualizations();
    setInterval(updateAllVisualizations, 1000);
});