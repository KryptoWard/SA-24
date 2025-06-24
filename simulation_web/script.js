        // Initialisation de la grille
        // Grid initialization
        function initializeGrid() {
            const gridLines = document.getElementById('gridLines');
            const gridSize = 16;

            for (let i = 1; i < gridSize; i++) {
                const hLine = document.createElement('div');
                hLine.className = 'grid-line-h';
                hLine.style.top = `${(i / gridSize) * 100}%`;
                gridLines.appendChild(hLine);

                const vLine = document.createElement('div');
                vLine.className = 'grid-line-v';
                vLine.style.left = `${(i / gridSize) * 100}%`;
                gridLines.appendChild(vLine);
            }
        }

        // Variables de simulation
        // Simulation variables
        let simulationActive = false;
        let simulationInterval;
        let currentPosition = {x: 50, y: 50};
        let trajectoryPoints = [];
        let currentTrajectoryIndex = 0;

        // Mise à jour du statut système
        // Update system status
        function updateStatus(message) {
            document.getElementById('systemStatus').textContent = message;
        }

        // Mise à jour des données en temps réel
        // Update real-time data
        function updateLiveData(x, y) {
            document.getElementById('posX').textContent = x.toFixed(2) + '%';
            document.getElementById('posY').textContent = y.toFixed(2) + '%';
            document.getElementById('accuracy').textContent = '±' + (Math.random() * 2 + 0.5).toFixed(1) + 'm';
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }

        // Génération de trajectoires
        // Trajectory generation
        function generateTrajectory(type) {
            const points = [];
            const numPoints = 20;

            switch(type) {
                case 'linear':
                    for (let i = 0; i <= numPoints; i++) {
                        points.push({
                            x: 20 + (i / numPoints) * 60,
                            y: 30 + (i / numPoints) * 40
                        });
                    }
                    break;

                case 'circular':
                    for (let i = 0; i <= numPoints; i++) {
                        const angle = (i / numPoints) * 2 * Math.PI;
                        points.push({
                            x: 50 + Math.cos(angle) * 25,
                            y: 50 + Math.sin(angle) * 25
                        });
                    }
                    break;

                case 'random':
                    points.push({x: 50, y: 50});
                    for (let i = 1; i <= numPoints; i++) {
                        const lastPoint = points[i-1];
                        points.push({
                            x: Math.max(10, Math.min(90, lastPoint.x + (Math.random() - 0.5) * 20)),
                            y: Math.max(10, Math.min(90, lastPoint.y + (Math.random() - 0.5) * 20))
                        });
                    }
                    break;
            }

            return points;
        }

        // Animation de déplacement
        // Movement animation
        function moveToPosition(x, y, isObject = true) {
            const element = isObject ? document.getElementById('trackingObject') : document.getElementById('trackingPerson');
            if (element) {
                element.style.left = x + '%';
                element.style.top = y + '%';
                updateLiveData(x, y);
            }
        }

        // Simulation de localisation d'objet
        // Object localization simulation
        function startObjectSimulation() {
            if (simulationActive) return;

            const trajectoryType = document.getElementById('trajectoryType').value;
            const speed = document.getElementById('speedSlider').value;

            trajectoryPoints = generateTrajectory(trajectoryType);
            currentTrajectoryIndex = 0;
            simulationActive = true;

            updateStatus('Simulation de localisation d\'objet en cours...');
            // Update status: Object localization simulation in progress...

            // Assurer que l'élément objet est visible
            // Ensure the object element is visible
            const objectElement = document.getElementById('trackingObject');
            objectElement.style.display = 'block';
            objectElement.className = 'object';

            simulationInterval = setInterval(() => {
                if (currentTrajectoryIndex >= trajectoryPoints.length) {
                    stopSimulation();
                    return;
                }

                const point = trajectoryPoints[currentTrajectoryIndex];
                moveToPosition(point.x, point.y, true);
                currentTrajectoryIndex++;

            }, 1000 / speed);
        }

        // Simulation de localisation de personne
        // Person localization simulation
        function startPersonSimulation() {
            if (simulationActive) return;

            const trajectoryType = document.getElementById('trajectoryType').value;
            const speed = document.getElementById('speedSlider').value;

            trajectoryPoints = generateTrajectory(trajectoryType);
            currentTrajectoryIndex = 0;
            simulationActive = true;

            updateStatus('Simulation de localisation de personne en cours...');
            // Update status: Person localization simulation in progress...

            // Changer l'apparence pour représenter une personne
            // Change appearance to represent a person
            const objectElement = document.getElementById('trackingObject');
            objectElement.style.display = 'block';
            objectElement.className = 'person';

            simulationInterval = setInterval(() => {
                if (currentTrajectoryIndex >= trajectoryPoints.length) {
                    stopSimulation();
                    return;
                }

                const point = trajectoryPoints[currentTrajectoryIndex];
                moveToPosition(point.x, point.y, false); // Pass false for person
                currentTrajectoryIndex++;

            }, 1000 / speed);
        }

        // Arrêt de la simulation
        // Stop simulation
        function stopSimulation() {
            simulationActive = false;
            if (simulationInterval) {
                clearInterval(simulationInterval);
            }
            updateStatus('Simulation terminée');
            // Update status: Simulation finished
        }

        // Réinitialisation
        // Reset
        function resetSimulation() {
            stopSimulation();
            currentPosition = {x: 50, y: 50};
            moveToPosition(50, 50, true); // Resetting with object appearance by default
            document.getElementById('trackingObject').className = 'object';
            updateStatus('Système réinitialisé');
            // Update status: System reset

            // Reset des données
            // Reset data
            document.getElementById('posX').textContent = '--';
            document.getElementById('posY').textContent = '--';
            document.getElementById('accuracy').textContent = '--';
            document.getElementById('lastUpdate').textContent = '--';
        }

        // Navigation fluide
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Initialisation au chargement de la page
        // Initialization on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeGrid();
            updateStatus('Système prêt');
            // Update status: System ready

            // Animation des éléments au scroll
            // Animate elements on scroll
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        if (entry.target.classList.contains('timeline-item')) {
                            entry.target.classList.add('animate');
                        } else {
                            entry.target.style.transform = 'translateY(0)';
                        }
                    }
                });
            }, observerOptions);

            // Observer les éléments à animer
            // Observe elements to animate
            document.querySelectorAll('.objective-card, .spec-card, .doc-card, .team-member, .timeline-item').forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(el);
            });

            // Animation spéciale pour les éléments de timeline
            // Special animation for timeline elements
            const timelineItems = document.querySelectorAll('.timeline-item');
            timelineItems.forEach((item, index) => {
                item.style.transitionDelay = `${index * 0.2}s`;
            });
        });

        // Mise à jour responsive de la grille
        // Responsive grid update
        window.addEventListener('resize', function() {
            // Ajuster la taille de la grille sur mobile si nécessaire
            // Adjust grid size on mobile if necessary
            const roomGrid = document.getElementById('roomGrid');
            if (window.innerWidth < 768) {
                roomGrid.style.width = '300px';
                roomGrid.style.height = '300px';
            } else {
                roomGrid.style.width = '400px';
                roomGrid.style.height = '400px';
            }
        });