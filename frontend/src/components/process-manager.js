import { LoadingManager } from './loading-manager.js';
import { ApiService } from './api-service.js';
import { fileStorage } from './file-storage.js';

export class ProcessManager {
    constructor(uiManager) {
        this.ui = uiManager;
        this.loadingManager = new LoadingManager();
        this.apiService = new ApiService();
    }

    async processFiles(customOutputPath = null) {
        try {
            // Validate selections
            if (!this.ui.selectedImagePaths || this.ui.selectedImagePaths.length === 0 || !this.ui.selectedExcelPath) {
                this.ui.showError('Please select both image folder and Excel file');
                return;
            }

            // Disable the process button and show loading state
            const processBtn = document.getElementById('process');
            if (processBtn) {
                processBtn.disabled = true;
                processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }

            // Show loading overlay
            this.loadingManager.show();

            // Generate unique output path based on Excel file name if not provided
            let outputPath = customOutputPath;
            if (!outputPath) {
                outputPath = this.generateOutputPathFromExcel(this.ui.selectedExcelPath);
            }

            // Process files with unique output path
            const result = await this.apiService.processFiles(
                this.ui.selectedImageFolder, 
                this.ui.selectedExcelPath,
                outputPath
            );
            
            // Hide loading overlay
            this.loadingManager.hide();
            
            // Check for success and extract the file path
            if (result.success === true) {
                // Extract the actual file path from Python response
                const actualFilePath = result.excel_file_path;
                
                if (actualFilePath) {
                    console.log('📁 Generated file path:', actualFilePath);
                    
                    // Add to JSON file
                    try {
                        await fileStorage.addToJSON(actualFilePath);
                        console.log('✅ Added to JSON successfully');
                        
                        // Add to UI display
                        this.ui.addGeneratedFile(actualFilePath);
                        
                        // Show success message
                        this.ui.showSuccessMessage({
                            ...result,
                            data: { updated_excel_path: actualFilePath }
                        });
                        
                    } catch (jsonError) {
                        console.error('❌ Error adding to JSON:', jsonError);
                        // Still show success but with warning
                        this.ui.showSuccessMessage(result);
                        this.ui.showNotification('File processed but failed to save to history');
                    }
                } else {
                    console.warn('⚠️ No file path returned from Python');
                    this.ui.showSuccessMessage(result);
                }
            } else {
                this.ui.showError(result.message || 'Processing completed with issues');
            }
            
        } catch (err) {
            console.error('❌ Processing error:', err);
            this.loadingManager.hide();
            
            // Better error handling for fetch failures
            if (err.message.includes('Cannot connect to server')) {
                this.ui.showError(err.message);
            } else {
                this.ui.showError('Processing error: ' + err.message);
            }
        } finally {
            // Re-enable the process button
            const processBtn = document.getElementById('process');
            if (processBtn) {
                processBtn.disabled = false;
                processBtn.innerHTML = '<i class="fas fa-rocket"></i> Process Files';
            }
        }
    }

    /**
     * Generate output path based on Excel file name with incremental numbering
     * @param {string} excelPath - Path to Excel template file
     * @returns {string} Unique numbered output path
     */
    generateOutputPathFromExcel(excelPath) {
        // Extract file name from Excel path
        const pathParts = excelPath.replace(/\\/g, '/').split('/');
        const fileName = pathParts[pathParts.length - 1];
        
        // Remove extension and get base name
        const baseName = fileName.replace(/\.[^/.]+$/, '');
        const extension = fileName.match(/\.[^/.]+$/)?.[0] || '.xlsx';
        
        // Generate unique path with timestamp
        const timestamp = Date.now();
        const counter = 1;
        const uniqueName = `${baseName}_${counter}_${timestamp}${extension}`;
        const outputPath = `C:/Users/tanwa/Downloads/${uniqueName}`;
        
        return outputPath;
    }

    /**
     * Generate path with timestamp instead of counter
     * @param {string} excelPath - Path to Excel template file
     * @returns {string} Timestamped output path
     */
    generateTimestampedOutputPath(excelPath) {
        const pathParts = excelPath.replace(/\\/g, '/').split('/');
        const fileName = pathParts[pathParts.length - 1];
        
        const baseName = fileName.replace(/\.[^/.]+$/, '');
        const extension = fileName.match(/\.[^/.]+$/)?.[0] || '.xlsx';
        
        const now = new Date();
        const timestamp = now.toISOString()
            .replace(/[:-]/g, '')
            .replace(/\..+/, '')
            .replace('T', '_');
        
        const timestampedName = `${baseName}_${timestamp}${extension}`;
        const outputPath = `C:/Users/tanwa/Downloads/${timestampedName}`;
        
        return outputPath;
    }

    /**
     * Simple counter-based naming
     * @param {string} excelPath - Path to Excel template file
     * @returns {string} Counter-based output path
     */
    generateCounterBasedPath(excelPath) {
        const pathParts = excelPath.replace(/\\/g, '/').split('/');
        const fileName = pathParts[pathParts.length - 1];
        
        const baseName = fileName.replace(/\.[^/.]+$/, '');
        const extension = fileName.match(/\.[^/.]+$/)?.[0] || '.xlsx';
        
        const counter = Date.now() % 10000;
        const numberedName = `${baseName}_${counter}${extension}`;
        const outputPath = `C:/Users/tanwa/Downloads/${numberedName}`;
        
        return outputPath;
    }

    /**
     * Process files to a custom directory with Excel-based naming
     * @param {string} customOutputDir - Custom output directory path
     */
    async processFilesToCustomDirectory(customOutputDir) {
        const pathParts = this.ui.selectedExcelPath.replace(/\\/g, '/').split('/');
        const fileName = pathParts[pathParts.length - 1];
        const baseName = fileName.replace(/\.[^/.]+$/, '');
        const extension = fileName.match(/\.[^/.]+$/)?.[0] || '.xlsx';
        
        const timestamp = Date.now();
        const customFileName = `${baseName}_${timestamp}${extension}`;
        const customOutputPath = `${customOutputDir}/${customFileName}`;
        
        await this.processFiles(customOutputPath);
    }
}