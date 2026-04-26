let charts = {};
let idActual = "";

window.onload = async function() {
    initCharts();
    while (typeof eel === 'undefined') await new Promise(r => setTimeout(r, 200));
    confirmarCarga();
};

document.getElementById('btn-cargar').onclick = confirmarCarga;
document.getElementById('farola-id').onkeypress = (e) => { if(e.key === 'Enter') confirmarCarga(); };

async function confirmarCarga() {
    idActual = document.getElementById('farola-id').value.trim();
    if(!idActual) return;
    
    reiniciarGraficas();
    const pack = await eel.inicializar_web(idActual)();
    
    if (pack.historico) pack.historico.forEach(l => procesarDato(l, l.fecha));
    if (pack.actual) procesarDato(pack.actual);
}

eel.expose(notificar_datos);
function notificar_datos(idRecibido, datos) {
    if (idRecibido == idActual) procesarDato(datos);
}

function procesarDato(datos, fechaManual = null) {
    const hora = fechaManual ? fechaManual.split(" ")[1] : new Date().toLocaleTimeString();
    
    if (!fechaManual) {
        // CAPADO A 2 DECIMALES EN INTERFAZ
        document.getElementById('val-temp').innerText = parseFloat(datos.temperatura).toFixed(2);
        document.getElementById('val-hum').innerText = parseFloat(datos.humedad).toFixed(2);
        document.getElementById('val-sonido').innerText = parseFloat(datos.sonido).toFixed(2);
        document.getElementById('val-luz').innerText = parseFloat(datos.luz).toFixed(2);
        
        actualizarActuadores(datos);
    }

    for (let key in charts) {
        let chart = charts[key];
        if (datos[key] !== undefined) {
            chart.data.labels.push(hora);
            chart.data.datasets[0].data.push(datos[key]);
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.update('none');
        }
    }
}

function actualizarActuadores(datos) {
    // Foco (Luz)
    document.getElementById('foco').className = datos.luz < 400 ? 'foco on' : 'foco';
    
    // Alerta (Sonido)
    document.getElementById('alerta').className = datos.sonido > 80 ? 'alerta danger' : 'alerta';
    
    // AGUA/VAPOR (Temperatura y Humedad alta)
    const vapor = document.getElementById('vapor');
    if (datos.temperatura > 30 && datos.humedad > 60) {
        vapor.classList.add('active');
    } else {
        vapor.classList.remove('active');
    }
    
    document.getElementById('status-text').innerText = "Viendo ID: " + idActual;
}

function initCharts() {
    const config = (col) => ({
        type: 'line',
        data: { labels: [], datasets: [{ data: [], borderColor: col, backgroundColor: col+'15', fill: true, tension: 0.3, pointRadius: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { grid: { color: '#252535' }, ticks: { color: '#888' } } } }
    });
    charts = {
        "temperatura": new Chart(document.getElementById('tempChart'), config('#ff5722')),
        "humedad": new Chart(document.getElementById('humChart'), config('#2196f3')),
        "sonido": new Chart(document.getElementById('soundChart'), config('#ffeb3b')),
        "luz": new Chart(document.getElementById('lightChart'), config('#00e676'))
    };
}

function reiniciarGraficas() {
    for (let k in charts) {
        charts[k].data.labels = [];
        charts[k].data.datasets[0].data = [];
        charts[k].update();
    }
}