// 通知の更新間隔（ミリ秒）
const NOTIFICATION_UPDATE_INTERVAL = 30000;

// 通知バッジの更新
function updateNotificationBadge() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('#notificationDropdown .badge');
            if (data.count > 0) {
                if (!badge) {
                    const newBadge = document.createElement('span');
                    newBadge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
                    newBadge.textContent = data.count;
                    document.querySelector('#notificationDropdown').appendChild(newBadge);
                } else {
                    badge.textContent = data.count;
                }
            } else if (badge) {
                badge.remove();
            }
        })
        .catch(error => console.error('Error updating notification badge:', error));
}

// 通知リストの更新
function updateNotificationList() {
    fetch('/api/notifications/recent')
        .then(response => response.json())
        .then(data => {
            const notificationList = document.querySelector('.notification-list');
            if (!notificationList) return;

            if (data.notifications.length === 0) {
                notificationList.innerHTML = `
                    <div class="dropdown-item text-center text-muted">
                        通知はありません
                    </div>
                `;
                return;
            }

            notificationList.innerHTML = data.notifications.map(notification => `
                <a href="${notification.link || '#'}" class="dropdown-item notification-item ${notification.read ? '' : 'unread'}">
                    <div class="d-flex align-items-center">
                        <div class="notification-icon ${notification.type}">
                            ${getNotificationIcon(notification.type)}
                        </div>
                        <div class="notification-content ms-3">
                            <p class="notification-text mb-0">${notification.content}</p>
                            <small class="notification-time">${formatTime(notification.created_at)}</small>
                        </div>
                    </div>
                </a>
            `).join('');
        })
        .catch(error => console.error('Error updating notification list:', error));
}

// 通知アイコンの取得
function getNotificationIcon(type) {
    switch (type) {
        case 'message':
            return '<i class="bi bi-chat-dots"></i>';
        case 'favorite':
            return '<i class="bi bi-heart"></i>';
        case 'successor_update':
            return '<i class="bi bi-briefcase"></i>';
        default:
            return '<i class="bi bi-bell"></i>';
    }
}

// 時間のフォーマット
function formatTime(createdAt) {
    const date = new Date(createdAt);
    const now = new Date();
    const diff = now - date;
    
    // 1時間以内
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分前`;
    }
    // 24時間以内
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}時間前`;
    }
    // それ以外
    return date.toLocaleDateString('ja-JP', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 通知を既読にマーク
function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateNotificationBadge();
            updateNotificationList();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

// 定期的な更新の開始
function startNotificationUpdates() {
    updateNotificationBadge();
    updateNotificationList();
    setInterval(() => {
        updateNotificationBadge();
        updateNotificationList();
    }, NOTIFICATION_UPDATE_INTERVAL);
}

// DOMContentLoadedイベントで初期化
document.addEventListener('DOMContentLoaded', () => {
    startNotificationUpdates();
}); 