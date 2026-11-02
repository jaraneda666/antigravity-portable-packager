"""
# Tool: empaquetar_antigravity.py

## Metadata
- Nombre: empaquetar_antigravity.py
- Versión: 1.1
- Lenguaje: Python
- Creada en proyecto: Antigravity_portable
- Fecha de creación: 2026-10-06
- Descripción: Automatiza el empaquetado, clonación y portabilización de la instalación completa de Antigravity (IDE, CLI agy, configuraciones en .gemini con GEMINI.md, proyectos del workspace y herramientas), generando lanzadores independientes y manifiesto de integridad SHA-256.
- Parámetros:
    --dest: Directorio de destino para la estructura portable (default: output/antigravity_portable_dist).
    --skip-binaries: Omitir los binarios pesados del IDE para empaquetar solo configuración, reglas y datos.
    --compress: Generar automáticamente archivo comprimido (.zip).
- Dependencias: Python 3.8+ (módulos estándar: os, sys, shutil, hashlib, argparse, pathlib, json).

## Uso
python empaquetar_antigravity.py --dest ../output/antigravity_portable_dist --compress
"""

import os
import sys
import time
import shutil
import hashlib
import argparse
from pathlib import Path
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXCLUDE_PATTERNS = [
    # Directorios de salida para evitar anidación infinita
    "output",
    "antigravity_portable_dist",
    # Respaldos obsoletos y duplicados en .gemini
    "antigravity-backup",
    # Caches de navegador de Chrome/Electron
    "Cache",
    "Code Cache",
    "GPUCache",
    "DawnCache",
    "ShaderCache",
    "Crashpad",
    "CrashpadMetrics",
    # Archivos temporales, compilados y de bloqueo
    "*.log",
    "*.tmp",
    "*.pyc",
    "*.zip",
    ".git",
    "knowledge.lock",
    "__pycache__",
]

