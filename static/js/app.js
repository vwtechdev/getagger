// CSRF para requisições HTMX (POST/PUT/DELETE).
document.body.addEventListener('htmx:configRequest', function (event) {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    if (m) {
        event.detail.headers['X-CSRFToken'] = m[1];
    }
});

// Service Worker para PWA (comportamento de app mobile).
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js', { scope: '/static/js/' });
}

// WebUSB — impressão RAW direto para impressora não fiscal
let printerDevice = null;
let printerType = null;
let printerConnected = localStorage.getItem('printerConnected') === 'true';
let printerError = '';

function _findOutEndpoint(device) {
    for (const iface of device.configurations[0].interfaces) {
        for (const alt of iface.alternates) {
            for (const ep of alt.endpoints) {
                if (ep.direction === 'out') return ep.endpointNumber;
            }
        }
    }
    return null;
}

async function connectUSB() {
    if (!('usb' in navigator)) return false;
    try {
        const device = await navigator.usb.requestDevice({ filters: [] });
        await device.open();
        await device.selectConfiguration(1);
        try { await device.reset(); } catch {}
        try { await device.detachKernelDriver(0); } catch {}
        await device.claimInterface(0);
        const ep = _findOutEndpoint(device);
        if (!ep) throw new Error('Nenhum endpoint OUT encontrado.');
        device._outEndpoint = ep;
        printerDevice = device;
        printerType = 'usb';
        printerConnected = true;
        printerError = '';
        localStorage.setItem('printerConnected', 'true');
        return true;
    } catch (e) {
        printerError = 'WebUSB: ' + e.message;
        return false;
    }
}

async function restorePrinter() {
    if (!('usb' in navigator) || !printerConnected) return;
    try {
        const devices = await navigator.usb.getDevices();
        for (const device of devices) {
            try {
                await device.open();
                await device.selectConfiguration(1);
                try { await device.reset(); } catch {}
                try { await device.detachKernelDriver(0); } catch {}
                await device.claimInterface(0);
                const ep = _findOutEndpoint(device);
                if (!ep) { await device.close(); continue; }
                device._outEndpoint = ep;
                printerDevice = device;
                printerError = '';
                return;
            } catch { try { await device.close(); } catch {} }
        }
        printerConnected = false;
        localStorage.removeItem('printerConnected');
    } catch {}
}

async function sendRawToPrinter(data) {
    if (!printerDevice) return false;
    try {
        const ep = printerDevice._outEndpoint || 1;
        const maxPacket = 64;
        for (let offset = 0; offset < data.byteLength; offset += maxPacket) {
            const chunk = data.slice(offset, offset + maxPacket);
            await printerDevice.transferOut(ep, chunk);
        }
        return true;
    } catch (e) {
        printerError = 'Falha ao enviar: ' + e.message;
        printerDevice = null;
        printerConnected = false;
        localStorage.removeItem('printerConnected');
        return false;
    }
}

async function testPrinter() {
    if (!printerConnected) return alert('Conecte uma impressora primeiro.');
    if (!printerDevice) await restorePrinter();
    if (!printerDevice) return alert('Reconexão automática falhou. Conecte novamente em Configurações.');
    const enc = new TextEncoder();
    const testData = enc.encode(
        '\x1b\x40' +          // ESC @ — init
        '\x1b\x21\x30' +      // ESC ! 0x30 — double height + double width
        '\x1b\x61\x01' +      // ESC a 1 — center
        '  GETAGGER OK\n' +
        '\x1b\x21\x00' +      // ESC ! 0 — normal
        '\x1b\x61\x00' +      // ESC a 0 — left
        'Impressora conectada.\n\n\n\n' +
        '\x1d\x56\x01'        // GS V 1 — partial cut
    );
    const ok = await sendRawToPrinter(testData);
    alert(ok ? 'Teste enviado com sucesso!' : 'Falha ao enviar teste.\n\n' + printerError);
}

async function printLabel(url, event) {
    if (!printerConnected) {
        window.open(url, '_blank');
        return;
    }
    if (!printerDevice) await restorePrinter();
    if (!printerDevice) {
        window.open(url, '_blank');
        return;
    }
    event.preventDefault();
    try {
        const resp = await fetch(url);
        const contentType = resp.headers.get('content-type') || '';
        if (!contentType.includes('text/plain')) {
            alert('Formato PDF detectado. Mude para TEXT_RAW nas Configurações para imprimir direto na impressora.');
            return;
        }
        const blob = await resp.blob();
        const buffer = await blob.arrayBuffer();
        const sent = await sendRawToPrinter(new Uint8Array(buffer));
        if (!sent) {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = url.split('/').pop().replace('.pdf', '.txt');
            a.click();
        }
    } catch {
        window.open(url, '_blank');
    }
}

