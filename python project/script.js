const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const idleState = document.getElementById('idleState');
const scanState = document.getElementById('scanState');
const scanStatus = document.getElementById('scanStatus');
const errorMsg = document.getElementById('errorMsg');
const results = document.getElementById('results');
const resetBtn = document.getElementById('resetBtn');

const statPages = document.getElementById('statPages');
const statWords = document.getElementById('statWords');
const statFile = document.getElementById('statFile');
const previewText = document.getElementById('previewText');
const downloadTxt = document.getElementById('downloadTxt');
const downloadPdf = document.getElementById('downloadPdf');

// Rotate status lines while we wait for the server, purely cosmetic —
// gives feedback during what can be a several-second OCR job.
const statusLines = [
  'Reading document…',
  'Locating word positions…',
  'Recognizing text…',
  'Creating image-only PDF…',
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
  idleState.classList.remove('hidden');
  fileInput.value = '';
});

function handleFile(file) {
  errorMsg.textContent = '';
    if (!file.name.toLowerCase().endsWith('.pdf'))
  {
    errorMsg.textContent = 'Please choose a .pdf file.';
    return;
  }

  idleState.classList.add('hidden');
  results.classList.add('hidden');
  scanState.classList.remove('hidden');
  startScanStatusLoop();

  const formData = new FormData();
  formData.append('pdf_file', file);

  fetch('/convert', { method: 'POST', body: formData })
    .then(async (res) => {
      const data = await res.json();
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
  statWords.textContent = data.total_words;
  statFile.textContent = data.source_filename || '—';
  previewText.textContent = data.preview || '(No text detected)';

  downloadTxt.href = `/download/${data.job_id}/${data.txt_filename}`;
  downloadPdf.href = `/download/${data.job_id}/${data.pdf_filename}`;

  results.classList.remove('hidden');
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
