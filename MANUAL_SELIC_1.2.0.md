# Manual de Usuario - SELIC 1.2.0 (Social Engineering Wordlist Generator)

SELIC es una herramienta avanzada de generación de diccionarios quirúrgicos para auditorías de seguridad e ingeniería social. A diferencia de los generadores de fuerza bruta tradicionales, SELIC se enfoca en la **psicología humana** y los patrones lógicos de creación de contraseñas.

---

## 🚀 1. Cómo empezar (Instalación y Uso)

### Requisitos
*   Python 3.8 o superior.
*   No requiere librerías externas (es 100% nativo).

### Ejecución
Dependiendo de tu sistema operativo, el comando puede variar:

#### En Windows:
*   **Modo Interactivo (Recomendado):** `py selic.py -i`
*   **Modo Mini (Rápido):** `py selic_mini.py`
*   **Modo GUI (Visual):** `py selic_gui.py`

#### En Linux / Mac:
*   **Modo Interactivo (Recomendado):** `python3 selic.py -i`
*   **Modo Mini (Rápido):** `python3 selic_mini.py`
*   **Modo GUI (Visual):** `python3 selic_gui.py`

*Nota: El flag `-i` es fundamental en `selic.py` para activar el asistente de preguntas. Si no lo pones, el programa esperará argumentos por línea de comandos.*

---

## 🧠 2. El Corazón: La Fragmentación Inteligente
Una de las dudas más comunes es: *"¿Por qué si ingresé 5 palabras, el programa dice que identificó 60?"*.
SELIC realiza una **Fase 0 de Normalización**:
*   **Fechas:** Extrae día, mes, año y combinaciones (DDMM, MMYYYY).
*   **Nombres:** Genera iniciales automáticas (`J.Diaz`), uniones (`JuanDiaz`) y separadores.
*   **Limpieza:** Elimina tildes y caracteres especiales innecesarios.
*   **Resultado:** Convierte tus datos crudos en todas las piezas posibles que un humano usaría para armar su clave.

---

## 📊 3. Niveles de Agresividad (Tiers)
SELIC opera en 4 niveles de profundidad:
*   **Nivel 1 (Básico):** Datos puros. Sin símbolos, sin leet. Alta probabilidad.
*   **Nivel 2 (Intermedio):** El nivel más "quirúrgico". Añade fechas, **Redundancia** (`adminadmin`), **Símbolos dobles** (`!!`) y parejas de palabras.
*   **Nivel 3 (Avanzado):** Todo lo anterior más **Leet Speak suave** (`4b3l`).
*   **Nivel 4 (Extremo):** Fuerza bruta total. Mezcla hasta 4 palabras, **Full Leet** y cruces caóticos de símbolos/números.

---

## 🔧 4. Sufijos Dinámicos (Anclas)

### ¿Qué son?
Los sufijos son fragmentos de texto (números, letras o símbolos) que SELIC pega al inicio y al final de cada palabra generada. Por ejemplo, si el dato es "Marco" y el sufijo es "2026", generará `Marco2026`, `2026Marco`, etc.

### Sufijos por defecto
SELIC viene con los siguientes sufijos activados: **`123, 2026, 2025`**.

### ¿Cómo cambiarlos?
Los sufijos se pueden controlar desde **tres lugares**:

#### A. Archivo de configuración (`selic.cfg`)
```ini
# Sufijos base (Los que SELIC prueba siempre por defecto)
default_suffixes = 123, 2026, 2025

# Sufijos extra (Para añadir anclas adicionales sin tocar los base)
extra_suffixes = SH, PRO, !
```
*   Si borras un sufijo de `default_suffixes`, SELIC dejará de usarlo permanentemente.
*   `extra_suffixes` se **suma** a los base. Úsalo para ataques específicos.

#### B. Durante la ejecución interactiva (CLI / Mini)
Al llegar a la pregunta de sufijos, verás:
```
Sufijos Base Configurados: 123, 2026, 2025
ENTER = Usar la lista Base | 'ninguno' = Borrar todos | O escribe para REEMPLAZAR
```
*   **ENTER:** Usa los sufijos base tal cual.
*   **`ninguno`** (mayúscula o minúscula): Anula todos los sufijos para esta ejecución.
*   **Escribir otros:** Reemplaza completamente la lista para esta ejecución.

#### C. En la GUI
La caja de texto "Sufijos" viene pre-rellenada con `123, 2026, 2025`. Puedes:
*   Dejarla como está para usar los defaults.
*   Borrar el contenido o escribir `ninguno` para no usar sufijos.
*   Escribir tus propios sufijos separados por coma.

> **Nota importante:** Los sufijos aceptan cualquier texto: números (`2026`), letras (`SH`, `PRO`) y símbolos (`!`, `@`). Todos van al mismo sistema.

---

## 🔑 5. Contraseñas Comunes Extras

SELIC incluye internamente una lista de contraseñas comunes (`123456`, `password`, `qwerty`, etc.) que se agregan automáticamente a cada wordlist generada.

Si deseas **añadir más contraseñas comunes** sin modificar el código, edita el archivo `selic.cfg`:
```ini
extra_common_passwords = micontraseña, clave123, empresa2026
```
Las contraseñas que añadas aquí se **sumarán** a la lista interna del sistema.

---

## 🎯 6. Patrones Avanzados (Estilo Crunch)

