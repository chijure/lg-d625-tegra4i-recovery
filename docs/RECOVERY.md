# Recuperación reproducible

Estos pasos corresponden al perfil y hashes de la unidad recuperada. Un
firmware o layout distinto requiere validar primero sus propios parámetros.
El código público conserva los límites y originales del caso probado.

## 1. Entorno e insumos

En PowerShell, desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe utils/extract_miniloader.py C:\ruta\nvflash.exe
.\.venv\Scripts\python.exe utils/prepare_backups.py C:\ruta\bct_raw_check.bin C:\ruta\EBT_live_20260925_orig.bin
.\.venv\Scripts\python.exe utils/build_payload.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La extracción acepta solamente el nvflash de hash fijado y no ejecuta ese
archivo. El generador debe reproducir exactamente el hash de `evidence/payload.json`.
El archivo de nombre histórico `PRISTINE_backup.cfg` no sustituye al volcado
crudo verificado: se descubrió que había sido sobrescrito.

Proporcionar el host tegrarcm T148 en `private/tools/`, con sus DLL, o pasar
su ruta a `utils/load_recovery.ps1`. Para construirlo desde fuente, ver
[host/UPSTREAM.md](../host/UPSTREAM.md). La guía se probó en Windows con WinUSB;
la portabilidad completa a Linux no se ha probado en hardware.

## 2. Entrar en APX y cargar solo en RAM

Con la batería cargada y colocada, desconectar USB, reiniciar con la batería
y mantener Vol+ y Vol− al conectar. El dispositivo probado enumera
`0955:7714`, APX. El controlador usado fue WinUSB.

```powershell
.\utils\load_recovery.ps1
```

La carga inicial devuelve 12 sectores del primer slot BCT. Las siguientes
operaciones reutilizan el miniloader cargado; no requieren reiniciar entre
cada comando. Reiniciar borra el código de recuperación de RAM.

## 3. Respaldar el estado actual

```powershell
.\.venv\Scripts\python.exe utils/nv3p.py 128 1920 private/backups/bct-current.bin
.\.venv\Scripts\python.exe utils/nv3p.py 12288 1680 private/backups/rbl-current.bin
.\.venv\Scripts\python.exe utils/nv3p.py 24576 1680 private/backups/ebt-current.bin
.\.venv\Scripts\python.exe utils/nv3p.py 4096 1 private/backups/scratch-sector4096-before.bin
```

El cliente crea nuevos archivos y se niega a truncar uno existente. Las
unidades son sectores lógicos de 512 bytes del miniloader, no sectores de
Linux ni las unidades de 4096 bytes del nvflash histórico.

## 4. Probar la escritura y devolver el sector de prueba

Crear un archivo `out/pattern512.bin` con `bytes(range(256))*2` y usar:

```powershell
.\.venv\Scripts\python.exe utils/nv3p.py 4096 1 out/pattern512.bin --write-verified
.\.venv\Scripts\python.exe utils/nv3p.py 4096 1 out/pattern-readback.bin
.\.venv\Scripts\python.exe utils/nv3p.py 4096 1 private/backups/scratch-sector4096-before.bin --write-verified
.\.venv\Scripts\python.exe utils/nv3p.py 4096 1 out/scratch-restored.bin
```

Comparar los archivos byte por byte: patrón contra lectura, y respaldo contra
sector devuelto. La selección del sector 4096 como zona sin uso se verificó
en la unidad documentada; no asumir ese layout para otros modelos.

## 5. Restaurar los originales revisados

Una vez verificado el escritor y respaldado el estado previo:

```powershell
.\.venv\Scripts\python.exe utils/nv3p.py 12288 1680 private/backups/bootloader-original.bin --write-verified
.\.venv\Scripts\python.exe utils/nv3p.py 128 1920 private/backups/bct-original-60-slots.bin --write-verified
```

El dispositivo envía una lectura de cada sector escrito. El host compara
todos sus bytes antes de permitir la siguiente escritura. Las fuentes
originales también deben coincidir con los hashes fijados. No se escribe EBT.

## 6. Verificar todo y probar Android

```powershell
.\.venv\Scripts\python.exe utils/nv3p.py 128 1920 out/bct-final.bin
.\.venv\Scripts\python.exe utils/nv3p.py 12288 1680 out/rbl-final.bin
.\.venv\Scripts\python.exe utils/nv3p.py 24576 1680 out/ebt-final.bin
Get-FileHash out/bct-final.bin,out/rbl-final.bin,out/ebt-final.bin -Algorithm SHA256
```

Comparar contra el perfil y los originales completos. Después, desconectar
USB, retirar/recolocar la batería y encender solo con Power, sin volumen.
En el caso probado apareció LG, después el indicador de batería baja y,
tras cargarla, Android. No se hizo factory reset ni se borraron datos.