def calcular_sha256(filepath):
    """Calcula el hash SHA-256 de un archivo binario."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def deberia_excluir(rel_path_str, name):
    """Determina si un archivo o directorio debe excluirse del paquete."""
    norm_rel = rel_path_str.replace("\\", "/").lower()
    norm_name = name.lower()
    
    for pattern in EXCLUDE_PATTERNS:
        pat_lower = pattern.lower()
        if pat_lower.startswith("*."):
            ext = pat_lower[1:]
            if norm_name.endswith(ext):
                return True
        elif f"/{pat_lower}/" in f"/{norm_rel}/" or norm_name == pat_lower:
            return True
    return False

def copiar_arbol_seguro(origen, destino, nombre_componente):
    """Copia una jerarquía de archivos omitiendo patrones excluidos y calculando inventario."""
    origen_path = Path(origen)
    destino_path = Path(destino)
    if not origen_path.exists():
        print(f"[-] ADVERTENCIA: Origen no encontrado para {nombre_componente}: {origen}")
        return {}

    print(f"[+] Copiando {nombre_componente}...")
    print(f"    Origen : {origen}")
    print(f"    Destino: {destino}")
    destino_path.mkdir(parents=True, exist_ok=True)
    inventario = {}
    total_archivos = 0
    total_bytes = 0

    for root, dirs, files in os.walk(origen_path):
        rel_root = os.path.relpath(root, origen_path)
        
        # Filtrar directorios a ignorar en tiempo real
        dirs[:] = [d for d in dirs if not deberia_excluir(os.path.join(rel_root, d), d)]

        dest_dir = destino_path / rel_root if rel_root != "." else destino_path
        dest_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            rel_file_path = os.path.join(rel_root, f) if rel_root != "." else f
            if deberia_excluir(rel_file_path, f):
                continue
            
            src_file = Path(root) / f
            dst_file = dest_dir / f

            try:
                shutil.copy2(src_file, dst_file)
                try:
                    if time.localtime(dst_file.stat().st_mtime).tm_year < 1980:
                        os.utime(dst_file, None)
                except Exception:
                    pass
                size = dst_file.stat().st_size
                total_archivos += 1
                total_bytes += size
                h = calcular_sha256(dst_file)
                rel_portable = os.path.relpath(dst_file, destino_path.parent)
                inventario[rel_portable.replace("\\", "/")] = {
                    "sha256": h,
                    "size_bytes": size
                }
            except Exception as e:
                print(f"    [!] Error al copiar {src_file}: {e}")

    mb = total_bytes / (1024 * 1024)
    print(f"    -> [OK] {total_archivos} archivos transferidos ({mb:.2f} MB)\n")
    return inventario

def generar_lanzadores(base_dir):
    """Crea scripts lanzadores portables (.cmd y .ps1) que redefinen las rutas relativas."""
    base_path = Path(base_dir)

    # 1. Lanzador CMD para Antigravity IDE Portable
    launcher_ide_cmd = base_path / "iniciar_antigravity_portable.cmd"
    content_ide_cmd = (
        "@echo off\r\n"
        "title Antigravity Portable Launcher\r\n"
        "setlocal enabledelayedexpansion\r\n"
        "set PORTABLE_ROOT=%~dp0\r\n"
        "if \"%PORTABLE_ROOT:~-1%\"==\"\\\" set PORTABLE_ROOT=%PORTABLE_ROOT:~0,-1%\r\n"
        "\r\n"
        "set USER_CONFIG=%PORTABLE_ROOT%\\config\\.gemini\r\n"
        "set WORKSPACE_ROOT=%PORTABLE_ROOT%\\workspace\r\n"
        "set IDE_BIN=%PORTABLE_ROOT%\\bin\\Antigravity IDE\\Antigravity IDE.exe\r\n"
        "set AGY_BIN=%PORTABLE_ROOT%\\bin\\agy\\bin\r\n"
        "\r\n"
        "set PATH=%AGY_BIN%;%PATH%\r\n"
        "\r\n"
        "echo ========================================================\r\n"
        "echo       ANTIGRAVITY PORTABLE - LANZADOR DE ENTORNO        \r\n"
        "echo ========================================================\r\n"
        "echo Raiz Portable   : %PORTABLE_ROOT%\r\n"
        "echo Configuraciones : %USER_CONFIG%\r\n"
        "echo Workspace       : %WORKSPACE_ROOT%\r\n"
        "echo Binario IDE     : %IDE_BIN%\r\n"
        "echo ========================================================\r\n"
        "\r\n"
        "REM Sincronizar/vincular enlace de .gemini al perfil de usuario si no existe\r\n"
        "if not exist \"%USERPROFILE%\\.gemini\" (\r\n"
        "    echo [*] Configurando acceso rapido de .gemini en perfil local...\r\n"
        "    powershell -NoProfile -Command \"New-Item -ItemType SymbolicLink -Path \\\"$HOME\\.gemini\\\" -Target \\\"%USER_CONFIG%\\\" -ErrorAction SilentlyContinue | Out-Null; if (!(Test-Path \\\"$HOME\\.gemini\\\")) { Copy-Item -Path \\\"%USER_CONFIG%\\\" -Destination \\\"$HOME\\.gemini\\\" -Recurse -Force }\"\r\n"
        ")\r\n"
        "\r\n"
        "if not exist \"%IDE_BIN%\" (\r\n"
        "    echo [ERROR] No se encontro el ejecutable en: \"%IDE_BIN%\"\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "start \"\" \"%IDE_BIN%\" \"%WORKSPACE_ROOT%\"\r\n"
    )
    with open(launcher_ide_cmd, "w", encoding="utf-8") as f:
        f.write(content_ide_cmd)

    # 2. Script de Despliegue / Clonación en Equipo Nuevo (PowerShell)
    deploy_ps1 = base_path / "clonar_en_nuevo_equipo.ps1"
    content_deploy_ps1 = (
        "# =========================================================================\n"
        "# Script de Clonación y Despliegue en Nuevo Equipo — Antigravity Portable\n"
        "# =========================================================================\n"
        "[CmdletBinding()]\n"
        "param (\n"
        "    [switch]$SoloConfiguracion,\n"
        "    [switch]$IncluirBinarios = $true,\n"
        "    [switch]$CrearAccesosDirectos = $true\n"
        ")\n"
        "\n"
        "$PortableRoot = $PSScriptRoot\n"
        "$TargetProfile = $HOME\n"
        "$TargetGemini = Join-Path $TargetProfile \".gemini\"\n"
        "\n"
        "Write-Host \"=== Sincronizacion de Antigravity Portable ===\" -ForegroundColor Cyan\n"
        "Write-Host \"Directorio Origen : $PortableRoot\" -ForegroundColor Yellow\n"
        "Write-Host \"Perfil de Destino : $TargetProfile\" -ForegroundColor Green\n"
        "\n"
        "# 1. Sincronizar configuraciones (.gemini y GEMINI.md)\n"
        "$SourceGemini = Join-Path $PortableRoot \"config\\.gemini\"\n"
        "if (Test-Path $SourceGemini) {\n"
        "    Write-Host \"`n[+] Restaurando configuraciones en $TargetGemini...\" -ForegroundColor Green\n"
        "    if (!(Test-Path $TargetGemini)) { New-Item -ItemType Directory -Path $TargetGemini -Force | Out-Null }\n"
        "    Copy-Item -Path \"$SourceGemini\\*\" -Destination $TargetGemini -Recurse -Force\n"
        "    Write-Host \"[✓] Configuraciones (.gemini, GEMINI.md, skills y MCPs) sincronizadas.\" -ForegroundColor Green\n"
        "}\n"
        "\n"
        "# 2. Restaurar Binarios de IDE y CLI\n"
        "if ($IncluirBinarios -and (-not $SoloConfiguracion)) {\n"
        "    $TargetLocal = Join-Path $HOME \"AppData\\Local\"\n"
        "    $SourceAgy = Join-Path $PortableRoot \"bin\\agy\"\n"
        "    $SourceIDE = Join-Path $PortableRoot \"bin\\Antigravity IDE\"\n"
        "    \n"
        "    if (Test-Path $SourceAgy) {\n"
        "        $TargetAgy = Join-Path $TargetLocal \"agy\"\n"
        "        Write-Host \"[+] Restaurando CLI agy en $TargetAgy...\" -ForegroundColor Green\n"
        "        Copy-Item -Path $SourceAgy -Destination $TargetLocal -Recurse -Force\n"
        "    }\n"
        "    if (Test-Path $SourceIDE) {\n"
        "        $TargetPrograms = Join-Path $TargetLocal \"Programs\\Antigravity IDE\"\n"
        "        Write-Host \"[+] Restaurando Antigravity IDE en $TargetPrograms...\" -ForegroundColor Green\n"
        "        $ProgDir = Split-Path $TargetPrograms\n"
        "        if (!(Test-Path $ProgDir)) { New-Item -ItemType Directory -Path $ProgDir -Force | Out-Null }\n"
        "        Copy-Item -Path $SourceIDE -Destination $ProgDir -Recurse -Force\n"
        "    }\n"
        "}\n"
        "\n"
        "# 3. Workspace opcional\n"
        "$TargetDocs = Join-Path $HOME \"Documents\\Antigravity projects\"\n"
        "$SourceWorkspace = Join-Path $PortableRoot \"workspace\"\n"
        "if ((Test-Path $SourceWorkspace) -and (-not (Test-Path $TargetDocs))) {\n"
        "    Write-Host \"[+] Restaurando proyectos en $TargetDocs...\" -ForegroundColor Green\n"
        "    Copy-Item -Path $SourceWorkspace -Destination $TargetDocs -Recurse -Force\n"
        "}\n"
        "\n"
        "Write-Host \"`n[✓] ¡Despliegue y clonación finalizada con éxito en el nuevo equipo!\" -ForegroundColor Cyan\n"
    )
    with open(deploy_ps1, "w", encoding="utf-8") as f:
        f.write(content_deploy_ps1)

    print("[+] Lanzadores y scripts generados:")
    print(f"    - {launcher_ide_cmd.name}")
    print(f"    - {deploy_ps1.name}\n")

def empaquetar(dest_dir, skip_binaries=False, do_compress=False, zip_name="antigravity_portable"):
    """Ejecuta el empaquetado integral."""
    dest_path = Path(dest_dir).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)
    print(f"============================================================")
    print(f"      INICIANDO EMPAQUETADO PORTABLE DE ANTIGRAVITY        ")
    print(f"============================================================")
    print(f"Destino: {dest_path}\n")

    user_home = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    gemini_source = user_home / ".gemini"
    ide_source = user_home / "AppData" / "Local" / "Programs" / "Antigravity IDE"
    agy_source = user_home / "AppData" / "Local" / "agy"
    workspace_source = user_home / "Documents" / "Antigravity projects"

    inventario_global = {}

    # 1. Configuración .gemini (con GEMINI.md)
    inv = copiar_arbol_seguro(gemini_source, dest_path / "config" / ".gemini", "1. Configuraciones Globales (.gemini con GEMINI.md)")
    inventario_global.update(inv)

    # 2. Binarios del IDE y CLI
    if not skip_binaries:
        inv = copiar_arbol_seguro(ide_source, dest_path / "bin" / "Antigravity IDE", "2. Binarios Antigravity IDE (Runtime)")
        inventario_global.update(inv)

        inv = copiar_arbol_seguro(agy_source, dest_path / "bin" / "agy", "3. CLI agy (Ejecutables y librerías)")
        inventario_global.update(inv)
    else:
        print("[*] Omitiendo copia de binarios pesados (--skip-binaries activo).")

    # 3. Workspace Projects (preferencias, memoria, tools y proyectos)
    inv = copiar_arbol_seguro(workspace_source, dest_path / "workspace", "4. Workspace Projects (Proyectos, Tools y Memoria)")
    inventario_global.update(inv)

    # 4. Lanzadores
    generar_lanzadores(dest_path)

    # 5. Manifiesto SHA-256 (JSON y TXT)
    manifest_file_json = dest_path / "manifest_sha256.json"
    with open(manifest_file_json, "w", encoding="utf-8") as f:
        json.dump(inventario_global, f, indent=2, ensure_ascii=False)

    manifest_file_txt = dest_path / "manifest_sha256.txt"
    with open(manifest_file_txt, "w", encoding="utf-8") as f:
        f.write("# Manifiesto de Integridad Criptografica SHA-256 — Antigravity Portable\n\n")
        for ruta, datos in sorted(inventario_global.items()):
            f.write(f"{datos['sha256']}  {ruta}  ({datos['size_bytes']} bytes)\n")

    print(f"[+] Manifiesto JSON : {manifest_file_json.name}")
    print(f"[+] Manifiesto TXT  : {manifest_file_txt.name} ({len(inventario_global)} archivos auditados)")

    # 6. Compresión ZIP opcional
    if do_compress:
        archive_name = zip_name if zip_name else dest_path.name
        zip_output = dest_path.parent / f"{archive_name}.zip"
        print(f"\n[+] Normalizando fechas de archivos para compatibilidad ZIP...")
        for root, dirs, files in os.walk(dest_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    if time.localtime(os.stat(fp).st_mtime).tm_year < 1980:
                        os.utime(fp, None)
                except Exception:
                    pass
        print(f"[+] Generando archivo comprimido {zip_output} ... (esto puede tardar unos momentos)")
        shutil.make_archive(str(dest_path.parent / archive_name), 'zip', dest_path)
        print(f"[OK] Archivo comprimido generado exitosamente: {zip_output}")

    print("\n============================================================")
    print("      EMPAQUETADO FINALIZADO EXITOSAMENTE")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Empaquetador de Antigravity Portable")
    parser.add_argument("--dest", default=os.path.join(os.path.dirname(__file__), "..", "output", "antigravity_portable_dist"), help="Directorio destino")
    parser.add_argument("--skip-binaries", action="store_true", help="Omitir binarios pesados del IDE")
    parser.add_argument("--compress", action="store_true", help="Generar archivo .zip")
    parser.add_argument("--zip-name", default="antigravity_portable", help="Nombre base para el archivo comprimido (.zip)")
    args = parser.parse_args()

    empaquetar(args.dest, args.skip_binaries, args.compress, args.zip_name)
