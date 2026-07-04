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
        get supported() {
            return typeof Html5Qrcode !== 'undefined' && !!navigator.mediaDevices;
        },
        async startScan() {
            this.error = '';
            this.scanning = true;
            await this.$nextTick();
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
