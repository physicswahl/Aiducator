// Four Environment CO2 Simulation for Step 2
// Simulates CO2 levels over a full day (24 hours) in 30 seconds

class MultiEnvironmentCO2Simulator {
    constructor() {
        this.isRunning = false;
        this.isPaused = false;
        this.canvases = {};
        this.contexts = {};
        this.data = {};
        this.currentTime = 0;
        this.maxTime = 24; // 24 hours
        this.simulationSpeed = 800; // milliseconds per hour
        this.interval = null;
        
        // Define environments with their characteristics
        this.environments = {
            'classroom': {
                name: 'Salle de Classe',
                color: '#007bff',
                baseline: 450,
                patterns: this.getClassroomPattern()
            },
            'park': {
                name: 'Parc',
                color: '#28a745',
                baseline: 380,
                patterns: this.getParkPattern()
            },
            'road': {
                name: 'Route',
                color: '#dc3545',
                baseline: 420,
                patterns: this.getRoadPattern()
            },
            'corridor': {
                name: 'Couloir d\'École',
                color: '#ffc107',
                baseline: 480,
                patterns: this.getCorridorPattern()
            }
        };
        
        this.initializeCanvases();
        this.resetData();
    }
    
    initializeCanvases() {
        Object.keys(this.environments).forEach(envId => {
            const canvas = document.getElementById(`${envId}Chart`);
            if (canvas) {
                this.canvases[envId] = canvas;
                this.contexts[envId] = canvas.getContext('2d');
                
                // Set canvas size
                canvas.width = canvas.offsetWidth;
                canvas.height = canvas.offsetHeight;
            }
        });
    }
    
    getClassroomPattern() {
        // School hours: 8 AM - 3 PM, highest during class times
        return [
            {hour: 0, multiplier: 1.0},   // Midnight - baseline
            {hour: 6, multiplier: 1.0},   // Early morning
            {hour: 8, multiplier: 1.8},   // School starts - rapid rise
            {hour: 10, multiplier: 2.2},  // Mid-morning classes
            {hour: 12, multiplier: 1.6},  // Lunch break
            {hour: 14, multiplier: 2.0},  // Afternoon classes
            {hour: 15, multiplier: 1.2},  // School ends
            {hour: 18, multiplier: 1.0},  // Evening
            {hour: 24, multiplier: 1.0}   // Back to baseline
        ];
    }
    
    getParkPattern() {
        // Outdoor environment with natural fluctuations and photosynthesis effect
        return [
            {hour: 0, multiplier: 1.1},   // Night - slightly higher
            {hour: 6, multiplier: 1.2},   // Dawn
            {hour: 8, multiplier: 0.9},   // Morning photosynthesis starts
            {hour: 12, multiplier: 0.8},  // Peak photosynthesis
            {hour: 15, multiplier: 0.85}, // Afternoon
            {hour: 18, multiplier: 1.0},  // Evening
            {hour: 21, multiplier: 1.1},  // Night - respiration
            {hour: 24, multiplier: 1.1}   // Late night
        ];
    }
    
    getRoadPattern() {
        // Traffic patterns with morning and evening rush hours
        return [
            {hour: 0, multiplier: 1.2},   // Late night traffic
            {hour: 6, multiplier: 1.8},   // Morning rush begins
            {hour: 8, multiplier: 2.5},   // Peak morning rush
            {hour: 10, multiplier: 1.6},  // Mid-morning
            {hour: 12, multiplier: 1.8},  // Lunch traffic
            {hour: 15, multiplier: 1.7},  // Afternoon
            {hour: 17, multiplier: 2.8},  // Evening rush peak
            {hour: 19, multiplier: 2.0},  // Evening traffic
            {hour: 22, multiplier: 1.4},  // Night traffic
            {hour: 24, multiplier: 1.2}   // Late night
        ];
    }
    
