/**
 * Log Scanner Supreme - Frontend Application
 */

class LogScanner {
    constructor() {
        this.uploadedFile = null;
        this.filePath = null;
        this.chunkResults = [];
        this.allIssues = [];
        this.currentChunk = 0;
        this.settings = {};
        
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
        this.clearBtn = document.getElementById('clear-btn');
        
        this.progressSection = document.getElementById('progress-section');
        this.progressFill = document.getElementById('progress-fill');
        this.progressStatus = document.getElementById('progress-status');
        this.chunkProgress = document.getElementById('chunk-progress');
        
        this.preprocessingSection = document.getElementById('preprocessing-section');
        this.errorCount = document.getElementById('error-count');
        this.warningCount = document.getElementById('warning-count');
        this.sampleIssues = document.getElementById('sample-issues');
        
        this.chunksSection = document.getElementById('chunks-section');
        this.chunkTabs = document.getElementById('chunk-tabs');
        this.chunkContent = document.getElementById('chunk-content');
        
        this.summarySection = document.getElementById('summary-section');
        this.executiveSummary = document.getElementById('executive-summary');
        this.keyFindings = document.getElementById('key-findings');
        this.rootCause = document.getElementById('root-cause');
        this.recommendations = document.getElementById('recommendations');
        
        this.issuesSection = document.getElementById('issues-section');
        this.issuesList = document.getElementById('issues-list');
        
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
        this.chunkSizeInput = document.getElementById('chunk-size-input');
        this.apiKeyWarning = document.getElementById('api-key-warning');
        this.configureApiBtn = document.getElementById('configure-api-btn');
        
        // Event Listeners
        this.setupEventListeners();
        
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
        
        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // Buttons
        this.analyzeBtn.addEventListener('click', () => this.startAnalysis());
        
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
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.filterIssues(e.target.dataset.filter));
        });
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.settingsModal.classList.contains('hidden')) {
                this.closeSettings();
            }
        });
    }
    
    // ==================== Settings Methods ====================
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            
            this.settings = data;
            
            // Populate model select
            this.modelSelect.innerHTML = '';
            if (data.available_models) {
                data.available_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    option.selected = model.id === data.model;
                    this.modelSelect.appendChild(option);
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
    
    async saveSettings() {
        const apiKey = this.apiKeyInput.value.trim();
        const model = this.modelSelect.value;
        const chunkSize = parseInt(this.chunkSizeInput.value);
        
        // Validate chunk size
        if (chunkSize < 500 || chunkSize > 10000) {
            alert('Chunk size must be between 500 and 10000');
            return;
        }
        
        const payload = {
            model: model,
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
        
        if (file.size > 50 * 1024 * 1024) {
            alert('File size exceeds 50MB limit.');
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
        this.chunkResults = [];
        this.allIssues = [];
        
        this.uploadArea.classList.remove('hidden');
        this.fileInfo.classList.add('hidden');
        this.fileInput.value = '';
        
        // Hide all result sections
        this.progressSection.classList.add('hidden');
        this.preprocessingSection.classList.add('hidden');
        this.chunksSection.classList.add('hidden');
        this.summarySection.classList.add('hidden');
        this.issuesSection.classList.add('hidden');
    }
    
    async startAnalysis() {
        if (!this.filePath) {
            alert('No file uploaded');
            return;
        }
        
        // Check if API key is configured
        if (!this.settings.api_key_configured) {
            alert('Please configure your GitHub Personal Access Token in Settings before analyzing.');
            this.openSettings();
            return;
        }
        
        // Reset state
        this.chunkResults = [];
        this.allIssues = [];
        
        // Show progress
        this.progressSection.classList.remove('hidden');
        this.progressFill.style.width = '0%';
        this.progressStatus.textContent = 'Starting analysis...';
        this.chunkProgress.innerHTML = '';
        
        // Hide other sections initially
        this.preprocessingSection.classList.add('hidden');
        this.chunksSection.classList.add('hidden');
        this.summarySection.classList.add('hidden');
        this.issuesSection.classList.add('hidden');
        
        // Disable button
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.textContent = '⏳ Analyzing...';
        
        try {
            const response = await fetch('/analyze-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filepath: this.filePath })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete events
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
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
                this.showFinalSummary(data.data);
                this.progressFill.style.width = '95%';
                break;
                
            case 'complete':
                this.progressFill.style.width = '100%';
                this.progressStatus.textContent = `Analysis complete! Analyzed ${data.data.chunks_analyzed} chunks, found ${data.data.total_issues} issues.`;
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
        this.preprocessingSection.classList.remove('hidden');
        
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
        this.totalChunks = data.total_chunks;
        
        let html = '';
        data.chunks_info.forEach(chunk => {
            html += `<span class="chunk-badge" id="chunk-badge-${chunk.num}">Chunk ${chunk.num}</span>`;
        });
        this.chunkProgress.innerHTML = html;
    }
    
    handleChunkResult(data) {
        this.chunkResults.push(data);
        
        // Collect issues
        if (data.issues && data.issues.length > 0) {
            data.issues.forEach(issue => {
                issue.chunk = data.chunk_num;
                this.allIssues.push(issue);
            });
        }
        
        // Update progress
        const badge = document.getElementById(`chunk-badge-${data.chunk_num}`);
        if (badge) {
            badge.classList.remove('processing');
            badge.classList.add('complete');
            if (data.issues && data.issues.length > 0) {
                badge.textContent = `Chunk ${data.chunk_num} ⚠️`;
            }
        }
        
        // Mark next chunk as processing
        const nextBadge = document.getElementById(`chunk-badge-${data.chunk_num + 1}`);
        if (nextBadge) {
            nextBadge.classList.add('processing');
        }
        
        // Update progress bar
        const progress = 15 + (data.chunk_num / this.totalChunks) * 75;
        this.progressFill.style.width = `${progress}%`;
        
        // Update chunks section
        this.updateChunksSection();
        
        // Update issues section
        this.updateIssuesSection();
    }
    
    updateChunksSection() {
        this.chunksSection.classList.remove('hidden');
        
        // Build tabs
        let tabsHtml = '';
        this.chunkResults.forEach((result, index) => {
            const hasErrors = result.issues && result.issues.some(i => i.severity === 'error');
            const activeClass = index === this.currentChunk ? 'active' : '';
            const errorClass = hasErrors ? 'has-errors' : '';
            tabsHtml += `
                <button class="chunk-tab ${activeClass} ${errorClass}" data-chunk="${index}">
                    Chunk ${result.chunk_num}
                    ${hasErrors ? '⚠️' : '✓'}
                </button>
            `;
        });
        this.chunkTabs.innerHTML = tabsHtml;
        
        // Add click handlers
        document.querySelectorAll('.chunk-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.currentChunk = parseInt(e.target.dataset.chunk);
                this.updateChunksSection();
            });
        });
        
        // Show current chunk content
        this.showChunkContent(this.chunkResults[this.currentChunk]);
    }
    
    showChunkContent(result) {
        let html = `
            <div class="chunk-summary">
                <h4>Lines ${result.lines}</h4>
                <p>${result.chunk_summary || 'No summary available'}</p>
            </div>
        `;
        
        // Issues
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
                                <ul>
                                    ${issue.possible_causes.map(c => `<li>${c}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
        }
        
        // Patterns
        if (result.patterns_detected && result.patterns_detected.length > 0) {
            html += '<div class="chunk-patterns"><h4>📊 Patterns Detected:</h4><ul>';
            result.patterns_detected.forEach(pattern => {
                html += `<li>${pattern}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Notable Events
        if (result.notable_events && result.notable_events.length > 0) {
            html += '<div class="chunk-events"><h4>📝 Notable Events:</h4><ul>';
            result.notable_events.forEach(event => {
                html += `<li>${event}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Running Issues Update
        if (result.running_issues_update) {
            html += `
                <div class="chunk-context">
                    <h4>🔗 Context Connection:</h4>
                    <p>${result.running_issues_update}</p>
                </div>
            `;
        }
        
        this.chunkContent.innerHTML = html;
    }
    
    showFinalSummary(data) {
        this.summarySection.classList.remove('hidden');
        
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
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    new LogScanner();
});
