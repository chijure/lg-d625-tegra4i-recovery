# Próxima etapa: imágenes boot/recovery sin firma

## Punto de partida

Android arranca con BCT, RBL y EBT originales verificados. Conservar el tag
`recovery-v0.1.0` y el archivo privado de investigación antes de experimentar.
El cliente público de recuperación admite solamente las restauraciones
originales y el sector de prueba definidos en el perfil.

**No existe un desbloqueo confirmado por este proyecto.** Un flag `unlocked`
de fastboot y la verificación propietaria `[LGE_SECURITY]` no deben tratarse
como el mismo mecanismo. La investigación anterior no estableció que el
parche v1/v2 permitiera iniciar imágenes sin firma.

## Hallazgos anteriores que deben retomarse

- Hay dos copias activas del bootloader, EBT y RBL. Cambiar solo una copia
  no demostró que el BootROM hubiera ejecutado el candidato.
- El BCT contiene hashes de los bootloaders. El cambio del hash RBL en sus
  60 copias dejó inválido el arranque y motivó esta recuperación.
- El chequeo histórico en el offset de archivo `0x12600`, de `beq` a `b`,
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
