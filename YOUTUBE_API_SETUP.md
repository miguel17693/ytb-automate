# 🔑 Configuración de APIs de YouTube

Esta guía te ayudará a obtener las credenciales necesarias para usar la YouTube Data API v3.

## 📋 Requisitos

- Una cuenta de Google
- 10-15 minutos

## 🎯 Paso 1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en el menú desplegable de proyectos (arriba a la izquierda)
4. Clic en **"Nuevo Proyecto"**
5. Nombre del proyecto: `Karaoke Automation` (o el que quieras)
6. Clic en **"Crear"**
7. Espera unos segundos a que se cree

## 🔌 Paso 2: Activar YouTube Data API v3

1. En el menú lateral, ve a **"APIs y servicios"** → **"Biblioteca"**
2. Busca: `YouTube Data API v3`
3. Haz clic en **"YouTube Data API v3"**
4. Clic en **"Habilitar"**
5. Espera a que se active (unos segundos)

## 🔑 Paso 3: Crear API Key (Para búsquedas)

Esta API Key se usa para buscar canciones populares.

1. Ve a **"APIs y servicios"** → **"Credenciales"**
2. Clic en **"Crear credenciales"** → **"Clave de API"**
3. Se creará tu API key
4. (Opcional pero recomendado) Clic en **"Restringir clave"**:
   - Nombre: `Karaoke API Key`
   - En "Restricciones de API", selecciona: **"YouTube Data API v3"**
   - Guarda
5. **Copia tu API key** (la necesitarás para el `.env`)

### Añadir a tu proyecto

Edita el archivo `.env`:
```env
YOUTUBE_API_KEY=AIzaSyAbCd1234567890EfGhIjKlMnOpQrStUvWxYz
```

## 📤 Paso 4: Configurar OAuth 2.0 (Para subir videos)

Solo necesario si quieres que el sistema suba videos automáticamente a YouTube.

### 4.1 Configurar Pantalla de Consentimiento

1. Ve a **"APIs y servicios"** → **"Pantalla de consentimiento de OAuth"**
2. Selecciona **"Externo"** → **"Crear"**
3. Rellena:
   - **Nombre de la aplicación**: `Karaoke Automation`
   - **Correo electrónico de asistencia**: tu email
   - **Correo de contacto del desarrollador**: tu email
4. Clic en **"Guardar y continuar"**
5. En **"Alcances"** (Scopes):
   - Clic en **"Añadir o quitar alcances"**
   - Busca y selecciona: `YouTube Data API v3 - .../auth/youtube.upload`
   - Guardar
6. Clic en **"Guardar y continuar"**
7. En **"Usuarios de prueba"**:
   - Clic en **"Añadir usuarios"**
   - Añade tu email de Google
   - Guardar
8. Clic en **"Guardar y continuar"**
9. Revisa y clic en **"Volver al panel"**

### 4.2 Crear Credenciales OAuth

1. Ve a **"APIs y servicios"** → **"Credenciales"**
2. Clic en **"Crear credenciales"** → **"ID de cliente de OAuth"**
3. Tipo de aplicación: **"Aplicación de escritorio"**
4. Nombre: `Karaoke Desktop Client`
5. Clic en **"Crear"**
6. Aparecerá un popup con tus credenciales
7. Clic en **"Descargar JSON"**
8. Renombra el archivo descargado a `client_secrets.json`
9. Mueve `client_secrets.json` a la raíz de tu proyecto

### 4.3 Primera Autenticación

La primera vez que uses la subida a YouTube:

1. Ejecuta: `python main.py`
2. Selecciona una opción que requiera subida
3. Se abrirá tu navegador automáticamente
4. Inicia sesión con tu cuenta de Google
5. Acepta los permisos (verás un warning de "app no verificada", es normal)
6. Clic en **"Avanzado"** → **"Ir a Karaoke Automation (no seguro)"**
7. Acepta los permisos
8. El navegador mostrará "The authentication flow has completed"
9. Ya está! Se guardará en `token.pickle` para futuros usos

