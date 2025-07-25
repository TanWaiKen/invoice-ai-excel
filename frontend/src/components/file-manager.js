import {SelectFolder, ValidateImgFiles, SelectExcelFile, ValidateExcelFile} from "../../wailsjs/go/main/App.js";

export class FileManager {
    constructor(uiManager) {
        this.ui = uiManager;
    }

    async selectFolder() {
        try {
            const files = await SelectFolder();
            if (!files || files.length === 0) {
                return; // User cancelled or no files
            }

            const validFiles = await ValidateImgFiles(files);
            if (validFiles.length === 0) {
                this.ui.showError('No valid image files found in the selected folder');
                return;
            }

            this.ui.updateFolderDisplay(validFiles);
        } catch (err) {
            this.ui.showError('Error selecting folder: ' + err.message);
            console.error('Folder selection error:', err);
        }
    }

    async selectExcelFile() {
        try {
            const excelFile = await SelectExcelFile();
            if (!excelFile) {
                return; // User cancelled selection
            }

            const isValid = await ValidateExcelFile(excelFile);
            if (!isValid) {
                this.ui.showError('Selected file is not a valid Excel file');
                return;
            }
            
            this.ui.updateExcelDisplay(excelFile);
        } catch (err) {
            this.ui.showError('Error selecting Excel file: ' + err.message);
            console.error('Excel file selection error:', err);
        }
    }
}