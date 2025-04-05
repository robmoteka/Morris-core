/**
 * form_chains_tabs.js
 * Skrypt do obsługi formularza łańcuchów z zakładkami wertykalnymi
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja Bootstrap Tabs
    initBootstrapTabs();
    
    // Inicjalizacja edytorów JSON dla parametrów pluginów
    initJsonEditors();
    
    // Obsługa przełączania typu triggera
    setupTriggerTypeToggle();
    
    // Obsługa dodawania nowego kroku
    setupAddStepTab();
    
    // Obsługa usuwania kroków
    setupDeleteStepButtons();
    
    // Obsługa wyboru pluginu
    setupPluginSelects();
    
    // Obsługa aktualizacji JSON z formularza i odwrotnie
    setupJsonEditorSync();
});

/**
 * Inicjalizuje obsługę Bootstrap Tabs
 */
function initBootstrapTabs() {
    const tabEls = document.querySelectorAll('#stepsTab button[data-bs-toggle="tab"]');
    
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Usuń klasę active ze wszystkich zakładek i zawartości
            document.querySelectorAll('#stepsTab .nav-link').forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            
            document.querySelectorAll('.step-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Dodaj klasę active do klikniętej zakładki
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            
            // Pokaż odpowiednią zawartość
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            if (target) {
                target.classList.add('active');
            }
        });
    });
}

/**
 * Inicjalizuje edytory JSON dla parametrów pluginów
 */
function initJsonEditors() {
    const jsonEditorContainers = document.querySelectorAll('.json-editor');
    
    jsonEditorContainers.forEach(container => {
        const index = container.dataset.index;
        const inputField = document.querySelector(`.step-params-input[name="steps[${index}][params]"]`);
        
        const editor = new JSONEditor(container, {
            mode: 'tree',
            modes: ['tree', 'code', 'form', 'text'],
            onChangeText: function(jsonString) {
                inputField.value = jsonString;
            }
        });
        
        try {
            // Bezpieczne parsowanie wartości JSON
            let jsonValue = '{}';
            if (inputField && inputField.value) {
                jsonValue = inputField.value.trim();
                // Sprawdź, czy wartość jest otoczona cudzysłowiami (co może powodować błędy)
                if (jsonValue.startsWith('"') && jsonValue.endsWith('"')) {
                    // Usuń zewnętrzne cudzysłowy i zdekoduj zawartość
                    jsonValue = JSON.parse(jsonValue);
                }
            }
            const json = typeof jsonValue === 'string' ? JSON.parse(jsonValue) : jsonValue;
            editor.set(json);
        } catch (e) {
            console.error('Błąd parsowania JSON:', e);
            editor.set({});
        }
        
        // Zapisz referencję do edytora w atrybucie data
        container.editor = editor;
    });
}

/**
 * Konfiguruje obsługę przełączania typu triggera (webhook/mqtt)
 */
function setupTriggerTypeToggle() {
    const triggerRadios = document.querySelectorAll('.trigger-type');
    const webhookConfig = document.getElementById('webhookConfig');
    const mqttConfig = document.getElementById('mqttConfig');
    
    triggerRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'webhook') {
                webhookConfig.classList.remove('d-none');
                mqttConfig.classList.add('d-none');
            } else if (this.value === 'mqtt') {
                webhookConfig.classList.add('d-none');
                mqttConfig.classList.remove('d-none');
            }
        });
    });
}

/**
 * Konfiguruje obsługę dodawania nowego kroku poprzez zakładkę "+"
 */
