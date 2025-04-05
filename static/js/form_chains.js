/**
 * form_chains.js - Skrypt obsługujący formularze łańcuchów przetwarzania
 * 
 * Ten plik zawiera funkcje do dynamicznego zarządzania formularzem edycji łańcuchów przetwarzania,
 * w tym dodawanie/usuwanie kroków, konwersję między formularzem a JSON-em oraz obsługę edytorów JSON.
 */

// Licznik kroków - używany do generowania unikalnych identyfikatorów
let stepCounter = 0;

// Po załadowaniu dokumentu
document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja licznika kroków na podstawie istniejących elementów
    updateStepNumbers();
    
    // Obsługa przycisku dodawania kroku
    const addStepButton = document.getElementById('addStepButton');
    if (addStepButton) {
        addStepButton.addEventListener('click', addStep);
    }
    
    // Obsługa przycisków usuwania kroków
    setupDeleteStepHandlers();
});

/**
 * Aktualizuje numerację kroków na podstawie ich pozycji w dokumencie
 */
function updateStepNumbers() {
    // Pobierz wszystkie elementy kroków
    const stepItems = document.querySelectorAll('.step-item');
    
    // Zaktualizuj licznik kroków
    stepCounter = stepItems.length;
    
    // Zaktualizuj numerację i nazwy pól
    stepItems.forEach((item, index) => {
        // Zaktualizuj numer wyświetlany użytkownikowi
        const stepNumberElement = item.querySelector('.step-number');
        if (stepNumberElement) {
            stepNumberElement.textContent = index + 1;
        }
        
        // Zaktualizuj nazwy pól formularza
        const nameInput = item.querySelector('.step-name');
        const typeSelect = item.querySelector('.step-type');
        const configInput = item.querySelector('.step-config-input');
        
        if (nameInput) nameInput.name = `steps[${index}][name]`;
        if (typeSelect) typeSelect.name = `steps[${index}][type]`;
        if (configInput) configInput.name = `steps[${index}][config]`;
    });
}

/**
 * Dodaje nowy krok do formularza łańcucha
 */
function addStep() {
    // Zwiększ licznik kroków
    stepCounter++;
    
    // Utwórz nowy element kroku
    const stepHtml = `
    <div class="step-item card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
            <span>Krok #<span class="step-number">${stepCounter}</span></span>
            <button type="button" class="btn btn-sm btn-danger delete-step">Usuń</button>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label class="form-label">Nazwa kroku</label>
                <input type="text" class="form-control step-name" name="steps[${stepCounter-1}][name]" 
                       value="step_${stepCounter}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Typ kroku</label>
                <select class="form-select step-type" name="steps[${stepCounter-1}][type]" required>
                    <option value="">Wybierz typ...</option>
                    <option value="processor">Processor</option>
                    <option value="transformer">Transformer</option>
                    <option value="validator">Validator</option>
                    <option value="filter">Filter</option>
                    <option value="plugin">Plugin</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Konfiguracja (JSON)</label>
                <div class="json-editor" data-index="${stepCounter-1}"></div>
                <input type="hidden" class="step-config-input" name="steps[${stepCounter-1}][config]" value="{}">
            </div>
        </div>
    </div>
    `;
    
    // Pobierz kontener kroków
    const stepsContainer = document.getElementById('stepsContainer');
    
    // Usuń informację o braku kroków, jeśli istnieje
    const infoAlert = stepsContainer.querySelector('.alert-info');
    if (infoAlert) {
        infoAlert.remove();
    }
    
    // Dodaj nowy krok do kontenera
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = stepHtml;
    const newStep = tempDiv.firstElementChild;
    stepsContainer.appendChild(newStep);
    
    // Inicjalizuj edytor JSON dla nowego kroku
    const jsonEditorContainer = newStep.querySelector('.json-editor');
    const configInput = newStep.querySelector('.step-config-input');
    
    const stepEditor = new JSONEditor(jsonEditorContainer, {
        mode: 'tree',
        onChangeText: function(jsonString) {
            configInput.value = jsonString;
        }
    });
    
    stepEditor.set({});
    
    // Dodaj obsługę usuwania
    const deleteButton = newStep.querySelector('.delete-step');
    deleteButton.addEventListener('click', function() {
        deleteStep(newStep);
    });
    
    // Zaktualizuj numerację kroków
    updateStepNumbers();
}

