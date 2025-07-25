export class ApiService {
    constructor() {
        this.API_URL = 'http://localhost:8000';
    }

    async processFiles(imageFolder, excelPath, outputPath = null) {
        try {
            console.log('🚀 Starting process...');
            
            // Health check first
            console.log('🔍 Checking server health...');
            await this.healthCheck();
            console.log('✅ Server is healthy, proceeding...');
            
            // Prepare request data
            const requestData = {
                image_folder: imageFolder,
                excel_template_path: excelPath,
                output_excel_path: outputPath
            };
            
            console.log('📤 Sending request:', requestData);

            const response = await fetch(`${this.API_URL}/process-invoices`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('❌ Error response:', errorData);
                throw new Error(errorData.detail || 'Failed to process files');
            }

            const data = await response.json();
            console.log('✅ Processing completed successfully');
            console.log('📄 Response data:', data);
            
            return {
                success: true,
                ...data
            };
        } catch (error) {
            console.error('❌ API Error:', error);
            throw new Error('Error processing files: ' + error.message);
        }
    }

    async healthCheck() {
        try {
            const response = await fetch(`${this.API_URL}/health`);
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Health check failed:', error);
            throw new Error('Cannot connect to server. Please ensure the Python backend is running on http://localhost:8000');
        }
    }
}

// Export default instance
export const apiService = new ApiService();