function setupAddStepTab() {
    const addStepTab = document.getElementById('add-step-tab');
    
    if (addStepTab) {
        addStepTab.addEventListener('click', function() {
            // Pobierz aktualną liczbę kroków
            const stepTabs = document.querySelectorAll('.steps-tabs .nav-item:not(:last-child)');
            const newIndex = stepTabs.length;
            
            // Utwórz nową zakładkę
            const newTab = createStepTab(newIndex);
            
            // Utwórz zawartość zakładki
            const newContent = createStepContent(newIndex);
            
            // Dodaj zakładkę przed przyciskiem "+"
            addStepTab.parentNode.insertAdjacentElement('beforebegin', newTab);
            
            // Dodaj zawartość do kontenera
            const tabContent = document.getElementById('stepsTabContent');
            tabContent.appendChild(newContent);
            
            // Usuń komunikat o braku kroków, jeśli istnieje
            const noStepsAlert = tabContent.querySelector('.alert');
            if (noStepsAlert) {
                noStepsAlert.remove();
            }
            
            // Aktywuj nową zakładkę - ręczna aktywacja
            const tabButton = newTab.querySelector('button');
            
            // Usuń klasę active ze wszystkich zakładek i zawartości
            document.querySelectorAll('#stepsTab .nav-link').forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            
            document.querySelectorAll('.step-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Dodaj klasę active do nowej zakładki
            tabButton.classList.add('active');
            tabButton.setAttribute('aria-selected', 'true');
            
            // Pokaż odpowiednią zawartość
            newContent.classList.add('active');
            
            // Dodaj obsługę kliknięcia dla nowej zakładki
            tabButton.addEventListener('click', function(event) {
                event.preventDefault();
                
                // Usuń klasę active ze wszystkich zakładek i zawartości
                document.querySelectorAll('#stepsTab .nav-link').forEach(tab => {
                    tab.classList.remove('active');
                    tab.setAttribute('aria-selected', 'false');
                });
                
                document.querySelectorAll('.step-tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Dodaj klasę active do klikniętej zakładki
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');
                
                // Pokaż odpowiednią zawartość
                const target = document.querySelector(this.getAttribute('data-bs-target'));
                if (target) {
                    target.classList.add('active');
                }
            });
            
            // Inicjalizuj edytor JSON dla nowego kroku
            initJsonEditorForStep(newIndex);
            
            // Zaktualizuj obsługę zdarzeń
            setupDeleteStepButtons();
            setupPluginSelects();
        });
    }
}

/**
 * Tworzy element zakładki dla nowego kroku
 * @param {number} index - Indeks nowego kroku
 * @returns {HTMLElement} Element zakładki
 */
function createStepTab(index) {
    const li = document.createElement('li');
    li.className = 'nav-item';
    li.setAttribute('role', 'presentation');
    
    li.innerHTML = `
        <button class="nav-link" 
                id="step-tab-${index}" 
                data-bs-toggle="tab" 
                data-bs-target="#step-content-${index}" 
                type="button" 
                role="tab" 
                aria-controls="step-content-${index}" 
                aria-selected="false">
            Krok ${index + 1}
        </button>
    `;
    
    return li;
}

/**
 * Tworzy zawartość zakładki dla nowego kroku
 * @param {number} index - Indeks nowego kroku
 * @returns {HTMLElement} Element zawartości zakładki
 */
function createStepContent(index) {
    const div = document.createElement('div');
    div.className = 'step-tab-content';
    div.id = `step-content-${index}`;
    div.setAttribute('role', 'tabpanel');
    div.setAttribute('aria-labelledby', `step-tab-${index}`);
    
    // Pobierz listę pluginów z pierwszego selecta (jeśli istnieje)
    let pluginOptions = '<option value="">Wybierz plugin...</option>';
    const firstSelect = document.querySelector('.plugin-select');
    
    if (firstSelect) {
        // Kopiuj opcje z istniejącego selecta
        const options = Array.from(firstSelect.options);
        pluginOptions = options.map(option => {
            const value = option.value;
            const text = option.textContent;
            const description = option.dataset.description || '';
            const type = option.dataset.type || '';
            
            return `<option value="${value}" data-description="${description}" data-type="${type}">${text}</option>`;
        }).join('');
    } else {
        // Jeśli nie ma żadnego selecta, dodaj domyślne opcje dla lokalnych pluginów
        pluginOptions = `
            <option value="">Wybierz plugin...</option>
            <option value="UppercasePlugin" data-description="Konwertuje wartości tekstowe w danych wejściowych na wielkie litery" data-type="local">UppercasePlugin (local)</option>
            <option value="LogPlugin" data-description="Loguje otrzymane dane i przekazuje je dalej bez zmian." data-type="local">LogPlugin (local)</option>
            <option value="remote:" data-description="Zdalny plugin niestandardowy. Wprowadź pełną nazwę poniżej.">Inny zdalny plugin</option>
        `;
    }
    
    div.innerHTML = `
        <div class="step-item">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4>Krok ${index + 1}</h4>
                <button type="button" class="btn btn-danger delete-step-btn" data-step-index="${index}">
                    <i class="bi bi-trash"></i> Usuń krok
                </button>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Plugin</label>
                <select class="form-select plugin-select" name="steps[${index}][plugin]" required>
                    ${pluginOptions}
                </select>
            </div>
            
            <!-- Pole dla zdalnych pluginów -->
            <div class="mb-3 remote-plugin-field d-none">
                <label class="form-label">Nazwa zdalnego pluginu</label>
                <input type="text" class="form-control remote-plugin-name" 
                       name="remote_plugin_name_${index}"
                       placeholder="remote:device:plugin">
                <div class="form-text">Format: remote:device:plugin</div>
            </div>
            
            <!-- Opis pluginu -->
            <div class="mb-3 plugin-description-container"></div>
            
            <div class="mb-3">
                <label class="form-label">Parametry pluginu (JSON)</label>
                <div class="json-editor" data-index="${index}"></div>
                <input type="hidden" class="step-params-input" name="steps[${index}][params]" value="{}">
                <div class="form-text plugin-params-help">
                    Parametry konfiguracyjne dla pluginu.
                </div>
            </div>
        </div>
    `;
    
    return div;
}

/**
 * Inicjalizuje edytor JSON dla nowego kroku
 * @param {number} index - Indeks kroku
 */
function initJsonEditorForStep(index) {
    const container = document.querySelector(`.json-editor[data-index="${index}"]`);
    const inputField = document.querySelector(`.step-params-input[name="steps[${index}][params]"]`);
    
    if (container && inputField) {
        const editor = new JSONEditor(container, {
            mode: 'tree',
            modes: ['tree', 'code', 'form', 'text'],
            onChangeText: function(jsonString) {
                inputField.value = jsonString;
            }
        });
        
        try {
            const json = JSON.parse(inputField.value || '{}');
            editor.set(json);
        } catch (e) {
            console.error('Błąd parsowania JSON:', e);
            editor.set({});
        }
        
        // Zapisz referencję do edytora w atrybucie data
        container.editor = editor;
    }
}

/**
 * Konfiguruje obsługę przycisków usuwania kroków
 */
function setupDeleteStepButtons() {
    const deleteButtons = document.querySelectorAll('.delete-step-btn');
    
    deleteButtons.forEach(button => {
        // Usuń poprzednie listenery, aby uniknąć duplikacji
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function(e) {
            e.stopPropagation(); // Zapobiega aktywacji zakładki
            
            const stepIndex = this.dataset.stepIndex;
            const tabElement = document.getElementById(`step-tab-${stepIndex}`).parentNode;
            const contentElement = document.getElementById(`step-content-${stepIndex}`);
            
            // Sprawdź, czy usuwana zakładka jest aktywna
            const isActive = contentElement.classList.contains('active');
            
            // Usuń zakładkę i jej zawartość
            tabElement.remove();
            contentElement.remove();
            
            // Jeśli usunięta zakładka była aktywna, aktywuj pierwszą dostępną
            if (isActive) {
                const firstTab = document.querySelector('.steps-tabs .nav-link:not(.add-step-tab)');
                if (firstTab) {
                    // Ręczna aktywacja zakładki
                    // Usuń klasę active ze wszystkich zakładek i zawartości
                    document.querySelectorAll('#stepsTab .nav-link').forEach(tab => {
                        tab.classList.remove('active');
                        tab.setAttribute('aria-selected', 'false');
                    });
                    
                    document.querySelectorAll('.step-tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    // Dodaj klasę active do pierwszej zakładki
                    firstTab.classList.add('active');
                    firstTab.setAttribute('aria-selected', 'true');
                    
                    // Pokaż odpowiednią zawartość
                    const target = document.querySelector(firstTab.getAttribute('data-bs-target'));
                    if (target) {
                        target.classList.add('active');
                    }
                }
            }
            
            // Przenumeruj pozostałe zakładki
            renumberStepTabs();
            
            // Jeśli nie ma już żadnych kroków, dodaj komunikat
            const remainingSteps = document.querySelectorAll('.step-tab-content');
            if (remainingSteps.length === 0) {
                const tabContent = document.getElementById('stepsTabContent');
                tabContent.innerHTML = `
                    <div class="alert alert-info m-3">
                        Brak zdefiniowanych kroków. Kliknij "+" aby dodać pierwszy krok.
                    </div>
                `;
            }
            
            // Zaktualizuj podgląd JSON
            updateJsonFromForm();
        });
    });
}

/**
 * Przenumerowuje zakładki kroków po usunięciu
 */
function renumberStepTabs() {
    const stepTabs = document.querySelectorAll('.steps-tabs .nav-item:not(:last-child)');
    
    stepTabs.forEach((tab, newIndex) => {
        const button = tab.querySelector('button');
        const contentId = button.getAttribute('data-bs-target').replace('#step-content-', '');
        
        // Aktualizuj tekst zakładki
        button.textContent = `Krok ${newIndex + 1}`;
        
        // Aktualizuj atrybuty zakładki
        button.id = `step-tab-${newIndex}`;
        button.setAttribute('data-bs-target', `#step-content-${newIndex}`);
        button.setAttribute('aria-controls', `step-content-${newIndex}`);
        
        // Aktualizuj zawartość zakładki
        const content = document.getElementById(`step-content-${contentId}`);
        if (content) {
            content.id = `step-content-${newIndex}`;
            content.setAttribute('aria-labelledby', `step-tab-${newIndex}`);
            
            // Aktualizuj nagłówek kroku
            const stepHeader = content.querySelector('h4');
            if (stepHeader) {
                stepHeader.textContent = `Krok ${newIndex + 1}`;
            }
            
            // Aktualizuj indeks przycisku usuwania
            const deleteButton = content.querySelector('.delete-step-btn');
            if (deleteButton) {
                deleteButton.setAttribute('data-step-index', newIndex);
            }
            
            // Aktualizuj nazwy pól formularza
            const pluginSelect = content.querySelector('.plugin-select');
            if (pluginSelect) {
                pluginSelect.name = `steps[${newIndex}][plugin]`;
            }
            
            const remotePluginInput = content.querySelector('.remote-plugin-name');
            if (remotePluginInput) {
                remotePluginInput.name = `remote_plugin_name_${newIndex}`;
            }
            
            const paramsInput = content.querySelector('.step-params-input');
            if (paramsInput) {
                paramsInput.name = `steps[${newIndex}][params]`;
            }
            
            const jsonEditor = content.querySelector('.json-editor');
            if (jsonEditor) {
                jsonEditor.dataset.index = newIndex;
            }
        }
    });
}

/**
 * Konfiguruje obsługę wyboru pluginu
 */
function setupPluginSelects() {
    const pluginSelects = document.querySelectorAll('.plugin-select');
    
    pluginSelects.forEach(select => {
        // Usuń poprzednie listenery, aby uniknąć duplikacji
        const newSelect = select.cloneNode(true);
        select.parentNode.replaceChild(newSelect, select);
        
        newSelect.addEventListener('change', function() {
            const stepItem = this.closest('.step-item');
            const remoteField = stepItem.querySelector('.remote-plugin-field');
            const remoteInput = stepItem.querySelector('.remote-plugin-name');
            const descriptionContainer = stepItem.querySelector('.plugin-description-container');
            const paramsHelpContainer = stepItem.querySelector('.plugin-params-help');
            
            // Pobierz wybrany plugin i jego dane
            const selectedOption = this.options[this.selectedIndex];
            const pluginId = this.value;
            const description = selectedOption.dataset.description || 'Brak opisu';
            
            // Obsługa zdalnych pluginów
            if (pluginId === 'remote:') {
                remoteField.classList.remove('d-none');
                
                // Nasłuchuj zmian w polu nazwy zdalnego pluginu
                if (remoteInput) {
                    // Usuń poprzednie listenery, aby uniknąć duplikacji
                    const newInput = remoteInput.cloneNode(true);
                    remoteInput.parentNode.replaceChild(newInput, remoteInput);
                    
                    newInput.addEventListener('input', function() {
                        // Aktualizuj wartość selecta, aby zawierała pełną nazwę zdalnego pluginu
                        const remotePluginName = this.value.trim();
                        if (remotePluginName) {
                            // Znajdź select w tym samym kroku
                            const pluginSelect = this.closest('.step-item').querySelector('.plugin-select');
                            if (pluginSelect) {
                                // Ustaw wartość selecta na nazwę zdalnego pluginu
                                // Ale nie zmieniaj wybranej opcji w UI (zostaje "Inny zdalny plugin")
                                pluginSelect.value = remotePluginName;
                            }
                        }
                    });
                }
            } else {
                remoteField.classList.add('d-none');
                // Wyczyść pole zdalnego pluginu, jeśli wybrano inny typ
                if (remoteInput) {
                    remoteInput.value = '';
                }
            }
            
            // Aktualizuj opis pluginu
            descriptionContainer.innerHTML = `
                <div class="alert alert-info plugin-description">
                    ${description}
                </div>
            `;
            
            // Aktualizuj opis parametrów, jeśli dostępny
            if (selectedOption.dataset.paramsDescription) {
                paramsHelpContainer.innerHTML = selectedOption.dataset.paramsDescription;
            } else {
                paramsHelpContainer.innerHTML = 'Parametry konfiguracyjne dla pluginu.';
            }
            
            // Zaktualizuj podgląd JSON
            updateJsonFromForm();
        });
    });
}

/**
 * Konfiguruje synchronizację między formularzem a edytorem JSON
 */
function setupJsonEditorSync() {
    const updateJsonButton = document.getElementById('updateJsonFromForm');
    const updateFormButton = document.getElementById('updateFromJson');
    
    if (updateJsonButton) {
        updateJsonButton.addEventListener('click', function() {
            updateJsonFromForm();
        });
    }
    
    if (updateFormButton) {
        updateFormButton.addEventListener('click', function() {
            updateFormFromJson();
        });
    }
    
    // Aktualizuj JSON przy zmianie formularza
    document.getElementById('chainForm').addEventListener('change', function() {
        updateJsonFromForm();
    });
}

/**
 * Aktualizuje edytor JSON na podstawie danych z formularza
 */
function updateJsonFromForm() {
    const chainId = document.getElementById('chainId').value;
    const description = document.getElementById('chainDescription').value;
    
    // Określ typ triggera
    const triggerType = document.querySelector('input[name="trigger_type"]:checked').value;
    
    let trigger = '';
    if (triggerType === 'webhook') {
        const endpoint = document.getElementById('webhookEndpoint').value;
        trigger = 'webhook:' + endpoint;
    } else if (triggerType === 'mqtt') {
        const topic = document.getElementById('mqttTopic').value;
        trigger = 'mqtt:' + topic;
    }
    
    // Zbierz dane o krokach
    const steps = [];
    const stepContents = document.querySelectorAll('.step-tab-content');
    
    stepContents.forEach(content => {
        const pluginSelect = content.querySelector('.plugin-select');
        const paramsInput = content.querySelector('.step-params-input');
        
        if (pluginSelect && paramsInput) {
            let pluginId = pluginSelect.value;
            
            // Sprawdź, czy to zdalny plugin niestandardowy
            if (pluginId === 'remote:') {
                const remoteInput = content.querySelector('.remote-plugin-name');
                if (remoteInput && remoteInput.value) {
                    pluginId = remoteInput.value;
                }
            }
            
            let params = {};
            try {
                // Bezpieczne parsowanie wartości JSON
                let jsonValue = paramsInput.value.trim();
                // Sprawdź, czy wartość jest otoczona cudzysłowiami (co może powodować błędy)
                if (jsonValue.startsWith('"') && jsonValue.endsWith('"')) {
                    // Usuń zewnętrzne cudzysłowy i zdekoduj zawartość
                    jsonValue = JSON.parse(jsonValue);
                }
                params = typeof jsonValue === 'string' ? JSON.parse(jsonValue) : jsonValue;
            } catch (e) {
                console.error('Błąd parsowania JSON:', e);
            }
            
            steps.push({
                plugin: pluginId,
                params: params
            });
        }
    });
    
    // Utwórz obiekt JSON
    const chainData = {
        id: chainId,
        description: description,
        trigger: trigger,
        steps: steps
    };
    
    // Aktualizuj edytor JSON
    if (window.editor) {
        window.editor.set(chainData);
        document.getElementById('rawJsonInput').value = JSON.stringify(chainData);
    }
}

/**
 * Aktualizuje formularz na podstawie danych z edytora JSON
 */
function updateFormFromJson() {
    try {
        const jsonData = window.editor.get();
        
        // Aktualizuj podstawowe pola
        document.getElementById('chainId').value = jsonData.id || '';
        document.getElementById('chainDescription').value = jsonData.description || '';
        
        // Aktualizuj trigger
        const trigger = jsonData.trigger || '';
        if (trigger.startsWith('webhook:')) {
            document.getElementById('triggerWebhook').checked = true;
            // Użyj split z limitem 2, aby uzyskać tylko pierwszą część po dwukropku
            document.getElementById('webhookEndpoint').value = trigger.split(':', 2)[1] || '';
            document.getElementById('webhookConfig').classList.remove('d-none');
            document.getElementById('mqttConfig').classList.add('d-none');
        } else if (trigger.startsWith('mqtt:')) {
            document.getElementById('triggerMqtt').checked = true;
            // Użyj split z limitem 2, aby uzyskać tylko pierwszą część po dwukropku
            document.getElementById('mqttTopic').value = trigger.split(':', 2)[1] || '';
            document.getElementById('webhookConfig').classList.add('d-none');
            document.getElementById('mqttConfig').classList.remove('d-none');
        }
        
        // Aktualizuj kroki - najpierw usuń wszystkie istniejące
        const stepsContainer = document.getElementById('stepsTabContent');
        const stepTabs = document.querySelectorAll('.steps-tabs .nav-item:not(:last-child)');
        
        // Usuń zakładki
        stepTabs.forEach(tab => tab.remove());
        
        // Usuń zawartość zakładek
        while (stepsContainer.firstChild) {
            stepsContainer.removeChild(stepsContainer.firstChild);
        }
        
        // Dodaj nowe kroki
        if (jsonData.steps && jsonData.steps.length > 0) {
            jsonData.steps.forEach((step, index) => {
                // Symuluj kliknięcie przycisku dodawania
                document.getElementById('add-step-tab').click();
                
                // Poczekaj na utworzenie elementów DOM
                setTimeout(() => {
                    const stepContent = document.getElementById(`step-content-${index}`);
                    if (stepContent) {
                        const pluginSelect = stepContent.querySelector('.plugin-select');
                        const remoteField = stepContent.querySelector('.remote-plugin-field');
                        const remoteInput = stepContent.querySelector('.remote-plugin-name');
                        const paramsInput = stepContent.querySelector('.step-params-input');
                        const jsonEditor = stepContent.querySelector('.json-editor').editor;
                        
                        // Ustaw plugin
                        if (pluginSelect) {
                            // Sprawdź, czy to zdalny plugin niestandardowy
                            const pluginId = step.plugin || '';
                            if (pluginId.startsWith('remote:')) {
                                // Znajdź opcję "Inny zdalny plugin"
                                const remoteOption = Array.from(pluginSelect.options).find(opt => opt.value === 'remote:');
                                if (remoteOption) {
                                    // Wybierz opcję "Inny zdalny plugin"
                                    remoteOption.selected = true;
                                    
                                    // Pokaż pole do wprowadzenia nazwy zdalnego pluginu
                                    if (remoteField && remoteInput) {
                                        remoteField.classList.remove('d-none');
                                        remoteInput.value = pluginId;
                                        
                                        // Ustaw wartość selecta na pełną nazwę pluginu (dla formularza)
                                        pluginSelect.value = pluginId;
                                    }
                                }
                            } else {
                                // Dla standardowych pluginów po prostu ustaw wartość
                                pluginSelect.value = pluginId;
                            }
                            
                            // Wywołaj zdarzenie change, aby zaktualizować opis
                            const event = new Event('change');
                            pluginSelect.dispatchEvent(event);
                        }
                        
                        // Ustaw parametry
                        if (paramsInput && jsonEditor) {
                            const params = step.params || {};
                            paramsInput.value = JSON.stringify(params);
                            jsonEditor.set(params);
                        }
                    }
                }, 100);
            });
        } else {
            // Jeśli nie ma kroków, dodaj komunikat
            stepsContainer.innerHTML = `
                <div class="alert alert-info m-3">
                    Brak zdefiniowanych kroków. Kliknij "+" aby dodać pierwszy krok.
                </div>
            `;
        }
        
    } catch (e) {
        console.error('Błąd aktualizacji formularza z JSON:', e);
        alert('Wystąpił błąd podczas aktualizacji formularza. Sprawdź poprawność JSON.');
    }
}
