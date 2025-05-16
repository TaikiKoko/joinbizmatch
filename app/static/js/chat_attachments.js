// ファイルアップロード関連の変数
let selectedFiles = new Map();
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = new Set([
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt',
    'zip', 'rar', '7z'
]);

// ファイル選択時の処理
document.getElementById('file-input').addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    const filePreview = document.getElementById('file-preview');
    const selectedFilesContainer = filePreview.querySelector('.selected-files');
    
    files.forEach(file => {
        if (validateFile(file)) {
            const fileId = generateFileId();
            selectedFiles.set(fileId, file);
            appendFilePreview(fileId, file);
        }
    });
    
    if (selectedFiles.size > 0) {
        filePreview.classList.remove('d-none');
    }
    
    // 入力フィールドをリセット
    e.target.value = '';
});

// ファイルの検証
function validateFile(file) {
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (!ALLOWED_EXTENSIONS.has(extension)) {
        showError('許可されていないファイル形式です。');
        return false;
    }
    
    if (file.size > MAX_FILE_SIZE) {
        showError('ファイルサイズは10MB以下にしてください。');
        return false;
    }
    
    return true;
}

// ファイルIDの生成
function generateFileId() {
    return Math.random().toString(36).substr(2, 9);
}

// ファイルプレビューの追加
function appendFilePreview(fileId, file) {
    const selectedFilesContainer = document.querySelector('.selected-files');
    const filePreview = document.createElement('div');
    filePreview.className = 'selected-file';
    filePreview.dataset.fileId = fileId;
    
    const icon = getFileIcon(file.type);
    const size = formatFileSize(file.size);
    
    filePreview.innerHTML = `
        <i class="bi ${icon}"></i>
        <div class="selected-file-info">
            <div class="selected-file-name">${file.name}</div>
            <div class="selected-file-size">${size}</div>
        </div>
        <div class="selected-file-remove" onclick="removeFile('${fileId}')">
            <i class="bi bi-x"></i>
        </div>
    `;
    
    selectedFilesContainer.appendChild(filePreview);
}

// ファイルアイコンの取得
function getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) {
        return 'bi-image';
    } else if (mimeType.includes('pdf')) {
        return 'bi-file-pdf';
    } else if (mimeType.includes('word')) {
        return 'bi-file-word';
    } else if (mimeType.includes('excel')) {
        return 'bi-file-excel';
    } else if (mimeType.includes('text')) {
        return 'bi-file-text';
    } else {
        return 'bi-file-earmark';
    }
}

// ファイルサイズのフォーマット
function formatFileSize(size) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let index = 0;
    
    while (size >= 1024 && index < units.length - 1) {
        size /= 1024;
        index++;
    }
    
    return `${size.toFixed(1)} ${units[index]}`;
}

// ファイルの削除
function removeFile(fileId) {
    selectedFiles.delete(fileId);
    const filePreview = document.querySelector(`.selected-file[data-file-id="${fileId}"]`);
    if (filePreview) {
        filePreview.remove();
    }
    
    if (selectedFiles.size === 0) {
        document.getElementById('file-preview').classList.add('d-none');
    }
}

// エラーメッセージの表示
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.chat-container');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// ファイルアップロードの処理
async function uploadFile(file, chatRoomId) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`/chat/${chatRoomId}/upload`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'ファイルのアップロードに失敗しました');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error uploading file:', error);
        showError(error.message);
        throw error;
    }
}

// フォーム送信時の処理
document.getElementById('chat-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    const files = Array.from(selectedFiles.values());
    const chatRoomId = document.querySelector('.chat-container').dataset.chatRoomId;
    
    if (!message && files.length === 0) {
        return;
    }
    
    try {
        // ファイルのアップロード
        const uploadPromises = files.map(file => uploadFile(file, chatRoomId));
        const uploadResults = await Promise.all(uploadPromises);
        
        // メッセージの送信
        const response = await fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                message: message,
                attachments: uploadResults.map(result => result.attachment)
            })
        });
        
        if (response.ok) {
            messageInput.value = '';
            selectedFiles.clear();
            document.getElementById('file-preview').classList.add('d-none');
            document.querySelector('.selected-files').innerHTML = '';
            
            // メッセージリストの更新
            updateMessageList();
        } else {
            showError('メッセージの送信に失敗しました。');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('エラーが発生しました。');
    }
}); 