// WebSocket接続を管理
let socket = io();
window.socket = socket; // どこからでも同じインスタンスを参照できるように
const currentUserId = window.chatConfig.currentUserId;

// デバッグログ
function debugLog(type, message, data = null) {
    console.log(`[Chat Rooms Debug] ${type}: ${message}`, data);
}

// WebSocket接続の初期化
function initializeWebSocket() {
    debugLog('init', 'Initializing WebSocket', { currentUserId });

    socket.on('connect', () => {
        debugLog('connect', 'WebSocket connected', { currentUserId });
        // ユーザールームに参加
        socket.emit('join_user_room', { user_id: currentUserId }, (response) => {
            debugLog('join_user_room', 'Response received', response);
            if (!response || response.error) {
                debugLog('error', 'Failed to join user room', response);
            }
            // join完了後にリスナー登録
            console.log('registering update_unread_count listener');
            socket.on('update_unread_count', function(data) {
                console.log('[Debug] update_unread_count event received:', data);
                // 全体未読数を更新
                if (data && typeof data.total_count === 'number') {
                    updateCompanyMypageUnreadBadge(data.total_count);
                } else if (data && typeof data.count === 'number' && !data.room_id) {
                    // 後方互換性: 全体数のみの場合
                    updateCompanyMypageUnreadBadge(data.count);
                }
                // 個別ルームの未読数を更新
                if (data && data.room_counts) {
                    // 複数ルーム対応
                    for (const [roomId, count] of Object.entries(data.room_counts)) {
                        updateUnreadCount(roomId, count);
                    }
                } else if (data && data.room_id && typeof data.count === 'number') {
                    // 単一ルーム対応
                    updateUnreadCount(data.room_id, data.count);
                } else if (data && data.counts) {
                    // 既存の複数ルーム形式対応
                    for (const [roomId, count] of Object.entries(data.counts)) {
                        updateUnreadCount(roomId, count);
                    }
                }
            });
        });
    });

    socket.on('disconnect', () => {
        debugLog('disconnect', 'WebSocket disconnected');
    });

    socket.on('error', (error) => {
        debugLog('error', 'WebSocket error', error);
    });

    // 既存の接続がある場合は即座にユーザールームに参加
    if (socket.connected) {
        debugLog('init', 'Socket already connected, joining user room', { currentUserId });
        socket.emit('join_user_room', { user_id: currentUserId }, (response) => {
            debugLog('join_user_room', 'Response received', response);
            // join完了後にリスナー登録
            console.log('registering update_unread_count listener');
            socket.on('update_unread_count', function(data) {
                console.log('[Debug] update_unread_count event received:', data);
                // 全体未読数を更新
                if (data && typeof data.total_count === 'number') {
                    updateCompanyMypageUnreadBadge(data.total_count);
                } else if (data && typeof data.count === 'number' && !data.room_id) {
                    // 後方互換性: 全体数のみの場合
                    updateCompanyMypageUnreadBadge(data.count);
                }
                // 個別ルームの未読数を更新
                if (data && data.room_counts) {
                    // 複数ルーム対応
                    for (const [roomId, count] of Object.entries(data.room_counts)) {
                        updateUnreadCount(roomId, count);
                    }
                } else if (data && data.room_id && typeof data.count === 'number') {
                    // 単一ルーム対応
                    updateUnreadCount(data.room_id, data.count);
                } else if (data && data.counts) {
                    // 既存の複数ルーム形式対応
                    for (const [roomId, count] of Object.entries(data.counts)) {
                        updateUnreadCount(roomId, count);
                    }
                }
            });
        });
    }
}

// 初期化を実行
initializeWebSocket();

// 未読メッセージの更新
function updateUnreadCount(roomId, count) {
    debugLog('updateUnreadCount', 'Updating unread count', { roomId, count });
    const roomElement = document.querySelector(`[data-room-id="${roomId}"]`);
    if (!roomElement) {
        debugLog('updateUnreadCount', 'Room element not found', { roomId });
        return;
    }
    
    const badgeElement = roomElement.querySelector('.chat-room-badge');
    if (count > 0) {
        if (badgeElement) {
            badgeElement.textContent = count;
            debugLog('updateUnreadCount', 'Updated existing badge', { roomId, count });
        } else {
            const metaElement = roomElement.querySelector('.chat-room-meta');
            const newBadge = document.createElement('div');
            newBadge.className = 'chat-room-badge';
            newBadge.textContent = count;
            metaElement.appendChild(newBadge);
            debugLog('updateUnreadCount', 'Created new badge', { roomId, count });
        }
    } else if (badgeElement) {
        badgeElement.remove();
        debugLog('updateUnreadCount', 'Removed badge', { roomId });
    }
}

// 最新メッセージの更新
function updateLastMessage(roomId, message) {
    const roomElement = document.querySelector(`[data-room-id="${roomId}"]`);
    if (!roomElement) return;
    
    const messageElement = roomElement.querySelector('.chat-room-message');
    const timeElement = roomElement.querySelector('.chat-room-time');
    
    if (messageElement) {
        messageElement.textContent = message.content.length > 50 
            ? message.content.substring(0, 50) + '...' 
            : message.content;
    }
    
    if (timeElement) {
        timeElement.textContent = new Date(message.created_at).toLocaleString();
    }
}

// 企業マイページ用 未読バッジ更新関数
function updateCompanyMypageUnreadBadge(count) {
    const badge = document.getElementById('unread-message-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = '';
        } else {
            badge.style.display = 'none';
        }
    }
}

// WebSocketイベントリスナー
socket.on('new_message', (data) => {
    debugLog('new_message', 'Received new message', data);
    const message = data.message;
    const sender = data.sender;

    // 自分が送信者でない場合は未読カウントを更新
    if (sender.id !== currentUserId) {
        const currentCount = parseInt(document.querySelector(`[data-room-id="${message.chat_room_id}"] .chat-room-badge`)?.textContent || '0');
        updateUnreadCount(message.chat_room_id, currentCount + 1);
        // 企業マイページ用バッジも更新
        const badge = document.getElementById('unread-message-badge');
        if (badge) {
            let badgeCount = parseInt(badge.textContent || '0');
            badgeCount = isNaN(badgeCount) ? 0 : badgeCount;
            updateCompanyMypageUnreadBadge(badgeCount + 1);
        }
    }
    
    // 最新メッセージを更新
    updateLastMessage(message.chat_room_id, message);
}); 