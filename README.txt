# SELIC 1.1.0 (Social Engineering List Creator) 🦂

SELIC es una herramienta avanzada para la generación de diccionarios de ingeniería social, optimizada para rendimiento y estabilidad.

> [!IMPORTANT]
> **Nota sobre el cambio de nombre:** Este proyecto anteriormente se conocía como `social_wordlist.py`. A partir de la versión 1.1.0, el motor ha sido renombrado a **SELIC** y el script principal ahora es `selic.py`.

## 📌 Versiones
*   **Versión Actual (v1.1.0):** [selic.py](./selic.py) - Recomendada por su bajo consumo de RAM y motor de streaming.
*   **Versión Antigua (v1.0.0):** Si por alguna razón necesitas la versión original (`social_wordlist.py`), puedes encontrarla en la sección de [Releases](https://github.com/TU_USUARIO/selic/releases/tag/v1.0.0).


## 💻 Instalación / Actualización

# Configura tu entorno de forma interactiva
python3 selic.py --setup

# Ejecuta el asistente tradicional
python3 selic.py -i

PRUEBA DE RENDIMIENTO POR CLI:
py social_wordlist.py --name "Juan Garcia Perez" --birth-year "19/05/2002" --decompose-numbers --digits --specials --leet --complexity 5 --max-length 20 --output passlist1.txt

py social_wordlist.py --name "uan Garcia Perez" --birth-year "19/05/2002" --decompose-numbers --digits --specials --no-leet --complexity 5 --max-length 20 --output passlist2.txt
