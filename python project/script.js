const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const idleState = document.getElementById('idleState');
const scanState = document.getElementById('scanState');
const scanStatus = document.getElementById('scanStatus');
const errorMsg = document.getElementById('errorMsg');
const results = document.getElementById('results');
const resetBtn = document.getElementById('resetBtn');

const statPages = document.getElementById('statPages');
const statFile = document.getElementById('statFile');
const imageGrid = document.getElementById('imageGrid');
const downloadImages = document.getElementById('downloadImages');
const downloadPdf = document.getElementById('downloadPdf');
const downloadOcrPdf = document.getElementById('downloadOcrPdf');
const downloadText = document.getElementById('downloadText');

const statusLines = [
  'Rendering PDF pages…',
  'Recognizing text on each page…',
  'Building searchable PDF…',
  'Saving page images…',
  'Almost done…',
];
let statusInterval = null;

function startScanStatusLoop() {
  let i = 0;
  scanStatus.textContent = statusLines[0];
  statusInterval = setInterval(() => {
    i = (i + 1) % statusLines.length;
    scanStatus.textContent = statusLines[i];
  }, 1400);
}

function stopScanStatusLoop() {
  clearInterval(statusInterval);
}

dropzone.addEventListener('click', () => {
  if (!scanState.classList.contains('hidden')) return; // busy
  fileInput.click();
});

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

resetBtn.addEventListener('click', () => {
  results.classList.add('hidden');
  errorMsg.textContent = '';
  imageGrid.replaceChildren();
  scanState.classList.add('hidden');
  idleState.classList.remove('hidden');
  fileInput.value = '';
  stopScanStatusLoop();
});

function handleFile(file) {
  errorMsg.textContent = '';
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    errorMsg.textContent = 'Please choose a .pdf file.';
    return;
  }

  stopScanStatusLoop();
  idleState.classList.add('hidden');
  results.classList.add('hidden');
  scanState.classList.remove('hidden');
  startScanStatusLoop();

  const formData = new FormData();
  formData.append('pdf_file', file);

  fetch('/convert', { method: 'POST', body: formData })
    .then(async (res) => {
      const contentType = res.headers.get('content-type') || '';
      let data = null;
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        const message = await res.text();
        throw new Error(message || 'Something went wrong.');
      }
      if (!res.ok) throw new Error(data.error || 'Something went wrong.');
      return data;
    })
    .then((data) => showResults(data))
    .catch((err) => {
      errorMsg.textContent = err.message;
      scanState.classList.add('hidden');
      idleState.classList.remove('hidden');
    })
    .finally(() => stopScanStatusLoop());
}

function showResults(data) {
  scanState.classList.add('hidden');
  idleState.classList.remove('hidden');

  statPages.textContent = data.page_count;
  statFile.textContent = data.source_filename || '—';

  imageGrid.replaceChildren();
  data.image_filenames.forEach((filename, index) => {
    const card = document.createElement('figure');
    card.className = 'image-card';
    const image = document.createElement('img');
    image.src = `/download/${data.job_id}/${encodeURIComponent(filename)}`;
    image.alt = `Converted page ${index + 1}`;
    image.loading = 'lazy';
    const caption = document.createElement('figcaption');
    caption.textContent = `Page ${index + 1}`;
    card.append(image, caption);
    imageGrid.append(card);
  });

  downloadImages.href = `/download/${data.job_id}/${encodeURIComponent(data.zip_filename)}`;
  downloadPdf.href = `/download/${data.job_id}/${encodeURIComponent(data.pdf_filename)}`;
  downloadOcrPdf.href = `/download/${data.job_id}/${encodeURIComponent(data.ocr_pdf_filename)}`;
  downloadText.href = `/download/${data.job_id}/${encodeURIComponent(data.text_filename)}`;

  results.classList.remove('hidden');
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
