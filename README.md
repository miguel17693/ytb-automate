# 🎤 Sistema de Karaoke Automatizado

Sistema completamente automatizado para generar videos de karaoke de canciones populares de YouTube. Descarga canciones, separa voces/instrumental, aplica modificaciones sutiles, transcribe letras, genera videos con letras sincronizadas y sube a YouTube.

## ✨ Características

- 🔍 **Búsqueda de Tendencias**: Encuentra automáticamente canciones populares en YouTube (España)
- 📥 **Descarga Automática**: Descarga audio de YouTube con `yt-dlp`
- 🎵 **Separación Vocal**: Separa voces e instrumental con Spleeter
- 🔧 **Modificación Sutil**: Aplica cambios sutiles al instrumental (pitch, tempo, filtros)
- 📝 **Transcripción**: Transcribe letras con Whisper (OpenAI)
- ✨ **Generación de Karaoke**: Crea videos con:
  - Letras sincronizadas palabra por palabra
  - Resaltado de palabras en tiempo real
  - Visualizador de onda de audio
  - Fondos personalizables
  - Animaciones de entrada/salida
- 📤 **Subida a YouTube**: Sube automáticamente con metadata optimizada
- 💾 **Base de Datos**: SQLite para trackear canciones procesadas

## 🏗️ Estructura del Proyecto

```
ytb-automate/
├── src/
│   ├── database.py           # Gestión de BD SQLite
│   ├── utils.py              # Funciones auxiliares
│   ├── orchestrator.py       # Búsqueda de tendencias YouTube
│   ├── audio_modifier.py     # Modificación sutil del audio
│   ├── lyrics_generator.py   # Generación de archivos .ass
│   ├── video_generator.py    # Creación de videos con FFmpeg
│   ├── youtube_uploader.py   # Subida a YouTube
│   └── processor.py          # Pipeline principal
├── data/
│   ├── downloads/            # Audio descargado
│   ├── processed/            # Vocals/instrumental separados
│   ├── videos/               # Videos finales
│   └── backgrounds/          # Fondos para videos
├── db/
│   └── karaoke.db           # Base de datos SQLite
├── logs/                     # Logs del sistema
├── config.yaml              # Configuración principal
├── .env                     # Variables de entorno (API keys)
├── requirements.txt         # Dependencias Python
├── main.py                  # Punto de entrada
└── README.md
```

## 📋 Requisitos Previos

### Software Necesario

1. **Python 3.9 o superior**
2. **FFmpeg** (para procesamiento de audio/video)
   - Windows: Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)
   - Añade FFmpeg a tu PATH
3. **Git** (para clonar el repositorio)

### APIs Requeridas

