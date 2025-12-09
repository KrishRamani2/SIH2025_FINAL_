// --- TTP Editor Logic ---
let ttpTreeData = [];
let currentTTPPath = null;

async function initTTPEditor() {
    const container = document.getElementById('ttp-tree-container');
    const btnNew = document.getElementById('btn-new-ttp-file');
    const btnUpload = document.getElementById('btn-upload-ttp');

    if (currentUserRole === 'node_admin') {
        if (btnNew) btnNew.style.display = 'none';
        if (btnUpload) btnUpload.style.display = 'none';
    } else {
        if (btnNew) btnNew.style.display = '';
        if (btnUpload) btnUpload.style.display = '';
    }

    container.innerHTML = '<div class="text-center opacity-40 text-xs py-4"><i class="fas fa-circle-notch fa-spin mr-2"></i> Loading files...</div>';

    try {
        const res = await fetch('/api/ttp/tree');
        if (res.ok) {
            ttpTreeData = await res.json();
            renderTTPTree(ttpTreeData, container);
        } else {
            container.innerHTML = '<div class="text-center text-red-500 text-xs py-4">Failed to load files</div>';
        }
    } catch (e) {
        console.error(e);
        container.innerHTML = '<div class="text-center text-red-500 text-xs py-4">Error connecting to server</div>';
    }
}

function renderTTPTree(nodes, container) {
    container.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'pl-2 border-l border-white/5 ml-2 space-y-1';
    if (container.id === 'ttp-tree-container') ul.className = 'space-y-1'; // Root level

    nodes.forEach(node => {
        const li = document.createElement('li');

        if (node.type === 'directory') {
            li.innerHTML = `
                <div class="flex items-center gap-2 cursor-pointer hover:bg-white/5 p-1 rounded group" onclick="toggleTTPFolder(this)">
                    <i class="fas fa-folder text-yellow-500/80 group-hover:text-yellow-500 transition-colors text-xs"></i>
                    <span class="text-xs opacity-80 group-hover:opacity-100 select-none">${node.name}</span>
                    <i class="fas fa-chevron-right ml-auto text-[10px] opacity-40 transition-transform"></i>
                </div>
                <div class="hidden"></div>
            `;
            const subContainer = li.querySelector('div:last-child');
            if (node.children && node.children.length > 0) {
                renderTTPTree(node.children, subContainer);
            } else {
                subContainer.innerHTML = '<div class="pl-4 text-[10px] opacity-30 py-1">Empty</div>';
            }
        } else {
            li.innerHTML = `
                <div class="flex items-center gap-2 cursor-pointer hover:bg-white/5 p-1 rounded group" 
                    onclick="loadTTPFile('${node.path}', '${node.name}')">
                    <i class="fas fa-file-code text-blue-500/80 group-hover:text-blue-500 transition-colors text-xs"></i>
                    <span class="text-xs opacity-80 group-hover:opacity-100 truncate">${node.name}</span>
                </div>
            `;
        }
        ul.appendChild(li);
    });
    container.appendChild(ul);
}

function toggleTTPFolder(element) {
    const subContainer = element.nextElementSibling;
    const arrow = element.querySelector('.fa-chevron-right');

    if (subContainer.classList.contains('hidden')) {
        subContainer.classList.remove('hidden');
        arrow.classList.add('rotate-90');
    } else {
        subContainer.classList.add('hidden');
        arrow.classList.remove('rotate-90');
    }
}

async function loadTTPFile(path, name) {
    currentTTPPath = path;
    const editor = document.getElementById('ttp-editor-content');
    const filenameEl = document.getElementById('ttp-editor-filename');
    const pathEl = document.getElementById('ttp-editor-path');
    const btnSave = document.getElementById('btn-save-ttp');

    filenameEl.innerText = name;
    pathEl.innerText = path;
    editor.value = 'Loading...';
    editor.disabled = true;
    btnSave.disabled = true;

    try {
        const res = await fetch(`/api/ttp/file?path=${encodeURIComponent(path)}`);
        if (res.ok) {
            const data = await res.json();
            editor.value = data.content;

            if (currentUserRole === 'node_admin') {
                editor.disabled = true;
                btnSave.style.display = 'none';
                showToast('Read-only mode: Node Admin cannot edit files', 'info');
            } else {
                editor.disabled = false;
                btnSave.style.display = '';
                btnSave.disabled = false;
            }
        } else {
            editor.value = 'Failed to load content.';
        }
    } catch (e) {
        console.error(e);
        editor.value = 'Error loading content.';
    }
}

