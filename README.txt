

***

# SELIC v1.1.0 - The "Rock Solid" & Performance Update 💎⚡

¡Bienvenidos a la versión 1.1.0 de **SELIC (Social Engineering List Creator)**! 

En esta actualización hemos rediseñado el núcleo del motor para transformar a SELIC en una herramienta de grado profesional, capaz de manejar diccionarios masivos sin comprometer la estabilidad de tu sistema.

## 🌟 Novedades y Mejoras Principales

### 🧠 1. Nuevo Motor de Flujo (Streaming) y Deduplicación Híbrida
- **Cero bloqueos por RAM:** Gracias a la implementación de **Generadores Python (`yield`)**, SELIC ya no guarda millones de contraseñas en memoria. Escribe directamente en el disco línea por línea, permitiendo generar archivos de Gigabytes con un uso de RAM mínimo (<100MB).
- **Gestión de Memoria Inteligente:** Si superas el límite de `max_ram` (por defecto 3GB), SELIC activa automáticamente un proceso de limpieza usando el motor nativo de tu SO (**PowerShell Sort/Unique** en Windows o `sort -u` en Linux). ¡Tu PC nunca se colgará!

### ⚙️ 2. Motor de Heurística y Precisión
- **Límites de Seguridad:** SELIC ahora es inteligente. Si detecta más de **80 tokens** de entrada, limita la profundidad de mezcla para evitar que generes archivos infinitos por accidente.
- **Estimación Realista:** El algoritmo de cálculo ahora incluye un **"Factor de Penalización" (0.7)** para longitudes cortas, dándote una cifra mucho más honesta antes de iniciar la tarea.

### 📊 3. Panel de Estadísticas y Progreso en Vivo
- **Threaded Progress Bar:** Una barra de progreso fluida que muestra velocidad (líneas/seg) y peso del archivo en tiempo real sin saturar tu CPU.
- **Auditoría Final:** Al terminar, verás un análisis detallado: tiempo total, contraseñas únicas, longitud promedio y distribución de complejidad (alfanuméricas vs símbolos).

### 🔧 4. Correcciones y Mejoras de Calidad (UX)
- **Modo GUI (Beta):** Se añade soporte para interfaz gráfica básica mediante el flag `--gui`.
- **Configuración Externa:** SELIC ahora lee `selic.cfg` automáticamente, permitiendo predefinir tus preferencias y mapeos de Leet Speak.
- **Diccionarios Base:** Se inyectan automáticamente contraseñas comunes (top passwords globales) para garantizar efectividad inmediata.

## 💻 Instalación / Actualización

# Configura tu entorno de forma interactiva
python3 selic.py --setup

# Ejecuta el asistente tradicional
python3 selic.py -i

PRUEBA DE RENDIMIENTO POR CLI:
py social_wordlist.py --name "Juan Garcia Perez" --birth-year "19/05/2002" --decompose-numbers --digits --specials --leet --complexity 5 --max-length 20 --output passlist1.txt

py social_wordlist.py --name "uan Garcia Perez" --birth-year "19/05/2002" --decompose-numbers --digits --specials --no-leet --complexity 5 --max-length 20 --output passlist2.txt
