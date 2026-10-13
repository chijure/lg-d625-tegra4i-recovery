# Próxima etapa: imágenes boot/recovery sin firma

## Punto de partida

Android arranca con BCT, RBL y EBT originales verificados. Conservar el tag
`recovery-v0.1.0` y el archivo privado de investigación antes de experimentar.
El cliente público de recuperación admite solamente las restauraciones
originales y el sector de prueba definidos en el perfil.

**El candidato v2 permitió arrancar la recovery stock con su firma alterada
en la unidad D62510c probada el 13 de octubre de 2026.** Fastboot reportó
`unlocked: yes` y `secure: no`, aceptó `fastboot boot`, y el usuario confirmó
la pantalla de recovery. Un flag de fastboot por sí solo no prueba que se
haya superado la verificación propietaria `[LGE_SECURITY]`; aquí también
se comprobó el arranque. TWRP, kernels modificados y otras unidades todavía
no se han probado.

## Hallazgos anteriores que deben retomarse

- Hay dos copias activas del bootloader, EBT y RBL. Cambiar solo una copia
  no demostró que el BootROM hubiera ejecutado el candidato.
- El BCT contiene hashes de los bootloaders. El cambio del hash RBL en sus
  60 copias dejó inválido el arranque y motivó esta recuperación.
- El chequeo histórico en el offset de archivo vivo `0x125e4`, de `beq` a `b`,
  se conserva como candidato offline en `research/unlock/candidate_patch.py`.
  No debe presentarse como un unlock funcional.
- El banner de firma puede aparecer por rutas distintas. Debe reconstruirse
  la cadena real desde el bootloader vivo cuyo SHA256 está en el perfil;
  el EBT de staging/USP tiene un hash distinto.
- La unidad reportó operating mode 3 y SBK no quemado. No asumir que el
  fallo de firma de LG implica fusibles seguros o que otra unidad comparte
  ese estado.

## Secuencia de investigación

1. Registrar estado normal: firmware, fastboot y hash de las imágenes stock.
2. Volver a analizar RBL/EBT original vivo, distinguiendo AVP y CCPLEX.
3. Identificar todas las decisiones que rechazan boot/recovery sin firma.
4. Construir un candidato offline con hash de entrada y diff exacto.
5. Probar una variable por vez y registrar qué copia ejecutó el dispositivo.
6. Conservar originales/restauración verificable durante cada prueba.

Trabajar en la rama `research/bootloader-unlock`. La recuperación verificada
debe seguir disponible aunque un candidato posterior falle.

## Instalación administrada por nvflash

La ayuda local de nvflash 4.10.1800 (`--cmdhelp --download`) indica
`--download <N/pname> <filename> --bl <bootloader> --go` para NvProduction.
El dispositivo reportó operating mode 3 antes de la recuperación; verificar
ese estado nuevamente antes de instalar. La variante `--updatebct BLINFO`
con blob corresponde a modo seguro PKC/SBK, según esa misma ayuda.

No editar manualmente el BCT ni instalar candidatos con `--rawdevicewrite`.
El flujo administrado debe mantener los metadatos de arranque coherentes;
esto no significa que los hashes del BCT puedan permanecer idénticos al
cambiar el bootloader. Leer y comparar el resultado de la operación.

El staging/USP tiene un prefijo de 28 bytes: el offset histórico `0x12600`
equivale a `0x125e4` en el respaldo vivo. El candidato offline ahora usa
el offset vivo y conserva la comprobación SHA256 de la entrada original.

### Prueba del 13 de octubre de 2026

El nvflash original cargó el servidor Wiko en RAM y leyó la tabla de
particiones. Reportó nuevamente modo 3 y SBK no quemado. Las lecturas
administradas de EBT (5) y RBL (4) contenían el bootloader original
SHA256 `10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7`.
La región de 60 copias del BCT coincidía con el respaldo recuperado.

El servidor Wiko no implementa `--resume --getbct` (estado 3,
`operation not implemented`); la lectura del área BCT completa sí funcionó.

Se ejecutó `nvflash --resume --download 5 <candidato-v2> --sync`.
El candidato SHA256
`c2c787a409ef6fd3ea01f9225dca4f40d81cf5164de631f9bb067bf4ff43541b`
cambia tres bytes: `88 b1` a `11 e0` en `0xec5e`, y `d0` a `e0` en
`0x125e5`. Nvflash informó transferencia de 860160 bytes y salida 0.
La conexión USB desapareció después del comando; los intentos inmediatos
de lectura respondieron `USB device not found`.

Se reinició físicamente y Android D62510c arrancó. Después, por ADB se
entró en fastboot y se ejecutó `fastboot boot recovery_test_badsig.img`.
La imagen stock tiene un byte de su firma alterado, con kernel y ramdisk
intactos; SHA256
`8c55f9f3b1f3298415d4d8c83a6191a9b2e414645927a297b2c019431841575a`.
Fastboot aceptó la carga y el usuario confirmó recovery con Android/menú.
La prueba fue en RAM; no instaló una nueva recovery ni borró userdata.

Tras un nuevo arranque APX se repitió el bootstrap original y las lecturas:

- EBT contiene exactamente los 860160 bytes del candidato v2.
- La partición RBL completa sigue idéntica al respaldo anterior.
- En las 60 copias originales del BCT, el hash EBT coincide con el AES-CMAC
  del candidato: `d32d749ea72110408fbe4861288892f2`.
- El hash RBL permanece intacto en esas 60 copias.
- En la primera de esas copias, solamente cambiaron los campos de 16 bytes
  en `0x310` (firma BCT) y `0x1308` (hash EBT). Nvflash también escribió una
  copia BCT en el bloque inicial; no se conservaron todos los bytes del
  área BCT, porque la actualización de integridad es parte de la instalación.

## Secuencia reproducible para esta unidad

Se necesita el nvflash original 4.10.1800, el servidor Wiko compatible,
el BCT original verificado y el respaldo vivo exacto de EBT. No distribuir
estos binarios privados ni usar un BCT de otra unidad. Mantener la batería
colocada durante APX.

```text
python research/unlock/candidate_patch.py bootloader-original.bin candidate-v2.bin --variant v2
nvflash --bct bct-original-slot.cfg --getpartitiontable ptable.txt --bl bootloader.bin --go
nvflash --resume --read 5 ebt-before.bin
nvflash --resume --read 4 rbl-before.bin
nvflash --resume --download 5 candidate-v2.bin --sync
```

Los nombres del ejemplo son rutas locales. `--bl bootloader.bin` carga el
servidor Wiko en RAM; `--download 5 candidate-v2.bin` instala el candidato
LG en EBT. No confundir los dos archivos. Comprobar los hashes y la tabla
de particiones antes de escribir. Después de `--sync` se perdió la
conexión: para leer y verificar se necesitó otro arranque APX y bootstrap.
La restauración de EBT debe usar el original con el mismo flujo
`--resume --download 5 bootloader-original.bin --sync`, para que nvflash
vuelva a gestionar la integridad. No usar una escritura raw del original
con metadatos del candidato.
