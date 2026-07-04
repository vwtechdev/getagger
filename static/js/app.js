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
        async startScan() {
            this.scanning = true;
            this.$nextTick(() => {
                this.scanner = new Html5Qrcode('scanner-preview');
                this.scanner.start(
                    { facingMode: 'environment' },
                    { fps: 10, qrbox: { width: 250, height: 150 } },
                    (decodedText) => {
                        this.$refs.serialInput.value = decodedText;
                        this.$refs.serialInput.dispatchEvent(new Event('input', { bubbles: true }));
                        this.stopScan();
                    },
                    () => {}
                ).catch(() => { this.scanning = false; });
            });
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
