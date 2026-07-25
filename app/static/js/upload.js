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
                progressBar.className = 'h-full bg-emerald-500 rounded-full transition-all duration-150';
                showNotification('success', 'File Uploaded Successfully', `Stored securely: ${response.filename} (${formatBytes(response.file_size)})`);
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

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
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
