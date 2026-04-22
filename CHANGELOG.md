# Changelog - SELIC (Social Engineering Wordlist Generator)

## [1.2.0] - 2026-04-22
### 🚀 1. Re-Arquitectura del Núcleo (Core)
El motor ha sido extraído a `selic_core.py`, permitiendo que múltiples interfaces usen la misma lógica de generación de alto rendimiento.
*   **Sincronización Total:** Ambas herramientas (`selic.py` y `selic_mini.py`) comparten el mismo motor heurístico calibrado.

### 🧠 2. Heurística Avanzada (Cierre de Puntos Ciegos)
Se han implementado patrones de comportamiento humano real detectados en auditorías:
*   **Redundancia:** Generación de repeticiones de palabras (`adminadmin`).
*   **Símbolos Gemelos:** Inyección de símbolos dobles comunes (`!!`, `@@`, `..`).
*   **Iniciales Inteligentes:** Variantes automáticas como `J.Diaz` o `Diaz_J`.

### 🛡️ 3. Blindaje y Seguridad (NUEVO)
*   **Freno Absurdo (5B):** Sistema de bloqueo para generaciones superiores a 5,000 millones de líneas, con bypass mediante frase de seguridad ("ACEPTO EL RIESGO").
*   **Freno de Pánico (5GB):** Monitorización en tiempo real del espacio en disco. Detiene la generación si el espacio libre cae por debajo de 5GB para proteger la integridad del S.O.
*   **Sensor de Disco Previo:** Estimación de peso vs Espacio libre antes de iniciar la tarea.

### 📊 4. Transparencia y Control
*   **Termómetro de Nivel:** Indicador visual que proyecta el nivel de agresividad (1-4) basado en ajustes manuales.
*   **Estimador Pro-Activo:** Rediseño total del cálculo basado en "Pool Real de Tokens" con factor de escala heurístico (0.10).
*   **Configurabilidad Total:** Todas las variables de seguridad (límites de RAM, límites de generación) son editables desde `selic.cfg`.

### 🛠️ 5. Mejoras Técnicas
*   **Generadores Python:** Uso intensivo de `yield` para mantener el consumo de RAM bajo (<50MB).
*   **Deduplicación Híbrida:** RAM rápida con caída automática a disco (Sort) para evitar crasheos.

---

## [1.1.0-BETA] - Anterior
*   Separación de tokens por categorías.
*   Implementación de Leet Speak básico.