    getCorridorPattern() {
        // School corridor with class changes and break times
        return [
            {hour: 0, multiplier: 1.0},   // Night - empty
            {hour: 7, multiplier: 1.5},   // Staff arrival
            {hour: 8, multiplier: 2.5},   // Students arrive - high traffic
            {hour: 9, multiplier: 1.3},   // In class - lower traffic
            {hour: 10, multiplier: 2.0},  // Break time
            {hour: 11, multiplier: 1.4},  // Back in class
            {hour: 12, multiplier: 2.3},  // Lunch break - high traffic
            {hour: 13, multiplier: 1.5},  // After lunch
            {hour: 15, multiplier: 2.8},  // School ends - highest traffic
            {hour: 16, multiplier: 1.2},  // After school activities
            {hour: 18, multiplier: 1.0},  // Evening cleanup
            {hour: 24, multiplier: 1.0}   // Night
        ];
    }
    
    resetData() {
        this.currentTime = 0;
        Object.keys(this.environments).forEach(envId => {
            this.data[envId] = [];
        });
        this.drawAllGraphs();
    }
    
    interpolatePattern(patterns, hour) {
        // Find the two points to interpolate between
        for (let i = 0; i < patterns.length - 1; i++) {
            if (hour >= patterns[i].hour && hour <= patterns[i + 1].hour) {
                const t = (hour - patterns[i].hour) / (patterns[i + 1].hour - patterns[i].hour);
                return patterns[i].multiplier + t * (patterns[i + 1].multiplier - patterns[i].multiplier);
            }
        }
        return 1.0; // Default multiplier
    }
    
    calculateCO2Level(envId, hour) {
        const env = this.environments[envId];
        const multiplier = this.interpolatePattern(env.patterns, hour);
        
        // Add some random variation (±5%)
        const variation = 0.95 + Math.random() * 0.1;
        
        return env.baseline * multiplier * variation;
    }
    
    start() {
        if (this.isRunning && !this.isPaused) return;
        
        this.isRunning = true;
        this.isPaused = false;
        
        this.interval = setInterval(() => {
            if (!this.isPaused) {
                this.updateSimulation();
            }
        }, this.simulationSpeed);
        
        this.updateButtonStates();
    }
    
    pause() {
        this.isPaused = !this.isPaused;
        this.updateButtonStates();
    }
    
    stop() {
        this.isRunning = false;
        this.isPaused = false;
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.updateButtonStates();
    }
    
    reset() {
        this.stop();
        this.resetData();
        this.updateButtonStates();
    }
    
    updateSimulation() {
        this.currentTime += 1; // 1 hour increment
        
        // Add data points for each environment
        Object.keys(this.environments).forEach(envId => {
            const co2Level = this.calculateCO2Level(envId, this.currentTime);
            this.data[envId].push({
                time: this.currentTime,
                ppm: co2Level
            });
        });
        
        this.drawAllGraphs();
        
        // Check if simulation is complete
        if (this.currentTime >= this.maxTime) {
            this.stop();
        }
    }
    
    drawAllGraphs() {
        Object.keys(this.environments).forEach(envId => {
            this.drawGraph(envId);
        });
    }
    
    drawGraph(envId) {
        const canvas = this.canvases[envId];
        const ctx = this.contexts[envId];
        const env = this.environments[envId];
        
        if (!canvas || !ctx) return;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Set up graph dimensions
        const margin = 40;
        const graphWidth = canvas.width - 2 * margin;
        const graphHeight = canvas.height - 2 * margin;
        
        // Draw background
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid
        this.drawGrid(ctx, margin, graphWidth, graphHeight);
        
        // Draw axes
        this.drawAxes(ctx, margin, graphWidth, graphHeight, envId);
        
        // Draw data line
        if (this.data[envId].length > 1) {
            this.drawDataLine(ctx, margin, graphWidth, graphHeight, envId);
        }
        
        // Draw title
        ctx.fillStyle = '#000';
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(env.name, canvas.width / 2, 20);
    }
    
