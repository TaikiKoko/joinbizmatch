let socket = io();
let page = 1;
const messagesPerPage = 20;
let isLoading = false;
let hasMoreMessages = true;
const currentUserId = window.chatConfig.currentUserId;
const roomId = window.chatConfig.roomId;
let pendingMessages = new Map();
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;

// デバッグモードの設定
const DEBUG = true;

// 詳細なログ出力
function debugLog(type, message, data = null) {
    if (!DEBUG) return;
    const timestamp = new Date().toISOString();
    const logMessage = {
        type,
        timestamp,
        message,
        data
    };
    console.log(`[Chat Debug] ${JSON.stringify(logMessage, null, 2)}`);
}

// メッセージの遅延読み込み
async function loadMessages(roomId, page) {
    if (isLoading || !hasMoreMessages) return;
    isLoading = true;
    debugLog('load', 'Loading messages', { roomId, page });
    
    try {
        const response = await fetch(`/api/chat/rooms/${roomId}/messages?page=${page}&per_page=${messagesPerPage}`);
        const data = await response.json();
        
        if (data.messages.length < messagesPerPage) {
            hasMoreMessages = false;
        }
        
        appendMessages(data.messages, true);
        page++;
        debugLog('load', 'Messages loaded successfully', { count: data.messages.length });
    } catch (error) {
        debugLog('error', 'Failed to load messages', { error: error.toString() });
    } finally {
        isLoading = false;
    }
}

// WebSocketイベントのログ出力
function logEvent(eventType, data) {
    const logData = {
        event: eventType,
        timestamp: new Date().toISOString(),
        data: data
    };
    console.log(`[WebSocket Client] ${JSON.stringify(logData)}`);
}

// WebSocket接続の初期化
function initializeWebSocket(roomId) {
    debugLog('init', 'Initializing WebSocket', { roomId });
    
    socket.on('connect', () => {
        debugLog('connect', 'WebSocket connected');
        reconnectAttempts = 0;
        socket.emit('join_chat', { room_id: roomId });
        
        // チャットページを開いたことを通知
        socket.emit('chat_page_opened', { room_id: roomId });
    });

    socket.on('join_confirmation', (data) => {
        debugLog('join', 'Joined chat room', data);
        if (data.success) {
            loadMessages(roomId, page);
        }
    });

    socket.on('message_confirmation', (data) => {
        debugLog('confirm', 'Message confirmation received', data);
        if (data.success) {
            const message = data.message;
            handleMessageConfirmation(message);
        }
    });

    socket.on('new_message', (data) => {
        debugLog('receive', 'New message received', data);
        handleNewMessage(data);
    });

    socket.on('update_read_status', (data) => {
        debugLog('read_status', 'Read status update received', data);
        updateMessageReadStatus(data);
    });

    socket.on('disconnect', () => {
        debugLog('disconnect', 'WebSocket disconnected');
        handleDisconnect();
    });

    socket.on('error', (error) => {
        debugLog('error', 'WebSocket error', { error: error.toString() });
        handleError(error);
    });

    // 接続状態の監視
    setInterval(checkConnectionStatus, 5000);
}

// メッセージ確認の処理
function handleMessageConfirmation(message) {
    for (const [tempId, pendingMessage] of pendingMessages.entries()) {
        if (pendingMessage.content === message.content && 
            pendingMessage.sender_id === message.sender_id) {
            pendingMessage.serverMessageId = message.id;
            debugLog('link', 'Temporary message linked', {
                tempId,
                messageId: message.id
            });
            break;
        }
    }
}

// 新規メッセージの処理
function handleNewMessage(message) {
    let tempMessageRemoved = false;
    
    // 一時メッセージの確認と処理
    for (const [tempId, pendingMessage] of pendingMessages.entries()) {
        if (pendingMessage.serverMessageId === message.id || 
            (pendingMessage.content === message.content && 
             pendingMessage.sender_id === message.sender_id)) {
            removeTempMessage(tempId);
            pendingMessages.delete(tempId);
            tempMessageRemoved = true;
            debugLog('temp', 'Removed temporary message', {
                tempId,
                messageId: message.id
            });
            break;
        }
    }
    
    // 重複チェック
    if (!tempMessageRemoved) {
        const existingMessage = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMessage) {
            debugLog('duplicate', 'Message already exists', {
                messageId: message.id
            });
            return;
        }
    }
    
    // メッセージを追加
    appendMessages([message]);
    
    // 他のユーザーからのメッセージの場合は既読にする
    if (message.sender_id !== currentUserId) {
        markMessageAsRead(message.id);
    }
}

// 既読状態の更新
function updateMessageReadStatus(data) {
    const { room_id, reader_id, message_ids } = data;
    
    message_ids.forEach(messageId => {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const statusElement = messageElement.querySelector('.message-status');
            if (statusElement) {
                statusElement.className = 'message-status read';
                statusElement.textContent = '✅ 既読';
            }
        }
    });
}

// 切断処理
function handleDisconnect() {
    if (reconnectAttempts < maxReconnectAttempts) {
        setTimeout(() => {
            reconnectAttempts++;
            socket.connect();
            debugLog('reconnect', 'Attempting to reconnect', {
                attempt: reconnectAttempts,
                maxAttempts: maxReconnectAttempts
            });
        }, reconnectDelay);
    } else {
        debugLog('reconnect', 'Max reconnection attempts reached');
        alert('サーバーとの接続が切断されました。ページを再読み込みしてください。');
    }
}

// エラー処理
function handleError(error) {
    debugLog('error', 'Error occurred', { error: error.toString() });
    console.error('WebSocket error:', error);
}

