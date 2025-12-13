const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const statusDiv = document.getElementById('status');

let pollInterval = null;
let currentDocId = null;


dropZone.addEventListener('click', () => {
  fileInput.click();
});


dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});


fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file) handleFile(file);
});

async function handleFile(file) {
  if (!file.name.endsWith('.docx')) {
    statusDiv.innerHTML = '<div class="alert alert-danger">Только .docx файлы разрешены!</div>';
    return;
  }

  statusDiv.innerHTML = '<div class="alert alert-info">Загрузка на сервер...</div>';
  await uploadFile(file);
}


async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка загрузки');
    }

    const result = await response.json();
    currentDocId = result.id;


    statusDiv.innerHTML = `
      <div class="alert alert-info">
        <strong>Файл загружен. Обработка...</strong>
        <div class="spinner-border spinner-border-sm ms-2" role="status"></div>
      </div>
    `;


    pollInterval = setInterval(() => {
      checkStatus(currentDocId);
    }, 3000);

  } catch (error) {
    statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
  }
}


async function checkStatus(docId) {
  try {
    const response = await fetch(`/status/${docId}`);
    if (!response.ok) throw new Error('Документ не найден');

    const result = await response.json();

    if (result.status === 'COMPLETED') {

      clearInterval(pollInterval);
      pollInterval = null;

      statusDiv.innerHTML = `
        <div class="alert alert-success">
          <strong>✅ Обработка завершена!</strong>
          <br>
          <button class="btn btn-success mt-2" onclick="downloadFile('${docId}')">
            💾 Скачать файл
          </button>
        </div>
      `;
    } else if (result.status === 'FAILED') {
      clearInterval(pollInterval);
      pollInterval = null;

      statusDiv.innerHTML = `
        <div class="alert alert-danger">
          Ошибка при обработке файла.
        </div>
      `;
    }

  } catch (error) {
    console.error("Ошибка проверки статуса:", error);
    if (pollInterval) clearInterval(pollInterval);
    statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка сети: ${error.message}</div>`;
  }
}


async function downloadFile(docId) {
  try {
    const response = await fetch(`/download/${docId}`);
    if (!response.ok) throw new Error('Не удалось скачать файл');

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `processed_document_${docId}.docx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    alert('Ошибка скачивания: ' + error.message);
  }
}