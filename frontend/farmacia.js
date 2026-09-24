const PHARMACY_API_URL = '/farmacia/medicamentos';

const pharmacyState = {
    q: '',
    page: 1,
    totalPages: 1
};

const searchInput = document.getElementById('pharmacySearchInput');
const labInput = document.getElementById('pharmacyLabInput');
const distInput = document.getElementById('pharmacyDistInput');
const labDropdown = document.getElementById('pharmacyLabDropdown');
const distDropdown = document.getElementById('pharmacyDistDropdown');
const btnSearch = document.getElementById('pharmacyBtnSearch');
const btnClear = document.getElementById('pharmacyBtnClear');
const cardsContainer = document.getElementById('pharmacyCardsContainer');
const resultsCount = document.getElementById('pharmacyResultsCount');
const btnPrev = document.getElementById('pharmacyBtnPrev');
const btnNext = document.getElementById('pharmacyBtnNext');
const pageInfo = document.getElementById('pharmacyPageInfo');
const detailModal = document.getElementById('pharmacyDetailModal');
const closeModal = document.getElementById('pharmacyCloseModal');
const modalDetails = document.getElementById('pharmacyModalDetails');
const editForm = document.getElementById('pharmacyEditForm');
const editFields = document.getElementById('pharmacyEditFields');
const viewActions = document.getElementById('pharmacyViewActions');
const btnEdit = document.getElementById('pharmacyBtnEdit');
const btnCancelEdit = document.getElementById('pharmacyBtnCancelEdit');
const btnSaveEdit = document.getElementById('pharmacyBtnSaveEdit');
const pharmacyToast = document.getElementById('pharmacyToast');
let selectedPharmacyMedicine = null;
let pharmacyToastTimer;

const editFieldConfig = [
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

async function fetchPharmacyFilters() {
    try {
        const [labsResponse, distributorsResponse] = await Promise.all([
            fetch('/farmacia/laboratorios'),
            fetch('/farmacia/distribuidores')
        ]);
        if (!labsResponse.ok || !distributorsResponse.ok) throw new Error('No se pudieron cargar los filtros');
        pharmacyState.labs = await labsResponse.json();
        pharmacyState.distribuidores = await distributorsResponse.json();
    } catch (error) {
        console.error(error);
    }
}

function setupPharmacyDropdown(input, dropdown, values, onSelect) {
    const render = () => {
        dropdown.innerHTML = '';
        const filter = input.value.toLowerCase();
        const matches = values.filter(value => value.toLowerCase().includes(filter));

        if (!matches.length) {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.textContent = 'Sin resultados';
            dropdown.appendChild(item);
            return;
        }

        matches.forEach(value => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.textContent = value;
            item.addEventListener('click', () => {
                input.value = value;
                onSelect(value);
                dropdown.classList.add('hidden');
            });
            dropdown.appendChild(item);
        });
    };

    input.addEventListener('focus', () => {
        render();
        dropdown.classList.remove('hidden');
    });
    input.addEventListener('input', () => {
        onSelect('');
        render();
        dropdown.classList.remove('hidden');
    });
    document.addEventListener('click', event => {
        if (!input.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.add('hidden');
        }
    });
}
async function fetchPharmacyMedicines() {
    pharmacyState.q = searchInput.value.trim();
    resultsCount.textContent = 'Cargando resultados...';
    cardsContainer.innerHTML = '';

    const params = new URLSearchParams({ page: pharmacyState.page });
    if (pharmacyState.q) params.set('q', pharmacyState.q);
    if (pharmacyState.laboratorio) params.set('laboratorio', pharmacyState.laboratorio);
    if (pharmacyState.distribuidor) params.set('distribuidor', pharmacyState.distribuidor);

    try {
        const response = await fetch(`${PHARMACY_API_URL}?${params.toString()}`);
        if (!response.ok) throw new Error(`Error ${response.status}`);

        const result = await response.json();
        pharmacyState.totalPages = result.total_pages || 0;
        resultsCount.textContent = `${result.total} medicamentos en farmacia`;
        pageInfo.textContent = `P\u00e1gina ${result.page} de ${result.total_pages || 1}`;
        btnPrev.disabled = pharmacyState.page <= 1;
        btnNext.disabled = pharmacyState.totalPages === 0 || pharmacyState.page >= pharmacyState.totalPages;
        renderPharmacyCards(result.data);
    } catch (error) {
        resultsCount.textContent = 'No se pudieron cargar los medicamentos de farmacia';
        console.error(error);
    }
}

