/**
 * Log Scanner Supreme - Frontend Application
 */

class LogScanner {
    constructor() {
        this.uploadedFile = null;
        this.filePath = null;
        this.chunkResults = {};       // keyed by chunk number (1-indexed)
        this.chunkMeta = [];          // metadata from preview
        this.allIssues = [];
        this.currentChunk = 0;
        this.settings = {};
        this.finalSummary = null;
        this.totalChunksAvailable = 0;
        this.expandedChunk = null;    // currently expanded chunk number
        this.analyzingChunks = new Set(); // chunks currently being analyzed
        
        this.init();
    }
    
    init() {
        // DOM Elements
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.fileInfo = document.getElementById('file-info');
        this.fileName = document.getElementById('file-name');
        this.fileMeta = document.getElementById('file-meta');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.fastSummaryBtn = document.getElementById('fast-summary-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.issueDescription = document.getElementById('issue-description');
        this.logTypeDisplay = document.getElementById('log-type-display');
        this.logTypeText = document.getElementById('log-type-text');
        this.detectedLogType = '';
        
        this.progressSection = document.getElementById('progress-section');
        this.progressFill = document.getElementById('progress-fill');
        this.progressStatus = document.getElementById('progress-status');
        this.chunkProgress = document.getElementById('chunk-progress');
        
        this.preprocessingSection = document.getElementById('preprocessing-section');
        this.errorCount = document.getElementById('error-count');
        this.warningCount = document.getElementById('warning-count');
        this.sampleIssues = document.getElementById('sample-issues');
        
        this.summarySection = document.getElementById('summary-section');
        this.executiveSummary = document.getElementById('executive-summary');
        this.keyFindings = document.getElementById('key-findings');
        this.rootCause = document.getElementById('root-cause');
        this.recommendations = document.getElementById('recommendations');
        
        this.issuesSection = document.getElementById('issues-section');
        this.issuesList = document.getElementById('issues-list');
        
        // Chunk selection elements
        this.chunkSelectionSection = document.getElementById('chunk-selection-section');
        this.chunkSelectionGrid = document.getElementById('chunk-selection-grid');
        this.analyzeAllBtn = document.getElementById('analyze-all-btn');
        this.generateSummaryBtn = document.getElementById('generate-summary-btn');
        
        // Settings elements
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.settingsClose = document.getElementById('settings-close');
        this.settingsCancel = document.getElementById('settings-cancel');
        this.settingsSave = document.getElementById('settings-save');
        this.apiKeyInput = document.getElementById('api-key-input');
        this.toggleApiKey = document.getElementById('toggle-api-key');
        this.testApiKey = document.getElementById('test-api-key');
        this.apiKeyStatus = document.getElementById('api-key-status');
        this.modelSelect = document.getElementById('model-select');
        this.fastModelSelect = document.getElementById('fast-model-select');
        this.chunkSizeInput = document.getElementById('chunk-size-input');
        this.apiKeyWarning = document.getElementById('api-key-warning');
        this.configureApiBtn = document.getElementById('configure-api-btn');
        
        // Prompt editor elements
        this.promptEditorModal = document.getElementById('prompt-editor-modal');
        this.editFastPromptsBtn = document.getElementById('edit-fast-prompts-btn');
        this.promptSystem = document.getElementById('prompt-system');
        this.promptUser = document.getElementById('prompt-user');
        this.promptFocus = document.getElementById('prompt-focus');
        this.promptEditorClose = document.getElementById('prompt-editor-close');
        this.promptEditorCancel = document.getElementById('prompt-editor-cancel');
        this.promptEditorSave = document.getElementById('prompt-editor-save');
        this.promptEditorReset = document.getElementById('prompt-editor-reset');
        
        // Event Listeners
        this.setupEventListeners();
        
        // Initialize chat elements
        this.initChatElements();
        
        // Load initial settings
        this.loadSettings();
    }
    
    setupEventListeners() {
        // File input
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });
        
        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('dragover');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });
        
        this.uploadArea.addEventListener('click', (e) => {
            if (e.target.tagName === 'LABEL' || 
                e.target.tagName === 'INPUT' || 
                e.target.closest('label')) {
                return;
            }
            this.fileInput.click();
        });
        
        this.fileInput.addEventListener('click', () => {
            this.fileInput.value = '';
        });
        
        // Buttons
        this.analyzeBtn.addEventListener('click', () => this.previewChunks());
        this.fastSummaryBtn.addEventListener('click', () => this.runFastSummary());
        this.analyzeAllBtn.addEventListener('click', () => this.startAnalysisAll());
        this.generateSummaryBtn.addEventListener('click', () => this.generateSummary());
        
        // Settings event listeners
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        this.settingsClose.addEventListener('click', () => this.closeSettings());
        this.settingsCancel.addEventListener('click', () => this.closeSettings());
        this.settingsSave.addEventListener('click', () => this.saveSettings());
        this.settingsModal.querySelector('.modal-overlay').addEventListener('click', () => this.closeSettings());
        
        this.toggleApiKey.addEventListener('click', () => {
            const type = this.apiKeyInput.type === 'password' ? 'text' : 'password';
            this.apiKeyInput.type = type;
            this.toggleApiKey.textContent = type === 'password' ? '👁️' : '🔒';
        });
        
        this.testApiKey.addEventListener('click', () => this.testApiKeyConnection());
        
        this.configureApiBtn.addEventListener('click', () => this.openSettings());
        this.clearBtn.addEventListener('click', () => this.clearFile());
        
        // Prompt editor event listeners
        this.editFastPromptsBtn.addEventListener('click', () => this.openPromptEditor());
        this.promptEditorClose.addEventListener('click', () => this.closePromptEditor());
        this.promptEditorCancel.addEventListener('click', () => this.closePromptEditor());
        this.promptEditorSave.addEventListener('click', () => this.savePrompts());
        this.promptEditorReset.addEventListener('click', () => this.resetPrompts());
        this.promptEditorModal.querySelector('.modal-overlay').addEventListener('click', () => this.closePromptEditor());
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.filterIssues(e.target.dataset.filter));
        });
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (!this.promptEditorModal.classList.contains('hidden')) {
                    this.closePromptEditor();
                } else if (!this.settingsModal.classList.contains('hidden')) {
                    this.closeSettings();
                }
            }
        });
    }
    
    // ==================== Settings Methods ====================
    
    formatModelLabel(model) {
        let label = model.name;
        if (model.max_context_tokens) {
            const ctxK = Math.round(model.max_context_tokens / 1000);
            label += ` [${ctxK}k ctx`;
            if (model.max_output_tokens) {
                const outK = Math.round(model.max_output_tokens / 1000);
                label += ` / ${outK}k out`;
            }
            label += ']';
        }
        return label;
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            
            this.settings = data;
            
            // Populate model selects
            this.modelSelect.innerHTML = '';
            this.fastModelSelect.innerHTML = '';
            if (data.available_models) {
                data.available_models.forEach(model => {
                    const label = this.formatModelLabel(model);
                    
                    const option1 = document.createElement('option');
                    option1.value = model.id;
                    option1.textContent = label;
                    option1.selected = model.id === data.model;
                    this.modelSelect.appendChild(option1);
                    
                    const option2 = document.createElement('option');
                    option2.value = model.id;
                    option2.textContent = label;
                    option2.selected = model.id === data.fast_model;
                    this.fastModelSelect.appendChild(option2);
                });
            }
            
            // Set chunk size
            this.chunkSizeInput.value = data.chunk_size || 3000;
            
            // Show/hide API key warning
            if (!data.api_key_configured) {
                this.apiKeyWarning.classList.remove('hidden');
            } else {
                this.apiKeyWarning.classList.add('hidden');
            }
            
            // Clear API key input (for security)
            this.apiKeyInput.value = '';
            this.apiKeyInput.placeholder = data.api_key_masked || 'sk-...';
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    openSettings() {
        this.settingsModal.classList.remove('hidden');
        this.apiKeyStatus.textContent = '';
        this.apiKeyStatus.className = 'api-key-status';
        document.body.style.overflow = 'hidden';
    }
    
    closeSettings() {
        this.settingsModal.classList.add('hidden');
        document.body.style.overflow = '';
        this.apiKeyInput.value = '';
        this.apiKeyInput.type = 'password';
        this.toggleApiKey.textContent = '👁️';
    }
    
    // ==================== Prompt Editor Methods ====================
    
    async openPromptEditor() {
        try {
            const response = await fetch('/api/prompts/fast_summary');
            if (!response.ok) throw new Error('Failed to load prompts');
            const data = await response.json();
            
            this.promptSystem.value = data.system_prompt || '';
            this.promptUser.value = data.user_prompt || '';
            this.promptFocus.value = data.focus_instruction_template || '';
            
            this.promptEditorModal.classList.remove('hidden');
        } catch (error) {
            console.error('Failed to load prompts:', error);
            alert('Failed to load prompts: ' + error.message);
        }
    }
    
    closePromptEditor() {
        this.promptEditorModal.classList.add('hidden');
    }
    
    async savePrompts() {
        const payload = {
            system_prompt: this.promptSystem.value,
            user_prompt: this.promptUser.value,
            focus_instruction_template: this.promptFocus.value
        };
        
        try {
            this.promptEditorSave.disabled = true;
            this.promptEditorSave.textContent = 'Saving...';
            
            const response = await fetch('/api/prompts/fast_summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            if (data.error) {
                alert('Error saving prompts: ' + data.error);
                return;
            }
            
            this.closePromptEditor();
        } catch (error) {
            alert('Failed to save prompts: ' + error.message);
        } finally {
            this.promptEditorSave.disabled = false;
            this.promptEditorSave.textContent = 'Save Prompts';
        }
    }
    
    async resetPrompts() {
        if (!confirm('Reset all Fast Summary prompts to defaults? This cannot be undone.')) return;
        
        try {
            const response = await fetch('/api/prompts/fast_summary');
            if (!response.ok) throw new Error('Failed to fetch current prompts');
            
            // Fetch the default prompts from the original file
            // We'll re-fetch and the backend will have defaults
            const defaultPrompts = {
                system_prompt: "You are an expert log analyst providing a fast summary of a log file.{{focus_instruction}}\n\nYou are given a condensed view of the log including the first and last 300 lines, plus all error/warning lines with ±4 lines of surrounding context.\n\nAnalyze the log file for:\n- Errors, exceptions, failures, crashes\n- Warnings and deprecations\n- Timeouts, excessive delays, slow operations\n- Dropped connections, connection resets, refused connections\n- Retries, backoff, throttling\n- Resource issues (memory, CPU, disk)\n\nIMPORTANT: Return ONLY a valid JSON object, no markdown code fences or extra text.\n\nReturn a JSON object with this structure:\n{\n    \"executive_summary\": \"A brief 3-5 sentence overview of the log file's health\",\n    \"overall_health\": \"healthy|degraded|critical\",\n    \"key_findings\": [\n        {\n            \"title\": \"Finding title\",\n            \"severity\": \"critical|high|medium|low\",\n            \"description\": \"Detailed description\",\n            \"affected_components\": [],\n            \"evidence\": \"Key log lines or patterns observed\"\n        }\n    ],\n    \"recommendations\": [\n        {\n            \"priority\": \"immediate|short-term|long-term\",\n            \"action\": \"Specific recommended action\",\n            \"rationale\": \"Why this action is recommended\"\n        }\n    ],\n    \"statistics\": {\n        \"total_errors\": 0,\n        \"total_warnings\": 0,\n        \"most_frequent_issue\": \"Description\"\n    }\n}\n\nReturn ONLY the JSON object.",
                user_prompt: "Provide a fast summary of this log file ({{total_lines}} total lines).\n\nPre-scan found {{error_count}} potential error lines and {{warning_count}} potential warning lines.\n\nHere is the condensed log content (error/warning lines with surrounding context, plus file start/end):\n\n```\n{{condensed_text}}\n```\n\nAnalyze and return your findings as JSON.",
                focus_instruction_template: "\n\n## PRIMARY FOCUS\nThe user is specifically investigating: \"{{issue_description}}\"\nPay special attention to anything related to this issue, but also report other serious problems."
            };
            
            const saveResponse = await fetch('/api/prompts/fast_summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(defaultPrompts)
            });
            
            if (saveResponse.ok) {
                this.promptSystem.value = defaultPrompts.system_prompt;
                this.promptUser.value = defaultPrompts.user_prompt;
                this.promptFocus.value = defaultPrompts.focus_instruction_template;
            }
        } catch (error) {
            alert('Failed to reset prompts: ' + error.message);
        }
    }
    
    // ==================== Save Settings ====================

    async saveSettings() {
        const apiKey = this.apiKeyInput.value.trim();
        const model = this.modelSelect.value;
        const fastModel = this.fastModelSelect.value;
        const chunkSize = parseInt(this.chunkSizeInput.value);
        
        // Validate chunk size
        if (chunkSize < 500 || chunkSize > 100000) {
            alert('Chunk size must be between 500 and 100,000');
            return;
        }
        
        const payload = {
            model: model,
            fast_model: fastModel,
            chunk_size: chunkSize
        };
        
        // Only include API key if a new one was entered
        if (apiKey) {
            payload.api_key = apiKey;
        }
        
        try {
            this.settingsSave.disabled = true;
            this.settingsSave.textContent = 'Saving...';
            
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert('Error saving settings: ' + data.error);
                return;
            }
            
            // Update local settings
            this.settings = { ...this.settings, ...data };
            
            // Update warning banner
            if (data.api_key_configured) {
                this.apiKeyWarning.classList.add('hidden');
            }
            
            // Update placeholder
            if (data.api_key_masked) {
                this.apiKeyInput.placeholder = data.api_key_masked;
            }
            
            this.closeSettings();
            
        } catch (error) {
            alert('Failed to save settings: ' + error.message);
        } finally {
            this.settingsSave.disabled = false;
            this.settingsSave.textContent = 'Save Settings';
        }
    }
    
    async testApiKeyConnection() {
        const apiKey = this.apiKeyInput.value.trim();
        
        this.testApiKey.disabled = true;
        this.testApiKey.textContent = 'Testing...';
        this.apiKeyStatus.textContent = '';
        this.apiKeyStatus.className = 'api-key-status';
        
        try {
            const response = await fetch('/api/settings/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey || null })
            });
            
            const data = await response.json();
            
            if (data.valid) {
                this.apiKeyStatus.textContent = '✅ ' + data.message;
                this.apiKeyStatus.className = 'api-key-status success';
            } else {
                this.apiKeyStatus.textContent = '❌ ' + data.error;
                this.apiKeyStatus.className = 'api-key-status error';
            }
            
        } catch (error) {
            this.apiKeyStatus.textContent = '❌ Connection failed: ' + error.message;
            this.apiKeyStatus.className = 'api-key-status error';
        } finally {
            this.testApiKey.disabled = false;
            this.testApiKey.textContent = 'Test API Key';
        }
    }
    
    // ==================== File Handling Methods ====================
    
    handleFileSelect(e) {
        if (e.target.files.length) {
            this.handleFile(e.target.files[0]);
        }
    }
    
    async handleFile(file) {
        // Validate file
        const allowedExtensions = ['log', 'txt', 'json', 'xml', 'csv', 'out', 'err'];
        const extension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(extension)) {
            alert(`File type .${extension} is not supported. Allowed: ${allowedExtensions.join(', ')}`);
            return;
        }
        
        this.uploadedFile = file;
        
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            this.filePath = data.filepath;
            this.showFileInfo(data);
            
            // Auto-detect log type
            this.detectLogType();
            
        } catch (error) {
            alert('Failed to upload file: ' + error.message);
        }
    }
    
    showFileInfo(data) {
        this.uploadArea.classList.add('hidden');
        this.fileInfo.classList.remove('hidden');
        
        this.fileName.textContent = data.filename;
        this.fileMeta.textContent = `${this.formatSize(data.size)} • ${data.lines.toLocaleString()} lines`;
    }
    
    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    
    clearFile() {
        this.uploadedFile = null;
        this.filePath = null;
        this.detectedLogType = '';
        this.chunkResults = {};
        this.chunkMeta = [];
        this.allIssues = [];
        this.finalSummary = null;
        this.totalChunksAvailable = 0;
        this.expandedChunk = null;
        this.analyzingChunks = new Set();
        
        this.uploadArea.classList.remove('hidden');
        this.fileInfo.classList.add('hidden');
        this.fileInput.value = '';
        
        // Hide log type display
        this.logTypeDisplay.classList.add('hidden');
        this.logTypeText.textContent = '';
        
        // Reset button text
        this.fastSummaryBtn.textContent = '⚡ Fast Summary';
        
        // Hide all result sections
        this.progressSection.classList.add('hidden');
        this.preprocessingSection.classList.add('hidden');
        this.summarySection.classList.add('hidden');
        this.issuesSection.classList.add('hidden');
        this.chunkSelectionSection.classList.add('hidden');
        
        // Hide and clear chat section
        if (this.chatSection) this.chatSection.classList.add('hidden');
        if (this.chatMessages) this.chatMessages.innerHTML = '';
        if (this.chunkContextArea) this.chunkContextArea.value = '';
        if (this.fullContextArea) this.fullContextArea.value = '';
        this.shadowContext = '';
        this.lastQuery = '';
        
        if (this.issueDescription) this.issueDescription.value = '';
    }
    
    // ==================== Log Type Detection ====================
    
    async detectLogType() {
        if (!this.filePath || !this.settings.api_key_configured) return;
        
        // Show detecting state and disable action buttons
        this.logTypeDisplay.classList.remove('hidden');
        this.logTypeDisplay.classList.add('detecting');
        this.logTypeText.textContent = '🔍 Detecting log type...';
        this.fastSummaryBtn.disabled = true;
        this.analyzeBtn.disabled = true;
        
        try {
            const response = await fetch('/api/detect-log-type', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath: this.filePath })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.logTypeDisplay.classList.add('hidden');
                this.fastSummaryBtn.disabled = false;
                this.analyzeBtn.disabled = false;
                console.error('Log type detection failed:', data.error);
                return;
            }
            
            this.detectedLogType = data.log_type || 'Unknown';
            
            this.logTypeDisplay.classList.remove('detecting');
            this.logTypeText.textContent = `📋 This appears to be a ${this.detectedLogType}`;
            if (data.description) {
                this.logTypeText.textContent += ` — ${data.description}`;
            }
            
            // Re-enable and update button text
            this.fastSummaryBtn.disabled = false;
            this.analyzeBtn.disabled = false;
            
        } catch (error) {
            this.logTypeDisplay.classList.add('hidden');
            this.fastSummaryBtn.disabled = false;
            this.analyzeBtn.disabled = false;
            console.error('Log type detection failed:', error);
        }
    }
    
    // ==================== Fast Summary ====================

    async runFastSummary() {
        if (!this.filePath) {
            alert('No file uploaded');
            return;
        }
        
        if (!this.settings.api_key_configured) {
            alert('Please configure your GitHub Personal Access Token in Settings before analyzing.');
            this.openSettings();
            return;
        }
        
        this.fastSummaryBtn.disabled = true;
        this.analyzeBtn.disabled = true;
        this.fastSummaryBtn.textContent = '⏳ Summarizing...';
        
        // Show progress
        this.progressSection.classList.remove('hidden');
        this.progressFill.style.width = '30%';
        this.progressStatus.textContent = 'Generating fast summary...';
        this.chunkProgress.innerHTML = '';
        
        // Hide previous results
        this.summarySection.classList.add('hidden');
        this.issuesSection.classList.add('hidden');
        this.chunkSelectionSection.classList.add('hidden');
        this.preprocessingSection.classList.add('hidden');
        
        try {
            const issueDesc = this.issueDescription ? this.issueDescription.value.trim() : '';
            
            const response = await fetch('/api/fast-summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filepath: this.filePath,
                    issue_description: issueDesc,
                    log_type: this.detectedLogType
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            this.progressFill.style.width = '100%';
            this.progressStatus.textContent = 'Fast summary complete!';
            
            // Show final summary
            if (data.final_summary) {
                this.finalSummary = data.final_summary;
                this.showFinalSummary(data.final_summary);
            }
            
            // Store condensed log for chat context
            if (data.condensed_log) {
                this.shadowContext = `### Raw Log Content (condensed view — first/last 300 lines + error/warning lines with context):\n\`\`\`\n${data.condensed_log}\n\`\`\``;
            }
            
            // Show chat section so user can ask follow-up questions
            this.showChatSection();
            
            setTimeout(() => {
                this.progressSection.classList.add('hidden');
            }, 1500);
            
        } catch (error) {
            alert('Fast summary failed: ' + error.message);
        } finally {
            this.fastSummaryBtn.disabled = false;
            this.analyzeBtn.disabled = false;
            this.fastSummaryBtn.textContent = '⚡ Fast Summary';
        }
    }
    
    async previewChunks() {
        if (!this.filePath) {
            alert('No file uploaded');
            return;
        }
        
        if (!this.settings.api_key_configured) {
            alert('Please configure your GitHub Personal Access Token in Settings before analyzing.');
            this.openSettings();
            return;
        }
        
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.textContent = '⏳ Loading chunks...';
        
        try {
            const response = await fetch('/api/preview-chunks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath: this.filePath })
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            document.getElementById('preview-error-count').textContent = data.preprocessing.error_count;
            document.getElementById('preview-warning-count').textContent = data.preprocessing.warning_count;
            
            this.totalChunksAvailable = data.total_chunks;
            this.chunkMeta = data.chunks_info;
            this.chunkResults = {};
            this.allIssues = [];
            this.expandedChunk = null;
            this.analyzingChunks = new Set();
            
            this.renderChunkGrid();
            
            this.chunkSelectionSection.classList.remove('hidden');
            this.chunkSelectionSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
        } catch (error) {
            alert('Failed to preview chunks: ' + error.message);
        } finally {
            this.analyzeBtn.disabled = false;
            this.analyzeBtn.textContent = '🚀 Analyze Log';
        }
    }
    
    // ==================== Dynamic Chunk Grid ====================
    
    renderChunkGrid() {
        let gridHtml = '';
        this.chunkMeta.forEach(chunk => {
            const result = this.chunkResults[chunk.num];
            const isAnalyzed = !!result;
            const isAnalyzing = this.analyzingChunks.has(chunk.num);
            const isExpanded = this.expandedChunk === chunk.num;
            const hasErrors = isAnalyzed && result.issues && result.issues.some(i => i.severity === 'error');
            const hasWarnings = isAnalyzed && result.issues && result.issues.some(i => i.severity === 'warning');
            const issueCount = isAnalyzed && result.issues ? result.issues.length : 0;
            
            let statusClass = '';
            let statusIcon = '';
            if (isAnalyzing) {
                statusClass = 'analyzing';
                statusIcon = '<span class="chunk-status-icon analyzing-spinner">⏳</span>';
            } else if (isAnalyzed) {
                statusClass = hasErrors ? 'scanned-errors' : (hasWarnings ? 'scanned-warnings' : 'scanned-clean');
                statusIcon = hasErrors ? '<span class="chunk-status-icon">⚠️</span>' : 
                             (hasWarnings ? '<span class="chunk-status-icon">⚡</span>' : 
                              '<span class="chunk-status-icon">✅</span>');
            } else {
                statusIcon = '<span class="chunk-status-icon">📄</span>';
            }
            
            gridHtml += `
                <div class="chunk-select-card ${statusClass} ${isExpanded ? 'expanded' : ''}" 
                     data-chunk="${chunk.num}" id="chunk-select-${chunk.num}">
                    <div class="chunk-select-header" data-chunk-header="${chunk.num}">
                        ${statusIcon}
                        <strong>Chunk ${chunk.num}</strong>
                        <span class="chunk-select-meta-inline">Lines ${chunk.lines} &bull; ${chunk.tokens} tok</span>
                        ${isAnalyzed && issueCount > 0 ? `<span class="chunk-issue-badge">${issueCount} issue${issueCount !== 1 ? 's' : ''}</span>` : ''}
                        ${isAnalyzed && issueCount === 0 ? '<span class="chunk-clean-badge">Clean</span>' : ''}
                        <span class="chunk-expand-icon">${isExpanded ? '▲' : '▼'}</span>
                    </div>
                    <div class="chunk-expand-content ${isExpanded ? '' : 'hidden'}" id="chunk-expand-${chunk.num}">
                        ${this.renderChunkExpandedContent(chunk.num)}
                    </div>
                </div>
            `;
        });
        this.chunkSelectionGrid.innerHTML = gridHtml;
        
        // Add click handlers to headers
        document.querySelectorAll('[data-chunk-header]').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation();
                const chunkNum = parseInt(header.dataset.chunkHeader);
                this.toggleChunkExpand(chunkNum);
            });
        });
        
        // Add click handlers to analyze buttons
        document.querySelectorAll('.chunk-analyze-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const chunkNum = parseInt(btn.dataset.chunk);
                this.analyzeSingleChunk(chunkNum);
            });
        });
        
        this.updateGenerateSummaryBtn();
    }
    
    renderChunkExpandedContent(chunkNum) {
        const result = this.chunkResults[chunkNum];
        const isAnalyzing = this.analyzingChunks.has(chunkNum);
        const chunk = this.chunkMeta.find(c => c.num === chunkNum);
        
        if (isAnalyzing) {
            return `
                <div class="chunk-detail-loading">
                    <div class="analyzing-indicator">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                    <p>Analyzing chunk ${chunkNum}...</p>
                </div>
            `;
        }
        
        if (!result) {
            return `
                <div class="chunk-detail-preview">
                    <div class="chunk-select-preview">${this.escapeHtml(chunk ? chunk.preview : '')}</div>
                    <button class="btn btn-primary btn-small chunk-analyze-btn" data-chunk="${chunkNum}">
                        🔍 Analyze This Chunk
                    </button>
                </div>
            `;
        }
        
        return this.renderChunkResults(result);
    }
    
    renderChunkResults(result) {
        let html = '<div class="chunk-detail-results">';
        html += `<div class="chunk-summary"><h4>📋 TL;DR</h4><p>${result.chunk_summary || 'No summary available'}</p></div>`;
        
        if (result.issues && result.issues.length > 0) {
            html += '<div class="chunk-issues"><h4>🚨 Issues Found:</h4>';
            result.issues.forEach(issue => {
                html += `
                    <div class="issue-card ${issue.severity}">
                        <div class="issue-header">
                            <span class="issue-type">
                                <span class="severity-badge ${issue.severity}">${issue.severity}</span>
                                ${issue.type}
                            </span>
                        </div>
                        <p class="issue-description">${issue.description}</p>
                        ${issue.possible_causes && issue.possible_causes.length > 0 ? `
                            <div class="issue-causes">
                                <strong>Possible Causes:</strong>
                                <ul>${issue.possible_causes.map(c => `<li>${c}</li>`).join('')}</ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<p class="muted" style="margin-top: 0.75rem;">No issues found in this chunk.</p>';
        }
        
        const hasPatterns = result.patterns_detected && result.patterns_detected.length > 0;
        const hasEvents = result.notable_events && result.notable_events.length > 0;
        
        if (hasPatterns || hasEvents) {
            html += '<div class="chunk-summary-section"><h4>📝 Summary:</h4>';
            if (hasPatterns) {
                html += '<div class="summary-subsection"><strong>Patterns Detected:</strong><ul>';
                result.patterns_detected.forEach(p => { html += `<li>${p}</li>`; });
                html += '</ul></div>';
            }
            if (hasEvents) {
                html += '<div class="summary-subsection"><strong>Notable Events:</strong><ul>';
                result.notable_events.forEach(ev => { html += `<li>${ev}</li>`; });
                html += '</ul></div>';
            }
            html += '</div>';
        }
        
        if (result.running_issues_update) {
            html += `<div class="chunk-context"><h4>🔗 Context Connection:</h4><p>${result.running_issues_update}</p></div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    toggleChunkExpand(chunkNum) {
        if (this.expandedChunk === chunkNum) {
            this.expandedChunk = null;
        } else {
            this.expandedChunk = chunkNum;
        }
        this.renderChunkGrid();
        
        if (this.expandedChunk) {
            const card = document.getElementById(`chunk-select-${chunkNum}`);
            if (card) {
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    }
    
    async analyzeSingleChunk(chunkNum) {
        if (this.analyzingChunks.has(chunkNum)) return;
        
        this.analyzingChunks.add(chunkNum);
        this.expandedChunk = chunkNum;
        this.renderChunkGrid();
        
        try {
            const issueDesc = this.issueDescription ? this.issueDescription.value.trim() : '';
            
            // Build running context from previously analyzed chunks
            let runningSummary = '';
            let previousIssues = [];
            for (let i = 1; i < chunkNum; i++) {
                const prev = this.chunkResults[i];
                if (prev) {
                    runningSummary += `\nChunk ${i}: ${prev.chunk_summary || 'No summary'}`;
                    if (prev.running_issues_update) {
                        runningSummary += ` | Issues: ${prev.running_issues_update}`;
                    }
                    if (prev.issues) {
                        previousIssues = previousIssues.concat(prev.issues);
                    }
                }
            }
            
            const response = await fetch('/api/analyze-chunk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filepath: this.filePath,
                    chunk_num: chunkNum,
                    issue_description: issueDesc,
                    running_summary: runningSummary,
                    previous_issues: previousIssues
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                alert(`Error analyzing chunk ${chunkNum}: ${result.error}`);
                return;
            }
            
            this.chunkResults[chunkNum] = result;
            
            if (result.issues && result.issues.length > 0) {
                result.issues.forEach(issue => {
                    issue.chunk = chunkNum;
                    this.allIssues.push(issue);
                });
            }
            
            this.updateIssuesSection();
            this.showChatSection();
            
        } catch (error) {
            alert(`Failed to analyze chunk ${chunkNum}: ${error.message}`);
        } finally {
            this.analyzingChunks.delete(chunkNum);
            this.renderChunkGrid();
        }
    }
    
    updateGenerateSummaryBtn() {
        const analyzedCount = Object.keys(this.chunkResults).length;
        if (analyzedCount > 0) {
            this.generateSummaryBtn.disabled = false;
            this.generateSummaryBtn.textContent = `📝 Generate Summary (${analyzedCount} chunks)`;
        } else {
            this.generateSummaryBtn.disabled = true;
            this.generateSummaryBtn.textContent = '📝 Generate Summary';
        }
    }
    
    async generateSummary() {
        const analyzedChunks = Object.keys(this.chunkResults).map(Number).sort((a, b) => a - b);
        if (analyzedChunks.length === 0) return;
        
        this.generateSummaryBtn.disabled = true;
        this.generateSummaryBtn.textContent = '⏳ Generating...';
        
        try {
            const issueDesc = this.issueDescription ? this.issueDescription.value.trim() : '';
            const response = await fetch('/analyze-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filepath: this.filePath,
                    issue_description: issueDesc,
                    selected_chunks: analyzedChunks
                })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'final_summary') {
                                this.finalSummary = data.data;
                                this.showFinalSummary(data.data);
                            } else if (data.type === 'complete') {
                                this.showChatSection();
                            } else if (data.type === 'chunk_result') {
                                const chunkNum = data.data.chunk_num;
                                this.chunkResults[chunkNum] = data.data;
                            }
                        } catch (e) {
                            console.error('Failed to parse:', line);
                        }
                    }
                }
            }
        } catch (error) {
            alert('Failed to generate summary: ' + error.message);
        } finally {
            this.generateSummaryBtn.disabled = false;
            this.updateGenerateSummaryBtn();
        }
    }
    
    // ==================== Analyze All (Streaming) ====================
    
    async startAnalysisAll() {
        if (!this.filePath) return;
        if (!this.settings.api_key_configured) {
            alert('Please configure your GitHub Personal Access Token in Settings before analyzing.');
            this.openSettings();
            return;
        }
        
        this.chunkResults = {};
        this.allIssues = [];
        
        this.progressSection.classList.remove('hidden');
        this.progressFill.style.width = '0%';
        this.progressStatus.textContent = 'Starting analysis...';
        this.chunkProgress.innerHTML = '';
        
        this.preprocessingSection.classList.add('hidden');
        this.summarySection.classList.add('hidden');
        this.issuesSection.classList.add('hidden');
        
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.textContent = '⏳ Analyzing...';
        this.analyzeAllBtn.disabled = true;
        
        try {
            const issueDesc = this.issueDescription ? this.issueDescription.value.trim() : '';
            const response = await fetch('/analyze-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    filepath: this.filePath,
                    issue_description: issueDesc
                })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleStreamUpdate(data);
                        } catch (e) {
                            console.error('Failed to parse:', line);
                        }
                    }
                }
            }
            
        } catch (error) {
            alert('Analysis failed: ' + error.message);
        } finally {
            this.analyzeBtn.disabled = false;
            this.analyzeBtn.textContent = '🚀 Analyze Log';
            this.analyzeAllBtn.disabled = false;
        }
    }
    
    handleStreamUpdate(data) {
        switch (data.type) {
            case 'status':
                this.progressStatus.textContent = data.message;
                break;
                
            case 'preprocessing':
                this.showPreprocessing(data.data);
                this.progressFill.style.width = '10%';
                break;
                
            case 'chunking':
                this.setupChunkProgress(data.data);
                this.progressFill.style.width = '15%';
                break;
                
            case 'chunk_result':
                this.handleChunkResult(data.data);
                break;
                
            case 'final_summary':
                this.finalSummary = data.data;
                this.showFinalSummary(data.data);
                this.progressFill.style.width = '95%';
                break;
                
            case 'complete':
                this.progressFill.style.width = '100%';
                this.progressStatus.textContent = `Analysis complete! Analyzed ${data.data.chunks_analyzed} chunks, found ${data.data.total_issues} issues.`;
                this.showChatSection();
                // Re-render the chunk grid with results
                this.renderChunkGrid();
                setTimeout(() => {
                    this.progressSection.classList.add('hidden');
                }, 2000);
                break;
                
            case 'error':
                this.progressStatus.textContent = `Error: ${data.error}`;
                this.progressFill.style.width = '0%';
                break;
        }
    }
    
    showPreprocessing(data) {
        // Stats already shown in the Log Chunks section; skip the duplicate card
        
        this.errorCount.textContent = data.error_count;
        this.warningCount.textContent = data.warning_count;
        
        // Show sample errors
        let samplesHtml = '';
        
        if (data.sample_errors.length > 0) {
            samplesHtml += '<h4>Sample Errors Found:</h4>';
            data.sample_errors.forEach(err => {
                samplesHtml += `
                    <div class="sample-issue">
                        <span class="line-num">Line ${err.line}:</span>
                        ${this.escapeHtml(err.content)}
                    </div>
                `;
            });
        }
        
        if (data.sample_warnings.length > 0) {
            samplesHtml += '<h4 style="margin-top: 1rem;">Sample Warnings Found:</h4>';
            data.sample_warnings.slice(0, 5).forEach(warn => {
                samplesHtml += `
                    <div class="sample-issue">
                        <span class="line-num">Line ${warn.line}:</span>
                        ${this.escapeHtml(warn.content)}
                    </div>
                `;
            });
        }
        
        this.sampleIssues.innerHTML = samplesHtml;
    }
    
    setupChunkProgress(data) {
        this.totalChunks = data.analyzed_chunks || data.total_chunks;
        
        let html = '';
        data.chunks_info.forEach(chunk => {
            html += `<span class="chunk-badge" id="chunk-badge-${chunk.num}">Chunk ${chunk.num}</span>`;
        });
        this.chunkProgress.innerHTML = html;
    }
    
    handleChunkResult(data) {
        // Store into chunkResults by chunk number
        this.chunkResults[data.chunk_num] = data;
        
        // Collect issues
        if (data.issues && data.issues.length > 0) {
            data.issues.forEach(issue => {
                issue.chunk = data.chunk_num;
                this.allIssues.push(issue);
            });
        }
        
        // Update progress badge
        const badge = document.getElementById(`chunk-badge-${data.chunk_num}`);
        if (badge) {
            badge.classList.remove('processing');
            badge.classList.add('complete');
            if (data.issues && data.issues.length > 0) {
                badge.textContent = `Chunk ${data.chunk_num} ⚠️`;
            }
        }
        
        const nextBadge = document.getElementById(`chunk-badge-${data.chunk_num + 1}`);
        if (nextBadge) {
            nextBadge.classList.add('processing');
        }
        
        const analyzedCount = Object.keys(this.chunkResults).length;
        const progress = 15 + (analyzedCount / this.totalChunks) * 75;
        this.progressFill.style.width = `${progress}%`;
        
        // Update issues section
        this.updateIssuesSection();
    }
    
    showFinalSummary(data) {
        this.summarySection.classList.remove('hidden');
        
        // Scaling Status (ARC controller logs)
        const scalingStatusEl = document.getElementById('scaling-status');
        if (data.scaling_status) {
            const ss = data.scaling_status;
            scalingStatusEl.classList.remove('hidden');
            
            let scaleSetsHtml = '';
            if (ss.scale_sets && ss.scale_sets.length > 0) {
                scaleSetsHtml = '<ul class="scaling-details">';
                ss.scale_sets.forEach(s => {
                    const upIcon = s.scales_up ? '✅' : '❌';
                    const downIcon = s.scales_down ? '✅' : '❌';
                    scaleSetsHtml += `<li><strong>${s.name}</strong>: ${s.min_observed} → ${s.max_observed} runners (scale up: ${upIcon} scale down: ${downIcon})</li>`;
                });
                scaleSetsHtml += '</ul>';
            }
            
            if (ss.is_scaling) {
                scalingStatusEl.className = 'scaling-status-banner scaling-healthy';
                scalingStatusEl.innerHTML = `
                    <div class="scaling-header">✅ ARC Scaling: Working</div>
                    <p>${ss.summary || 'Scale sets are scaling up and down successfully.'}</p>
                    ${scaleSetsHtml}
                    <p class="scaling-note">ARC is functioning correctly. Any remaining issues may be in the customer's Kubernetes environment.</p>
                `;
            } else {
                scalingStatusEl.className = 'scaling-status-banner scaling-unhealthy';
                scalingStatusEl.innerHTML = `
                    <div class="scaling-header">⚠️ ARC Scaling: Issues Detected</div>
                    <p>${ss.summary || 'No clear evidence of scale sets scaling up and down.'}</p>
                    ${scaleSetsHtml}
                `;
            }
        } else {
            scalingStatusEl.classList.add('hidden');
        }
        
        // Executive Summary
        const health = data.overall_health || 'unknown';
        this.executiveSummary.className = `executive-summary ${health}`;
        this.executiveSummary.innerHTML = `
            <span class="health-badge ${health}">${health}</span>
            <p>${data.executive_summary || 'Analysis complete.'}</p>
            ${data.issue_timeline ? `<p style="margin-top: 0.5rem; color: var(--text-secondary);"><strong>Timeline:</strong> ${data.issue_timeline}</p>` : ''}
        `;
        
        // Key Findings
        if (data.key_findings && data.key_findings.length > 0) {
            let findingsHtml = '';
            data.key_findings.forEach(finding => {
                findingsHtml += `
                    <div class="finding-card ${finding.severity}">
                        <div class="finding-title">
                            <span class="severity-badge ${finding.severity}">${finding.severity}</span>
                            ${finding.title}
                        </div>
                        <p>${finding.description}</p>
                        ${finding.affected_components ? `<p style="margin-top: 0.5rem; font-size: 0.9rem;"><strong>Affected:</strong> ${finding.affected_components.join(', ')}</p>` : ''}
                    </div>
                `;
            });
            this.keyFindings.innerHTML = findingsHtml;
        } else {
            this.keyFindings.innerHTML = '<p class="muted">No significant findings.</p>';
        }
        
        // Root Cause Analysis
        if (data.root_cause_analysis && data.root_cause_analysis.length > 0) {
            let rootCauseHtml = '';
            data.root_cause_analysis.forEach(rca => {
                rootCauseHtml += `
                    <div class="root-cause-card">
                        <div class="finding-title">
                            <span class="severity-badge ${rca.confidence}">${rca.confidence} confidence</span>
                            ${rca.issue}
                        </div>
                        <p><strong>Likely Root Cause:</strong> ${rca.likely_root_cause}</p>
                        <p style="color: var(--text-secondary); margin-top: 0.5rem;">${rca.reasoning}</p>
                    </div>
                `;
            });
            this.rootCause.innerHTML = rootCauseHtml;
        } else {
            this.rootCause.innerHTML = '<p class="muted">No root cause analysis available.</p>';
        }
        
        // Recommendations
        if (data.recommendations && data.recommendations.length > 0) {
            let recsHtml = '';
            data.recommendations.forEach(rec => {
                recsHtml += `
                    <div class="recommendation-card ${rec.priority}">
                        <div class="finding-title">
                            <span class="priority-badge ${rec.priority}">${rec.priority}</span>
                            ${rec.action}
                        </div>
                        <p style="color: var(--text-secondary);">${rec.rationale}</p>
                    </div>
                `;
            });
            this.recommendations.innerHTML = recsHtml;
        } else {
            this.recommendations.innerHTML = '<p class="muted">No specific recommendations.</p>';
        }
    }
    
    updateIssuesSection() {
        if (this.allIssues.length === 0) return;
        
        this.issuesSection.classList.remove('hidden');
        this.renderIssues(this.allIssues);
    }
    
    renderIssues(issues) {
        let html = '';
        issues.forEach(issue => {
            html += `
                <div class="issue-card ${issue.severity}" data-severity="${issue.severity}">
                    <div class="issue-header">
                        <span class="issue-type">
                            <span class="severity-badge ${issue.severity}">${issue.severity}</span>
                            ${issue.type}
                        </span>
                        <span class="issue-lines">Chunk ${issue.chunk}</span>
                    </div>
                    <p class="issue-description">${issue.description}</p>
                    ${issue.possible_causes && issue.possible_causes.length > 0 ? `
                        <div class="issue-causes">
                            <strong>Possible Causes:</strong>
                            <ul>
                                ${issue.possible_causes.map(c => `<li>${c}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${issue.context ? `<p style="margin-top: 0.5rem; color: var(--text-muted); font-size: 0.9rem;"><strong>Context:</strong> ${issue.context}</p>` : ''}
                </div>
            `;
        });
        this.issuesList.innerHTML = html;
    }
    
    filterIssues(filter) {
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        // Filter issues
        if (filter === 'all') {
            this.renderIssues(this.allIssues);
        } else {
            const filtered = this.allIssues.filter(i => i.severity === filter);
            this.renderIssues(filtered);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ==================== Chat Methods ====================
    
    initChatElements() {
        // Chat DOM elements
        this.chatSection = document.getElementById('chat-section');
        this.chunkContextArea = document.getElementById('chunk-context');
        this.fullContextArea = document.getElementById('full-context');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.chatSend = document.getElementById('chat-send');
        
        if (this.chatSend) {
            this.chatSend.addEventListener('click', () => this.sendChatMessage());
        }
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }
        
        // Collapsible issues section toggle - use event delegation since section may not exist yet
        document.addEventListener('click', (e) => {
            const header = e.target.closest('#issues-header');
            if (header) {
                header.classList.toggle('collapsed');
                const content = document.getElementById('issues-content');
                if (content) {
                    content.classList.toggle('collapsed');
                }
            }
        });
    }
    
    generateChunkContext() {
        // Use expanded chunk or first analyzed chunk
        const chunkNum = this.expandedChunk || Object.keys(this.chunkResults).map(Number).sort((a,b) => a-b)[0];
        if (!chunkNum) return '';
        
        const currentResult = this.chunkResults[chunkNum];
        if (!currentResult) return '';
        
        let context = `### Chunk ${currentResult.chunk_num} (Lines ${currentResult.lines})\n\n`;
        
        if (currentResult.chunk_summary) {
            context += `**TL;DR:** ${currentResult.chunk_summary}\n\n`;
        }
        
        if (currentResult.issues && currentResult.issues.length > 0) {
            context += `**Issues Found (${currentResult.issues.length}):**\n`;
            currentResult.issues.forEach((issue, idx) => {
                context += `${idx + 1}. [${issue.severity.toUpperCase()}] ${issue.type}: ${issue.description}\n`;
                if (issue.possible_causes && issue.possible_causes.length > 0) {
                    context += `   Possible causes: ${issue.possible_causes.join(', ')}\n`;
                }
            });
            context += '\n';
        }
        
        if (currentResult.patterns_detected && currentResult.patterns_detected.length > 0) {
            context += `**Patterns Detected:**\n`;
            currentResult.patterns_detected.forEach(pattern => { context += `- ${pattern}\n`; });
            context += '\n';
        }
        
        if (currentResult.notable_events && currentResult.notable_events.length > 0) {
            context += `**Notable Events:**\n`;
            currentResult.notable_events.forEach(event => { context += `- ${event}\n`; });
            context += '\n';
        }
        
        if (currentResult.running_issues_update) {
            context += `**Context Connection:** ${currentResult.running_issues_update}\n`;
        }
        
        return context;
    }
    
    generateFullContext() {
        let context = '';
        
        if (this.finalSummary) {
            context += `### Overall Analysis Summary\n\n`;
            context += `**Health Status:** ${this.finalSummary.overall_health || 'Unknown'}\n\n`;
            if (this.finalSummary.executive_summary) context += `**Executive Summary:** ${this.finalSummary.executive_summary}\n\n`;
            if (this.finalSummary.issue_timeline) context += `**Issue Timeline:** ${this.finalSummary.issue_timeline}\n\n`;
            
            if (this.finalSummary.key_findings && this.finalSummary.key_findings.length > 0) {
                context += `**Key Findings:**\n`;
                this.finalSummary.key_findings.forEach(f => {
                    context += `- [${f.severity.toUpperCase()}] ${f.title}: ${f.description}\n`;
                });
                context += '\n';
            }
            
            if (this.finalSummary.root_cause_analysis && this.finalSummary.root_cause_analysis.length > 0) {
                context += `**Root Cause Analysis:**\n`;
                this.finalSummary.root_cause_analysis.forEach(rca => {
                    context += `- Issue: ${rca.issue}\n  Root Cause: ${rca.likely_root_cause} (${rca.confidence} confidence)\n`;
                });
                context += '\n';
            }
        }
        
        if (this.allIssues.length > 0) {
            const errorCount = this.allIssues.filter(i => i.severity === 'error').length;
            const warningCount = this.allIssues.filter(i => i.severity === 'warning').length;
            const infoCount = this.allIssues.filter(i => i.severity === 'info').length;
            
            context += `### All Issues Summary\nTotal: ${this.allIssues.length} issues (${errorCount} errors, ${warningCount} warnings, ${infoCount} info)\n\n`;
            
            const issuesByType = {};
            this.allIssues.forEach(issue => {
                const key = `${issue.severity}:${issue.type}`;
                if (!issuesByType[key]) issuesByType[key] = { severity: issue.severity, type: issue.type, count: 0, examples: [] };
                issuesByType[key].count++;
                if (issuesByType[key].examples.length < 2) issuesByType[key].examples.push(issue.description);
            });
            
            Object.values(issuesByType).sort((a, b) => b.count - a.count).forEach(item => {
                context += `- **${item.type}** (${item.severity}): ${item.count} occurrences\n`;
                item.examples.forEach(ex => {
                    context += `  Example: ${ex.substring(0, 100)}${ex.length > 100 ? '...' : ''}\n`;
                });
            });
        }
        
        const analyzedNums = Object.keys(this.chunkResults).map(Number).sort((a,b) => a-b);
        if (analyzedNums.length > 0) {
            context += `\n### Chunk-by-Chunk Summary\n`;
            analyzedNums.forEach(num => {
                const chunk = this.chunkResults[num];
                context += `\n**Chunk ${chunk.chunk_num}** (Lines ${chunk.lines}):\n`;
                context += chunk.chunk_summary || 'No summary';
                context += '\n';
            });
        }
        
        return context;
    }
    
    updateChatContexts() {
        if (this.chunkContextArea) {
            this.chunkContextArea.value = this.generateChunkContext();
        }
        if (this.fullContextArea) {
            this.fullContextArea.value = this.generateFullContext();
        }
    }
    
    showChatSection() {
        if (this.chatSection) {
            this.chatSection.classList.remove('hidden');
            this.shadowContext = ''; // Initialize shadow context
            this.updateChatContexts();
        }
    }
    
    getRawExcerptForChunk(chunkNum) {
        const chunk = this.chunkResults[chunkNum];
        if (!chunk || !chunk.raw_excerpt) return '';
        return `### Raw Log Lines from Chunk ${chunk.chunk_num} (Lines ${chunk.lines}):\n\`\`\`\n${chunk.raw_excerpt}\n\`\`\``;
    }
    
    async sendChatMessage() {
        const query = this.chatInput.value.trim();
        if (!query) return;
        
        // Disable input while sending
        this.chatInput.disabled = true;
        this.chatSend.disabled = true;
        
        // Remove any existing suggestion buttons
        this.removeSuggestions();
        
        this.addChatMessage(query, 'user');
        this.chatInput.value = '';
        
        // Show typing indicator
        const typingId = this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    filepath: this.filePath || '',
                    chunk_context: this.chunkContextArea ? this.chunkContextArea.value : '',
                    full_context: this.fullContextArea ? this.fullContextArea.value : '',
                    shadow_context: this.shadowContext || ''
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (data.error) {
                this.addChatMessage(`Error: ${data.error}`, 'assistant error');
            } else {
                // Show retrieval steps if any occurred
                if (data.retrieval_steps && data.retrieval_steps.length > 0) {
                    this.addChatMessage('🔍 ' + data.retrieval_steps.join(' → '), 'system-info');
                }
                
                this.addChatMessage(data.response, 'assistant');
                
                // Show suggested follow-up buttons
                if (data.suggestions && data.suggestions.length > 0) {
                    this.showSuggestions(data.suggestions);
                }
            }
            
        } catch (error) {
            this.removeTypingIndicator(typingId);
            this.addChatMessage(`Error: ${error.message}`, 'assistant error');
        } finally {
            this.chatInput.disabled = false;
            this.chatSend.disabled = false;
            this.chatInput.focus();
        }
    }
    
    updateTypingIndicator(id, message) {
        const element = document.getElementById(id);
        if (element) {
            const bubble = element.querySelector('.chat-bubble');
            if (bubble) {
                bubble.innerHTML = `<span class="context-loading">${message}</span> <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;
            }
        }
    }
    
    addChatMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        
        // Convert markdown-style formatting to HTML for assistant messages
        if (role === 'assistant' && !role.includes('error')) {
            bubble.innerHTML = this.formatChatResponse(content);
        } else {
            bubble.textContent = content;
        }
        
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showSuggestions(suggestions) {
        this.removeSuggestions();
        const container = document.createElement('div');
        container.className = 'chat-suggestions';
        container.id = 'chat-suggestions';
        
        suggestions.forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'chat-suggestion-btn';
            btn.textContent = text;
            btn.addEventListener('click', () => {
                this.chatInput.value = text;
                this.sendChatMessage();
            });
            container.appendChild(btn);
        });
        
        this.chatMessages.appendChild(container);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    removeSuggestions() {
        const existing = document.getElementById('chat-suggestions');
        if (existing) existing.remove();
    }
    
    formatChatResponse(text) {
        // Simple markdown formatting
        let html = this.escapeHtml(text);
        
        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        
        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');
        
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }
    
    showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant';
        messageDiv.id = id;
        
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble typing';
        bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return id;
    }
    
    removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    new LogScanner();
});
