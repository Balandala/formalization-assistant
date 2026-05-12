const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const statusDiv = document.getElementById('status');
const dropZoneText = document.getElementById('dropZoneText');
const titleForm = document.getElementById('titleForm');
const modeUpload = document.getElementById('mode-upload');
const modeTitle = document.getElementById('mode-title');
const addTitleCheckbox = document.getElementById('addTitleCheckbox');
const includeTitleInput = document.getElementById('includeTitle');
const checkOnlyContainer = document.getElementById('checkOnlyContainer');
const checkOnlyInput = document.getElementById('checkOnly');
const tocContainer = document.getElementById('tocContainer');
const generateTocInput = document.getElementById('generateToc');
const tocPageInput = document.getElementById('tocPageNumber');

let pollInterval = null;
let currentDocId = null;

const container = dropZone.parentElement;

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function showStatusError(message) {
    statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${escapeHtml(message)}</div>`;
}

async function readErrorMessage(response, fallback) {
    try {
        const errorData = await response.json();
        return errorData.detail || fallback;
    } catch {
        return fallback;
    }
}

function syncUploadOptions() {
    if (checkOnlyInput.checked) {
        includeTitleInput.checked = false;
    }
    includeTitleInput.disabled = checkOnlyInput.checked;
}

function syncTocOptions() {
    tocPageInput.disabled = !generateTocInput.checked;
}

function getFormattingOptions() {
    const tocPageNumber = Number.parseInt(tocPageInput.value, 10);
    return {
        generateToc: generateTocInput.checked,
        tocPageNumber: Number.isNaN(tocPageNumber) || tocPageNumber < 1 ? 2 : tocPageNumber,
    };
}

function updateMode() {
    titleForm.style.display = 'none';
    addTitleCheckbox.style.display = 'none';
    checkOnlyContainer.style.display = 'none';
    tocContainer.style.display = 'none';

    if (modeTitle.checked) {
        titleForm.style.display = 'block';
        dropZoneText.textContent = 'Кликните, чтобы сгенерировать титульный лист';
    } else {
        dropZoneText.textContent = 'Перетащите сюда файл .docx или кликните, чтобы выбрать';
        addTitleCheckbox.style.display = 'block';
        checkOnlyContainer.style.display = 'block';
        tocContainer.style.display = 'block';
        syncUploadOptions();
        syncTocOptions();
    }
}

modeUpload.addEventListener('change', updateMode);
modeTitle.addEventListener('change', updateMode);
checkOnlyInput.addEventListener('change', syncUploadOptions);
generateTocInput.addEventListener('change', syncTocOptions);
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
        showStatusError('Только .docx файлы разрешены!');
        return;
    }

    statusDiv.innerHTML = '';
    const checkOnly = checkOnlyInput.checked;
    const includeTitle = includeTitleInput.checked;
    const formattingOptions = getFormattingOptions();

    if (checkOnly) {
        await uploadFile(file, true, formattingOptions);
        return;
    }

    if (!includeTitle) {
        await uploadFile(file, false, formattingOptions);
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
        await uploadWithCover(file, formattingOptions);
    };

    statusDiv.innerHTML = '';
    statusDiv.appendChild(submitButton);
}


function renderCompletedState(docId, report) {
    const checkOnly = Boolean(report && report.check_only);
    const successTitle = checkOnly ? '✅ Проверка завершена!' : '✅ Готово!';
    const previewLabel = checkOnly ? 'Предпросмотр исходного файла' : 'Предпросмотр';
    const diffButton = report && report.diff_path
        ? `
            <button class="btn btn-outline-secondary me-2" onclick="openDiff('${docId}')">
                <i class="bi bi-file-diff"></i> Diff
            </button>
        `
        : '';
    const downloadButton = checkOnly
        ? ''
        : `
            <button class="btn btn-success" onclick="downloadFile('${docId}')">
                <i class="bi bi-download"></i> Скачать файл
            </button>
        `;
    const note = checkOnly
        ? '<div class="mt-2 small text-muted">Исходный файл не изменялся.</div>'
        : '';

    statusDiv.innerHTML = `
        <div class="alert alert-success">
            <strong>${successTitle}</strong>
            <div class="mt-2">
                ${diffButton}
                <button class="btn btn-outline-primary me-2" onclick="openPreview('${docId}')">
                    <i class="bi bi-eye"></i> ${previewLabel}
                </button>
                ${downloadButton}
            </div>
            ${note}
        </div>
        ${renderReport(report)}
    `;
}

async function uploadFile(file, checkOnly = false, formattingOptions = getFormattingOptions()) {
    statusDiv.innerHTML = checkOnly
        ? '<div class="alert alert-info">Проверка документа...</div>'
        : '<div class="alert alert-info">Загрузка...</div>';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('check_only', String(checkOnly));
    formData.append('generate_toc', String(formattingOptions.generateToc));
    formData.append('toc_page_number', String(formattingOptions.tocPageNumber));

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(
                await readErrorMessage(
                    response,
                    checkOnly ? 'Ошибка проверки' : 'Ошибка загрузки',
                ),
            );
        }

        const result = await response.json();
        currentDocId = result.id;
        if (result.status === 'COMPLETED') {
            renderCompletedState(result.id, result.report);
            return;
        }
        if (result.status === 'FAILED') {
            showStatusError('Ошибка обработки');
            return;
        }
        startPolling(result.id);
    } catch (error) {
        showStatusError(error.message);
    }
}


async function uploadWithCover(file, formattingOptions = getFormattingOptions()) {
    const formData = new FormData();

    formData.append('file', file);
    formData.append('institute', document.getElementById('institute').value);
    formData.append('work_type', document.getElementById('work_type').value);
    formData.append('subject', document.getElementById('subject').value);
    formData.append('theme', document.getElementById('theme').value);
    formData.append('author', document.getElementById('author').value);
    formData.append('group', document.getElementById('group').value);
    formData.append('chief', document.getElementById('chief').value);
    formData.append('post', document.getElementById('post').value);
    formData.append('generate_toc', String(formattingOptions.generateToc));
    formData.append('toc_page_number', String(formattingOptions.tocPageNumber));

    statusDiv.innerHTML = '<div class="alert alert-info">Загрузка и генерация титульного листа...</div>';

    try {
        const response = await fetch('/upload-with-title', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(
                await readErrorMessage(response, 'Ошибка при загрузке с титульным листом'),
            );
        }

        const result = await response.json();
        currentDocId = result.id;
        if (result.status === 'COMPLETED') {
            renderCompletedState(result.id, result.report);
            return;
        }
        startPolling(result.id);
    } catch (error) {
        showStatusError(error.message);
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

        if (!response.ok) {
            throw new Error(await readErrorMessage(response, 'Ошибка генерации'));
        }

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
        showStatusError(error.message);
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

    const checkOnly = Boolean(report.check_only);
    const items = [];
    if (report.paragraphs_formatted > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет нормализовано абзацев' : 'Отформатировано параграфов'}: <strong>${report.paragraphs_formatted}</strong></li>`);
    if (report.headings_detected > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет оформлено заголовков' : 'Определено заголовков'}: <strong>${report.headings_detected}</strong></li>`);
    if (report.heading_page_breaks_added > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет добавлено разрывов страницы перед заголовками' : 'Добавлено разрывов страницы перед заголовками'}: <strong>${report.heading_page_breaks_added}</strong></li>`);
    if (report.figures_numbered > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет пронумеровано рисунков' : 'Пронумеровано рисунков'}: <strong>${report.figures_numbered}</strong></li>`);
    if (report.tables_numbered > 0)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет пронумеровано таблиц' : 'Пронумеровано таблиц'}: <strong>${report.tables_numbered}</strong></li>`);
    if (report.page_numbering_added)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет добавлена нумерация страниц' : 'Добавлена нумерация страниц'}</li>`);
    if (report.page_fields_set)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будут установлены поля страницы' : 'Установлены поля страницы'}</li>`);
    if (report.table_of_contents_generated)
        items.push(`<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> ${checkOnly ? 'Будет сгенерировано содержание' : 'Сгенерировано содержание'}${report.table_of_contents_entries > 0 ? `: <strong>${report.table_of_contents_entries}</strong>` : ''}${report.table_of_contents_page ? `, страница <strong>${report.table_of_contents_page}</strong>` : ''}</li>`);

    if (items.length === 0 && (!report.details || report.details.length === 0)) return '';

    let detailsHtml = '';
    if (report.details && report.details.length > 0) {
        const detailItems = report.details
            .map((detail) => `<li class="list-group-item list-group-item-light small">${escapeHtml(detail)}</li>`)
            .join('');
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
            <div class="card-header"><i class="bi bi-clipboard-check"></i> ${checkOnly ? 'Отчёт о проверке' : 'Отчёт о форматировании'}</div>
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

function openDiff(docId) {
    const frame = document.getElementById('diffFrame');
    frame.src = `/diff/${docId}`;
    const modal = new bootstrap.Modal(document.getElementById('diffModal'));
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
                const report = result.report ?? await fetchReport(docId);
                renderCompletedState(docId, report);
            } else if (result.status === 'FAILED') {
                clearInterval(pollInterval);
                showStatusError('Ошибка обработки');
            }
        } catch (e) {
            clearInterval(pollInterval);
            showStatusError('Ошибка сети');
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
