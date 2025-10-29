# 🚀 Guía de Inicio Rápido

## Primeros Pasos (5 minutos)

### 1. Instalar Dependencias Básicas

**Necesitas:**
- Python 3.9+ instalado
- FFmpeg instalado y en PATH

**Verificar instalación:**
```bash
python --version  # Debe ser 3.9 o superior
ffmpeg -version   # Debe mostrar información de FFmpeg
```

### 2. Configurar el Proyecto

**Opción A: Script automático (Windows)**
```bash
setup.bat
```

**Opción B: Script automático (Linux/Mac)**
```bash
chmod +x setup.sh
./setup.sh
```

**Opción C: Manual**
```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
cp .env.example .env
```

### 3. Obtener YouTube API Key

1. Ve a https://console.cloud.google.com/
2. Crea un nuevo proyecto (o usa uno existente)
3. Activa "YouTube Data API v3"
4. Ve a "Credenciales" → "Crear credenciales" → "Clave de API"
5. Copia la API key

### 4. Configurar API Key

Edita el archivo `.env`:
```env
YOUTUBE_API_KEY=tu_api_key_aqui
```

### 5. Primera Prueba (SIN subir a YouTube)

**Opción A: Test Automático (Recomendado)**

```bash
python test_system.py
```

Este script te guiará paso a paso y NO subirá nada a YouTube.

**Opción B: Menú Principal**

```bash
python main.py
```

Selecciona opción **2** para procesar una URL específica.

**Importante:**
- ✅ El video se guardará en `data/videos/`
- ❌ NO se subirá a YouTube (está deshabilitado por defecto)
- 🎵 Usa una canción CORTA (2-3 minutos) primero

Ejemplo de URL de prueba:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### 📖 Para más detalles sobre testing:

Ver **`TESTING.md`** para guía completa de testing sin YouTube.

## ⚙️ Checklist de Verificación

Antes de procesar canciones, verifica:

- [ ] Python 3.9+ instalado
- [ ] FFmpeg instalado y en PATH
- [ ] Dependencias instaladas (`pip list | grep whisper`)
- [ ] `.env` configurado con YouTube API key
- [ ] Al menos 4GB de RAM libre
- [ ] Espacio en disco (mínimo 5GB por canción)

## 🎯 Uso Básico

### Procesar una Canción Específica

```bash
python main.py
# Opción 2 → Ingresar URL → Esperar
```

### Buscar Tendencias

```bash
python main.py
# Opción 1 → Buscar tendencias
# Opción 3 → Procesar pendientes
```

## ⏱️ Tiempos Estimados

Para una canción de 3 minutos:

| Paso | Tiempo (CPU) | Tiempo (GPU) |
|------|--------------|--------------|
| Descarga | 30s | 30s |
| Separación (Spleeter) | 2-3 min | 1 min |
| Transcripción (Whisper base) | 1-2 min | 30s |
| Generación video | 2-3 min | 2-3 min |
| **TOTAL** | **~8-10 min** | **~4-5 min** |

## 🔧 Soluciones Rápidas

### Error: "FFmpeg not found"
```bash
# Windows: Descargar de https://www.gyan.dev/ffmpeg/builds/
# Añadir bin\ a PATH del sistema

# Linux
sudo apt install ffmpeg

# Mac
brew install ffmpeg
```

### Error: "No module named 'whisper'"
```bash
pip install openai-whisper
```

### Error: "YouTube API quota exceeded"
- Has alcanzado el límite diario de la API
- Espera 24 horas o crea otro proyecto

### Spleeter muy lento
- Es normal en CPU
- Usa canciones más cortas (<3 min)
- O considera usar GPU

### Whisper muy lento
```yaml
# En config.yaml, cambia:
audio:
  transcription:
    model: "tiny"  # Más rápido, menos preciso
```

## 📁 Archivos Importantes

```
.env              → API keys (¡NO subir a Git!)
config.yaml       → Configuración principal
main.py           → Ejecutar aquí
logs/karaoke.log  → Ver errores aquí
```

## 🎨 Personalización Rápida

### Cambiar Colores de Letras

Edita `config.yaml`:
```yaml
video:
  lyrics:
    primary_color: "&H00FFFFFF"    # Blanco
    highlight_color: "&H0000FFFF"  # Amarillo
```

**Formato de color ASS: `&HAABBGGRR` (hex invertido)**
- Blanco: `&H00FFFFFF`
- Amarillo: `&H0000FFFF`
- Rojo: `&H000000FF`
- Verde: `&H0000FF00`
- Azul: `&H00FF0000`

### Cambiar Visualizador

```yaml
video:
  visualizer:
    type: "spectrum"  # o "waveform"
    color: "magenta"  # cyan, magenta, yellow, green, etc.
```

## 🎓 Siguiente Nivel

Una vez que funcione la prueba básica:

1. **Buscar tendencias**: Usa opción 1 del menú
2. **Procesar por lotes**: Usa opción 3 del menú
3. **Configurar OAuth**: Para subida automática a YouTube
4. **Ajustar calidad**: Prueba modelo Whisper `small` o `medium`
5. **Personalizar estilos**: Experimenta con `config.yaml`

## 💡 Tips

- **Empieza con canciones cortas** (2-3 min) para probar
- **Revisa los logs** si algo falla (`logs/karaoke.log`)
- **Usa Whisper 'base'** para balance velocidad/calidad
- **Desactiva modificación de audio** si no la necesitas
- **Videos en 'private'** por defecto (evita problemas copyright)

## 🆘 ¿Necesitas Ayuda?

1. Revisa `logs/karaoke.log` para errores detallados
2. Consulta el README.md completo
3. Abre un issue en GitHub

## 🎉 ¡Listo!

Ya deberías estar generando tus primeros karaokes. ¡Disfruta! 🎤
