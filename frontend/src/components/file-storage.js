import { DeleteFileFromJSON, AddFileToJSON } from '../../wailsjs/go/main/App.js';

export class FileStorage {

    async deleteFromJSON(filePath) {
        try {
            const success = await DeleteFileFromJSON(filePath);
            return success;
        } catch (error) {
            console.error('Error removing from JSON:', error);
            return false;
        }
    }

    async addToJSON(filePath) {
        try {
            const success = await AddFileToJSON(filePath);
            return success;
        } catch (error) {
            console.error('Error adding to JSON:', error);
            return false;
        }
    }

}

export const fileStorage = new FileStorage();