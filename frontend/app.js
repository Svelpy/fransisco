const API_URL = '';

let state = {
    q: '',
    laboratorio: '',
    distribuidor: '',
    page: 1,
    totalPages: 1,
    labs: [],
    distribuidores: []
};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const labInput = document.getElementById('labInput');
const distInput = document.getElementById('distInput');
const labDropdown = document.getElementById('labDropdown');
const distDropdown = document.getElementById('distDropdown');
const btnSearch = document.getElementById('btnSearch');
const btnClear = document.getElementById('btnClear');
const cardsContainer = document.getElementById('cardsContainer');
const resultsCount = document.getElementById('resultsCount');
const btnPrev = document.getElementById('btnPrev');
const btnNext = document.getElementById('btnNext');
const pageInfo = document.getElementById('pageInfo');
const detailModal = document.getElementById('detailModal');
const closeModal = document.getElementById('closeModal');

// Init
async function init() {
    await fetchFilters();
    setupDropdown(labInput, labDropdown, state.labs, (val) => state.laboratorio = val);
    setupDropdown(distInput, distDropdown, state.distribuidores, (val) => state.distribuidor = val);

    // Event Listeners
    btnSearch.addEventListener('click', () => { state.page = 1; fetchMedicamentos(); });
    btnClear.addEventListener('click', clearFilters);
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { state.page = 1; fetchMedicamentos(); } });

    btnPrev.addEventListener('click', () => { if (state.page > 1) { state.page--; fetchMedicamentos(); } });
    btnNext.addEventListener('click', () => { if (state.page < state.totalPages) { state.page++; fetchMedicamentos(); } });

    closeModal.addEventListener('click', () => detailModal.classList.add('hidden'));
    detailModal.addEventListener('click', (e) => { if (e.target === detailModal) detailModal.classList.add('hidden'); });

    // Copy to clipboard setup
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const targetId = e.target.getAttribute('data-target');
            const element = document.getElementById(targetId);
            let textToCopy = '';

            if (element.tagName === 'A') textToCopy = element.href;
            else textToCopy = element.textContent;

            if (textToCopy) {
                await navigator.clipboard.writeText(textToCopy);
                const originalText = e.target.textContent;
                e.target.textContent = '✔️';
                setTimeout(() => e.target.textContent = originalText, 2000);
            }
        });
    });

    fetchMedicamentos();
}

async function fetchFilters() {
    try {
        const [labsRes, distRes] = await Promise.all([
            fetch(`${API_URL}/laboratorios`),
            fetch(`${API_URL}/distribuidores`)
        ]);
        state.labs = await labsRes.json();
        state.distribuidores = await distRes.json();
    } catch (err) {
        console.error("Error fetching filters", err);
    }
}

function setupDropdown(input, dropdown, dataList, onSelect) {
    input.addEventListener('focus', () => {
        renderDropdown(dropdown, dataList, input.value, input, onSelect);
        dropdown.classList.remove('hidden');
    });

    input.addEventListener('input', () => {
        renderDropdown(dropdown, dataList, input.value, input, onSelect);
        onSelect(''); // Si escribe, se resetea la seleccion exacta hasta que elija una
    });

    // Cierra dropdown al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
}

function renderDropdown(dropdown, dataList, filterText, inputElement, onSelect) {
    dropdown.innerHTML = '';
    const filtered = dataList.filter(item => item.toLowerCase().includes(filterText.toLowerCase()));

    if (filtered.length === 0) {
        const div = document.createElement('div');
        div.className = 'dropdown-item';
        div.textContent = 'Sin resultados';
        dropdown.appendChild(div);
        return;
    }

    filtered.forEach(item => {
        const div = document.createElement('div');
        div.className = 'dropdown-item';
        div.textContent = item;
        div.addEventListener('click', () => {
            inputElement.value = item;
            onSelect(item);
            dropdown.classList.add('hidden');
        });
        dropdown.appendChild(div);
    });
}

function clearFilters() {
    searchInput.value = '';
    labInput.value = '';
    distInput.value = '';
    state.q = '';
    state.laboratorio = '';
    state.distribuidor = '';
    state.page = 1;
    fetchMedicamentos();
}

async function fetchMedicamentos() {
    state.q = searchInput.value;

    resultsCount.textContent = "Cargando resultados...";
    cardsContainer.innerHTML = '';

    const params = new URLSearchParams();
    if (state.q) params.append('q', state.q);
    if (state.laboratorio) params.append('laboratorio', state.laboratorio);
    if (state.distribuidor) params.append('distribuidor', state.distribuidor);
    params.append('page', state.page);

    try {
        const res = await fetch(`${API_URL}/medicamentos?${params.toString()}`);
        const json = await res.json();

        state.totalPages = json.total_pages;
        resultsCount.textContent = `${json.total} medicamentos encontrados`;
        pageInfo.textContent = `Página ${json.page} de ${json.total_pages || 1}`;

        btnPrev.disabled = state.page <= 1;
        btnNext.disabled = state.page >= state.totalPages;

        renderCards(json.data);
    } catch (err) {
        resultsCount.textContent = "Error al cargar resultados";
        console.error(err);
    }
}

function renderCards(medicamentos) {
    if (medicamentos.length === 0) {
        cardsContainer.innerHTML = '<p>No se encontraron resultados.</p>';
        return;
    }

    medicamentos.forEach(med => {
        const card = document.createElement('div');
        card.className = 'card';

        const line = [med.laboratorio, med.distribuidor].filter(Boolean).join(' - ');

        card.innerHTML = `
            <div class="card-title">${med.nombre || 'Sin Nombre'}</div>
            <div class="card-subtitle">${line}</div>
            <div style="font-size: 0.875rem; margin-top: 0.5rem;">${med.principio_activo || '-'}</div>
            <button class="card-btn">Ver más</button>
        `;

        card.querySelector('button').addEventListener('click', () => openModal(med));
        cardsContainer.appendChild(card);
    });
}