// Alpine.js
document.addEventListener('alpine:init', () => {
    Alpine.data('barcodeScanner', () => ({
        scanning: false,
        scanner: null,
        error: '',
        cameraState: 'prompt',
        permissionPending: false,
        _videoTrack: null,
        _nativeScanning: false,
        _detector: null,
        get supported() {
            return 'BarcodeDetector' in window || typeof Html5Qrcode !== 'undefined';
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
            if ('BarcodeDetector' in window) {
                await this._startNativeScan();
            } else {
                await this._startHtml5Scan();
            }
        },
        async _startNativeScan() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment' }
                });
                const container = document.getElementById('scanner-preview');
                if (!container) return;
                const video = document.createElement('video');
                video.setAttribute('autoplay', '');
                video.setAttribute('playsinline', '');
                video.style.width = '100%';
                video.style.height = '100%';
                video.style.objectFit = 'cover';
                container.innerHTML = '';
                container.appendChild(video);
                video.srcObject = stream;
                await video.play();
                this._videoTrack = stream.getVideoTracks()[0];
                const formats = await BarcodeDetector.getSupportedFormats().catch(() => []);
                this._detector = new BarcodeDetector({
                    formats: formats.filter(f =>
                        ['code_128','code_39','codabar','ean_13','ean_8','upc_a','upc_e','qr_code','data_matrix'].includes(f)
                    )
                });
                this._nativeScanning = true;
                this._detectLoop();
            } catch (e) {
                this.error = 'Não foi possível acessar a câmera. Verifique as permissões e tente novamente, ou digite o número manualmente.';
                this.scanning = false;
            }
        },
        async _detectLoop() {
            while (this._nativeScanning) {
                const video = document.querySelector('#scanner-preview video');
                if (!video || !this._nativeScanning) break;
                try {
                    const codes = await this._detector.detect(video);
                    if (codes.length > 0) {
                        this.$refs.serialInput.value = codes[0].rawValue;
                        this.$refs.serialInput.dispatchEvent(new Event('input', { bubbles: true }));
                        this.stopScan();
                        return;
                    }
                } catch {}
                await new Promise(r => setTimeout(r, 150));
            }
        },
        async _startHtml5Scan() {
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
                this._videoTrack = this._getVideoTrack();
            } catch (e) {
                this.error = 'Não foi possível acessar a câmera. Verifique as permissões e tente novamente, ou digite o número manualmente.';
                this.scanning = false;
                if (this.scanner) { this.scanner.clear(); }
            }
        },
        _getVideoTrack() {
            const video = document.querySelector('#scanner-preview video');
            if (video && video.srcObject) {
                return video.srcObject.getVideoTracks()[0];
            }
            return null;
        },

        stopScan() {
            this._nativeScanning = false;
            this._detector = null;
            this._videoTrack = null;
            if (this.scanner) {
                this.scanner.stop().then(() => {
                    this.scanner.clear();
                    this.scanning = false;
                }).catch(() => { this.scanning = false; });
            } else {
                const video = document.querySelector('#scanner-preview video');
                if (video && video.srcObject) {
                    video.srcObject.getTracks().forEach(t => t.stop());
                    video.srcObject = null;
                }
                this.scanning = false;
            }
        },
    }));

    Alpine.data('webusbPrinter', () => ({
        init() {
            this.connected = printerConnected;
            this.error = printerError;
            if (printerConnected && !printerDevice) {
                restorePrinter().then(() => {
                    this.connected = printerConnected;
                    this.error = printerError;
                });
            }
        },
        connected: false,
        error: '',
        get supported() { return 'usb' in navigator; },
        async connectUSB() {
            const ok = await window.connectUSB();
            if (!ok) {
                alert('Conexão USB falhou.\n\n' + printerError);
            } else {
                this.connected = true;
                this.error = '';
            }
        },
        async disconnect() {
            if (printerDevice) {
                try { await printerDevice.close(); } catch {}
                printerDevice = null;
            }
            printerType = null;
            printerConnected = false;
            printerError = '';
            localStorage.removeItem('printerConnected');
            this.connected = false;
            this.error = '';
        },
        test() {
            if (!printerConnected) return alert('Conecte uma impressora primeiro.');
            testPrinter();
        },
    }));
});
