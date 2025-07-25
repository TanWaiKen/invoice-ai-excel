import { fileStorage } from './file-storage.js';
import { ProcessManager } from './process-manager.js';
import { FileManager } from './file-manager.js';
import { OpenFile } from '../../wailsjs/go/main/App.js';

export class UIManager {
    constructor() {
        this.selectedImagePaths = [];
        this.selectedImageFolder = '';
        this.selectedExcelPath = '';
        this.generatedFiles = []; 
        this.activeTab = 'upload';

        // Initialize managers with reference to this UI
        this.processManager = new ProcessManager(this);
        this.fileManager = new FileManager(this);

        this.initializeApp();
    }

    async initializeApp() {
        await this.loadJSONFile();
        this.createInitialUI();
        this.setupEventListeners();
    }

    async loadJSONFile() {
        try {
            const response = await fetch('./src/data/file_path.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const jsonData = await response.json();
            
            this.generatedFiles = jsonData.map((file, index) => ({
                id: index + 1,
                path: file.file_path,
                name: file.file_path.split(/[\\\/]/).pop(),
                timestamp: 'From History'
            }));
            
        } catch (error) {
            console.error('Error loading JSON file:', error);
            this.generatedFiles = [];
        }
    }

    createInitialUI() {
        document.querySelector('#app').innerHTML = `
        <div class="container">
            <div class="header">
                <h1>Excel AI Updater</h1>
                <p>Upload images and Excel template to process invoices with AI</p>
            </div>

            <div class="tab-container">
                <div class="tab-nav">
                    <button class="tab-btn active" data-tab="upload">
                        <i class="fas fa-upload"></i> Upload Files
                    </button>
                    <button class="tab-btn" data-tab="output">
                        <i class="fas fa-download"></i> Generated Files
                        <span id="outputCount" class="tab-count">${this.generatedFiles.length}</span>
                    </button>
                </div>

                <div class="tab-content active" id="uploadTab">
                    <div class="section">
                        <h2>Image Upload</h2>
                        <div class="file-upload">
                            <button id="selectFolder" class="btn">
                                <i class="fas fa-images"></i> Select Image Folder
                            </button>
                            <div id="folderPath" class="path-info">
                                <div class="path-display empty">
                                    <i class="fas fa-folder"></i> No folder selected yet
                                </div>
                            </div>
                            <div id="imageList"></div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>Excel Template</h2>
                        <div class="file-upload">
                            <button id="selectExcel" class="btn excel-btn">
                                <i class="fas fa-file-excel"></i> Select Excel File
                            </button>
                            <div id="excelPath" class="path-info">
                                <div class="path-display empty">
                                    <i class="fas fa-file-excel"></i> No file selected yet
                                </div>
                            </div>
                            <div id="excelInfo"></div>
                        </div>
                    </div>
                    
                    <button id="process" class="btn primary" disabled>
                        <i class="fas fa-rocket"></i> Process Files
                    </button>
                </div>

                <div class="tab-content" id="outputTab">
                    <div class="section">
                        <h2>Generated Excel Files</h2>
                        <div id="outputFilesList" class="output-files-container">
                            <!-- Generated Excel files will appear here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        this.setupTabSwitching();
        this.updateOutputDisplay();
        this.updateOutputCounter();
    }

    setupEventListeners() {
        // Select folder button - Use FileManager
        const selectFolderBtn = document.getElementById('selectFolder');
        if (selectFolderBtn) {
            selectFolderBtn.addEventListener('click', async () => {
                await this.fileManager.selectFolder();
            });
        }

        // Select Excel button - Use FileManager
        const selectExcelBtn = document.getElementById('selectExcel');
        if (selectExcelBtn) {
            selectExcelBtn.addEventListener('click', async () => {
                await this.fileManager.selectExcelFile();
            });
        }

        // Process button - Use ProcessManager
        const processBtn = document.getElementById('process');
        if (processBtn) {
            processBtn.addEventListener('click', async () => {
                if (!this.selectedImagePaths.length || !this.selectedExcelPath) {
                    this.showError('Please select both images and Excel file');
                    return;
                }

                await this.processManager.processFiles();
            });
        }
    }

    updateOutputDisplay() {
        const outputContainer = document.getElementById('outputFilesList');
        
        if (!outputContainer) return;
        
        if (this.generatedFiles.length === 0) {
            outputContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-excel"></i>
                    <p>No files generated yet</p>
                    <small>Process some images to see generated Excel files here</small>
                </div>
            `;
            return;
        }

        outputContainer.innerHTML = `
            <div class="files-list">
                ${this.generatedFiles.map(file => `
                    <div class="file-item-row">
                        <div class="file-info">
                            <i class="fas fa-file-excel"></i>
                            <div class="file-details">
                                <span class="file-name" title="${file.name}">${file.name}</span>
                                <small class="file-time">${file.timestamp}</small>
                                <small class="file-path" title="${file.path}">${file.path}</small>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="btn-open" onclick="window.uiManager.openFile('${file.path.replace(/\\/g, '\\\\')}')" title="Open File">
                                <i class="fas fa-external-link-alt"></i> Open
                            </button>
                            <button class="btn-delete" onclick="window.uiManager.deleteFile(${file.id})" title="Remove from List">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    updateOutputCounter() {
        const counter = document.getElementById('outputCount');
        if (counter) {
            counter.textContent = this.generatedFiles.length;
            counter.style.display = this.generatedFiles.length > 0 ? 'inline' : 'none';
        }
    }

    addGeneratedFile(filePath) {
        const newFile = {
            id: this.generatedFiles.length + 1,
            path: filePath,
            name: filePath.split(/[\\\/]/).pop(),
            timestamp: new Date().toLocaleString()
        };

        this.generatedFiles.unshift(newFile);
        this.updateOutputDisplay();
        this.updateOutputCounter();
    }

    async deleteFile(fileId) {
        const fileToDelete = this.generatedFiles.find(f => f.id === fileId);
        if (!fileToDelete) {
            this.showError('File record not found');
            return;
        }
        
        try {
            const success = await fileStorage.deleteFromJSON(fileToDelete.path);
            
            if (success) {
                this.generatedFiles = this.generatedFiles.filter(f => f.id !== fileId);
                
                this.generatedFiles.forEach((file, index) => {
                    file.id = index + 1;
                });
                
                this.updateOutputDisplay();
                this.updateOutputCounter();
                
                this.showNotification(`"${fileToDelete.name}" removed from list (file preserved)`);
            } else {
                this.showError(`Failed to remove "${fileToDelete.name}" from list`);
            }
            
        } catch (error) {
            this.showError('Error removing file: ' + error.message);
        }
    }

    async openFile(filePath) {
        try {
            await OpenFile(filePath);
        } catch (error) {
            this.showError('Failed to open file: ' + error);
        }
    }

    switchToOutputTab() {
        document.querySelector('[data-tab="output"]')?.click();
    }

    setupTabSwitching() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                
                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(`${targetTab}Tab`).classList.add('active');
                
                this.activeTab = targetTab;
            });
        });
    }

    updateFolderDisplay(validFiles) {
        const folderPath = validFiles[0].Path.split('\\').slice(0, -1).join('\\');
        
        document.getElementById('folderPath').innerHTML = `
            <div class="path-display">
                <i class="fas fa-folder-open"></i> ${folderPath}
            </div>
        `;

        document.getElementById('imageList').innerHTML = `
            <div class="file-list">
                <div class="file-count">Found ${validFiles.length} image(s)</div>
                ${validFiles.map(file => `
                    <div class="file-item">
                        <span><i class="fas fa-image"></i> ${file.Name}</span>
                        <span class="file-type">Image</span>
                    </div>
                `).join('')}
            </div>
        `;

        this.selectedImagePaths = validFiles.map(file => file.Path);
        this.selectedImageFolder = folderPath;
        this.updateProcessButton();
    }

    updateExcelDisplay(excelFile) {
        document.getElementById('excelPath').innerHTML = `
            <div class="path-display">
                <i class="fas fa-file-excel"></i> ${excelFile.Path}
            </div>
        `;

        document.getElementById('excelInfo').innerHTML = `
            <div class="file-item">
                <span><i class="fas fa-file-excel"></i> ${excelFile.Name}</span>
                <span class="file-type">Excel</span>
            </div>
        `;

        this.selectedExcelPath = excelFile.Path;
        this.updateProcessButton();
    }

    updateProcessButton() {
        const hasImages = this.selectedImagePaths.length > 0;
        const hasExcel = this.selectedExcelPath !== '';
        const processBtn = document.getElementById('process');

        if (processBtn) {
            processBtn.disabled = !(hasImages && hasExcel);
        }
    }

    showError(message) {
        const existingError = document.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    showNotification(message) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'success-notification';
        notificationDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        document.body.appendChild(notificationDiv);
        setTimeout(() => notificationDiv.remove(), 3000);
    }

    showSuccessMessage(result) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `
            <div class="success-header">
                <i class="fas fa-check-circle"></i>
                <span>Success!</span>
            </div>
            <p>✅ ${result.message}</p>
        `;

        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            this.switchToOutputTab();
        }, 2000);
        
        setTimeout(() => successDiv.remove(), 5000);
    }
}

// Global functions for file operations
window.openFile = function(filePath) {
    console.log('Opening file:', filePath);
};

window.copyPath = function(filePath) {
    navigator.clipboard.writeText(filePath).then(() => {
        const notification = document.createElement('div');
        notification.className = 'copy-notification';
        notification.innerHTML = '<i class="fas fa-check"></i> Path copied to clipboard';
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
    });
};