/**
 * Usuwa wybrany krok z formularza
 * @param {HTMLElement} stepElement - Element HTML kroku do usunięcia
 */
function deleteStep(stepElement) {
    // Usuń element z DOM
    stepElement.remove();
    
    // Zaktualizuj numerację
    updateStepNumbers();
    
    // Jeśli nie ma już żadnych kroków, pokaż informację
    const stepsContainer = document.getElementById('stepsContainer');
    if (stepsContainer.children.length === 0) {
        stepsContainer.innerHTML = `
        <div class="alert alert-info">
            Brak zdefiniowanych kroków. Kliknij "Dodaj krok", aby rozpocząć budowanie łańcucha.
        </div>
        `;
    }
}

/**
 * Ustawia obsługę przycisków usuwania kroków
 */
function setupDeleteStepHandlers() {
    document.querySelectorAll('.delete-step').forEach(button => {
        button.addEventListener('click', function() {
            const stepElement = this.closest('.step-item');
            deleteStep(stepElement);
        });
    });
}

/**
 * Aktualizuje edytor JSON na podstawie danych z formularza
 * @param {JSONEditor} editor - Instancja edytora JSON
 */
function updateJsonFromForm(editor) {
    // Przygotuj obiekt dla łańcucha
    const chainObject = {
        id: document.getElementById('chainId').value,
        description: document.getElementById('chainDescription').value,
        steps: []
    };
    
    // Dodaj trigger na podstawie wybranego typu
    const triggerType = document.querySelector('input[name="trigger_type"]:checked');
    if (triggerType) {
        if (triggerType.value === 'webhook') {
            chainObject.webhook = {
                endpoint: document.getElementById('webhookEndpoint').value,
                methods: Array.from(document.getElementById('webhookMethods').selectedOptions).map(opt => opt.value)
            };
        } else if (triggerType.value === 'mqtt') {
            chainObject.mqtt = {
                topic: document.getElementById('mqttTopic').value,
                qos: parseInt(document.getElementById('mqttQos').value, 10)
            };
        }
    }
    
    // Dodaj kroki z formularza
    document.querySelectorAll('.step-item').forEach((stepItem, index) => {
        const nameInput = stepItem.querySelector('.step-name');
        const typeSelect = stepItem.querySelector('.step-type');
        const configInput = stepItem.querySelector('.step-config-input');
        
        if (nameInput && typeSelect && configInput) {
            const step = {
                name: nameInput.value,
                type: typeSelect.value
            };
            
            try {
                step.config = JSON.parse(configInput.value || '{}');
            } catch (e) {
                step.config = {};
                console.error('Błąd parsowania JSON dla kroku:', e);
            }
            
            chainObject.steps.push(step);
        }
    });
    
    // Zaktualizuj edytor JSON
    editor.set(chainObject);
    document.getElementById('rawJsonInput').value = JSON.stringify(chainObject);
}

/**
 * Aktualizuje formularz na podstawie danych z edytora JSON
 * @param {JSONEditor} editor - Instancja edytora JSON
 */
