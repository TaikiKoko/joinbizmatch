// 画像プレビューの機能を実装
class ImagePreview {
    constructor() {
        this.modal = null;
        this.currentImage = null;
        this.currentRotation = 0;
        this.currentZoom = 1;
        this.initializeModal();
        this.bindEvents();
    }

    initializeModal() {
        // モーダルのHTMLを追加
        const modalHTML = `
            <div class="modal fade" id="imagePreviewModal" tabindex="-1">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">画像プレビュー</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-0">
                            <div class="image-preview-container">
                                <img src="" alt="プレビュー画像">
                                <div class="image-preview-controls">
                                    <button class="btn" id="zoomInBtn">
                                        <i class="fas fa-search-plus"></i>
                                    </button>
                                    <button class="btn" id="zoomOutBtn">
                                        <i class="fas fa-search-minus"></i>
                                    </button>
                                    <button class="btn" id="rotateBtn">
                                        <i class="fas fa-redo"></i>
                                    </button>
                                    <button class="btn" id="downloadBtn">
                                        <i class="fas fa-download"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
    }

    bindEvents() {
        // 画像クリックイベントの設定
        document.addEventListener('click', (e) => {
            if (e.target.matches('.message-attachment img')) {
                this.showPreview(e.target.src);
            }
        });

        // コントロールボタンのイベント設定
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoom(1.2));
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoom(0.8));
        document.getElementById('rotateBtn').addEventListener('click', () => this.rotate());
        document.getElementById('downloadBtn').addEventListener('click', () => this.download());

        // モーダルが閉じられた時のリセット
        document.getElementById('imagePreviewModal').addEventListener('hidden.bs.modal', () => {
            this.reset();
        });
    }

    showPreview(imageUrl) {
        this.currentImage = document.querySelector('#imagePreviewModal img');
        this.currentImage.src = imageUrl;
        this.modal.show();
    }

    zoom(factor) {
        this.currentZoom *= factor;
        this.currentZoom = Math.max(0.5, Math.min(3, this.currentZoom));
        this.updateTransform();
    }

    rotate() {
        this.currentRotation += 90;
        this.updateTransform();
    }

    updateTransform() {
        this.currentImage.style.transform = `rotate(${this.currentRotation}deg) scale(${this.currentZoom})`;
    }

    download() {
        const link = document.createElement('a');
        link.href = this.currentImage.src;
        link.download = 'image.jpg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    reset() {
        this.currentRotation = 0;
        this.currentZoom = 1;
        if (this.currentImage) {
            this.currentImage.style.transform = '';
        }
    }
}

// 画像プレビューの初期化
document.addEventListener('DOMContentLoaded', () => {
    new ImagePreview();
}); 