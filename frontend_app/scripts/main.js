document.getElementById('uploadBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('fileInput');
  const googleDocLink = document.getElementById('googleDocLink').value;
  const file = fileInput.files[0];
  const statusDiv = document.getElementById('status');

  let uploadFile = null;

  if (googleDocLink) {
    statusDiv.innerHTML = '<div class="alert alert-info">Скачивание из Google Docs...</div>';

    const docId = extractFileId(googleDocLink);
    if (!docId) {
      statusDiv.innerHTML = '<div class="alert alert-danger">Неверная ссылка на Google Docs</div>';
      return;
    }

    try {
      uploadFile = await downloadFromGoogleDocs(docId);
      statusDiv.innerHTML = '<div class="alert alert-success">Документ загружен из Google Docs. Загрузка на сервер...</div>';
    } catch (error) {
      statusDiv.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
      return;
    }
  } else if (file) {
    if (!file.name.endsWith('.docx')) {
      statusDiv.innerHTML = '<div class="alert alert-danger">Только .docx файлы разрешены!</div>';
      return;
    }
    uploadFile = file;
  } else {
    statusDiv.innerHTML = '<div class="alert alert-warning">Выберите файл или вставьте ссылку!</div>';
    return;
  }

  statusDiv.innerHTML = '<div class="alert alert-info">Загрузка на сервер...</div>';

  const formData = new FormData();
  formData.append('file', uploadFile);

  try {
    const response = await fetch('/upload', {  // используем относительный путь
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка загрузки');
    }

    const result = await response.json();

    statusDiv.innerHTML = `
      <div class="alert alert-success">
        <strong>Файл загружен!</strong><br>
        ID: ${result.id}<br>
        <button class="btn btn-sm btn-outline-secondary mt-2" onclick="checkStatus('${result.id}')">Проверить статус</button>
        <button class="btn btn-sm btn-outline-info mt-2" onclick="downloadFile('${result.id}')">Скачать</button>
      </div>
    `;
  } catch (error) {
    statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
  }
});

async function checkStatus(docId) {
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = '<div class="alert alert-info">Проверка статуса...</div>';

    try {
        const response = await fetch(`http://localhost:8000/status/${docId}`);
        if (!response.ok) throw new Error('Документ не найден');

        const result = await response.json();
        statusDiv.innerHTML = `
      <div class="alert alert-${result.status === 'COMPLETED' ? 'success' : 'warning'}">
        <strong>Статус:</strong> ${result.status}<br>
        ID: ${result.id}<br>
        ${result.status === 'COMPLETED' ? `<button class="btn btn-sm btn-outline-info mt-2" onclick="downloadFile('${result.id}')">Скачать</button>` : ''}
      </div>
    `;
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message} при проверке статуса</div>`;
    }
}
async function downloadFile(docId) {
  try {
    const response = await fetch(`http://localhost:8000/download/${docId}`);
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

function extractFileId(url) {
  const match = url.match(/\/d\/([^\/]+)/);
  return match ? match[1] : null;
}


async function downloadFromGoogleDocs(docId) {
  const exportUrl = `https://docs.google.com/document/d/${docId}/export?format=docx`;

  try {
    const response = await fetch(exportUrl);
    if (!response.ok) throw new Error("Не удалось скачать документ");

    const blob = await response.blob();
    const file = new File([blob], "google_doc.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
    return file;
  } catch (error) {
    throw new Error("Ошибка загрузки из Google Docs: " + error.message);
  }
}