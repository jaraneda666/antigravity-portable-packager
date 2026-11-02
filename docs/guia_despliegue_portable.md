# Guía de Despliegue y Uso — Antigravity Portable

Esta guía documenta la estructura, opciones de despliegue y procedimientos para ejecutar la distribución portable de Antigravity en otro equipo con Windows (10 u 11).

---

## 1. Estructura del Paquete Distribuible

El paquete generado en `output/antigravity_portable_dist/` contiene:

```text
antigravity_portable_dist/
├── bin/
│   ├── Antigravity IDE/       → Binarios del runtime del IDE (Electron / Chromium)
│   └── agy/                   → Binarios de la interfaz de línea de comandos (CLI)
├── config/
│   └── .gemini/               → Configuración global completa:
│       ├── GEMINI.md          → Directivas permanentes de comportamiento del sistema
│       ├── config/            → AGENTS.md, mcp_config.json y plugins
│       ├── skills/            → Skills globales instalados
│       └── antigravity-ide/   → user_settings.pb y configuraciones locales
├── workspace/                 → Copia íntegra de proyectos, herramientas y memoria:
│   ├── AGENTS.md              → Directivas del workspace
│   ├── tools/                 → Scripts de automatización y tools globales
│   ├── memory/                → Historial episódico de aprendizaje y preferencias
│   └── [Proyectos]/           → Repositorios y código de proyectos activos
├── iniciar_antigravity_portable.cmd → Lanzador directo agnóstico a la ruta
├── clonar_en_nuevo_equipo.ps1       → Script de instalación / clonación en disco local
├── manifest_sha256.json             → Manifiesto de integridad criptográfica (JSON)
└── manifest_sha256.txt              → Manifiesto en texto plano para auditoría rápida
```

---

## 2. Modalidades de Uso en el Nuevo Equipo

### Modalidad A — Ejecución Portable Directa (Plug & Play)
*Ideal para utilizar desde un pendrive, disco externo o sin modificar la instalación del sistema operativo.*

1. Conectá el almacenamiento externo en la nueva máquina.
2. Ingresá a la carpeta `antigravity_portable_dist`.
3. Hacé doble clic en **`iniciar_antigravity_portable.cmd`**.
   - El script detecta la ruta actual de la unidad (`%~dp0`).
   - Vincula automáticamente `.gemini` y `GEMINI.md` para que el IDE lea las reglas.
   - Abre `Antigravity IDE` cargando directamente el workspace con todos los proyectos y herramientas listos para trabajar.

### Modalidad B — Clonación Completa al Nuevo Equipo
*Ideal para dejar la máquina nueva exactamente idéntica a tu estación de trabajo actual.*

1. Copiá la carpeta del paquete al nuevo equipo.
2. Abrí una ventana de PowerShell y ejecutá:
   ```powershell
   .\clonar_en_nuevo_equipo.ps1
   ```
3. El script se encarga de:
   - Sincronizar `.gemini` y `GEMINI.md` en `$HOME\.gemini`.
   - Restaurar `agy` CLI en `$HOME\AppData\Local\agy`.
   - Restaurar `Antigravity IDE` en `$HOME\AppData\Local\Programs\Antigravity IDE`.
   - Clonar el workspace en `$HOME\Documents\Antigravity projects`.

---

## 3. Verificación de Integridad (SHA-256)

Para auditar que ningún archivo se corrompió durante la transferencia o compresión:

```powershell
# En PowerShell:
Get-FileHash -Path "bin\Antigravity IDE\Antigravity IDE.exe" -Algorithm SHA256
```
Cotejá el valor resultante con la entrada correspondiente en `manifest_sha256.txt`.

---

## 4. Consideraciones de Seguridad y Buenas Prácticas
- **Llaves SSH y Credenciales:** Si tenés claves privadas SSH (`id_ed25519`), asegurate de copiarlas únicamente a través de canales seguros a tu nuevo equipo (`$HOME\.ssh\`).
- **Antivirus de Windows:** Al ejecutar por primera vez desde un disco extraíble, es posible que Windows Defender SmartScreen pida confirmación para iniciar el ejecutable (`Más información` -> `Ejecutar de todas formas`).
