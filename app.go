package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	wailsRuntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

type App struct {
	ctx context.Context
}

type FileInfo struct {
	Name string
	Path string
	Type string
}

type FilePathEntry struct {
	FilePath string `json:"file_path"`
	Type     string `json:"type"`
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) DeleteFileFromJSON(filePath string) (bool, error) {
	jsonFilePath := "./frontend/src/data/file_path.json"

	var existingData []FilePathEntry

	if _, err := os.Stat(jsonFilePath); os.IsNotExist(err) {
		return false, fmt.Errorf("JSON file not found")
	}

	fileData, err := os.ReadFile(jsonFilePath)
	if err != nil {
		return false, err
	}

	err = json.Unmarshal(fileData, &existingData)
	if err != nil {
		return false, err
	}

	normalizedTarget := strings.ReplaceAll(strings.TrimSpace(filePath), "\\", "/")

	var updatedData []FilePathEntry
	found := false

	for _, item := range existingData {
		itemPath := strings.ReplaceAll(strings.TrimSpace(item.FilePath), "\\", "/")

		if itemPath == normalizedTarget || filepath.Base(itemPath) == filepath.Base(normalizedTarget) {
			found = true
			continue
		}

		updatedData = append(updatedData, item)
	}

	if !found {
		return false, fmt.Errorf("file path not found in JSON")
	}

	updatedJSON, err := json.MarshalIndent(updatedData, "", "  ")
	if err != nil {
		return false, err
	}

	err = os.WriteFile(jsonFilePath, updatedJSON, 0644)
	if err != nil {
		return false, err
	}

	return true, nil
}

func (a *App) AddFileToJSON(filePath string) (bool, error) {
	jsonFilePath := "./frontend/src/data/file_path.json"

	var existingData []FilePathEntry

	if _, err := os.Stat(jsonFilePath); !os.IsNotExist(err) {
		fileData, err := os.ReadFile(jsonFilePath)
		if err != nil {
			return false, err
		}

		json.Unmarshal(fileData, &existingData)
	}

	normalizedPath := strings.ReplaceAll(filePath, "\\", "/")
	for _, item := range existingData {
		if strings.ReplaceAll(item.FilePath, "\\", "/") == normalizedPath {
			return true, nil
		}
	}

	newEntry := FilePathEntry{
		FilePath: normalizedPath,
		Type:     "excel",
	}

	existingData = append([]FilePathEntry{newEntry}, existingData...)

	if len(existingData) > 50 {
		existingData = existingData[:50]
	}

	os.MkdirAll(filepath.Dir(jsonFilePath), 0755)

	updatedJSON, err := json.MarshalIndent(existingData, "", "  ")
	if err != nil {
		return false, err
	}

	err = os.WriteFile(jsonFilePath, updatedJSON, 0644)
	if err != nil {
		return false, err
	}

	return true, nil
}

func (a *App) SelectFolder() ([]FileInfo, error) {
	// Open folder selection dialog with smaller size
	selectedDir, err := wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:  "Select Image Folder",
	})
	if err != nil {
		return nil, err
	}

	// If no directory was selected, return empty result
	if selectedDir == "" {
		return []FileInfo{}, nil
	}

	var files []FileInfo
	// Read directory contents
	entries, err := os.ReadDir(selectedDir)
	if err != nil {
		return nil, err
	}

	// Process each file in the directory
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		filename := entry.Name()
		ext := strings.ToLower(filepath.Ext(filename))

		// Check if file is an image
		if ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".gif" {
			fullPath := filepath.Join(selectedDir, filename)
			files = append(files, FileInfo{
				Name: filename,
				Path: fullPath,
				Type: "image",
			})
		}
	}

	return files, nil
}

func (a *App) ValidateImgFiles(files []FileInfo) []FileInfo {
	var validFiles []FileInfo
	for _, file := range files {
		ext := strings.ToLower(filepath.Ext(file.Path))
		// Only validate image files here
		if ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".gif" {
			validFiles = append(validFiles, FileInfo{
				Name: file.Name,
				Path: file.Path,
				Type: "image",
			})
		}
	}
	return validFiles
}

// Add new function for Excel file selection
func (a *App) SelectExcelFile() (*FileInfo, error) {
	selectedFile, err := wailsRuntime.OpenFileDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title: "Select Excel File",
		Filters: []wailsRuntime.FileFilter{
			{
				DisplayName: "Excel Files (*.xlsx, *.xls)",
				Pattern:     "*.xlsx;*.xls",
			},
		},
	})

	if err != nil {
		return nil, err
	}

	if selectedFile == "" {
		return nil, nil
	}

	return &FileInfo{
		Name: filepath.Base(selectedFile),
		Path: selectedFile,
		Type: "excel",
	}, nil
}

func (a *App) ValidateExcelFile(file *FileInfo) bool {
	if file == nil {
		return false
	}
	ext := strings.ToLower(filepath.Ext(file.Path))
	return ext == ".xlsx" || ext == ".xls"
}

// NEW: Open file in default application
func (a *App) OpenFile(filePath string) error {
	// Clean and validate the file path
	cleanPath := filepath.Clean(filePath)

	// Check if file exists
	if _, err := os.Stat(cleanPath); os.IsNotExist(err) {
		return fmt.Errorf("file does not exist: %s", cleanPath)
	}

	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "windows":
		// Use 'start' command on Windows
		cmd = exec.Command("cmd", "/c", "start", "", cleanPath)
	case "darwin":
		// Use 'open' command on macOS
		cmd = exec.Command("open", cleanPath)
	case "linux":
		// Use 'xdg-open' command on Linux
		cmd = exec.Command("xdg-open", cleanPath)
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}

	return nil
}

// NEW: Open folder in file explorer
func (a *App) OpenFolder(folderPath string) error {
	// Clean and validate the folder path
	cleanPath := filepath.Clean(folderPath)

	// Check if folder exists
	if _, err := os.Stat(cleanPath); os.IsNotExist(err) {
		return fmt.Errorf("folder does not exist: %s", cleanPath)
	}

	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "windows":
		// Use 'explorer' command on Windows
		cmd = exec.Command("explorer", cleanPath)
	case "darwin":
		// Use 'open' command on macOS
		cmd = exec.Command("open", cleanPath)
	case "linux":
		// Use file manager on Linux (try multiple options)
		fileManagers := []string{"nautilus", "dolphin", "thunar", "pcmanfm", "caja"}
		for _, fm := range fileManagers {
			if _, err := exec.LookPath(fm); err == nil {
				cmd = exec.Command(fm, cleanPath)
				break
			}
		}
		if cmd == nil {
			return fmt.Errorf("no suitable file manager found on Linux")
		}
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to open folder: %v", err)
	}

	return nil
}

// NEW: Get file size in human readable format
func (a *App) GetFileSize(filePath string) (string, error) {
	cleanPath := filepath.Clean(filePath)

	info, err := os.Stat(cleanPath)
	if err != nil {
		return "", err
	}

	size := info.Size()

	// Convert to human readable format
	const unit = 1024
	if size < unit {
		return fmt.Sprintf("%d B", size), nil
	}

	div, exp := int64(unit), 0
	for n := size / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}

	units := []string{"KB", "MB", "GB", "TB"}
	return fmt.Sprintf("%.1f %s", float64(size)/float64(div), units[exp]), nil
}
