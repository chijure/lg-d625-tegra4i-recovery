# Entrada de firmware local

`t148_nvflash_miniloader.bin` se extrae localmente de la versión revisada de
`nvflash.exe`. No se incluye en Git. El generador verifica longitud y SHA256
antes de aplicar offsets. Consultar `utils/extract_miniloader.py`.