## 📊 Límites de la API

### Cuota Diaria Gratuita

YouTube Data API v3 tiene límites:

- **Cuota diaria**: 10,000 unidades/día
- **Búsqueda**: ~100 unidades cada una
- **Subida de video**: ~1,600 unidades cada una

**Cálculos aproximados por día:**
- ~100 búsquedas de tendencias
- ~6 subidas de video
- Combinado: ~50 búsquedas + 3 subidas

### Solicitar Aumento de Cuota

Si necesitas más:

1. Ve a **"APIs y servicios"** → **"Cuotas"**
2. Selecciona **"YouTube Data API v3"**
3. Clic en **"Solicitar aumento de cuota"**
4. Rellena el formulario explicando tu uso
5. Espera aprobación (puede tardar días)

## 🔒 Seguridad

### ⚠️ IMPORTANTE: Proteger tus Credenciales

**NUNCA compartas públicamente:**
- ❌ API Key
- ❌ `client_secrets.json`
- ❌ `token.pickle`
- ❌ Archivo `.env`

**El `.gitignore` ya está configurado para excluir estos archivos.**

### Buenas Prácticas

1. **Usar diferentes proyectos** para desarrollo y producción
2. **Restringir API keys** a solo YouTube Data API v3
3. **Rotar credenciales** periódicamente
4. **Monitorear uso** en Google Cloud Console
5. **No hardcodear** API keys en el código

## 🧪 Verificar Configuración

### Test de API Key

```python
python -c "
from src.orchestrator import TrendingOrchestrator
from src.database import Database
from utils import load_config

config = load_config()
db = Database(config['paths']['database'])
orch = TrendingOrchestrator(config, db)
songs = orch.search_trending_songs()
print(f'✅ API Key funciona! Encontradas {len(songs)} canciones')
"
```

### Test de OAuth (si configurado)

```python
python -c "
from src.youtube_uploader import YouTubeUploader
from utils import load_config

config = load_config()
uploader = YouTubeUploader(config)
if uploader.youtube:
    print('✅ OAuth configurado correctamente')
else:
    print('❌ OAuth no configurado')
"
```

## 🆘 Solución de Problemas

### Error: "API key not valid"

- Verifica que copiaste la API key completa
- Asegúrate que está en `.env` como `YOUTUBE_API_KEY=...`
- Verifica que YouTube Data API v3 está habilitada
- Comprueba las restricciones de la API key

### Error: "The request cannot be completed because you have exceeded your quota"

- Has alcanzado el límite diario (10,000 unidades)
- Espera hasta mañana (se resetea a medianoche Pacific Time)
- O solicita aumento de cuota

### Error: "Access Not Configured"

- YouTube Data API v3 no está habilitada
- Ve al paso 2 y habilítala

### OAuth no funciona / "redirect_uri_mismatch"

- Asegúrate de usar **"Aplicación de escritorio"** (no "Aplicación web")
- Re-descarga `client_secrets.json`
- Borra `token.pickle` y vuelve a autenticar

### "This app isn't verified" en OAuth

- Es normal para apps en desarrollo
- Clic en "Avanzado" → "Ir a [nombre app] (no seguro)"
- Para producción, considera verificar la app con Google

## 📚 Referencias

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [API Key Best Practices](https://cloud.google.com/docs/authentication/api-keys)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [YouTube API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)

## ✅ Checklist Final

Antes de usar el sistema, verifica:

- [ ] Proyecto creado en Google Cloud Console
- [ ] YouTube Data API v3 habilitada
- [ ] API Key creada y copiada
- [ ] API Key añadida a `.env`
- [ ] (Opcional) Pantalla de consentimiento OAuth configurada
- [ ] (Opcional) `client_secrets.json` descargado
- [ ] Test de API Key exitoso

---

¿Problemas? Consulta la [documentación oficial](https://developers.google.com/youtube/v3/getting-started) o abre un [issue](https://github.com/miguel17693/ytb-automate/issues) 🚀
