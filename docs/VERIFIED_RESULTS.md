# Recuperación verificada — 2026-10-13

El propietario confirmó: **“YA ENTRO EN ANDROID”** después de restaurar
los originales y cargar la batería. Esto confirma recuperación del arranque;
no confirma un desbloqueo del bootloader.

## Evidencia

| Región | Sector lógico de 512 bytes | Sectores | SHA256 final |
| --- | ---: | ---: | --- |
| BCT, 60 slots | 128 | 1920 | `1771092fc30b1ec43921eab3784f32c649afedd817cc248776d4a0adc7976107` |
| RBL | 12288 | 1680 | `10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7` |
| EBT | 24576 | 1680 | `10bc066b7f99256f87b05e82b5087c5c6f815a3e865dc094169176fcc69706f7` |

Las regiones se leyeron completas después de la restauración y coincidieron
byte por byte. EBT ya estaba original y no se escribió. Las particiones de
Android y sus datos no se borraron.

El BCT previo tenía exactamente 960 diferencias respecto al original:
16 bytes de hash RBL en cada uno de 60 slots. RBL contenía el candidato
parcheado v2 de septiembre; EBT coincidía con el bootloader original.

La prueba del escritor usó el sector sin uso 4096, cuyo contenido se respaldó.
Se escribió un patrón de 512 bytes, se verificó con lectura inmediata y una
lectura independiente, se restauró el contenido anterior y se volvió a leer.

La evidencia estructurada está en
[`recovery-2026-10-13.json`](../evidence/recovery-2026-10-13.json).

## Respaldos que no deben confundirse

Un archivo histórico llamado `common_bct_PRISTINE_backup.cfg` había sido
sobrescrito por un comando GetBct: solo tenía dos bytes no nulos. No se usó
para restaurar. El origen válido fue `bct_raw_check.bin`, un volcado crudo
de 4MiB con SHA256
`0f44cee2f99c37ee1f5b55768c33f60e129ef9017aa4837d6c4167b79092cd1e`.

Contiene 60 BCT idénticos, de 5424 bytes, separados 16KiB a partir del offset
`0x10000`. Cada copia original tiene SHA256
`8583855d33606748415f65ae291a194500bab1110c8d8cc34119c59854423193`.