### ¿Qué son?
Los patrones te permiten definir **estructuras fijas** de contraseña donde cada marcador representa **una sola posición de carácter**. Funcionan de manera similar a la herramienta Crunch de Kali Linux.

### Marcadores disponibles

| Marcador | Significado | Pool de caracteres |
| :---: | :--- | :--- |
| `#` | 1 carácter del pool social (tus datos) | Caracteres individuales de tus datos |
| `%` | 1 número | 0-9 |
| `@` | 1 letra minúscula | a-z |
| `,` | 1 letra MAYÚSCULA | A-Z |
| `?` | 1 símbolo especial | !@#$%^&*_+-= |

### Texto fijo en patrones
Todo lo que **no sea** un marcador se mantiene como texto literal:
```
IV%%%CO  →  IV000CO, IV001CO, IV002CO... IV999CO
V#9      →  Va9, Vb9, Vc9... (usando caracteres de tus datos)
```

### Escape de marcadores
Si necesitas usar un marcador como texto literal, pon `\` delante:
```
precio\?%%%  →  precio?000, precio?001... precio?999
```
El `\?` se trata como el carácter `?` literal, no como un marcador de símbolo.

### Múltiples patrones
Puedes ingresar **varios patrones** a la vez:
*   **CLI Normal:** Se te preguntará patrón por patrón. Presiona ENTER sin escribir para terminar.
*   **GUI:** Escribe un patrón por línea (presiona Enter para separar líneas).

### ¿Qué ignora el patrón?
Los patrones son "autoritarios": **no** aplican Leet Speak, sufijos, complejidad ni mezcla. Generan la estructura exacta que definiste. Sin embargo, el motor heurístico normal sigue funcionando en paralelo y genera sus propias contraseñas con todas las reglas activas.

### Validación
Si un patrón no contiene al menos un marcador válido, SELIC mostrará un error antes de generar para evitar resultados inesperados.

---

## 🛡️ 7. Sistemas de Seguridad (Protección de Hardware)
SELIC 1.2.0 incluye tres capas de seguridad para evitar que dañes tu sistema o llenes tu disco por error:

### A. El "Freno Absurdo" (Seguro de Usuario)
Si una configuración va a generar más de **5,000 Millones** de contraseñas, el programa se bloqueará. 
*   **Cómo desbloquear:** Escribe `ACEPTO EL RIESGO` cuando te lo pida, o cambia `allow_extreme_generation = true` en `selic.cfg`.

### B. Sensor de Espacio en Disco (Pre-Generación)
Antes de empezar, SELIC calcula el peso estimado del archivo y lo compara con tu espacio libre.
*   **Aviso Naranja:** Te informará si el espacio está muy justo para que tomes precauciones.

### C. Freno de Pánico de 5GB (Real-Time)
Si durante la generación tu disco llega a tener menos de **5 GB libres**, SELIC detendrá la escritura inmediatamente.
*   **Objetivo:** Evitar que el sistema operativo se congele o se corrompa por falta de espacio.

---

## ⚙️ 8. El "Medidor de Gravedad" y Diagnóstico Inteligente

### A. Diagnóstico Dinámico (CLI)
Cuando terminas de ingresar datos, SELIC analiza la complejidad de tus ajustes y te recomienda un **Nivel de Agresividad**. 
*   No tienes que adivinar: el sistema te dirá si tu configuración es "Social Medium" o "Extreme".

### B. Medidor de Bloques (GUI)
La interfaz gráfica incluye un indicador de 4 bloques (estilo batería):
*   **Verde**: Nivel 1 - Ataque rápido y seguro.
*   **Amarillo**: Nivel 2 - Ataque estándar asistido.
*   **Naranja**: Nivel 3 - Ataque profundo de ingeniería social.
*   **Rojo**: Nivel 4 - Ataque crítico/exhaustivo (Wordlist muy pesada).

### C. Resumen de Confirmación
Antes de generar, las tres interfaces muestran un **resumen completo** de toda la configuración:
*   **CLI Normal:** Resumen en texto con opción de `ENTER` para generar o `R` para reiniciar la configuración (tus respuestas previas se mantienen como defaults).
*   **Mini:** Resumen con opción de `ENTER` para generar o `R` para volver a empezar desde cero.
*   **GUI:** Diálogo emergente con Sí/No que lista todos los parámetros antes de lanzar la generación.

---

## 📁 9. Archivo de Configuración (`selic.cfg`)
Puedes personalizar todo el comportamiento:

| Variable | Descripción |
| :--- | :--- |
| `default_suffixes` | Sufijos base que SELIC usa por defecto (ej: `123, 2026, 2025`). |
| `extra_suffixes` | Sufijos adicionales que se suman a los base. |
| `extra_common_passwords` | Contraseñas comunes extra que se suman a la lista interna. |
| `max_ram` | Cuánta memoria (GB) usar para limpiar duplicados. |
| `extreme_generation_limit` | Dónde quieres que salte el freno de seguridad. |
| `allow_extreme_generation` | Bypass para el freno de seguridad (`true`/`false`). |
| `[leet]` | Sección de mapeo Leet Speak personalizable (ej: `a=4`). |

---
*Manual actualizado para la versión 1.2.0 — Sufijos Dinámicos, Patrones Crunch y Diagnóstico Asistido.*