function renderPharmacyCards(medicines) {
    if (!medicines.length) {
        const empty = document.createElement('p');
        empty.className = 'pharmacy-empty';
        empty.textContent = 'No se encontraron medicamentos en farmacia.';
        cardsContainer.appendChild(empty);
        return;
    }

    medicines.forEach(medicine => {
        const card = document.createElement('article');
        card.className = 'card pharmacy-card';

        const title = document.createElement('div');
        title.className = 'card-title';
        title.textContent = medicine.nombre || 'Sin nombre';

        const brand = document.createElement('div');
        brand.className = 'card-subtitle';
        brand.textContent = [medicine.laboratorio, medicine.distribuidor].filter(Boolean).join(' - ') || '-';

        const activeIngredient = document.createElement('div');
        activeIngredient.className = 'pharmacy-active-ingredient';
        activeIngredient.textContent = medicine.principio_activo || '-';

        const barcode = document.createElement('div');
        barcode.className = `barcode-badge${medicine.codigo_barra ? '' : ' barcode-missing'}`;
        barcode.textContent = medicine.codigo_barra
            ? `C\u00f3digo: ${medicine.codigo_barra}`
            : 'Sin c\u00f3digo de barras';

        const button = document.createElement('button');
        button.className = 'card-btn pharmacy-card-btn';
        button.textContent = 'Ver m\u00e1s';
        button.addEventListener('click', () => openPharmacyModal(medicine));

        card.append(title, brand, activeIngredient, barcode, button);
        cardsContainer.appendChild(card);
    });
}

function appendDetail(label, value, isLink = false) {
    const row = document.createElement('div');
    row.className = 'field-row';

    const info = document.createElement('div');
    info.className = 'field-info';

    const labelElement = document.createElement('span');
    labelElement.className = 'label';
    labelElement.textContent = label;

    const valueElement = document.createElement(isLink && value ? 'a' : 'span');
    valueElement.className = isLink ? 'value link' : 'value';
    valueElement.textContent = value || '-';
    if (isLink && value) {
        valueElement.href = value;
        valueElement.target = '_blank';
        valueElement.rel = 'noopener noreferrer';
    }

    info.append(labelElement, valueElement);
    row.appendChild(info);
    modalDetails.appendChild(row);
}

function openPharmacyModal(medicine) {
    selectedPharmacyMedicine = medicine;
    document.getElementById('pharmacyModalName').textContent = medicine.nombre || 'Sin nombre';
    document.getElementById('pharmacyModalBrand').textContent =
        [medicine.laboratorio, medicine.distribuidor].filter(Boolean).join(' - ') || '-';

    modalDetails.innerHTML = '';
    appendDetail('C\u00f3digo de barras', medicine.codigo_barra);
    appendDetail('Registro sanitario (RS)', medicine.rs);
    appendDetail('Principio activo', medicine.principio_activo);
    appendDetail('Categor\u00eda', medicine.categoria);
    appendDetail('Forma farmac\u00e9utica', medicine.forma_farmaceutica);
    appendDetail('Acci\u00f3n terap\u00e9utica', medicine.accion_terapeutica);
    appendDetail('Formulaci\u00f3n', medicine.formulacion);
    appendDetail('Presentaciones', medicine.presentaciones);
    appendDetail('Descripci\u00f3n', medicine.descripcion);
    appendDetail('Enlace de referencia', medicine.enlace, true);
    showPharmacyDetails();
    detailModal.classList.remove('hidden');
}

function showPharmacyDetails() {
    modalDetails.classList.remove('hidden');
    viewActions.classList.remove('hidden');
    editForm.classList.add('hidden');
}