function updateFormFromJson(editor) {
    try {
        // Pobierz dane z edytora JSON
        const chainObject = editor.get();
        
        // Aktualizuj podstawowe pola
        if (chainObject.id) {
            document.getElementById('chainId').value = chainObject.id;
        }
        
        if (chainObject.description) {
            document.getElementById('chainDescription').value = chainObject.description;
        }
        
        // Aktualizuj trigger
        if (chainObject.webhook) {
            document.getElementById('triggerWebhook').checked = true;
            document.getElementById('webhookConfig').classList.remove('d-none');
            document.getElementById('mqttConfig').classList.add('d-none');
            
            if (chainObject.webhook.endpoint) {
                document.getElementById('webhookEndpoint').value = chainObject.webhook.endpoint;
            }
            
            if (chainObject.webhook.methods && Array.isArray(chainObject.webhook.methods)) {
                const methodsSelect = document.getElementById('webhookMethods');
                Array.from(methodsSelect.options).forEach(option => {
                    option.selected = chainObject.webhook.methods.includes(option.value);
                });
            }
        } else if (chainObject.mqtt) {
            document.getElementById('triggerMqtt').checked = true;
            document.getElementById('mqttConfig').classList.remove('d-none');
            document.getElementById('webhookConfig').classList.add('d-none');
            
            if (chainObject.mqtt.topic) {
                document.getElementById('mqttTopic').value = chainObject.mqtt.topic;
            }
            
            if (chainObject.mqtt.qos !== undefined) {
                document.getElementById('mqttQos').value = chainObject.mqtt.qos;
            }
        }
        
        // Aktualizuj kroki łańcucha
        const stepsContainer = document.getElementById('stepsContainer');
        stepsContainer.innerHTML = ''; // Usuń istniejące kroki
        
        if (chainObject.steps && Array.isArray(chainObject.steps) && chainObject.steps.length > 0) {
            // Resetuj licznik kroków
            stepCounter = 0;
            
            // Dodaj nowe kroki
            chainObject.steps.forEach((step, index) => {
                stepCounter++;
                
                const stepHtml = `
                <div class="step-item card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>Krok #<span class="step-number">${index + 1}</span></span>
                        <button type="button" class="btn btn-sm btn-danger delete-step">Usuń</button>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Nazwa kroku</label>
                            <input type="text" class="form-control step-name" name="steps[${index}][name]" 
                                value="${step.name || ''}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Typ kroku</label>
                            <select class="form-select step-type" name="steps[${index}][type]" required>
                                <option value="">Wybierz typ...</option>
                                <option value="processor" ${step.type === 'processor' ? 'selected' : ''}>Processor</option>
                                <option value="transformer" ${step.type === 'transformer' ? 'selected' : ''}>Transformer</option>
                                <option value="validator" ${step.type === 'validator' ? 'selected' : ''}>Validator</option>
                                <option value="filter" ${step.type === 'filter' ? 'selected' : ''}>Filter</option>
                                <option value="plugin" ${step.type === 'plugin' ? 'selected' : ''}>Plugin</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Konfiguracja (JSON)</label>
                            <div class="json-editor" data-index="${index}"></div>
                            <input type="hidden" class="step-config-input" name="steps[${index}][config]" value='${JSON.stringify(step.config || {})}'>
                        </div>
                    </div>
                </div>
                `;
                
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = stepHtml;
                const newStep = tempDiv.firstElementChild;
                stepsContainer.appendChild(newStep);
            });
            
            // Inicjalizuj edytory JSON dla kroków
            document.querySelectorAll('.json-editor').forEach(function(container) {
                const index = container.dataset.index;
                const configInput = container.closest('.step-item').querySelector('.step-config-input');
                
                const stepEditor = new JSONEditor(container, {
                    mode: 'tree',
                    onChangeText: function(jsonString) {
                        configInput.value = jsonString;
                    }
                });
                
                try {
                    const configValue = JSON.parse(configInput.value || '{}');
                    stepEditor.set(configValue);
                } catch (e) {
                    stepEditor.set({});
                    console.error('Błąd parsowania JSON dla kroku:', e);
                }
            });
            
            // Dodaj obsługę usuwania
            setupDeleteStepHandlers();
        } else {
            // Brak kroków - pokaż informację
            stepsContainer.innerHTML = `
            <div class="alert alert-info">
                Brak zdefiniowanych kroków. Kliknij "Dodaj krok", aby rozpocząć budowanie łańcucha.
            </div>
            `;
        }
        
    } catch (e) {
        console.error('Błąd podczas aktualizacji formularza z JSON:', e);
        alert('Wystąpił błąd podczas aktualizacji formularza. Sprawdź konsolę przeglądarki po więcej szczegółów.');
    }
}
