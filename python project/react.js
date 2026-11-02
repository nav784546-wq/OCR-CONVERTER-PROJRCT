const { useEffect, useRef, useState } = React;

const statusLines = [
  'Rendering PDF pages…',
  'Recognizing text on each page…',
  'Building searchable PDF…',
  'Saving page images…',
  'Almost done…',
];

function OCRApp() {
  const fileInputRef = useRef(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [result, setResult] = useState(null);
  const [statusText, setStatusText] = useState('Recognizing text in PDF pages…');

  useEffect(() => {
    if (!isBusy) return;

    let index = 0;
    setStatusText(statusLines[0]);

    const timerId = setInterval(() => {
      index = (index + 1) % statusLines.length;
      setStatusText(statusLines[index]);
    }, 1400);

    return () => clearInterval(timerId);
  }, [isBusy]);

  function openPicker() {
    if (!isBusy) {
      fileInputRef.current?.click();
    }
  }

  function reset() {
    setResult(null);
    setErrorMsg('');
    setIsBusy(false);
    setStatusText('Recognizing text in PDF pages…');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleFile(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMsg('Please choose a .pdf file.');
      return;
    }

    setErrorMsg('');
    setIsBusy(true);
    setResult(null);

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

        if (!res.ok) {
          throw new Error(data.error || 'Something went wrong.');
        }

        return data;
      })
      .then((data) => {
        setResult(data);
        setIsBusy(false);
      })
      .catch((err) => {
        setErrorMsg(err.message);
        setIsBusy(false);
      });
  }

  function onInputChange(event) {
    const file = event.target.files?.[0];
    if (file) handleFile(file);
  }

  function onDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return React.createElement(
    'div',
    { className: 'page' },
    React.createElement(
      'header',
      { className: 'hero' },
      React.createElement('p', { className: 'eyebrow' }, 'PDF\u00A0OCR\u00A0CONVERTER\u00A0/\u00A0LOCAL'),
      React.createElement(
        'h1',
        null,
        'Turn PDF pages into',
        React.createElement('br', null),
        React.createElement('span', null, 'searchable text.')
      ),
      React.createElement(
        'p',
        { className: 'subhead' },
        'Drop in a PDF to recognize its text and convert every page into a high-resolution PNG. Download the searchable PDF, extracted text, or images.'
      )
    ),
    React.createElement(
      'section',
      {
        className: `scanner-bed${isDragging ? ' dragover' : ''}`,
        id: 'dropzone',
        onClick: openPicker,
        onDragOver: (event) => {
          event.preventDefault();
          setIsDragging(true);
        },
        onDragLeave: () => setIsDragging(false),
        onDrop: onDrop,
      },
      React.createElement('div', { className: 'bracket tl' }),
      React.createElement('div', { className: 'bracket tr' }),
      React.createElement('div', { className: 'bracket bl' }),
      React.createElement('div', { className: 'bracket br' }),
      !isBusy
        ? React.createElement(
            'div',
            { className: 'bed-content', id: 'idleState' },
            React.createElement(
              'svg',
              { width: '40', height: '52', viewBox: '0 0 40 52', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' },
              React.createElement('path', {
                d: 'M4 2H26L36 12V50H4V2Z',
                stroke: 'currentColor',
                'stroke-width': '2',
                'stroke-linejoin': 'round',
              }),
              React.createElement('path', {
                d: 'M26 2V12H36',
                stroke: 'currentColor',
                'stroke-width': '2',
                'stroke-linejoin': 'round',
              }),
              React.createElement('line', { x1: '10', y1: '24', x2: '30', y2: '24', stroke: 'currentColor', 'stroke-width': '1.5' }),
              React.createElement('line', { x1: '10', y1: '31', x2: '30', y2: '31', stroke: 'currentColor', 'stroke-width': '1.5' }),
              React.createElement('line', { x1: '10', y1: '38', x2: '22', y2: '38', stroke: 'currentColor', 'stroke-width': '1.5' })
            ),
            React.createElement(
              'p',
              { className: 'bed-label' },
              'Drop PDF here, or ',
              React.createElement('span', { className: 'link-text' }, 'browse files')
            ),
            React.createElement('p', { className: 'bed-sublabel' }, '.PDF · up to 100MB'),
            React.createElement('input', {
              ref: fileInputRef,
              type: 'file',
              id: 'fileInput',
              accept: 'application/pdf,.pdf',
              hidden: true,
              onChange: onInputChange,
            })
          )
        : React.createElement(
            'div',
            { className: 'bed-content', id: 'scanState' },
            React.createElement(
              'div',
              { className: 'scan-frame' },
              React.createElement('div', { className: 'page-icon' }),
              React.createElement('div', { className: 'sweep-line' })
            ),
            React.createElement('p', { className: 'scan-status' }, statusText)
          )
    ),
    React.createElement('p', { className: 'error-msg' }, errorMsg),
    result
      ? React.createElement(
          'section',
          { className: 'results', id: 'results' },
          React.createElement(
            'div',
            { className: 'stats-row' },
            React.createElement(
              'div',
              { className: 'stat' },
              React.createElement('span', { className: 'stat-value' }, result.page_count),
              React.createElement('span', { className: 'stat-label' }, 'PAGES')
            ),
            React.createElement(
              'div',
              { className: 'stat' },
              React.createElement('span', { className: 'stat-value' }, result.image_filenames?.length ?? 0),
              React.createElement('span', { className: 'stat-label' }, 'PNG IMAGES')
            ),
            React.createElement(
              'div',
              { className: 'stat' },
              React.createElement('span', { className: 'stat-value' }, result.source_filename || '—'),
              React.createElement('span', { className: 'stat-label' }, 'SOURCE FILE')
            )
          ),
          React.createElement(
            'div',
            { className: 'image-grid', 'aria-label': 'Converted page images' },
            (result.image_filenames || []).map((filename, index) =>
              React.createElement(
                'figure',
                { className: 'image-card', key: filename },
                React.createElement('img', {
                  src: `/download/${result.job_id}/${encodeURIComponent(filename)}`,
                  alt: `Converted page ${index + 1}`,
                  loading: 'lazy',
                }),
                React.createElement('figcaption', null, `Page ${index + 1}`)
              )
            )
          ),
          React.createElement(
            'div',
            { className: 'downloads' },
            React.createElement(
              'a',
              { className: 'dl-card', href: `/download/${result.job_id}/${encodeURIComponent(result.zip_filename)}`, download: true },
              React.createElement('span', { className: 'dl-kind' }, '.ZIP'),
              React.createElement('span', { className: 'dl-name' }, 'Download page images'),
              React.createElement('span', { className: 'dl-arrow' }, '→')
            ),
            React.createElement(
              'a',
              { className: 'dl-card', href: `/download/${result.job_id}/${encodeURIComponent(result.pdf_filename)}`, download: true },
              React.createElement('span', { className: 'dl-kind' }, '.PDF'),
              React.createElement('span', { className: 'dl-name' }, 'Unsearchable image-only PDF'),
              React.createElement('span', { className: 'dl-arrow' }, '→')
            ),
            React.createElement(
              'a',
              { className: 'dl-card', href: `/download/${result.job_id}/${encodeURIComponent(result.ocr_pdf_filename)}`, download: true },
              React.createElement('span', { className: 'dl-kind' }, '.PDF'),
              React.createElement('span', { className: 'dl-name' }, 'Searchable OCR PDF'),
              React.createElement('span', { className: 'dl-arrow' }, '→')
            ),
            React.createElement(
              'a',
              { className: 'dl-card', href: `/download/${result.job_id}/${encodeURIComponent(result.text_filename)}`, download: true },
              React.createElement('span', { className: 'dl-kind' }, '.TXT'),
              React.createElement('span', { className: 'dl-name' }, 'Extracted text'),
              React.createElement('span', { className: 'dl-arrow' }, '→')
            )
          ),
          React.createElement(
            'button',
            { className: 'reset-btn', onClick: reset },
            'Convert another PDF'
          )
        )
      : null
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  React.createElement(OCRApp)
);