1. **YouTube Data API v3**
   - Crea proyecto en [Google Cloud Console](https://console.cloud.google.com/)
   - Activa YouTube Data API v3
   - Crea API Key

2. **OAuth 2.0 Credentials** (para subir videos)
   - En el mismo proyecto de Google Cloud
   - Crea credenciales OAuth 2.0 (Desktop app)
   - Descarga `client_secrets.json`

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/miguel17693/ytb-automate.git
cd ytb-automate
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Nota importante sobre Torch (para Whisper):**
- Si tienes GPU NVIDIA con CUDA:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- Si no tienes GPU, el instalador por defecto usará CPU (más lento pero funcional)

### 4. Configurar FFmpeg

Verifica que FFmpeg está instalado:

```bash
ffmpeg -version
```

Si no lo está, descárgalo e instálalo:
- **Windows**: https://www.gyan.dev/ffmpeg/builds/
- Descomprime y añade la carpeta `bin` a tu PATH

### 5. Configurar variables de entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita `.env` y añade tu API key de YouTube:

```
YOUTUBE_API_KEY=tu_api_key_aqui
```

### 6. Configurar OAuth (opcional, para subir videos)

**NOTA: No necesitas esto para probar el sistema. La subida está deshabilitada por defecto.**

1. Descarga `client_secrets.json` de Google Cloud Console
2. Ponlo en la raíz del proyecto
3. La primera vez que ejecutes la subida, se abrirá un navegador para autenticarte

### 7. Ajustar configuración (opcional)

Edita `config.yaml` para personalizar:
- Región de YouTube (por defecto: España)
- Estilos de letras
- Colores del visualizador
- Modificaciones de audio
- etc.

## 🧪 Probar el Sistema (SIN subir a YouTube)

**¡Puedes probar todo el sistema sin configurar OAuth ni subir nada a YouTube!**

### Opción 1: Script de Test Rápido (Recomendado)

```bash
python test_system.py
```

Este script:
- ✅ Procesa una canción completa
- ✅ Genera el video de karaoke
- ✅ Guarda todo localmente en `data/videos/`
- ❌ NO sube nada a YouTube

**Recomendación**: Usa una canción CORTA (2-3 minutos) para la primera prueba.

### Opción 2: Usar el menú principal

```bash
python main.py
# Opción 2 → Ingresar URL → Video se guarda localmente
```

### Verificar que la subida está deshabilitada

En `config.yaml`:

```yaml
upload:
  auto_upload: false  # ← Debe estar en false (por defecto)
```

Con esto:
- ✅ Todo el procesamiento funciona normal
- ✅ Videos guardados en `data/videos/`
- ❌ NO se sube a YouTube

## 🎮 Uso

### Ejecutar el sistema

```bash
python main.py
```

### Menú Principal

El sistema presenta un menú interactivo con las siguientes opciones:

```
1. 🔍 Search for trending songs
   - Busca las canciones más populares en YouTube España
   - Añade nuevas canciones a la base de datos

2. 🎵 Process a specific YouTube URL
   - Procesa cualquier URL de YouTube manualmente
   - Útil para canciones específicas que quieras convertir

3. 📋 Process pending songs
   - Procesa todas las canciones pendientes en batch
   - Ejecuta el pipeline completo para cada canción

4. 📊 Show database stats
   - Muestra estadísticas de la base de datos
   - Canciones por estado, recientes, etc.

5. 🗑️ Clear failed songs
   - Resetea canciones fallidas a estado pendiente
   - Útil para reintentar después de corregir errores

0. ❌ Exit
```

### Ejemplo de Uso

#### Opción 1: Procesar canciones trending

```bash
python main.py
# Selecciona opción 1
# El sistema buscará tendencias y añadirá nuevas canciones
# Luego selecciona opción 3 para procesarlas
```

#### Opción 2: Procesar URL específica

```bash
python main.py
# Selecciona opción 2
# Ingresa: https://www.youtube.com/watch?v=VIDEO_ID
# El sistema procesará esa canción inmediatamente
```

## 🔧 Configuración Avanzada

### Modificación de Audio

En `config.yaml`, ajusta las modificaciones sutiles:

```yaml
audio:
  modification:
    enabled: true
    pitch_shift_semitones: 0.5  # Cambio de pitch (±0.5 semitones)
    tempo_change_percent: 2     # Cambio de tempo (2%)
    apply_filter: true          # Aplicar filtro sutil
```

### Estilos de Letras

Personaliza los estilos de karaoke:

```yaml
video:
  lyrics:
    font: "Arial"
    font_size: 48
    primary_color: "&H00FFFFFF"     # Blanco
    highlight_color: "&H0000FFFF"   # Amarillo
    border_size: 3
    fade_in_ms: 200
    fade_out_ms: 200
```

### Visualizador de Audio

```yaml
video:
  visualizer:
    type: "waveform"    # o "spectrum"
    color: "cyan"
    position: "bottom"  # top, bottom, center
    height: 200
```

## 📊 Pipeline de Procesamiento

El sistema ejecuta los siguientes pasos para cada canción:

1. **Descarga** 📥
   - Descarga audio de YouTube en formato WAV

2. **Separación** 🔀
   - Separa voces e instrumental con Spleeter
   - Genera `vocals.wav` e `instrumental.wav`

3. **Modificación** 🔧
   - Aplica cambios sutiles al instrumental
   - Pitch shift, tempo change, filtros

4. **Transcripción** 📝
   - Transcribe letras de la vocal con Whisper
   - Genera archivo SRT con timestamps

5. **Generación de Letras** ✨
   - Convierte SRT a formato ASS
   - Añade estilos y efectos de karaoke

6. **Generación de Video** 🎬
   - Combina instrumental modificado
   - Añade visualizador de audio
   - Superpone letras con resaltado
   - Renderiza video final MP4

7. **Subida** 📤 (opcional)
   - Sube video a YouTube
   - Genera título, descripción y tags optimizados

## ⚙️ Modelos y Calidad

### Whisper (Transcripción)

Modelos disponibles (ajustar en `config.yaml`):

- `tiny`: Rápido, menor precisión
- `base`: Balance razonable (por defecto)
- `small`: Mejor precisión
- `medium`: Muy buena precisión
- `large`: Máxima precisión (requiere mucha RAM/VRAM)

### Spleeter (Separación)

Configurado para 2 stems (vocals + accompaniment).

**Nota**: Spleeter requiere bastante RAM. Si tienes problemas, considera usar menos canciones simultáneas.

## 🐛 Solución de Problemas

### Error: "FFmpeg not found"

- Verifica que FFmpeg esté instalado: `ffmpeg -version`
- Añade FFmpeg a tu PATH del sistema

### Error: "CUDA out of memory" (Whisper)

- Usa un modelo más pequeño: `tiny` o `base`
- O desactiva CUDA editando el código para forzar CPU

### Error: "YouTube API quota exceeded"

- La API de YouTube tiene límites diarios
- Espera 24h o crea otro proyecto en Google Cloud

### Error: "Spleeter separation failed"

- Verifica que tienes suficiente RAM (mínimo 4GB libres)
- Prueba con canciones más cortas primero

### Videos sin audio

- Verifica que el archivo de audio existe
- Revisa los logs en `logs/karaoke.log`

## ⚠️ Advertencias Legales

**Este proyecto es para fines educativos y de investigación.**

- ⚖️ **Derechos de Autor**: Procesar y subir música con derechos de autor puede violar las leyes de copyright
- 🎵 **Content ID**: YouTube puede detectar y reclamar/bloquear videos con música con derechos
- 💰 **Monetización**: NO monetices videos generados sin los derechos apropiados
- 📜 **Licencias**: Solo usa música que tengas permiso para usar

**Recomendaciones**:
- Usa con música de dominio público o Creative Commons
- Obtén licencias apropiadas para música con derechos
- Marca videos como "privados" o "no listados" para uso personal
- Este sistema NO garantiza evasión de Content ID

## 🤝 Contribuciones

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Próximas Mejoras

- [ ] Soporte para Demucs (mejor separación que Spleeter)
- [ ] Interfaz web con Flask/FastAPI
- [ ] Scheduler automático (cron job)
- [ ] Fondos generados con IA (Stable Diffusion)
- [ ] Soporte para múltiples idiomas
- [ ] Detección automática de idioma
- [ ] Cache de modelos de Whisper
- [ ] Procesamiento paralelo de múltiples canciones
- [ ] Métricas y analytics

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Miguel** - [@miguel17693](https://github.com/miguel17693)

## 🙏 Agradecimientos

- OpenAI Whisper - Transcripción de audio
- Spleeter (Deezer) - Separación de fuentes
- yt-dlp - Descarga de YouTube
- FFmpeg - Procesamiento multimedia
- Google YouTube API - Búsqueda y subida

---

¿Preguntas? Abre un [issue](https://github.com/miguel17693/ytb-automate/issues) 🚀
