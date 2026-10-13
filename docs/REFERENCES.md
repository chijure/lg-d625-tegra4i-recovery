# Referencias usadas

## Repositorio de recuperación de Tegra 3

[`tofurky/tegra30_debrick`](https://github.com/tofurky/tegra30_debrick)
incluye guía, payloads, BCT, bootloaders y utilidades para Nexus 7 (2012)
y Ouya. Es la referencia comunitaria encontrada en el historial. No es
un repositorio de NVIDIA. Su estructura sirve como modelo para documentar
una recuperación completa y conservar sus herramientas.

Su uso de Fusée Gelée y sus imágenes Tegra 3 no se trasladan directamente
al LG D625/T148. En nuestra unidad se pudo cargar el miniloader mediante
RCM en operating mode 3, con SBK reportado como no quemado.

## Herramientas y documentación NVIDIA

- [`NVIDIA/tegrarcm`](https://github.com/NVIDIA/tegrarcm): transporte RCM/NV3P
  y carga de código en RAM. Revisión base local:
  `f6a46f1b342fe5ff531281e605b52b2a604a8aac`.
- [Tegra Boot Flow](https://http.download.nvidia.com/tegra-public-appnotes/tegra-boot-flow.html):
  procesador de arranque ARM7, RCM/IRAM y redundancia BCT/bootloaders.
- [BCT Overview](https://http.download.nvidia.com/tegra-public-appnotes/bct-overview.html):
  campos y responsabilidades de la Boot Configuration Table.
- [Flashing Tools](https://http.download.nvidia.com/tegra-public-appnotes/flashing-tools.html):
  distinción entre BootROM/RCM, miniloader y bootloader descargado.
- [`NVIDIA/cbootimage`](https://github.com/NVIDIA/cbootimage): referencia de
  estructuras BCT y hashes; no sustituye los respaldos de la unidad.
- [`NVIDIA/cbootimage-configs`](https://github.com/NVIDIA/cbootimage-configs):
  ejemplos de configuración de placas, no un BCT confirmado para D625.

## Investigación y plataforma

- [`NationalSecurityAgency/ghidra`](https://github.com/NationalSecurityAgency/ghidra):
  análisis estático. El miniloader se analiza como ARM little-endian v4T,
  base `0x4000e000`; no usar el perfil Cortex-A9 para sus instrucciones.
- [`desowin/usbpcap`](https://github.com/desowin/usbpcap): captura USB en Windows.
  La captura elevada funcionó el 2026-10-13 sin cambiar Kaspersky.
- [XDA: Unlocking bootloader tegra version](https://xdaforums.com/t/unlocking-bootloader-tegra-version.2933295/):
  contexto histórico del bloqueo específico del D625.

Los hallazgos y el arranque confirmado de esta unidad se conservan en
`evidence/` y en el archivo privado de investigación. Las referencias
externas no prueban por sí solas compatibilidad de imágenes ni offsets.