async function saveTTPFile() {
    if (currentUserRole === 'node_admin') {
        showToast('Permission Denied: Node Admin cannot save files', 'error');
        return;
    }
    if (!currentTTPPath) return;

    const editor = document.getElementById('ttp-editor-content');
    const btnSave = document.getElementById('btn-save-ttp');
    const content = editor.value;

    btnSave.disabled = true;
    btnSave.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Saving...';

    try {
        const res = await fetch('/api/ttp/file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-user-role': currentUserRole
            },
            body: JSON.stringify({ path: currentTTPPath, content: content })
        });

        if (res.ok) {
            showToast('File Saved Successfully', 'success');
            if (typeof restartEngine === 'function') {
                await restartEngine();
            }
        } else {
            showToast('Failed to save file', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error saving file', 'error');
    } finally {
        btnSave.disabled = false;
        btnSave.innerHTML = '<i class="fas fa-save"></i> Save Changes';
    }
}

function filterTTPTree(query) {
    const container = document.getElementById('ttp-tree-container');
    const items = container.querySelectorAll('li');

    if (!query) {
        items.forEach(item => item.classList.remove('hidden'));
        return;
    }

    query = query.toLowerCase();
    items.forEach(item => {
        const text = item.innerText.toLowerCase();
        if (text.includes(query)) {
            item.classList.remove('hidden');
            let parent = item.parentElement.closest('li');
            while (parent) {
                parent.classList.remove('hidden');
                parent = parent.parentElement.closest('li');
            }
        } else {
            item.classList.add('hidden');
        }
    });
}

// --- New TTP File Creation ---
function openNewTTPModal() {
    if (currentUserRole === 'node_admin') {
        showToast('Permission Denied: Node Admin cannot create files', 'error');
        return;
    }
    const modal = document.getElementById('new-ttp-modal');
    const select = document.getElementById('new-ttp-folder');

    // Flatten directories for selection
    const dirs = [];
    function traverse(nodes) {
        nodes.forEach(node => {
            if (node.type === 'directory') {
                dirs.push(node.path);
                if (node.children) traverse(node.children);
            }
        });
    }
    traverse(ttpTreeData);

    select.innerHTML = '<option value="" disabled selected>Select Folder...</option>';
    dirs.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.innerText = d;
        select.appendChild(opt);
    });

    modal.classList.remove('hidden');
}

async function createNewTTPFile() {
    const folder = document.getElementById('new-ttp-folder').value;
    const filename = document.getElementById('new-ttp-filename').value;

    if (!folder || !filename) {
        showToast('Please select a folder and enter a filename', 'warning');
        return;
    }

    if (!filename.endsWith('.json')) {
        showToast('Filename must end with .json', 'warning');
        return;
    }

    const fullPath = `${folder}/${filename}`;
    const defaultContent = `{
    "id": "${crypto.randomUUID()}",
    "name": "New TTP",
    "description": "Description of the TTP",
    "tactic": "initial-access",
    "technique": "T1000",
    "platform": "windows"
}`;

    try {
        const res = await fetch('/api/ttp/file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-user-role': currentUserRole
            },
            body: JSON.stringify({ path: fullPath, content: defaultContent })
        });

        if (res.ok) {
            showToast('File Created Successfully', 'success');
            document.getElementById('new-ttp-modal').classList.add('hidden');
            initTTPEditor(); // Refresh tree
            if (typeof restartEngine === 'function') {
                await restartEngine();
            }
        } else {
            showToast('Failed to create file', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error creating file', 'error');
    }
}

async function handleTTPUpload(input) {
    if (currentUserRole !== 'admin') {
        showToast('Only Admins can upload TTP files', 'warning');
        input.value = '';
        return;
    }

    const file = input.files[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
        showToast('Invalid file type. Please upload a .json file', 'warning');
        input.value = '';
        return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
        const content = e.target.result;
        const filename = file.name;
        const path = `Uploads/${filename}`;

        try {
            showToast(`Uploading ${filename}...`, 'info');
            const res = await fetch('/api/ttp/file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-user-role': currentUserRole
                },
                body: JSON.stringify({ path: path, content: content })
            });

            if (res.ok) {
                showToast('File Uploaded & Saved', 'success');

                const editor = document.getElementById('ttp-editor-content');
                const filenameEl = document.getElementById('ttp-editor-filename');
                const pathEl = document.getElementById('ttp-editor-path');
                const btnSave = document.getElementById('btn-save-ttp');

                editor.value = content;
                editor.disabled = false;
                btnSave.disabled = false;
                filenameEl.innerText = filename;
                pathEl.innerText = path;
                currentTTPPath = path;

                initTTPEditor(); // Refresh tree
                if (typeof restartEngine === 'function') {
                    await restartEngine();
                }
            } else {
                const err = await res.json();
                showToast(`Upload failed: ${err.detail}`, 'error');
            }
        } catch (e) {
            console.error(e);
            showToast('Error uploading file', 'error');
        }
    };
    reader.readAsText(file);
    input.value = '';
}
