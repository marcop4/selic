# Changelog - SELIC (Social Engineering Wordlist Generator)

## [1.2.0] - 2026-04-28 (Versión Oficial)
### Añadido
- **Sufijos Dinámicos**: Los sufijos por defecto (`123, 2026, 2025`) ahora son 100% configurables desde `selic.cfg` (`default_suffixes` + `extra_suffixes`). Se eliminó el hardcoding interno del motor.
- **Opción "ninguno"**: Escribir `ninguno` (en cualquier combinación de mayúsculas/minúsculas) en CLI, Mini o GUI anula todos los sufijos para esa ejecución.
- **`extra_common_passwords`**: Nueva variable en `selic.cfg` para añadir contraseñas comunes extra sin modificar el código fuente.
- **Resumen de Confirmación (GUI)**: Diálogo emergente Sí/No con resumen completo de configuración antes de generar.
- **Reiniciar Configuración (CLI)**: Opción `R` al final del resumen para reiniciar las preguntas con respuestas previas como defaults.
- **Volver a Empezar (Mini)**: Opción `R` al final del resumen para reiniciar desde cero.
- **Placeholder en Patrones (GUI)**: El campo de patrones ahora muestra un ejemplo sombreado que no se usa en la generación.
- **Validación de Patrones**: Error claro si un patrón no contiene marcadores válidos antes de generar.
- **Documentación de Escape**: El botón `[?]` de patrones ahora explica texto fijo, escape con `\` y múltiples patrones por línea.
- **Diagnóstico Dinámico (CLI/GUI)**: El sistema analiza tus ajustes y recomienda un nivel de agresividad óptimo.
- **Medidor de Gravedad (GUI)**: Indicador visual por bloques (Verde a Rojo) que muestra el impacto de la configuración en tiempo real.
- **Modo Quirúrgico (Prioridad)**: Si se definen patrones, SELIC ahora da prioridad absoluta a estos (estilo Crunch), omitiendo la generación por capas estándar para evitar wordlists excesivas y centrarse en la precisión.
- **Nuevo Marcador `*`**: Permite seleccionar **un solo carácter** de tus datos sociales (ej: 'M' de Marco) para patrones de longitud exacta.
- **Marcador `#` Refinado**: Ahora se especializa en **datos sociales enteros** (ej: 'Marco' completo) para combinar conceptos rápidamente.
- **Mutaciones en Patrones**: Los marcadores `*` y `#` ahora respetan las mutaciones activas (Leet, Caps, etc.) si el usuario lo desea.
- **Patrones en Mini**: Soporte completo para patrones avanzados (*, #, %, @...) en `selic_mini.py`.
- **Nuevos Campos GUI**: Fecha de nacimiento y selectores de longitud mín/máx integrados.
- **Botones de Ayuda [?]**: Documentación contextual dentro de la interfaz gráfica.
- **Priorización Heurística (Global)**: El sistema ahora "sabe" qué datos son más importantes (Nombre > Otros Datos). Las contraseñas más probables aparecen al principio de la wordlist, optimizando el tiempo de ataque.
- **Creación de Carpetas Automática**: SELIC ahora crea recursivamente cualquier directorio de salida que no exista (ej: `wordlists/`), eliminando la necesidad de gestionar carpetas manualmente.
- **Identidad de Salida (`_pro`, `_mini`, `_gui`)**: Nomenclatura automática de archivos según la interfaz usada para evitar colisiones de datos.

### Mejorado
- **Estética Cyber-Dark GUI**: Diálogos oscuros, scrollbars estilizadas y aislamiento de scroll principal para una mejor experiencia de usuario.
- **Resumen CLI Normal**: Ahora incluye Nombre, Nacimiento, DNI y Sufijos en el resumen rápido.
- **Resumen Mini**: Ahora muestra los sufijos configurados en la configuración final.
- **Ayuda de Sufijos (GUI)**: El botón `[?]` ahora menciona la opción `ninguno` y la posibilidad de usar letras/símbolos.
- **Consistencia de interfaces**: Las tres interfaces (CLI, Mini, GUI) ahora muestran los sufijos por defecto y permiten anularlos.
- **Estandarización UI**: Formato `[S/n]` profesional con resaltado en color verde para valores por defecto.
- **Lógica de Mezcla**: La complejidad 2 ahora permite "Mezcla de Parejas" por defecto en modo automático.
- **DNI/Documentos**: Soporte para documentos alfanuméricos y mejores fragmentaciones.
- **Detección de Ñ**: Soporte nativo para caracteres especiales hispanos.
- **Sincronización `selic.cfg` en Mini**: La versión ligera ahora lee y respeta la configuración global (sufijos, longitudes, etc.).
- **UX Quirúrgica**: Instrucciones aclaratorias en el asistente CLI sobre extensiones automáticas y manejo de directorios.

### Corregido
- Eliminadas inyecciones hardcodeadas de `"2024"` y `["123", "2024", "2025"]` en `selic_core.py` que ignoraban la configuración del usuario.
- El patrón de ejemplo `#%?#` ya no se usa como patrón real en la GUI (era un placeholder visual que contaminaba la generación).
- Error de concatenación `TypeError` en el motor de agresividad.
- Repetición de textos en los diagnósticos del CLI.
- Bug de inicialización de listas en la generación de patrones del modo Mini.
- SyntaxWarning por secuencias de escape en Python 3.12+.

## [1.2.0-BETA] - 2026-04-22
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
