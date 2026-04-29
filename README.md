# SELIC v1.2.0
**Social Engineering List Creator** - Generador Quirúrgico de Wordlists Asistido por Diagnóstico.

SELIC es un motor de ingeniería social avanzado diseñado para penetrar defensas basadas en la psicología del usuario. A diferencia de los generadores aleatorios, SELIC analiza los datos del objetivo y recomienda el nivel de ataque óptimo mediante un sistema de **Diagnóstico Dinámico**.

## 🌟 Novedades en la Versión 1.2.0 Oficial
Esta versión marca un hito en la evolución de SELIC, pasando de un script único a una **arquitectura modular de alto rendimiento** e incorporando las siguientes novedades:

*   **🧠 Motor Heurístico Pro (Core):** Nueva lógica que identifica patrones de redundancia (`adminadmin`), iniciales inteligentes (`J.Diaz`) y símbolos dobles.
*   **🛡️ Blindaje de Hardware:** Sistemas de seguridad integrados (Sensor de espacio en disco, Freno Absurdo y Pánico de 5GB) para proteger la integridad de tu disco y sistema operativo.
*   **⚡ Arquitectura Modular:** Separación de la lógica de generación (`selic_core.py`) de las interfaces de usuario.
*   **📊 Estimador Pro-Activo:** Cálculo real del tamaño del wordlist antes de iniciar la generación.
*   **✨ Sufijos Dinámicos**: Los sufijos (`123, 2026, 2025`) ahora se gestionan desde `selic.cfg`. Puedes cambiarlos, ampliarlos o desactivarlos escribiendo `ninguno`.
*   **🛡️ Contraseñas Comunes Extra**: Nueva variable `extra_common_passwords` en `selic.cfg` para ampliar la lista interna sin tocar código.
*   **🎯 Modo Quirúrgico (Patrones):** Nueva lógica donde los patrones tienen prioridad absoluta. Si usas patrones, SELIC se enfoca solo en ellos (estilo Crunch), evitando el ruido de la generación automática.
*   **✨ Marcadores Evolucionados:** Se incorpora el marcador `*` (un solo carácter de tus datos) para una precisión de longitud total, mientras `#` se mantiene para bloques de datos enteros.
*   **🛠️ Patrones Documentados**: El botón `[?]` ahora explica el uso de `*` vs `#`, texto fijo, escapes y múltiples patrones.
*   **✅ Resumen de Confirmación**: Las 3 interfaces (CLI, Mini, GUI) muestran un resumen completo antes de generar, con opción de reiniciar la configuración.
*   **🎨 Mejoras Visuales GUI**: Nueva interfaz Cyber-Dark, diálogos de confirmación oscuros personalizados, y validaciones reforzadas.

---

## 🚀 Modos de Ejecución

### 1. SELIC Pro (Interactivo)
Ideal para ataques quirúrgicos donde conoces detalles del objetivo. Incluye un asistente que te guía paso a paso.
```bash
python selic.py -i
```

### 2. SELIC Mini (Turbo)
Versión ligera y ultrarrápida sin dependencias. Perfecta para terminales rápidas o entornos restringidos.
```bash
python selic_mini.py
```

### 3. SELIC GUI (Visual)
Interfaz gráfica completa con medidores de gravedad visuales y fácil gestión de la palabra clave final. Ideal para Windows y usuarios de escritorio.
```bash
python selic_gui.py
```

---

## 🧠 Características Principales

| Característica | Descripción |
| :--- | :--- |
| **Normalización Fase 0** | Descompone nombres, fechas y datos crudos en tokens lógicos. |
| **4 Niveles de Tiers** | Desde ataques básicos (Tier 1) hasta fuerza bruta extrema (Tier 4). |
| **Leet Speak Dinámico** | Transformación inteligente de caracteres (ej: `a` -> `4`, `e` -> `3`). |
| **Deduplicación Híbrida** | Gestión eficiente de RAM y disco para evitar crasheos en archivos masivos. |

---

## 🛡️ Sistemas de Seguridad (Hardware Protection)
SELIC 1.2.0 es el primer generador que se preocupa por la salud de tu equipo:

1.  **Freno Absurdo (5B):** Si la generación supera los 5,000 millones de combinaciones, se requiere confirmación explícita (`ACEPTO EL RIESGO`).
2.  **Sensor de Disco Previo:** Analiza si tienes espacio suficiente antes de empezar.
3.  **Freno de Pánico (5GB):** Detiene la generación automáticamente si el espacio libre en disco cae por debajo de 5GB.

---

## ⚙️ Configuración Personalizada (`selic.cfg`)
Puedes ajustar el comportamiento del motor editando el archivo de configuración:
*   `default_suffixes`: Sufijos base que se usan por defecto (ej: `123, 2026, 2025`).
*   `extra_suffixes`: Sufijos adicionales para ataques específicos (se suman a los base).
*   `extra_common_passwords`: Contraseñas comunes extra añadidas a la lista interna.
*   `max_ram`: Límite de memoria para procesamiento de duplicados.
*   `allow_extreme_generation`: Bypass para el freno de seguridad.
*   `[leet]`: Personalización de las reglas de sustitución Leet Speak.

---

## 🛠️ Requisitos
*   Python 3.8 o superior.
*   Sin dependencias externas (100% Native Python).

---

## 📜 Disclaimer
*Esta herramienta ha sido creada con fines educativos y de auditoría profesional. El uso de SELIC para atacar infraestructuras sin autorización previa es ilegal y responsabilidad exclusiva del usuario final.*

---
**Desarrollado con precisión para la nueva era de la seguridad ofensiva.**
