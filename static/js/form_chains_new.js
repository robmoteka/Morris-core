/**
 * form_chains_new.js - Skrypt obsługujący formularze łańcuchów przetwarzania
 * 
 * Ten plik zawiera funkcje do dynamicznego zarządzania formularzem edycji łańcuchów przetwarzania,
 * w tym dodawanie/usuwanie kroków, obsługę wyboru pluginów, konwersję między formularzem a JSON-em 
 * oraz obsługę edytorów JSON.
 */

// Licznik kroków - używany do generowania unikalnych identyfikatorów
let stepCounter = 0;

// Słownik edytorów JSON dla kroków
const stepEditors = {};

// Po załadowaniu dokumentu
document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja licznika kroków na podstawie istniejących elementów
    updateStepNumbers();
    
    // Inicjalizacja edytorów JSON dla istniejących kroków
    initializeJsonEditors();
    
    // Obsługa przycisku dodawania kroku
    const addStepButton = document.getElementById('addStepButton');
    if (addStepButton) {
        addStepButton.addEventListener('click', addStep);
    }
    
    // Obsługa przycisków usuwania kroków
    setupDeleteStepHandlers();
    
    // Obsługa wyboru pluginu
    setupPluginSelectHandlers();
    
    // Obsługa przycisków aktualizacji JSON
    const updateJsonButton = document.getElementById('updateJsonFromForm');
    if (updateJsonButton) {
        updateJsonButton.addEventListener('click', function() {
            const jsonEditor = window.editor; // Globalna instancja edytora JSON
            if (jsonEditor) {
                updateJsonFromForm(jsonEditor);
            }
        });
    }
    
    const updateFormButton = document.getElementById('updateFromJson');
    if (updateFormButton) {
        updateFormButton.addEventListener('click', function() {
            const jsonEditor = window.editor; // Globalna instancja edytora JSON
            if (jsonEditor) {
                updateFormFromJson(jsonEditor);
            }
        });
    }
    
    // Obsługa przełączania typu triggera
    setupTriggerTypeHandlers();
});

/**
 * Inicjalizuje edytory JSON dla istniejących kroków
 */
function initializeJsonEditors() {
    document.querySelectorAll('.json-editor').forEach(container => {
        const index = container.getAttribute('data-index');
        const paramsInput = container.closest('.card-body').querySelector('.step-params-input');
        
        if (paramsInput) {
            try {
                const paramsValue = JSON.parse(paramsInput.value || '{}');
                
                const editor = new JSONEditor(container, {
                    mode: 'tree',
                    onChangeText: function(jsonString) {
                        paramsInput.value = jsonString;
                    }
                });
                
                editor.set(paramsValue);
                stepEditors[index] = editor;
            } catch (e) {
                console.error('Błąd inicjalizacji edytora JSON:', e);
            }
        }
    });
}

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
        const pluginSelect = item.querySelector('.plugin-select');
        const paramsInput = item.querySelector('.step-params-input');
        const remotePluginField = item.querySelector('.remote-plugin-name');
        
        if (pluginSelect) pluginSelect.name = `steps[${index}][plugin]`;
        if (paramsInput) paramsInput.name = `steps[${index}][params]`;
        if (remotePluginField) remotePluginField.name = `remote_plugin_name_${index}`;
        
        // Zaktualizuj data-index dla edytora JSON
        const jsonEditor = item.querySelector('.json-editor');
        if (jsonEditor) {
            jsonEditor.setAttribute('data-index', index);
        }
    });
}

/**
 * Konfiguruje obsługę wyboru pluginu
 */
function setupPluginSelectHandlers() {
    document.querySelectorAll('.plugin-select').forEach(select => {
        select.addEventListener('change', function() {
            handlePluginSelect(this);
        });
        
        // Wywołaj raz, aby ustawić początkowy stan
        handlePluginSelect(select);
    });
}

/**
 * Obsługuje zmianę wyboru pluginu
 * @param {HTMLSelectElement} selectElement - Element select pluginu
 */
