# SELIC v1.2.0
**Social Engineering List Creator** - Generador Quirúrgico de Wordlists Asistido por Diagnóstico.

SELIC es un motor de ingeniería social avanzado diseñado para penetrar defensas basadas en la psicología del usuario. A diferencia de los generadores aleatorios, SELIC analiza los datos del objetivo y recomienda el nivel de ataque óptimo mediante un sistema de **Diagnóstico Dinámico**.

### 🌟 Novedades de la v1.2.0-BETA:
- **Diagnóstico Asistido**: El sistema detecta automáticamente la "Gravedad" de tu ataque y te sugiere el mejor nivel de agresividad.
- **Medidor de Gravedad Visual (GUI)**: Nueva interfaz Cyber-Dark con indicador de 4 bloques de colores (Verde -> Rojo).
- **Potencia Universal**: Ahora el modo Mini, el CLI normal y la GUI comparten el mismo motor de Patrones Avanzados y lógica de mezcla.
- **Estándar Profesional**: Implementación de flujos interactivos con valores predeterminados inteligentes `[S/n]`.

---

## 🌟 Novedades en la Versión 1.2.0
Esta versión marca un hito en la evolución de SELIC, pasando de un script único a una **arquitectura modular de alto rendimiento**.

*   **🧠 Motor Heurístico Pro (Core):** Nueva lógica que identifica patrones de redundancia (`adminadmin`), iniciales inteligentes (`J.Diaz`) y símbolos dobles.
*   **🛡️ Blindaje de Hardware:** Sistemas de seguridad integrados para proteger la integridad de tu disco y sistema operativo.
*   **⚡ Arquitectura Modular:** Separación de la lógica de generación (`selic_core.py`) de las interfaces de usuario.
*   **📊 Estimador Pro-Activo:** Cálculo real del tamaño del wordlist antes de iniciar la generación.

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
*   `max_ram`: Límite de memoria para procesamiento de duplicados.
*   `allow_extreme_generation`: Bypass para el freno de seguridad.
*   `leet_mappings`: Personalización de las reglas de sustitución.

---

## 🛠️ Requisitos
*   Python 3.8 o superior.
*   Sin dependencias externas (100% Native Python).

---

## 📜 Disclaimer
*Esta herramienta ha sido creada con fines educativos y de auditoría profesional. El uso de SELIC para atacar infraestructuras sin autorización previa es ilegal y responsabilidad exclusiva del usuario final.*

---
**Desarrollado con precisión para la nueva era de la seguridad ofensiva.**
