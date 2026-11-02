# Portable Environment Packager

Conjunto de utilitarios para clonación, empaquetado y portabilización de entornos de desarrollo aislados en Windows. Genera paquetes autocontenidos calculando manifiestos de integridad criptográfica SHA-256 sin dependencia de rutas absolutas.

---

## Arquitectura y Componentes

- **Empaquetador:** `empaquetar_antigravity.py` para recolección de binarios y dependencias.
- **Integridad:** Verificación mediante tablas hash SHA-256.
- **Lanzadores:** Scripts PowerShell y Batch con rutas relativas basadas en `%USERPROFILE%` y `$PSScriptRoot`.

---

## Instrucciones de Uso

```powershell
# Generación de paquete portable
python empaquetar_antigravity.py --output D:\PortableEnv
```

---

## Consideraciones de Seguridad

- Este repositorio almacena código fuente, utilitarios de prueba y documentación técnica de ingeniería.
- Todas las credenciales, llaves privadas y variables de entorno deben suministrarse de forma local mediante archivos no versionados.
- Las herramientas de auditoría contenidas deben utilizarse exclusivamente en entornos autorizados y laboratorios de prueba.

---

**Autor:** Security Analyst  
**Licencia:** Uso Privado / Propietario