function handlePluginSelect(selectElement) {
    const stepItem = selectElement.closest('.step-item');
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const remotePluginField = stepItem.querySelector('.remote-plugin-field');
    const descriptionContainer = stepItem.querySelector('.plugin-description-container');
    
    // Obsługa pola dla zdalnych pluginów
    if (selectElement.value === 'remote:') {
        if (remotePluginField) {
            remotePluginField.classList.remove('d-none');
        }
    } else {
        if (remotePluginField) {
            remotePluginField.classList.add('d-none');
        }
    }
    
    // Aktualizacja opisu pluginu
    if (descriptionContainer) {
        if (selectedOption && selectedOption.dataset.description) {
            descriptionContainer.innerHTML = `
                <div class="alert alert-info plugin-description">
                    ${selectedOption.dataset.description}
                </div>
            `;
        } else {
            descriptionContainer.innerHTML = '';
        }
    }
}

/**
 * Konfiguruje obsługę przełączania typu triggera
 */
function setupTriggerTypeHandlers() {
    document.querySelectorAll('.trigger-type').forEach(radio => {
        radio.addEventListener('change', function() {
            // Ukryj wszystkie konfiguracje triggerów
            document.querySelectorAll('.trigger-config').forEach(config => {
                config.classList.add('d-none');
            });
            
            // Pokaż konfigurację dla wybranego typu
            const selectedType = this.value;
            const configElement = document.getElementById(`${selectedType}Config`);
            if (configElement) {
                configElement.classList.remove('d-none');
            }
        });
    });
}

/**
 * Dodaje nowy krok do formularza łańcucha
 */
