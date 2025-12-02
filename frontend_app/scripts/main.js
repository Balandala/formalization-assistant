document.getElementById('uploadBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('fileInput');
  const file = fileInput.files[0];
  const statusDiv = document.getElementById('status');

  if (!file) {
    statusDiv.innerHTML = '<div class="alert alert-warning">Выберите файл!</div>';
    return;
  }

  if (!file.name.endsWith('.docx')) {
    statusDiv.innerHTML = '<div class="alert alert-danger">Только .docx файлы разрешены!</div>';
    return;
  }

  // Показываем процесс загрузки
  statusDiv.innerHTML = '<div class="alert alert-info">Загрузка...</div>';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка загрузки');
    }

    const result = await response.json();

    // Успешно загружено
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

// Функция проверки статуса
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
    statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
  }
}

// Функция скачивания
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