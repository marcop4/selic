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

#### En Linux / Mac:
*   **Modo Interactivo (Recomendado):** `python3 selic.py -i`
*   **Modo Mini (Rápido):** `python3 selic_mini.py`

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

## 🛡️ 4. Sistemas de Seguridad (Protección de Hardware)
SELIC 1.2.0 incluye tres capas de seguridad para evitar que dañes tu sistema o llenes tu disco por error:

### A. El "Freno Absurdo" (Seguro de Usuario)
Si una configuración va a generar más de **5,000 Millones** de contraseñas, el programa se bloqueará. 
*   **Cómo desbloquear:** Escribe `ACEPTO EL RIESGO` cuando te lo pida, o cambia `allow_extreme_generation = true` en `selic.cfg`.

### B. Sensor de Espacio en Disco (Pre-Generación)
Antes de empezar, SELIC calcula el peso estimado del archivo y lo compara con tu espacio libre.
*   **Aviso Naranja:** Te informará si el espacio está muy justo para que tomes precauciones.

### C. Freno de Pánico de 5GB (Real-Time)
Si durante la generación tu disco llega a tener menos de **5 GB libres**, SELIC detendrá la escritura inmediatamente.
*   **Objetivo:** Evitar que el sistema operativo (Windows/Linux) se congele o se corrompa por falta de espacio. Guardará lo que lleve hecho hasta ese momento.

---

## ⚙️ 5. El "Termómetro" y el Estimador
En el modo manual de `selic.py`, verás un **Nivel Proyectado**. 
*   Si tus ajustes manuales equivalen a un ataque masivo, el termómetro se pondrá en **Nivel 4 (Extremo)**. 
*   El estimador de tiempo y cantidad tiene un margen de seguridad del 10%, por lo que la cifra que veas suele ser un poco más alta de lo que realmente terminará siendo, dándote un margen de maniobra real.

---

## 📁 6. Archivo de Configuración (`selic.cfg`)
Puedes personalizar todo el comportamiento:
*   **`max_ram`**: Cuánta memoria usar para limpiar duplicados.
*   **`extreme_generation_limit`**: Dónde quieres que salte el freno de seguridad.
*   **`leet_mappings`**: Cambia qué letras se reemplazan por qué números.

---
*Manual actualizado para la versión 1.2.0 Oficial - Seguridad y Precisión Quirúrgica.*
