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
    const rulesSourceBadge = document.getElementById('rulesSourceBadge');

    // Annunciator strip lamps
    const lamps = {
        parse: document.getElementById('lampParse'),
        rules: document.getElementById('lampRules'),
        ai: document.getElementById('lampAi'),
        report: document.getElementById('lampReport'),
    };
    const LAMP_ORDER = ['parse', 'rules', 'ai', 'report'];
    let lampSweepInterval = null;

    function setLamp(key, state) {
        const el = lamps[key];
        if (!el) return;
        el.classList.remove('is-active', 'is-pass', 'is-fail');
        if (state) el.classList.add(state);
    }

    function resetLamps() {
        LAMP_ORDER.forEach((key) => setLamp(key, null));
    }

    function stopLampSweep() {
        if (lampSweepInterval) {
            clearInterval(lampSweepInterval);
            lampSweepInterval = null;
        }
    }

    // While we're waiting on the server (parse -> rules -> AI -> report all
    // happen in one request), sweep the lamps amber in sequence so there's
    // real, honest feedback that something is happening, rather than a
    // static spinner. Final states get set from the actual response.
    function startLampSweep() {
        stopLampSweep();
        resetLamps();
        let i = 0;
        setLamp(LAMP_ORDER[0], 'is-active');
        lampSweepInterval = setInterval(() => {
            setLamp(LAMP_ORDER[i], 'is-pass');
            i = (i + 1) % LAMP_ORDER.length;
            setLamp(LAMP_ORDER[i], 'is-active');
        }, 650);
    }

    // Custom test cases / rules UI
    const rulesModeDefault = document.getElementById('rulesModeDefault');
    const rulesModeCustom = document.getElementById('rulesModeCustom');
    const customRulesPanel = document.getElementById('customRulesPanel');
    const rulesFileInput = document.getElementById('rulesFileInput');
    const customRulesTextarea = document.getElementById('customRulesTextarea');
    const customRulesError = document.getElementById('customRulesError');
    const loadExampleRulesBtn = document.getElementById('loadExampleRulesBtn');

    const EXAMPLE_RULES = {
        rules: [
            { field: "method", type: "required", severity: "error", message: "Every test case needs an HTTP method." },
            { field: "expected_status", type: "range", min: 100, max: 599, severity: "error" },
            { field: "endpoint", type: "starts_with", value: "/", severity: "warning" },
            { field: "headers.Authorization", type: "required", severity: "info", message: "Consider testing with an Authorization header." }
        ]
    };

    function toggleRulesMode() {
        const isCustom = rulesModeCustom.checked;
        customRulesPanel.classList.toggle('hidden', !isCustom);
        customRulesError.classList.add('hidden');
    }

    rulesModeDefault.addEventListener('change', toggleRulesMode);
    rulesModeCustom.addEventListener('change', toggleRulesMode);

    loadExampleRulesBtn.addEventListener('click', () => {
        customRulesTextarea.value = JSON.stringify(EXAMPLE_RULES, null, 2);
    });

    // Uploading a rules file populates the textarea (the textarea is what
    // actually gets submitted, so pasted/edited text and an uploaded file
    // both flow through the same field).
    rulesFileInput.addEventListener('change', (e) => {
        const rulesFile = e.target.files[0];
        if (!rulesFile) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            customRulesTextarea.value = ev.target.result;
        };
        reader.readAsText(rulesFile);
    });

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
            dropzone.classList.add('is-dragging');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('is-dragging');
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
        notification.classList.remove('hidden', 'bg-phosphor/10', 'border-phosphor/30', 'text-phosphor', 'bg-caution/10', 'border-caution/30', 'text-caution');

        if (type === 'success') {
            notification.classList.add('bg-phosphor/10', 'border-phosphor/30', 'text-phosphor');
            notificationIcon.innerHTML = `
                <svg class="w-5 h-5 text-phosphor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
        } else {
            notification.classList.add('bg-caution/10', 'border-caution/30', 'text-caution');
            notificationIcon.innerHTML = `
                <svg class="w-5 h-5 text-caution" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
        }

        notificationTitle.textContent = title;
        notificationMessage.textContent = message;
        notification.classList.remove('hidden');
    }

    function handleFileUpload(file) {
        // If "my own test cases" is selected, the custom rules JSON must be
        // present and valid before we even start the upload.
        customRulesError.classList.add('hidden');
        let customRulesJson = null;
        if (rulesModeCustom.checked) {
            const rawRules = customRulesTextarea.value.trim();
            if (!rawRules) {
                customRulesError.textContent = 'Paste your rules JSON or upload a rules file, or switch back to "Default test cases".';
                customRulesError.classList.remove('hidden');
                return;
            }
            try {
                JSON.parse(rawRules);
                customRulesJson = rawRules;
            } catch (e) {
                customRulesError.textContent = 'Custom rules is not valid JSON: ' + e.message;
                customRulesError.classList.remove('hidden');
                return;
            }
        }

        // Reset states
        progressContainer.classList.remove('hidden');
        notification.classList.add('hidden');
        resultsPanel.classList.add('hidden');
        aiSummaryBox.classList.add('hidden');
        reportDownloads.classList.add('hidden');
        fileNameDisplay.textContent = file.name;
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        progressBar.className = 'h-full bg-instrument-amber rounded-full transition-all duration-150';
        resetLamps();

        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);
        if (customRulesJson) {
            formData.append('custom_rules', customRulesJson);
        }

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressPercentage.textContent = percentComplete + '%';
                if (percentComplete >= 100 && !lampSweepInterval) {
                    startLampSweep();
                }
            }
        });

        xhr.addEventListener('load', () => {
            stopLampSweep();

            if (xhr.status >= 200 && xhr.status < 300) {
                const response = JSON.parse(xhr.responseText);

                if (response.status === 'failed') {
                    progressBar.className = 'h-full bg-caution rounded-full transition-all duration-150';
                    setLamp('parse', 'is-fail');
                    setLamp('rules', null);
                    setLamp('ai', null);
                    setLamp('report', null);
                    showNotification('error', 'Analysis Failed', response.error || 'The pipeline could not process this file.');
                    return;
                }

                progressBar.className = 'h-full bg-phosphor rounded-full transition-all duration-150';
                showNotification('success', 'Analysis Complete', `${file.name} ran through the full pipeline successfully.`);
                showResults(response);
            } else {
                let errorMsg = 'An error occurred during upload.';
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.detail || errorMsg;
                } catch(e) {}
                progressBar.className = 'h-full bg-caution rounded-full transition-all duration-150';
                setLamp('parse', 'is-fail');
                showNotification('error', 'Upload Failed', errorMsg);
            }
        });

        xhr.addEventListener('error', () => {
            stopLampSweep();
            progressBar.className = 'h-full bg-caution rounded-full transition-all duration-150';
            setLamp('parse', 'is-fail');
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

        // Set final lamp states from the actual response rather than the sweep guess.
        setLamp('parse', 'is-pass');
        setLamp('rules', (ruleEngine.error_count || 0) > 0 ? 'is-fail' : 'is-pass');
        setLamp('ai', (aiAnalysis && !aiAnalysis.skipped_reason) ? 'is-pass' : 'is-fail');
        setLamp('report', (response.report_pdf_url && response.report_xlsx_url) ? 'is-pass' : 'is-fail');

        statTestCases.textContent = spec.test_cases ? spec.test_cases.length : 0;
        statErrors.textContent = ruleEngine.error_count || 0;
        statWarnings.textContent = ruleEngine.warning_count || 0;

        const source = ruleEngine.source || 'default';
        rulesSourceBadge.textContent = source === 'custom' ? 'Custom rules' : 'Default rules';
        rulesSourceBadge.className = source === 'custom'
            ? 'console-label px-2 py-0.5 rounded-full border border-phosphor/30 bg-phosphor/10 text-phosphor'
            : 'console-label px-2 py-0.5 rounded-full border border-panel-wire text-instrument-gray';

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