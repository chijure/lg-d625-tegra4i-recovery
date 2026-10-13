# tegrarcm y soporte T148

Base: https://github.com/NVIDIA/tegrarcm

Commit: `f6a46f1b342fe5ff531281e605b52b2a604a8aac`.

`tegrarcm-t148.patch` conserva las modificaciones usadas durante la
investigación: PID T148, formato RCM 20.1, NV3P v1, lecturas propias y
diagnósticos. `compat.h` y `config.h` soportan la compilación MinGW64.

La opción histórica `--rawwrite` de este host no espera el nuevo readback de
escritura. Para restaurar, usar el cliente Python `utils/nv3p.py`; tegrarcm
se usa para la carga inicial mediante `--rawread`.

Aplicar el parche a la revisión fijada en una copia local de trabajo.
`build-mingw.sh` compila sin acceder al dispositivo.

Requiere MSYS2 MinGW64 con gcc/g++, libusb, Crypto++ y pkg-config.
Desde la terminal MinGW64:

```bash
git clone https://github.com/NVIDIA/tegrarcm.git /ruta/tegrarcm
git -C /ruta/tegrarcm checkout f6a46f1b342fe5ff531281e605b52b2a604a8aac
git -C /ruta/tegrarcm apply /ruta/lg-d625-tegra4i-recovery/host/tegrarcm-t148.patch
bash host/build-mingw.sh /ruta/tegrarcm
```

El script fija las rutas de herramientas y pkg-config a MinGW64. El host
recompilado se conserva fuera de Git; se comprueba compilación y CLI offline.
El ejecutable usado en la recuperación original queda en el archivo privado.