function addStep() {
    // Zwiększ licznik kroków
    stepCounter++;
    
    // Pobierz listę pluginów z pierwszego selecta (jeśli istnieje)
    let pluginOptionsHtml = '<option value="">Wybierz plugin...</option>';
    const firstPluginSelect = document.querySelector('.plugin-select');
    
    if (firstPluginSelect) {
        Array.from(firstPluginSelect.options).forEach(option => {
            pluginOptionsHtml += `<option value="${option.value}" 
                data-description="${option.dataset.description || ''}"
                data-type="${option.dataset.type || ''}">${option.text}</option>`;
        });
    }
    
    // Utwórz nowy element kroku
    const stepHtml = `
    <div class="step-item card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
            <span>Krok #<span class="step-number">${stepCounter}</span></span>
            <button type="button" class="btn btn-sm btn-danger delete-step">Usuń</button>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label class="form-label">Plugin</label>
                <select class="form-select plugin-select" name="steps[${stepCounter-1}][plugin]" required>
                    ${pluginOptionsHtml}
                </select>
            </div>
            
            <!-- Pole dla zdalnych pluginów -->
            <div class="mb-3 remote-plugin-field d-none">
                <label class="form-label">Nazwa zdalnego pluginu</label>
                <input type="text" class="form-control remote-plugin-name" 
                       name="remote_plugin_name_${stepCounter-1}"
                       placeholder="remote:device:plugin">
                <div class="form-text">Format: remote:device:plugin</div>
            </div>
            
            <!-- Opis pluginu -->
            <div class="mb-3 plugin-description-container">
            </div>
            
            <div class="mb-3">
                <label class="form-label">Parametry pluginu (JSON)</label>
                <div class="json-editor" data-index="${stepCounter-1}"></div>
                <input type="hidden" class="step-params-input" name="steps[${stepCounter-1}][params]" value="{}">
                <div class="form-text plugin-params-help">
                    Parametry konfiguracyjne dla pluginu.
                </div>
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
    const paramsInput = newStep.querySelector('.step-params-input');
    
    const stepEditor = new JSONEditor(jsonEditorContainer, {
        mode: 'tree',
        onChangeText: function(jsonString) {
            paramsInput.value = jsonString;
        }
    });
    
    stepEditor.set({});
    stepEditors[stepCounter-1] = stepEditor;
    
    // Dodaj obsługę wyboru pluginu
    const pluginSelect = newStep.querySelector('.plugin-select');
    if (pluginSelect) {
        pluginSelect.addEventListener('change', function() {
            handlePluginSelect(this);
        });
    }
    
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
            const endpoint = document.getElementById('webhookEndpoint').value;
            chainObject.trigger = `webhook:${endpoint}`;
        } else if (triggerType.value === 'mqtt') {
            const topic = document.getElementById('mqttTopic').value;
            chainObject.trigger = `mqtt:${topic}`;
        }
    }
    
    // Dodaj kroki z formularza
    document.querySelectorAll('.step-item').forEach((stepItem) => {
        const pluginSelect = stepItem.querySelector('.plugin-select');
        const paramsInput = stepItem.querySelector('.step-params-input');
        const remotePluginField = stepItem.querySelector('.remote-plugin-name');
        
        let pluginName = '';
        if (pluginSelect) {
            pluginName = pluginSelect.value;
            
            // Jeśli to zdalny plugin niestandardowy, użyj pełnej nazwy
            if (pluginName === 'remote:' && remotePluginField && remotePluginField.value) {
                pluginName = remotePluginField.value;
            }
        }
        
        // Przygotuj krok
        const step = {
            plugin: pluginName
        };
        
        // Dodaj parametry, jeśli istnieją
        if (paramsInput) {
            try {
                const params = JSON.parse(paramsInput.value || '{}');
                if (Object.keys(params).length > 0) {
                    step.params = params;
                }
            } catch (e) {
                console.error('Błąd parsowania parametrów JSON:', e);
            }
        }
        
        chainObject.steps.push(step);
    });
    
    // Zaktualizuj edytor JSON
    editor.set(chainObject);
    
    // Zaktualizuj ukryte pole formularza
    document.getElementById('rawJsonInput').value = JSON.stringify(chainObject);
}

/**
 * Aktualizuje formularz na podstawie danych z edytora JSON
 * @param {JSONEditor} editor - Instancja edytora JSON
 */
function updateFormFromJson(editor) {
    try {
        // Pobierz dane z edytora JSON
        const chainData = editor.get();
        
        // Aktualizuj podstawowe pola
        if (chainData.id) {
            document.getElementById('chainId').value = chainData.id;
        }
        
        if (chainData.description) {
            document.getElementById('chainDescription').value = chainData.description;
        }
        
        // Aktualizuj trigger
        if (chainData.trigger) {
            let triggerType = null;
            let triggerValue = '';
            
            if (chainData.trigger.startsWith('webhook:')) {
                triggerType = 'webhook';
                triggerValue = chainData.trigger.split(':', 1)[1];
                
                // Zaznacz radio button dla webhook
                const webhookRadio = document.getElementById('triggerWebhook');
                if (webhookRadio) {
                    webhookRadio.checked = true;
                }
                
                // Ustaw wartość endpointu
                const webhookEndpoint = document.getElementById('webhookEndpoint');
                if (webhookEndpoint) {
                    webhookEndpoint.value = triggerValue;
                }
                
                // Pokaż konfigurację webhook
                document.querySelectorAll('.trigger-config').forEach(config => {
                    config.classList.add('d-none');
                });
                const webhookConfig = document.getElementById('webhookConfig');
                if (webhookConfig) {
                    webhookConfig.classList.remove('d-none');
                }
                
            } else if (chainData.trigger.startsWith('mqtt:')) {
                triggerType = 'mqtt';
                triggerValue = chainData.trigger.split(':', 1)[1];
                
                // Zaznacz radio button dla mqtt
                const mqttRadio = document.getElementById('triggerMqtt');
                if (mqttRadio) {
                    mqttRadio.checked = true;
                }
                
                // Ustaw wartość tematu
                const mqttTopic = document.getElementById('mqttTopic');
                if (mqttTopic) {
                    mqttTopic.value = triggerValue;
                }
                
                // Pokaż konfigurację mqtt
                document.querySelectorAll('.trigger-config').forEach(config => {
                    config.classList.add('d-none');
                });
                const mqttConfig = document.getElementById('mqttConfig');
                if (mqttConfig) {
                    mqttConfig.classList.remove('d-none');
                }
            }
        }
        
        // Aktualizuj kroki
        if (chainData.steps && Array.isArray(chainData.steps)) {
            // Usuń istniejące kroki
            const stepsContainer = document.getElementById('stepsContainer');
            stepsContainer.innerHTML = '';
            
            // Dodaj nowe kroki na podstawie danych z JSON
            chainData.steps.forEach((step, index) => {
                addStepFromJson(step, index);
            });
            
            // Zaktualizuj numerację
            updateStepNumbers();
        }
        
        // Zaktualizuj ukryte pole formularza
        document.getElementById('rawJsonInput').value = JSON.stringify(chainData);
        
    } catch (e) {
        console.error('Błąd aktualizacji formularza z JSON:', e);
        alert('Wystąpił błąd podczas aktualizacji formularza z JSON. Sprawdź konsolę przeglądarki.');
    }
}

/**
 * Dodaje krok na podstawie danych z JSON
 * @param {Object} stepData - Dane kroku
 * @param {number} index - Indeks kroku
 */
function addStepFromJson(stepData, index) {
    // Zwiększ licznik kroków
    stepCounter++;
    
    // Pobierz listę pluginów z pierwszego selecta (jeśli istnieje)
    let pluginOptionsHtml = '<option value="">Wybierz plugin...</option>';
    const firstPluginSelect = document.querySelector('.plugin-select');
    
    if (firstPluginSelect) {
        Array.from(firstPluginSelect.options).forEach(option => {
            const selected = option.value === stepData.plugin ? 'selected' : '';
            pluginOptionsHtml += `<option value="${option.value}" 
                data-description="${option.dataset.description || ''}"
                data-type="${option.dataset.type || ''}"
                ${selected}>${option.text}</option>`;
        });
    }
    
    // Sprawdź, czy to zdalny plugin niestandardowy
    const isRemoteCustom = stepData.plugin && stepData.plugin.startsWith('remote:') && 
                          !document.querySelector(`.plugin-select option[value="${stepData.plugin}"]`);
    
    // Utwórz nowy element kroku
    const stepHtml = `
    <div class="step-item card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
            <span>Krok #<span class="step-number">${index + 1}</span></span>
            <button type="button" class="btn btn-sm btn-danger delete-step">Usuń</button>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label class="form-label">Plugin</label>
                <select class="form-select plugin-select" name="steps[${index}][plugin]" required>
                    ${pluginOptionsHtml}
                </select>
            </div>
            
            <!-- Pole dla zdalnych pluginów -->
            <div class="mb-3 remote-plugin-field ${isRemoteCustom ? '' : 'd-none'}">
                <label class="form-label">Nazwa zdalnego pluginu</label>
                <input type="text" class="form-control remote-plugin-name" 
                       name="remote_plugin_name_${index}"
                       value="${isRemoteCustom ? stepData.plugin : ''}"
                       placeholder="remote:device:plugin">
                <div class="form-text">Format: remote:device:plugin</div>
            </div>
            
            <!-- Opis pluginu -->
            <div class="mb-3 plugin-description-container">
                ${stepData.plugin ? `<div class="alert alert-info plugin-description">Plugin: ${stepData.plugin}</div>` : ''}
            </div>
            
            <div class="mb-3">
                <label class="form-label">Parametry pluginu (JSON)</label>
                <div class="json-editor" data-index="${index}"></div>
                <input type="hidden" class="step-params-input" name="steps[${index}][params]" 
                       value='${JSON.stringify(stepData.params || {})}'>
                <div class="form-text plugin-params-help">
                    Parametry konfiguracyjne dla pluginu.
                </div>
            </div>
        </div>
    </div>
    `;
    
    // Pobierz kontener kroków
    const stepsContainer = document.getElementById('stepsContainer');
    
    // Dodaj nowy krok do kontenera
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = stepHtml;
    const newStep = tempDiv.firstElementChild;
    stepsContainer.appendChild(newStep);
    
    // Inicjalizuj edytor JSON dla nowego kroku
    const jsonEditorContainer = newStep.querySelector('.json-editor');
    const paramsInput = newStep.querySelector('.step-params-input');
    
    const stepEditor = new JSONEditor(jsonEditorContainer, {
        mode: 'tree',
        onChangeText: function(jsonString) {
            paramsInput.value = jsonString;
        }
    });
    
    try {
        stepEditor.set(stepData.params || {});
    } catch (e) {
        console.error('Błąd ustawienia parametrów JSON:', e);
        stepEditor.set({});
    }
    
    stepEditors[index] = stepEditor;
    
    // Dodaj obsługę wyboru pluginu
    const pluginSelect = newStep.querySelector('.plugin-select');
    if (pluginSelect) {
        pluginSelect.addEventListener('change', function() {
            handlePluginSelect(this);
        });
        
        // Jeśli to zdalny plugin niestandardowy, ustaw opcję "Inny zdalny plugin"
        if (isRemoteCustom) {
            // Znajdź opcję "Inny zdalny plugin"
            for (let i = 0; i < pluginSelect.options.length; i++) {
                if (pluginSelect.options[i].value === 'remote:') {
                    pluginSelect.selectedIndex = i;
                    break;
                }
            }
        }
    }
    
    // Dodaj obsługę usuwania
    const deleteButton = newStep.querySelector('.delete-step');
    deleteButton.addEventListener('click', function() {
        deleteStep(newStep);
    });
}
