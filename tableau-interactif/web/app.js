// Le navigateur reçoit les formes. Leur création se fait dans client.py.
const canvas = document.getElementById('board');
const context = canvas.getContext('2d');
const wrap = document.getElementById('board-wrap');
const notice = document.getElementById('notice');
const clearButton = document.getElementById('clear-button');
const dialog = document.getElementById('clear-dialog');
const labels = {point:'Point', line:'Ligne', circle:'Cercle', rectangle:'Rectangle', square:'Carré'};
let shapes = [];
let connected = false;
let socket;
let retry;
let closed = false;

function drawShape(shape, target = context) {
  target.fillStyle = `rgb(${shape.color.join(',')})`;
  target.strokeStyle = target.fillStyle;
  target.lineWidth = 4;
  target.lineCap = 'round';
  target.beginPath();
  switch (shape.shape) {
    case 'point': target.arc(shape.x, shape.y, 4, 0, 2 * Math.PI); target.fill(); break;
    case 'line': target.moveTo(shape.x1, shape.y1); target.lineTo(shape.x2, shape.y2); target.stroke(); break;
    case 'circle': target.arc(shape.x, shape.y, shape.radius, 0, 2 * Math.PI); target.fill(); break;
    case 'rectangle': target.fillRect(shape.x, shape.y, shape.width, shape.height); break;
    case 'square': target.fillRect(shape.x, shape.y, shape.cote, shape.cote); break;
  }
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (const shape of shapes) drawShape(shape);
  document.getElementById('empty').hidden = shapes.length > 0;
  document.getElementById('shape-count').textContent = shapes.length;
  document.getElementById('shape-plural').textContent = shapes.length === 1 ? '' : 's';
  canvas.setAttribute('aria-label', `Dessin partagé : ${shapes.length} forme(s)`);
  const last = shapes[shapes.length - 1];
  document.getElementById('last-shape').textContent = last ? labels[last.shape] : 'À vous de jouer';
  clearButton.disabled = !connected || shapes.length === 0;
  const palette = document.getElementById('palette');
  palette.replaceChildren();
  const colors = [...new Set(shapes.map(shape => shape.color.join(',')))];
  if (!colors.length) {
    const empty = document.createElement('span');
    empty.className = 'muted';
    empty.textContent = 'La palette se remplit au fil des dessins.';
    palette.append(empty);
  }
  for (const color of colors.slice(0, 24)) {
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.backgroundColor = `rgb(${color})`;
    swatch.title = `RGB ${color}`;
    swatch.setAttribute('aria-label', `Couleur RGB ${color}`);
    palette.append(swatch);
  }
}

function setConnection(value, message) {
  connected = value;
  document.getElementById('connection').className = 'connection ' + (value ? 'connected' : 'offline');
  document.getElementById('connection-text').textContent = message;
  clearButton.disabled = !value || shapes.length === 0;
  if (!value) document.getElementById('viewers').textContent = 'En attente de connexion';
}

function showClients(count) {
  document.getElementById('viewers').textContent = `${count} tableau${count === 1 ? '' : 'x'} connecté${count === 1 ? '' : 's'}`;
}

async function connect() {
  if (closed) return;
  try {
    const response = await fetch('/config');
    if (!response.ok) throw new Error('Configuration indisponible');
    const config = await response.json();
    const address = new URL(window.location.href);
    address.protocol = address.protocol === 'https:' ? 'wss:' : 'ws:';
    address.port = config.ws_port;
    address.pathname = '/';
    address.search = '';
    address.hash = '';
    socket = new WebSocket(address.href);
    socket.onopen = () => { setConnection(true, 'Connecté en direct'); notice.textContent = ''; };
    socket.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.type === 'snapshot') { shapes = message.shapes; showClients(message.clients); render(); }
      else if (message.type === 'shape') { shapes.push(message.shape); notice.textContent = ''; render(); }
      else if (message.type === 'clear') { shapes = []; render(); notice.textContent = 'Le tableau a été effacé.'; }
      else if (message.type === 'clients') showClients(message.count);
    };
    socket.onclose = () => {
      setConnection(false, 'Reconnexion…');
      if (!closed) retry = setTimeout(connect, 2000);
    };
    socket.onerror = () => socket.close();
  } catch (error) {
    setConnection(false, 'Serveur indisponible');
    if (!closed) retry = setTimeout(connect, 2000);
  }
}

const gridButton = document.getElementById('grid-button');
wrap.classList.add('grid');
gridButton.addEventListener('click', () => {
  const active = wrap.classList.toggle('grid');
  gridButton.setAttribute('aria-pressed', String(active));
});

clearButton.addEventListener('click', () => {
  dialog.returnValue = 'cancel';
  dialog.showModal();
});
dialog.addEventListener('close', async () => {
  if (dialog.returnValue !== 'clear') return;
  try {
    const response = await fetch('/clear', {method:'POST'});
    if (!response.ok) throw new Error('Effacement impossible');
  } catch (error) { notice.textContent = 'Impossible d’effacer : vérifie la connexion au serveur.'; }
});

document.getElementById('export-button').addEventListener('click', () => {
  const image = document.createElement('canvas');
  image.width = canvas.width;
  image.height = canvas.height;
  const output = image.getContext('2d');
  output.fillStyle = '#fffef9';
  output.fillRect(0, 0, image.width, image.height);
  for (const shape of shapes) drawShape(shape, output);
  const link = document.createElement('a');
  link.download = 'atelier-commun.png';
  link.href = image.toDataURL('image/png');
  link.click();
  notice.textContent = 'L’image du tableau a été préparée pour le téléchargement.';
});

canvas.addEventListener('pointermove', event => {
  const bounds = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - bounds.left) * canvas.width / bounds.width);
  const y = Math.floor((event.clientY - bounds.top) * canvas.height / bounds.height);
  document.getElementById('coordinates').textContent = `x ${x} · y ${y}`;
});
canvas.addEventListener('pointerleave', () => {
  document.getElementById('coordinates').textContent = 'Origine : en haut à gauche';
});
window.addEventListener('beforeunload', () => {
  closed = true;
  clearTimeout(retry);
  if (socket) socket.close();
});
render();
connect();
