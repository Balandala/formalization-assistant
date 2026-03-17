const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const statusDiv = document.getElementById('status');
const dropZoneText = document.getElementById('dropZoneText');
const titleForm = document.getElementById('titleForm');
const modeUpload = document.getElementById('mode-upload');
const modeTitle = document.getElementById('mode-title');
const addTitleCheckbox = document.getElementById('addTitleCheckbox');

let pollInterval = null;
let currentDocId = null;

const container = dropZone.parentElement;

function updateMode() {
    titleForm.style.display = 'none';
    addTitleCheckbox.style.display = 'none';

    if (modeTitle.checked) {
        titleForm.style.display = 'block';
        dropZoneText.textContent = 'Кликните, чтобы сгенерировать титульный лист';
    } else {
        dropZoneText.textContent = 'Перетащите сюда файл .docx или кликните, чтобы выбрать';
        addTitleCheckbox.style.display = 'block';
    }
}

modeUpload.addEventListener('change', updateMode);
modeTitle.addEventListener('change', updateMode);
updateMode();



dropZone.addEventListener('click', () => {
    if (modeTitle.checked) {
        const valid = titleForm.checkValidity();
        if (!valid) {
            alert('Заполните все поля для титульного листа');
            return;
        }
        generateTitle();
    } else {
        fileInput.click();
    }
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

    statusDiv.innerHTML = '';
    const includeTitle = document.getElementById('includeTitle').checked;

    if (!includeTitle) {
        await uploadFile(file);
        return;
    }


    const formClone = titleForm.cloneNode(true);
    formClone.id = 'titleFormActive';
    formClone.style.display = 'block';


    container.innerHTML = '';
    container.appendChild(formClone);


    const submitButton = document.createElement('button');
    submitButton.className = 'btn btn-primary mt-3';
    submitButton.textContent = 'Сгенерировать с титульным листом';
    submitButton.onclick = async () => {
        const valid = formClone.checkValidity();
        if (!valid) {
            alert('Заполните все поля');
            return;
        }
        await uploadWithCover(file);
    };

    statusDiv.innerHTML = '';
    statusDiv.appendChild(submitButton);
}


async function uploadFile(file) {
    statusDiv.innerHTML = '<div class="alert alert-info">Загрузка...</div>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) throw new Error((await response.json()).detail || 'Ошибка загрузки');

        const result = await response.json();
        currentDocId = result.id;
        startPolling(result.id);
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
    }
}


async function uploadWithCover(file) {
    console.log("uploadWithCover вызвана", file);
    const formData = new FormData();

    // Явно добавляем нужные поля
    formData.append('file', file);
    formData.append('institute', document.getElementById('institute').value);
    formData.append('work_type', document.getElementById('work_type').value);
    formData.append('subject', document.getElementById('subject').value);
    formData.append('theme', document.getElementById('theme').value);
    formData.append('author', document.getElementById('author').value);
    formData.append('group', document.getElementById('group').value);
    formData.append('chief', document.getElementById('chief').value);
    formData.append('post', document.getElementById('post').value);

    statusDiv.innerHTML = '<div class="alert alert-info">Загрузка и генерация титульного листа...</div>';

    try {
        const response = await fetch('/upload-with-title', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
            throw new Error(errorData.detail || 'Ошибка при загрузке с титульным листом');
        }

        const result = await response.json();
        currentDocId = result.id;
        startPolling(result.id);
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
    }
}


