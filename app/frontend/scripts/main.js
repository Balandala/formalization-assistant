const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const statusDiv = document.getElementById('status');
const dropZoneText = document.getElementById('dropZoneText');
const titleForm = document.getElementById('titleForm');
const modeUpload = document.getElementById('mode-upload');
const modeTitle = document.getElementById('mode-title');

let pollInterval = null;
let currentDocId = null;


function updateMode() {
    const addTitleCheckbox = document.getElementById('addTitleCheckbox');

    titleForm.style.display = 'none';
    addTitleCheckbox.style.display = 'none';

    if (modeTitle.checked) {
        titleForm.style.display = 'block';
        dropZoneText.textContent = 'Кликните, чтобы сгенерировать титульный лист';
        fileInput.style.display = 'none';
    } else {
        dropZoneText.textContent = 'Перетащите сюда файл .docx или кликните, чтобы выбрать';
        fileInput.style.display = 'none';
        addTitleCheckbox.style.display = 'block'; // Показываем чекбокс только в режиме загрузки
    }
}

modeUpload.addEventListener('change', updateMode);
modeTitle.addEventListener('change', updateMode);
updateMode();



dropZone.addEventListener('click', () => {
    if (modeTitle.checked) {

        const valid = document.getElementById('titleForm').checkValidity();
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

    // Сброс статуса и формы
    statusDiv.innerHTML = '';

    const includeTitle = document.getElementById('includeTitle').checked;

    if (!includeTitle) {
        await uploadFile(file); // Просто загружаем
        return;
    }

    // Если чекбокс выбран — показываем форму и кнопку
    titleForm.style.display = 'block';

    const submitButton = document.createElement('button');
    submitButton.className = 'btn btn-primary mt-2';
    submitButton.textContent = 'Сгенерировать с титульным листом';
    submitButton.onclick = async () => {
        const valid = titleForm.checkValidity();
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
                <br>
                <button class="btn btn-success mt-2" onclick="downloadFile('${result.id}')">
                    Скачать титульный лист
                </button>
            </div>
        `;
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
    }
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
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>✅ Готово!</strong>
                        <br>
                        <button class="btn btn-success mt-2" onclick="downloadFile('${docId}')">
                            Скачать файл
                        </button>
                    </div>
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