function openModal(med) {
    selectedMedicamento = med;
    document.getElementById('modalNombre').textContent = med.nombre || '-';
    document.getElementById('modalMarca').textContent = [med.laboratorio, med.distribuidor].filter(Boolean).join(' - ');

    document.getElementById('modalPrincipioActivo').textContent = med.principio_activo || '-';
    document.getElementById('modalRs').textContent = med.rs || '-';
    document.getElementById('modalCategoria').textContent = med.categoria || '-';
    document.getElementById('modalDescripcion').textContent = med.descripcion || '-';
    document.getElementById('modalAccion').textContent = med.accion_terapeutica || '-';
    document.getElementById('modalForma').textContent = med.forma_farmaceutica || '-';

    const enlaceEl = document.getElementById('modalEnlace');
    if (med.enlace) {
        enlaceEl.href = med.enlace;
        enlaceEl.textContent = 'Ver prospecto / INFO';
    } else {
        enlaceEl.href = '#';
        enlaceEl.textContent = '-';
    }

    detailModal.classList.remove('hidden');
}

// Iniciar app
init();

let selectedMedicamento = null;

const createFieldConfig = [
    { name: 'codigo_barra', label: 'C\u00f3digo de barras' },
    { name: 'rs', label: 'Registro sanitario (RS)' },
    { name: 'nombre', label: 'Nombre', required: true },
    { name: 'forma_farmaceutica', label: 'Forma farmac\u00e9utica' },
    { name: 'laboratorio', label: 'Laboratorio' },
    { name: 'distribuidor', label: 'Distribuidor' },
    { name: 'principio_activo', label: 'Principio activo' },
    { name: 'enlace', label: 'Enlace' },
    { name: 'accion_terapeutica', label: 'Acci\u00f3n terap\u00e9utica' },
    { name: 'categoria', label: 'Categor\u00eda' },
    { name: 'formulacion', label: 'Formulaci\u00f3n', multiline: true },
    { name: 'presentaciones', label: 'Presentaciones', multiline: true },
    { name: 'descripcion', label: 'Descripci\u00f3n', multiline: true }
];

const createModal = document.getElementById('createModal');
const createForm = document.getElementById('createForm');
const createFields = document.getElementById('createFields');
const btnCreateFrom = document.getElementById('btnCreateFrom');
const btnCancelCreate = document.getElementById('btnCancelCreate');
const closeCreateModal = document.getElementById('closeCreateModal');
const btnSaveCreate = document.getElementById('btnSaveCreate');
const toast = document.getElementById('toast');
let toastTimer;

function openCreateModal(med) {
    if (!med) return;

    createFields.innerHTML = '';

    createFieldConfig.forEach(field => {
        const wrapper = document.createElement('label');
        wrapper.className = `form-field${field.multiline ? ' form-field-wide' : ''}`;

        const label = document.createElement('span');
        label.className = 'form-label';
        label.textContent = field.label;

        const control = document.createElement(field.multiline ? 'textarea' : 'input');
        control.name = field.name;
        control.value = med[field.name] ?? '';
        control.readOnly = true;
        control.required = Boolean(field.required);
        control.className = 'clone-input is-locked';
        control.setAttribute('aria-label', field.label);
        control.title = 'Haz clic para editar este campo';

        control.addEventListener('click', () => {
            if (!control.readOnly) return;
            control.readOnly = false;
            control.classList.remove('is-locked');
            control.classList.add('is-editing');
            control.focus();
            control.select();
        });

        wrapper.append(label, control);
        createFields.appendChild(wrapper);
    });

    createModal.classList.remove('hidden');
}

function showToast(message, type = 'success') {
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.className = `toast toast-${type}`;
    toastTimer = setTimeout(() => toast.classList.add('hidden'), 3500);
}

function formatApiError(errorBody) {
    if (typeof errorBody?.detail === 'string') return errorBody.detail;
    if (Array.isArray(errorBody?.detail)) {
        return errorBody.detail.map(error => error.msg).join('. ');
    }
    return 'No se pudo crear el medicamento';
}

btnCreateFrom.addEventListener('click', () => openCreateModal(selectedMedicamento));

function cancelCreate() {
    createModal.classList.add('hidden');
    showToast('Operaci\u00f3n cancelada', 'cancel');
}

btnCancelCreate.addEventListener('click', cancelCreate);
closeCreateModal.addEventListener('click', cancelCreate);

createForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {};
    const formData = new FormData(createForm);
    createFieldConfig.forEach(field => {
        const value = String(formData.get(field.name) ?? '').trim();
        payload[field.name] = value || null;
    });

    if (!payload.nombre) {
        showToast('El nombre del medicamento es obligatorio', 'error');
        return;
    }

    btnSaveCreate.disabled = true;
    btnSaveCreate.textContent = 'Guardando...';

    try {
        const response = await fetch(`${API_URL}/farmacia/medicamentos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(formatApiError(body));

        createModal.classList.add('hidden');
        detailModal.classList.add('hidden');
        showToast('Medicamento agregado a tu farmacia correctamente');
        await fetchMedicamentos();
    } catch (error) {
        showToast(error.message || 'No se pudo crear el medicamento', 'error');
    } finally {
        btnSaveCreate.disabled = false;
        btnSaveCreate.textContent = 'Guardar';
    }
});
