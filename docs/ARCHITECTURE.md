# Arquitectura y errores resueltos

## Procesador de arranque

El código RCM/miniloader ejecuta en el procesador auxiliar ARM7, no en los
Cortex-A9 que ejecutan Android. Los generadores deben emitir ARMv4T/Thumb-1.
La forma original de `BL` consta de dos medias palabras. Su coincidencia con
ciertas codificaciones Thumb-2 no prueba que ARM7 acepte `B.W`.

Los saltos fuera del rango de Thumb `B` usan `LDR` de un destino literal
alineado, seguido de `BX`; el bit 0 del destino conserva el estado Thumb.
El NOP compatible es `mov r8,r8` (`0x46c0`), no el hint Thumb-2 `0xbf00`.

## El borrado que destruía el código agregado

El scatter loader original en `0x4000e0d4` consulta una tabla en
`[0x4001de9c, 0x4001debc)`. Su segunda entrada especifica:

```
destination = 0x4001e61c
length      = 0x6728
handler     = 0x4000e134
```

El handler pone a cero **[0x4001e61c, 0x40024d44)**. Agregar código justo
después del archivo original, en `0x4001e620`, lo colocaba dentro de BSS:
se borraba antes de recibir el primer comando. Un margen de 256 bytes tampoco
evitaba ese rango. El dispatcher además copia 244 bytes a `0x4001e61c`.

## Layout verificado del payload

| Dirección IRAM | Uso |
| --- | --- |
| `0x4000e000` | Entrada original del miniloader |
| `0x4001d6d0` | Handler original sustituido por diez bytes LDR/BX/literal |
| `0x40026f64` | Tope de pila original |
| `0x40028000` | Despacho de comandos propios |
| `0x40028200` | Lector eMMC |
| `0x40029400` | Escritor con lectura posterior |
| `0x4002a000` | Buffer de escritura, 512 bytes |
| `0x4002a200` | Buffer de lectura de verificación |
| `0x4002a400` | Metadatos y parámetros de selección de partición |
| `0x4002a800` | Contenedor de inicialización de storage |
| `0x4002ac00` | Copia de la rutina de comandos SDMMC |

El payload final ocupa 118272 bytes. Los buffers nativos conocidos en
`0x4002ffc0`, `0x40032320` y `0x40032380` quedan fuera de estas asignaciones.

## Storage y direcciones

`0x4001ca74`, con índice de dispositivo 4 y configuración `0x11`, prepara
el driver nativo eMMC. Devuelve log2 de bloque 14 y log2 de página 9.
`0x4000f5b4` lee una página; `0x4000edf6` consulta estado: 2 pendiente,
1 completado. `0x4000f794` selecciona las particiones hardware eMMC y
normaliza el índice de bloque. El escritor usa el mismo selector.

**Las unidades no son intercambiables:** el cliente propio usa sectores
lógicos de 512 bytes que incluyen las áreas de arranque hardware. El nvflash
usado en la investigación tenía sectores de 4096 bytes. Los sectores de
Linux `/dev/block/mmcblk0` tienen otro origen; no aplicar estos números a `dd`.

Para CMD24 se copia la rutina original en `0x4000ec22`, omitiendo únicamente
las instrucciones `0x4000ec4e` y `0x4000ec50` que fuerzan RD1WT0=lectura.
La rutina original para lecturas queda intacta.

## NV3P

Se verificó NV3P versión 1, cabecera de 12 bytes: versión, tipo y secuencia.
El checksum es el complemento a dos de la suma de los bytes anteriores al
footer. El host usa lecturas USB con buffering.

- Comando 0: lectura propia. Comando 5: escritura propia.
- Ambos tienen longitud de argumentos inline cero.
- Sector/count llegan en un paquete DATA de ocho bytes posterior al ACK.
- Cada sector ocupa un paquete DATA de 512 bytes.
- En escritura, el ACK de recepción no significa escritura completada.
  El dispositivo lee el sector escrito y envía sus 512 bytes al host.
  El host compara todos los bytes y solo entonces confirma el paquete.