// 接続状態の確認
function checkConnectionStatus() {
    const status = {
        connected: socket.connected,
        pending: Array.from(pendingMessages.entries())
    };
    debugLog('status', 'Connection status check', status);
}

// メッセージの追加
function appendMessages(messages, prepend = false) {
    debugLog('append', 'Starting to append messages', { 
        count: messages.length, 
        prepend 
    });
    
    const chatMessages = document.getElementById('chat-messages');
    const fragment = document.createDocumentFragment();
    let needsScroll = false;
    
    messages.forEach(message => {
        const messageElement = createMessageElement(message);
        if (prepend) {
            fragment.prepend(messageElement);
        } else {
            fragment.append(messageElement);
            needsScroll = true;
        }
        
        debugLog('element', 'Message element created', { 
            messageId: message.id,
            isPrepend: prepend
        });
    });
    
    if (fragment.children.length > 0) {
        const wasAtBottom = chatMessages.scrollHeight - chatMessages.clientHeight <= chatMessages.scrollTop + 1;
        
        if (prepend) {
            chatMessages.prepend(fragment);
        } else {
            chatMessages.append(fragment);
            if (wasAtBottom || needsScroll) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
        
        debugLog('dom', 'Messages added to DOM', { 
            count: fragment.children.length,
            prepend,
            scrolled: wasAtBottom || needsScroll
        });
    }
}

// メッセージ要素の作成
function createMessageElement(message) {
    const div = document.createElement('div');
    div.className = `message ${message.sender_id === currentUserId ? 'sent' : 'received'}`;
    div.dataset.messageId = message.id;
    
    const content = `
        <div class="message-content">
            ${message.content ? `
                <div class="message-text">
                    ${escapeHtml(message.content)}
                </div>
            ` : ''}
            
            ${message.attachments ? `
                <div class="message-attachments">
                    ${message.attachments.map(attachment => `
                        <div class="attachment">
                            ${attachment.is_image ? `
                                <div class="attachment-image">
                                    <img src="${attachment.file_path}" 
                                         alt="${attachment.original_filename}"
                                         class="img-fluid rounded"
                                         loading="lazy">
                                </div>
                            ` : `
                                <div class="attachment-file">
                                    <i class="bi ${attachment.icon_class}"></i>
                                    <div class="attachment-info">
                                        <div class="attachment-name">${attachment.original_filename}</div>
                                        <div class="attachment-size">${formatFileSize(attachment.file_size)}</div>
                                    </div>
                                    <a href="${attachment.file_path}" 
                                       class="btn btn-sm btn-outline-primary"
                                       download>
                                        <i class="bi bi-download"></i>
                                    </a>
                                </div>
                            `}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="message-time">
                ${formatDateTime(message.created_at)}
                ${message.sender_id === currentUserId ? `
                    <span class="message-status ${message.is_read ? 'read' : 'unread'}">
                        ${message.is_read ? '✅ 既読' : '⏳ 未読'}
                    </span>
                ` : ''}
            </div>
        </div>
    `;
    
    div.innerHTML = content;
    return div;
}

// XSS対策
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 日時のフォーマット
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

// ファイルサイズのフォーマット
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// スクロールイベントの監視
document.getElementById('chat-messages').addEventListener('scroll', function(e) {
    if (e.target.scrollTop === 0 && hasMoreMessages) {
        loadMessages(roomId, page);
    }
});

// メッセージ送信
document.getElementById('chat-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    if (!content) return;
    
    try {
        const tempId = 'temp_' + Date.now();
        const tempMessage = {
            id: tempId,
            sender_id: currentUserId,
            content: content,
            created_at: new Date().toISOString(),
            is_read: false,
            sender: {
                id: currentUserId,
                username: document.querySelector('.chat-header .participant span').textContent
            }
        };
        
        debugLog('send', 'Preparing to send message', {
            tempId,
            content: content
        });
        
        // 送信中メッセージを記録
        pendingMessages.set(tempId, tempMessage);
        
        // メッセージを一時的に表示
        appendMessages([tempMessage]);
        messageInput.value = '';
        
        // サーバーにメッセージを送信
        socket.emit('send_message', {
            room_id: roomId,
            content: content
        }, (response) => {
            debugLog('response', 'Server response received', {
                tempId,
                success: response.success,
                error: response.error
            });
            
            if (!response.success) {
                removeTempMessage(tempId);
                pendingMessages.delete(tempId);
                console.error('Error sending message:', response.error);
                alert('メッセージの送信に失敗しました。');
                return;
            }
            
            // 成功の場合、一時メッセージとサーバーメッセージの紐付けを記録
            const pendingMessage = pendingMessages.get(tempId);
            if (pendingMessage) {
                pendingMessage.serverMessageId = response.message.id;
                debugLog('link', 'Temporary message linked with server message', {
                    tempId,
                    messageId: response.message.id
                });
            }
        });
    } catch (error) {
        debugLog('error', 'Error in message send process', {
            error: error.toString()
        });
        console.error('Error sending message:', error);
        alert('メッセージの送信に失敗しました。');
    }
});

// 一時メッセージの削除
function removeTempMessage(tempId) {
    const tempElement = document.querySelector(`[data-message-id="${tempId}"]`);
    if (tempElement) {
        tempElement.remove();
    }
    pendingMessages.delete(tempId);
}

// メッセージを既読にする
async function markMessageAsRead(messageId) {
    try {
        socket.emit('mark_read', { message_id: messageId });
    } catch (error) {
        console.error('Failed to mark message as read:', error);
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket(roomId);
    loadMessages(roomId, page);
});

function startChat(successorId) {
    window.location.href = `/chat/start/${successorId}`;
} 