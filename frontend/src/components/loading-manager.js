export class LoadingManager {
    constructor() {
        this.progressInterval = null;
    }

    show(){
        const loadingHTML = `
            <div id="loadingOverlay" class="loading-overlay">
                <div class="loading-container">
                    <div class="loading-spinner">
                        <div class="spinner-ring"></div>
                        <div class="spinner-ring"></div>
                        <div class="spinner-ring"></div>
                        <div class="spinner-ring"></div>
                    </div>
                    <h3 class="loading-title">Processing Your Files...</h3>
                    <p class="loading-subtitle">AI is analyzing receipts and updating Excel</p>
                    <div class="loading-progress">
                        <div class="progress-bar">
                            <div id="progressFill" class="progress-fill"></div>
                        </div>
                        <span id="progressText" class="progress-text">0%</span>
                    </div>
                    <div class="loading-steps">
                        <div id="step1" class="step active">📖 Reading Images</div>
                        <div id="step2" class="step">🤖 AI Processing</div>
                        <div id="step3" class="step">📊 Updating Excel</div>
                        <div id="step4" class="step">✅ Finalizing</div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
        this.simulateProgress();
    }

    hide() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('fade-out');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }

    simulateProgress() {
        let progress = 0;
        const steps = ['step1', 'step2', 'step3', 'step4'];
        let currentStep = 0;

        this.progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if(progress > 100) progress = 100;

            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');

            if (progressFill && progressText) {
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${Math.round(progress)}%`;
            }

            // Update steps
            const stepProgress = Math.floor(progress / 25);

            if (stepProgress > currentStep && stepProgress < steps.length) {
                const currentStepEl = document.getElementById(steps[currentStep]);
                if (currentStepEl) {
                    currentStepEl.classList.remove('active');
                    currentStepEl.classList.add('completed');
                }
                currentStep = stepProgress;
                if (currentStep < steps.length) {
                    const nextStepEl = document.getElementById(steps[currentStep]);
                    if (nextStepEl) {
                        nextStepEl.classList.add('active');
                    }
                }
            }

            if (progress >= 100) {
                clearInterval(this.progressInterval);
                steps.forEach(step => {
                    const element = document.getElementById(step);
                    if (element) {
                        element.classList.remove('active');
                        element.classList.add('completed');
                    }
                });
            }

        }, 200);
    }
}