document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const progressContainer = document.getElementById('uploadProgressContainer');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const progressPercentage = document.getElementById('progressPercentage');
    const progressBar = document.getElementById('progressBar');
    
    const notification = document.getElementById('notification');
    const notificationIcon = document.getElementById('notificationIcon');
    const notificationTitle = document.getElementById('notificationTitle');
    const notificationMessage = document.getElementById('notificationMessage');

    const resultsPanel = document.getElementById('resultsPanel');
    const statTestCases = document.getElementById('statTestCases');
    const statErrors = document.getElementById('statErrors');
    const statWarnings = document.getElementById('statWarnings');
    const aiSummaryBox = document.getElementById('aiSummaryBox');
    const aiSummaryText = document.getElementById('aiSummaryText');
    const reportDownloads = document.getElementById('reportDownloads');
    const downloadPdfLink = document.getElementById('downloadPdfLink');
    const downloadXlsxLink = document.getElementById('downloadXlsxLink');

    // Trigger click on input when clicking dropzone
    dropzone.addEventListener('click', () => fileInput.click());

    // File change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag-over styling
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('border-indigo-500', 'bg-slate-900/40');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('border-indigo-500', 'bg-slate-900/40');
        }, false);
    });

    // Drop handler
    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    function showNotification(type, title, message) {
        notification.classList.remove('hidden', 'bg-emerald-500/10', 'border-emerald-500/20', 'text-emerald-400', 'bg-rose-500/10', 'border-rose-500/20', 'text-rose-400');
        
        if (type === 'success') {
            notification.classList.add('bg-emerald-500/10', 'border-emerald-500/20', 'text-emerald-400');
            notificationIcon.innerHTML = `
                <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
        } else {
            notification.classList.add('bg-rose-500/10', 'border-rose-500/20', 'text-rose-400');
            notificationIcon.innerHTML = `
                <svg class="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
        }
        
        notificationTitle.textContent = title;
        notificationMessage.textContent = message;
        notification.classList.remove('hidden');
    }

    function handleFileUpload(file) {
        // Reset states
        progressContainer.classList.remove('hidden');
        notification.classList.add('hidden');
        resultsPanel.classList.add('hidden');
        aiSummaryBox.classList.add('hidden');
        reportDownloads.classList.add('hidden');
        fileNameDisplay.textContent = file.name;
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        
        // Reset color classes for progress bar
        progressBar.className = 'h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-150';
        
        // Use XMLHttpRequest to track progress
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressPercentage.textContent = percentComplete + '%';
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                const response = JSON.parse(xhr.responseText);

                if (response.status === 'failed') {
                    progressBar.className = 'h-full bg-rose-500 rounded-full transition-all duration-150';
                    showNotification('error', 'Analysis Failed', response.error || 'The pipeline could not process this file.');
                    return;
                }

                progressBar.className = 'h-full bg-emerald-500 rounded-full transition-all duration-150';
                showNotification('success', 'Analysis Complete', `${file.name} ran through the full pipeline successfully.`);
                showResults(response);
            } else {
                let errorMsg = 'An error occurred during upload.';
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.detail || errorMsg;
                } catch(e) {}
                progressBar.className = 'h-full bg-rose-500 rounded-full transition-all duration-150';
                showNotification('error', 'Upload Failed', errorMsg);
            }
        });

        xhr.addEventListener('error', () => {
            progressBar.className = 'h-full bg-rose-500 rounded-full transition-all duration-150';
            showNotification('error', 'Upload Failed', 'Network error or connection lost.');
        });

        // Uploading the spec file runs it through the full pipeline:
        // Parse -> Rule Engine -> AI Analysis -> Report.
        xhr.open('POST', '/api/v1/workspaces');
        xhr.send(formData);
    }

    function showResults(response) {
        const spec = response.spec || { test_cases: [] };
        const ruleEngine = response.rule_engine || { error_count: 0, warning_count: 0 };
        const aiAnalysis = response.ai_analysis;

        statTestCases.textContent = spec.test_cases ? spec.test_cases.length : 0;
        statErrors.textContent = ruleEngine.error_count || 0;
        statWarnings.textContent = ruleEngine.warning_count || 0;

        if (aiAnalysis && aiAnalysis.summary) {
            aiSummaryText.textContent = aiAnalysis.summary;
            aiSummaryBox.classList.remove('hidden');
        }

        if (response.report_pdf_url && response.report_xlsx_url) {
            downloadPdfLink.href = response.report_pdf_url;
            downloadXlsxLink.href = response.report_xlsx_url;
            reportDownloads.classList.remove('hidden');
        }

        resultsPanel.classList.remove('hidden');
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
});