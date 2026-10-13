# LG D625 Tegra 4i Recovery

Recuperación del **LG G2 Mini D625, NVIDIA Tegra 4i / T148**, desde APX/RCM
cuando un BCT inválido impide iniciar Android y bloquea los comandos de
escritura del bootloader de segunda etapa.

**Estado: recuperación completada en una unidad el 13 de octubre de 2026.**
Se restauraron RBL y las 60 copias originales del BCT. Las lecturas completas
posteriores confirmaron BCT, RBL y EBT byte por byte, y el propietario
confirmó el arranque en Android. Los datos de Android no se borraron.

En la rama `research/bootloader-unlock`, el parche v2 instalado mediante
`nvflash --resume --download 5 … --sync` permitió arrancar en RAM una recovery
stock con su firma alterada. Android también arrancó y la lectura posterior
confirmó EBT parcheado, RBL original y metadatos BCT actualizados por nvflash.
Consultar [la prueba y el procedimiento](docs/UNLOCK_RESEARCH.md); todavía
no se han probado TWRP ni kernels modificados.

## Qué aporta este repositorio

- Un generador reproducible de miniloader con código **ARMv4T / Thumb-1**.
- Lecturas y escrituras eMMC mediante NV3P, sin depender de DL_BL ni de un
  bootloader de Wiko que necesite validar el BCT dañado.
- Escrituras acotadas a BCT, RBL y un sector de prueba, con lectura de
  verificación antes de continuar al siguiente sector.
- El parche de soporte T148 para `NVIDIA/tegrarcm`, con su revisión base.
- La explicación de los cuelgues anteriores, pruebas verificadas y referencias.

La implementación y los offsets corresponden a la unidad/firmware documentados
en [el perfil](profiles/lg-d625-v0711.json). La evidencia disponible es de
una unidad; no se ha establecido compatibilidad con todos los D625. D620/D618,
Nexus 7 y Ouya tienen plataformas o layouts diferentes.

## Empezar

1. Consultar [los resultados verificados](docs/VERIFIED_RESULTS.md).
2. Preparar los insumos locales y seguir [la guía de recuperación](docs/RECOVERY.md).
3. Leer [la arquitectura y los fallos resueltos](docs/ARCHITECTURE.md).
4. Para continuar con imágenes sin firma, abrir [la investigación de desbloqueo](docs/UNLOCK_RESEARCH.md).

El repositorio no incluye dumps del dispositivo ni ejecutables de firmware.
Los insumos se proporcionan localmente en `vendor/` y `private/`, excluidos de Git.

## Organización

| Directorio | Contenido |
| --- | --- |
| `payload/` | Ensambladores Thumb-1 y generadores del código en IRAM |
| `utils/` | Extracción del miniloader, cliente NV3P y carga inicial |
| `host/` | Parche de tegrarcm, licencia NVIDIA y receta de compilación |
| `profiles/` | Layout y hashes de la recuperación verificada |
| `evidence/` | Verificación final sanitizada y hash del payload probado |
| `research/` | Scripts Ghidra y candidato histórico de parche offline |
| `tests/` | Comprobaciones offline; no acceden al teléfono |
| `private/` | Respaldos y herramientas locales, fuera del repositorio público |

## Referencias y créditos

La organización toma como referencia
[`tofurky/tegra30_debrick`](https://github.com/tofurky/tegra30_debrick), que
documenta recuperación de Nexus 7 (2012) y Ouya. Las herramientas base proceden
de [`NVIDIA/tegrarcm`](https://github.com/NVIDIA/tegrarcm). El método publicado
aquí está verificado en D625/T148; no requiere el payload Fusée Gelée de
aquellos dispositivos Tegra 3.

Más fuentes: [REFERENCES.md](docs/REFERENCES.md).

El código nuevo usa la licencia MIT. El código/parche derivado de tegrarcm
conserva la [licencia NVIDIA](host/NVIDIA-LICENSE); ver [NOTICE](NOTICE).
