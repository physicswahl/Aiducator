class CO2Simulator {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = 900;
        this.canvas.height = 600;
        
        // Simulation parameters
        this.isRunning = false;
        this.isPaused = false;
        this.data = [];
        this.currentTime = 0;
        this.maxTime = 30 * 60; // 30 minutes in seconds
        this.simulationSpeed = 120; // 2 minutes of data per second (doubled speed)
        this.baselinePPM = 460; // Start at 460ppm
        this.targetPPM = 700; // Classroom target
        this.currentPPM = this.baselinePPM;
        this.spikeActive = false;
        this.spikeStartTime = 0;
        this.spikeDuration = 120; // 2 minutes
        this.spikePeakPPM = 900;
        
        // Animation
        this.animationId = null;
        this.lastTimestamp = 0;
        
        // Graph styling (increased margins for better spacing)
        this.margin = { top: 30, right: 100, bottom: 80, left: 100 };
        this.graphWidth = this.canvas.width - this.margin.left - this.margin.right;
        this.graphHeight = this.canvas.height - this.margin.top - this.margin.bottom;
        
        // Initialize
        this.setupCanvas();
        this.drawGraph();
    }
    
    setupCanvas() {
        // Set up high DPI rendering
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        // Reset dimensions after scaling
        this.canvas.width = 900;
        this.canvas.height = 600;
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.isPaused = false;
        this.data = [];
        this.currentTime = 0;
        this.currentPPM = this.baselinePPM;
        this.spikeActive = false;
        
        // Add initial data point
        this.data.push({ time: 0, ppm: this.baselinePPM });
        
        this.animate();
        this.updateButtonStates();
    }
    
    pause() {
        this.isPaused = !this.isPaused;
        this.updateButtonStates();
        
        if (!this.isPaused && this.isRunning) {
            this.animate();
        }
    }
    
    stop() {
        this.isRunning = false;
        this.isPaused = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.updateButtonStates();
    }
    
    reset() {
        this.stop();
        this.data = [];
        this.currentTime = 0;
        this.currentPPM = this.baselinePPM;
        this.spikeActive = false;
        this.drawGraph();
        this.updateButtonStates();
    }
    
    triggerSpike() {
        if (!this.isRunning || this.spikeActive) return;
        
        this.spikeActive = true;
        this.spikeStartTime = this.currentTime;
    }
    
    animate() {
        if (!this.isRunning || this.isPaused) return;
        
        this.currentTime += this.simulationSpeed / 60; // Simulate time progression
        
        if (this.currentTime >= this.maxTime) {
            this.stop();
            return;
        }
        
        // Calculate PPM based on time and any active spikes
        this.updatePPM();
        
        // Add data point every 60 seconds of simulation (halved frequency)
        if (this.data.length === 0 || this.currentTime - this.data[this.data.length - 1].time >= 60) {
            this.data.push({
                time: this.currentTime,
                ppm: Math.round(this.currentPPM * 10) / 10
            });
        }
        
        this.drawGraph();
        
        this.animationId = requestAnimationFrame(() => {
            setTimeout(() => this.animate(), 16); // ~60 FPS
        });
    }
    
    updatePPM() {
        const timeProgress = this.currentTime / this.maxTime;
        
        // CLASSROOM: gradual increase from 460 to 700 over 30 minutes
        const classroomTrend = this.baselinePPM + (this.targetPPM - this.baselinePPM) * timeProgress;
        
        // Add some natural variation
        const variation = Math.sin(this.currentTime / 300) * 10 + Math.random() * 5 - 2.5;
        
        let targetClassroomPPM = classroomTrend + variation;
        
        // Handle spike if active (only affects classroom)
        if (this.spikeActive) {
            const spikeElapsed = this.currentTime - this.spikeStartTime;
            
            if (spikeElapsed < this.spikeDuration) {
                // Spike curve: quick rise and fall
                const spikeProgress = spikeElapsed / this.spikeDuration;
                let spikeFactor;
                
                if (spikeProgress < 0.3) {
                    // Quick rise to peak
                    spikeFactor = (spikeProgress / 0.3);
                } else {
                    // Gradual fall back to baseline
                    spikeFactor = 1 - ((spikeProgress - 0.3) / 0.7);
                }
                
                const spikeAmount = (this.spikePeakPPM - classroomTrend) * spikeFactor;
                targetClassroomPPM = classroomTrend + spikeAmount;
            } else {
                this.spikeActive = false;
            }
        }
        
        // Smooth transition to target PPM
        this.currentPPM += (targetClassroomPPM - this.currentPPM) * 0.1;
    }
    
    drawGraph() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw graph area
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(this.margin.left, this.margin.top, this.graphWidth, this.graphHeight);
        
        // Draw grid
        this.drawGrid();
        
        // Draw axes
        this.drawAxes();
        
        // Draw data
        this.drawData();
        
        // Draw current value indicator
        this.drawCurrentValue();
        
        // Draw status
        this.drawStatus();
    }
    
    drawGrid() {
        this.ctx.strokeStyle = '#e9ecef';
        this.ctx.lineWidth = 1;
        
        // Vertical grid lines (time)
        for (let t = 0; t <= this.maxTime; t += 300) { // Every 5 minutes
            const x = this.margin.left + (t / this.maxTime) * this.graphWidth;
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.margin.top);
            this.ctx.lineTo(x, this.margin.top + this.graphHeight);
            this.ctx.stroke();
        }
        
        // Horizontal grid lines (PPM)
        for (let ppm = 300; ppm <= 1000; ppm += 100) {
            const y = this.margin.top + this.graphHeight - ((ppm - 300) / 700) * this.graphHeight;
            this.ctx.beginPath();
            this.ctx.moveTo(this.margin.left, y);
            this.ctx.lineTo(this.margin.left + this.graphWidth, y);
            this.ctx.stroke();
        }
    }
    
    drawAxes() {
        this.ctx.strokeStyle = '#343a40';
        this.ctx.lineWidth = 2;
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = '#343a40';
        this.ctx.textAlign = 'center';
        
        // X-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.margin.left, this.margin.top + this.graphHeight);
        this.ctx.lineTo(this.margin.left + this.graphWidth, this.margin.top + this.graphHeight);
        this.ctx.stroke();
        
        // Y-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.margin.left, this.margin.top);
        this.ctx.lineTo(this.margin.left, this.margin.top + this.graphHeight);
        this.ctx.stroke();
        
        // X-axis labels (time)
        for (let t = 0; t <= this.maxTime; t += 600) { // Every 10 minutes
            const x = this.margin.left + (t / this.maxTime) * this.graphWidth;
            const minutes = t / 60;
            this.ctx.fillText(`${minutes}m`, x, this.margin.top + this.graphHeight + 20);
        }
        
        // Y-axis labels (PPM)
        this.ctx.textAlign = 'right';
        for (let ppm = 300; ppm <= 1000; ppm += 100) {
            const y = this.margin.top + this.graphHeight - ((ppm - 300) / 700) * this.graphHeight;
            this.ctx.fillText(`${ppm}`, this.margin.left - 10, y + 4);
        }
        
        // Axis titles
        this.ctx.textAlign = 'center';
        this.ctx.font = '14px Arial';
        this.ctx.fillText('Time (minutes)', this.margin.left + this.graphWidth / 2, this.canvas.height - 20);
        
        this.ctx.save();
        this.ctx.translate(20, this.margin.top + this.graphHeight / 2);
        this.ctx.rotate(-Math.PI / 2);
        this.ctx.fillText('CO₂ Concentration (PPM)', 0, 0);
        this.ctx.restore();
    }
    
    drawData() {
        // Draw classroom line (brown)
        if (this.data.length >= 2) {
            this.ctx.strokeStyle = '#8B4513'; // Brown color
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            
            for (let i = 0; i < this.data.length; i++) {
                const point = this.data[i];
                const x = this.margin.left + (point.time / this.maxTime) * this.graphWidth;
                const y = this.margin.top + this.graphHeight - ((point.ppm - 300) / 700) * this.graphHeight;
                
                if (i === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
            
            this.ctx.stroke();
            
            // Draw classroom data points
            this.ctx.fillStyle = '#8B4513';
            for (let i = 0; i < this.data.length; i++) {
                const point = this.data[i];
                const x = this.margin.left + (point.time / this.maxTime) * this.graphWidth;
                const y = this.margin.top + this.graphHeight - ((point.ppm - 300) / 700) * this.graphHeight;
                
                this.ctx.beginPath();
                this.ctx.arc(x, y, 3, 0, 2 * Math.PI);
                this.ctx.fill();
            }
        }
    }
    
    drawCurrentValue() {
        if (!this.isRunning || this.data.length === 0) return;
        
        const x = this.margin.left + (this.currentTime / this.maxTime) * this.graphWidth;
        const y = this.margin.top + this.graphHeight - ((this.currentPPM - 300) / 700) * this.graphHeight;
        
        // Current point (brown to match classroom line)
        this.ctx.fillStyle = '#8B4513';
        this.ctx.beginPath();
        this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Current value label
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(x + 10, y - 15, 80, 20);
        this.ctx.strokeStyle = '#8B4513';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(x + 10, y - 15, 80, 20);
        
        this.ctx.fillStyle = '#8B4513';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`${Math.round(this.currentPPM)} PPM`, x + 15, y - 2);
    }
    
    drawStatus() {
        // Status box (reduced height from 80 to 65)
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.ctx.fillRect(this.margin.left + this.graphWidth - 150, this.margin.top + 10, 140, 65);
        this.ctx.strokeStyle = '#dee2e6';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(this.margin.left + this.graphWidth - 150, this.margin.top + 10, 140, 65);
        
        // Status text
        this.ctx.fillStyle = '#343a40';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'left';
        
        const statusX = this.margin.left + this.graphWidth - 145;
        const statusY = this.margin.top + 25;
        
        this.ctx.fillText(`Status: ${this.isRunning ? (this.isPaused ? 'Paused' : 'Running') : 'Stopped'}`, statusX, statusY);
        this.ctx.fillText(`Time: ${Math.floor(this.currentTime / 60)}:${String(Math.floor(this.currentTime % 60)).padStart(2, '0')}`, statusX, statusY + 15);
        
        if (this.spikeActive) {
            this.ctx.fillStyle = '#dc3545';
            this.ctx.fillText('SPIKE ACTIVE', statusX, statusY + 30);
        }
    }
    
    updateButtonStates() {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        const resetBtn = document.getElementById('resetBtn');
        const spikeBtn = document.getElementById('spikeBtn');
        
        startBtn.disabled = this.isRunning;
        pauseBtn.disabled = !this.isRunning;
        stopBtn.disabled = !this.isRunning;
        resetBtn.disabled = this.isRunning && !this.isPaused;
        spikeBtn.disabled = !this.isRunning || this.spikeActive;
        
        pauseBtn.textContent = this.isPaused ? 'Resume' : 'Pause';
    }
}

// Initialize simulator when page loads
let co2Simulator;
document.addEventListener('DOMContentLoaded', function() {
    co2Simulator = new CO2Simulator('co2Chart');
});