async function generateTitle() {
    const data = {
        institute: document.getElementById('institute').value,
        work_type: document.getElementById('work_type').value,
        subject: document.getElementById('subject').value,
        theme: document.getElementById('theme').value,
        author: document.getElementById('author').value,
        group: document.getElementById('group').value,
        chief: document.getElementById('chief').value,
        post: document.getElementById('post').value,
    };

    const valid = Object.values(data).every(v => v);
    if (!valid) {
        alert('Заполните все поля');
        return;
    }

    statusDiv.innerHTML = '<div class="alert alert-info">Генерация титульного листа...</div>';

    try {
        const response = await fetch('/generate-title', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error((await response.json()).detail || 'Ошибка генерации');

        const result = await response.json();
        currentDocId = result.id;
        statusDiv.innerHTML = `
            <div class="alert alert-success">
                <strong>✅ Титульный лист готов!</strong>
                <div class="mt-2">
                    <button class="btn btn-outline-primary me-2" onclick="openPreview('${result.id}')">
                        <i class="bi bi-eye"></i> Предпросмотр
                    </button>
                    <button class="btn btn-success" onclick="downloadFile('${result.id}')">
                        <i class="bi bi-download"></i> Скачать титульный лист
                    </button>
                </div>
            </div>
        `;
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
    }
}


async function fetchReport(docId) {
    try {
        const response = await fetch(`/report/${docId}`);
        if (!response.ok) return null;
        return await response.json();
    } catch {
        return null;
    }
}

function renderReport(report) {
    if (!report) return '';

    const items = [];
    if (report.paragraphs_formatted > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Отформатировано параграфов: <strong>${report.paragraphs_formatted}</strong></li>`);
    if (report.headings_detected > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Определено заголовков: <strong>${report.headings_detected}</strong></li>`);
    if (report.figures_numbered > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Пронумеровано рисунков: <strong>${report.figures_numbered}</strong></li>`);
    if (report.tables_numbered > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Пронумеровано таблиц: <strong>${report.tables_numbered}</strong></li>`);
    if (report.page_numbering_added)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Добавлена нумерация страниц</li>`);
    if (report.page_fields_set)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> Установлены поля страницы</li>`);

    if (items.length === 0) return '';

    let detailsHtml = '';
    if (report.details && report.details.length > 0) {
        const detailItems = report.details.map(d => `<li class="list-group-item list-group-item-light small">${d}</li>`).join('');
        detailsHtml = `
            <div class="mt-2">
                <a class="btn btn-sm btn-outline-secondary" data-bs-toggle="collapse" href="#reportDetails" role="button">
                    <i class="bi bi-list-ul"></i> Подробности (${report.details.length})
                </a>
                <div class="collapse mt-2" id="reportDetails">
                    <ul class="list-group list-group-flush">${detailItems}</ul>
                </div>
            </div>
        `;
    }

    return `
        <div class="card mt-3">
            <div class="card-header"><i class="bi bi-clipboard-check"></i> Отчёт о форматировании</div>
            <ul class="list-group list-group-flush">${items.join('')}</ul>
            ${detailsHtml}
        </div>
    `;
}

function openPreview(docId) {
    const frame = document.getElementById('previewFrame');
    frame.src = `/preview/${docId}`;
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

function startPolling(docId) {
    statusDiv.innerHTML = `
        <div class="alert alert-info">
            <strong>Обработка...</strong>
            <div class="spinner-border spinner-border-sm ms-2" role="status"></div>
        </div>
    `;

    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${docId}`);
            if (!response.ok) throw new Error();

            const result = await response.json();
            if (result.status === 'COMPLETED') {
                clearInterval(pollInterval);
                const report = await fetchReport(docId);
                const reportHtml = renderReport(report);
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>✅ Готово!</strong>
                        <div class="mt-2">
                            <button class="btn btn-outline-primary me-2" onclick="openPreview('${docId}')">
                                <i class="bi bi-eye"></i> Предпросмотр
                            </button>
                            <button class="btn btn-success" onclick="downloadFile('${docId}')">
                                <i class="bi bi-download"></i> Скачать файл
                            </button>
                        </div>
                    </div>
                    ${reportHtml}
                `;
            } else if (result.status === 'FAILED') {
                clearInterval(pollInterval);
                statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка обработки</div>`;
            }
        } catch (e) {
            clearInterval(pollInterval);
            statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка сети</div>`;
        }
    }, 3000);
}

async function downloadFile(docId) {
    try {
        const response = await fetch(`/download/${docId}`);
        if (!response.ok) throw new Error('Не удалось скачать');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document_${docId}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert('Ошибка скачивания: ' + error.message);
    }
}