    drawGrid(ctx, margin, width, height) {
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        
        // Vertical lines (hours)
        for (let i = 0; i <= 24; i += 4) {
            const x = margin + (i / 24) * width;
            ctx.beginPath();
            ctx.moveTo(x, margin);
            ctx.lineTo(x, margin + height);
            ctx.stroke();
        }
        
        // Horizontal lines (CO2 levels)
        for (let i = 300; i <= 1000; i += 100) {
            const y = margin + height - ((i - 300) / 700) * height;
            ctx.beginPath();
            ctx.moveTo(margin, y);
            ctx.lineTo(margin + width, y);
            ctx.stroke();
        }
    }
    
    drawAxes(ctx, margin, width, height, envId) {
        const env = this.environments[envId];
        
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin + height);
        ctx.lineTo(margin + width, margin + height);
        ctx.stroke();
        
        // Y-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin);
        ctx.lineTo(margin, margin + height);
        ctx.stroke();
        
        // X-axis labels (hours)
        ctx.fillStyle = '#666';
        for (let i = 0; i <= 24; i += 6) {
            const x = margin + (i / 24) * width;
            ctx.fillText(`${i}:00`, x, margin + height + 20);
        }
        
        // Y-axis labels (CO2 ppm)
        ctx.textAlign = 'right';
        for (let i = 300; i <= 1000; i += 100) {
            const y = margin + height - ((i - 300) / 700) * height;
            ctx.fillText(`${i}`, margin - 10, y + 5);
        }
        
        // Axis titles
        ctx.textAlign = 'center';
        ctx.fillText('Temps (Heures)', margin + width / 2, canvas.height - 5);
        
        ctx.save();
        ctx.translate(15, margin + height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('CO₂ (ppm)', 0, 0);
        ctx.restore();
    }
    
    drawDataLine(ctx, margin, width, height, envId) {
        const env = this.environments[envId];
        const data = this.data[envId];
        
        ctx.strokeStyle = env.color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        for (let i = 0; i < data.length; i++) {
            const point = data[i];
            const x = margin + (point.time / this.maxTime) * width;
            const y = margin + height - ((point.ppm - 300) / 700) * height;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.stroke();
        
        // Draw current point
        if (data.length > 0) {
            const lastPoint = data[data.length - 1];
            const x = margin + (lastPoint.time / this.maxTime) * width;
            const y = margin + height - ((lastPoint.ppm - 300) / 700) * height;
            
            ctx.fillStyle = env.color;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();
            
            // Show current value
            ctx.fillStyle = '#000';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`${Math.round(lastPoint.ppm)} ppm`, x, y - 15);
        }
    }
    
    updateButtonStates() {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        const resetBtn = document.getElementById('resetBtn');
        
        if (startBtn) {
            startBtn.disabled = this.isRunning && !this.isPaused;
            startBtn.innerHTML = this.isRunning ? 
                '<i class="fas fa-play me-1"></i>Reprendre' : 
                '<i class="fas fa-play me-1"></i>Démarrer la Surveillance';
        }
        
        if (pauseBtn) {
            pauseBtn.disabled = !this.isRunning;
            pauseBtn.innerHTML = this.isPaused ? 
                '<i class="fas fa-play me-1"></i>Reprendre' : 
                '<i class="fas fa-pause me-1"></i>Pause';
        }
        
        if (stopBtn) {
            stopBtn.disabled = !this.isRunning;
        }
        
        if (resetBtn) {
            resetBtn.disabled = this.isRunning && !this.isPaused;
        }
    }
}

// Initialize the simulator when the page loads
let multiCO2Simulator;

document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for canvases to be properly sized
    setTimeout(() => {
        multiCO2Simulator = new MultiEnvironmentCO2Simulator();
        
        // Add event listeners to buttons
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        const resetBtn = document.getElementById('resetBtn');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => multiCO2Simulator.start());
        }
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => multiCO2Simulator.pause());
        }
        if (stopBtn) {
            stopBtn.addEventListener('click', () => multiCO2Simulator.stop());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => multiCO2Simulator.reset());
        }
    }, 500);
});

// Handle window resize
window.addEventListener('resize', function() {
    if (multiCO2Simulator) {
        multiCO2Simulator.initializeCanvases();
        multiCO2Simulator.drawAllGraphs();
    }
});