function showPharmacyToast(message, type = 'success') {
    clearTimeout(pharmacyToastTimer);
    pharmacyToast.textContent = message;
    pharmacyToast.className = `toast toast-${type}`;
    pharmacyToastTimer = setTimeout(() => pharmacyToast.classList.add('hidden'), 3500);
}

function formatPharmacyApiError(body) {
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail)) return body.detail.map(error => error.msg).join('. ');
    return 'No se pudieron guardar los cambios';
}

function openPharmacyEdit() {
    if (!selectedPharmacyMedicine) return;
    editFields.innerHTML = '';

    editFieldConfig.forEach(field => {
        const wrapper = document.createElement('label');
        wrapper.className = `form-field${field.multiline ? ' form-field-wide' : ''}`;

        const label = document.createElement('span');
        label.className = 'form-label';
        label.textContent = field.label;

        const control = document.createElement(field.multiline ? 'textarea' : 'input');
        control.className = 'clone-input';
        control.name = field.name;
        control.value = selectedPharmacyMedicine[field.name] ?? '';
        control.required = Boolean(field.required);
        control.setAttribute('aria-label', field.label);

        wrapper.append(label, control);
        editFields.appendChild(wrapper);
    });

    modalDetails.classList.add('hidden');
    viewActions.classList.add('hidden');
    editForm.classList.remove('hidden');
}

function closePharmacyModal() {
    detailModal.classList.add('hidden');
    showPharmacyDetails();
}

btnEdit.addEventListener('click', openPharmacyEdit);
btnCancelEdit.addEventListener('click', showPharmacyDetails);

editForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (!selectedPharmacyMedicine) return;

    const payload = {};
    const formData = new FormData(editForm);
    editFieldConfig.forEach(field => {
        const value = String(formData.get(field.name) ?? '').trim();
        payload[field.name] = value || null;
    });

    if (!payload.nombre) {
        showPharmacyToast('El nombre del medicamento es obligatorio', 'error');
        return;
    }

    btnSaveEdit.disabled = true;
    btnSaveEdit.textContent = 'Guardando...';

    try {
        const response = await fetch(`${PHARMACY_API_URL}/${selectedPharmacyMedicine.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(formatPharmacyApiError(body));

        selectedPharmacyMedicine = body;
        closePharmacyModal();
        showPharmacyToast('Medicamento de farmacia actualizado correctamente');
        await Promise.all([fetchPharmacyMedicines(), fetchPharmacyFilters()]);
    } catch (error) {
        showPharmacyToast(error.message || 'No se pudieron guardar los cambios', 'error');
    } finally {
        btnSaveEdit.disabled = false;
        btnSaveEdit.textContent = 'Guardar cambios';
    }
});

btnSearch.addEventListener('click', () => {
    pharmacyState.page = 1;
    fetchPharmacyMedicines();
});

btnClear.addEventListener('click', () => {
    searchInput.value = '';
    pharmacyState.q = '';
    pharmacyState.page = 1;
    fetchPharmacyMedicines();
});

searchInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
        pharmacyState.page = 1;
        fetchPharmacyMedicines();
    }
});

btnPrev.addEventListener('click', () => {
    if (pharmacyState.page > 1) {
        pharmacyState.page -= 1;
        fetchPharmacyMedicines();
    }
});

btnNext.addEventListener('click', () => {
    if (pharmacyState.page < pharmacyState.totalPages) {
        pharmacyState.page += 1;
        fetchPharmacyMedicines();
    }
});

closeModal.addEventListener('click', closePharmacyModal);
detailModal.addEventListener('click', event => {
    if (event.target === detailModal) closePharmacyModal();
});
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closePharmacyModal();
});

async function initPharmacy() {
    await fetchPharmacyFilters();
    setupPharmacyDropdown(
        labInput,
        labDropdown,
        pharmacyState.labs,
        value => { pharmacyState.laboratorio = value; }
    );
    setupPharmacyDropdown(
        distInput,
        distDropdown,
        pharmacyState.distribuidores,
        value => { pharmacyState.distribuidor = value; }
    );
    fetchPharmacyMedicines();
}

initPharmacy();
