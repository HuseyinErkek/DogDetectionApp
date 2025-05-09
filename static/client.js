const socket = io('http://127.0.0.1:5000');
const segmentList = document.getElementById('segmentList');
let sessionId = null;

socket.on('connect', () => {
    console.log('Sunucuya bağlanıldı.');
    const sessionId = socket.id;
    socket.emit('join_room', { sessionId: sessionId });
    segmentList.innerHTML = ''; // Temizle
    const testItem = document.createElement('li');
    testItem.innerText = 'Bağlantı Kuruldu!';
    segmentList.appendChild(testItem);
});

// Sunucudan sessionId alınması
socket.on('session_id', (data) => {
    sessionId = data.sessionId;
    console.log('Sunucudan alınan sessionId:', sessionId);
    // SessionId alındıktan sonra odaya katıl
    socket.emit('join_room', { sessionId: sessionId });
    segmentList.innerHTML = '';
});

// Yeni segment başladığında tetiklenir
socket.on('segment_started', (data) => {
    const { filename } = data;
    console.log('Yeni segment adı:', filename);

    // Bir listeye ekle
    const list = document.getElementById('segmentList');
    const li = document.createElement('li');
    li.innerText = `İşlenen Segment: ${filename}`;
    list.appendChild(li);
});

socket.on('progress', function(data) {


    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');

    if (typeof data.progress === 'number' && isFinite(data.progress)) {
        progressBar.value = data.progress;
        progressPercent.textContent = `%${data.progress.toFixed(2)}`;

        if (data.progress < 50) {
            progressBar.style.backgroundColor = "red";
        } else if (data.progress < 80) {
            progressBar.style.backgroundColor = "yellow";
        } else {
            progressBar.style.backgroundColor = "green";
        }
    } else {
        console.warn("Geçersiz toplam ilerleme verisi:", data.progress);
    }
});


socket.on('segment_progress', function(data) {
    const segmentProgressBar = document.getElementById('segmentProgressBar');
    const segmentProgressPercent = document.getElementById('segmentProgressPercent');

    if (typeof data.segment_progress === 'number' && isFinite(data.segment_progress)) {
        segmentProgressBar.value = data.segment_progress;
        segmentProgressPercent.textContent = `%${data.segment_progress.toFixed(2)}`;

        if (data.segment_progress < 50) {
            segmentProgressBar.style.backgroundColor = "red";
        } else if (data.segment_progress < 80) {
            segmentProgressBar.style.backgroundColor = "yellow";
        } else {
            segmentProgressBar.style.backgroundColor = "green";
        }
    } else {
        console.warn("Geçersiz segment ilerleme verisi:", data.segment_progress);
    }
});

socket.on('wait_timer', function(data) {
    const countdownDiv = document.getElementById('countdown');
    if (data && data.remaining_seconds !== undefined) {
        countdownDiv.textContent = `Kalan Süre: ${data.remaining_seconds} saniye`;
    } else {
        console.warn("Geçersiz veya eksik wait_timer verisi:", data);
    }
});

// Hata mesajı alındığında
socket.on('error', (data) => {
    alert('Hata: ' + data.message);
});

socket.on('server_close_message', function (data) {
    console.log('Sunucudan gelen mesaj:', data.message);
    document.getElementById('messages').innerHTML += `<p>${data.message}</p>`;
});