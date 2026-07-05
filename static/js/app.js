// CSRF para requisições HTMX (POST/PUT/DELETE).
document.body.addEventListener('htmx:configRequest', function (event) {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    if (m) {
        event.detail.headers['X-CSRFToken'] = m[1];
    }
});

// Service Worker para PWA (comportamento de app mobile).
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js', { scope: '/' });
}

// Alpine.js barcode scanner
document.addEventListener('alpine:init', () => {
    Alpine.data('barcodeScanner', () => ({
        scanning: false,
        scanner: null,
        error: '',
        cameraState: 'prompt',
        permissionPending: false,
        get supported() {
            return typeof Html5Qrcode !== 'undefined';
        },
        async init() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.cameraState = 'unsupported';
                return;
            }
            if (navigator.permissions && navigator.permissions.query) {
                try {
                    const result = await navigator.permissions.query({ name: 'camera' });
                    this.cameraState = result.state;
                    result.addEventListener('change', () => {
                        this.cameraState = result.state;
                    });
                } catch {
                    // Permissions API unavailable — fall through to getUserMedia probe
                }
            }
            if (this.cameraState === 'prompt') {
                this.permissionPending = true;
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: 'environment' }
                    });
                    stream.getTracks().forEach(t => t.stop());
                    this.cameraState = 'granted';
                } catch {
                    this.cameraState = 'denied';
                }
                this.permissionPending = false;
            }
        },
        async startScan() {
            if (this.permissionPending) return;
            if (this.cameraState === 'denied') {
                this.error = 'Permissão de câmera negada. Para escanear, ative a câmera nas configurações do navegador para este site.';
                this.scanning = true;
                return;
            }
            this.error = '';
            this.scanning = true;
            await this.$nextTick();
            await new Promise(r => requestAnimationFrame(r));
            try {
                this.scanner = new Html5Qrcode('scanner-preview');
                await this.scanner.start(
                    { facingMode: 'environment' },
                    { fps: 10, qrbox: { width: 250, height: 150 } },
                    (decodedText) => {
                        this.$refs.serialInput.value = decodedText;
                        this.$refs.serialInput.dispatchEvent(new Event('input', { bubbles: true }));
                        this.stopScan();
                    },
                    () => {}
                );
            } catch (e) {
                this.error = 'Não foi possível acessar a câmera. Verifique as permissões e tente novamente, ou digite o número manualmente.';
                this.scanning = false;
                if (this.scanner) { this.scanner.clear(); }
            }
        },
        stopScan() {
            if (this.scanner) {
                this.scanner.stop().then(() => {
                    this.scanner.clear();
                    this.scanning = false;
                }).catch(() => { this.scanning = false; });
            } else {
                this.scanning = false;
            }
        },
    }));
});
