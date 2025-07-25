import './styles/form.css';
import './styles/tabs.css';
import './styles/app.css';
import './styles/loading.css';
import { UIManager } from './components/ui-manager.js';
import { FileManager } from './components/file-manager.js';
import { ProcessManager } from './components/process-manager.js';

// Initialize the application
class App {
    constructor() {
        this.ui = new UIManager();
        this.fileManager = new FileManager(this.ui);
        this.processManager = new ProcessManager(this.ui);
        
        // Make UI manager globally accessible for onclick events
        window.uiManager = this.ui;
        
        this.init();
    }

    init() {
        // Create initial UI
        this.ui.createInitialUI();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Folder selection
        document.getElementById('selectFolder').addEventListener('click', () => {
            this.fileManager.selectFolder();
        });

        // Excel file selection
        document.getElementById('selectExcel').addEventListener('click', () => {
            this.fileManager.selectExcelFile();
        });

        // Process files
        document.getElementById('process').addEventListener('click', () => {
            this.processManager.processFiles();
        });
    }
}

// Start the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new App();
});