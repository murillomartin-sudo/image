# Convite animado — Vicente (Piquenique Jurássico)

Motion graphics 2.5D (HTML + CSS + JavaScript + GSAP) feito a partir da arte original, separada em camadas.
Vertical 4:5 · 1122×1402 px (resolução nativa da arte) · 15 s · sem áudio.

## Arquivos

| Caminho | O que é |
|---|---|
| `index.html` | Prévia da animação com play/pausa, reiniciar e linha do tempo |
| `output/convite-vicente-com-som.mp4` | Vídeo final **com música e efeitos sonoros** (H.264 + AAC 256 kbps) |
| `output/convite-vicente.mp4` | Vídeo final sem áudio (H.264, 30 fps, 1122×1402) |
| `output/convite-vicente.gif` | GIF animado (480 px de largura, 12 fps, em loop) |
| `assets/original.png` | Arte original |
| `assets/layers/` | Camadas recortadas (PNG com transparência), fundo limpo, névoa e textura da cachoeira |
| `export/render.mjs` | Exportador: renderiza quadro a quadro e gera o MP4 e o GIF |
| `assets/audio/soundtrack.wav` | Trilha sonora (música + efeitos), 48 kHz estéreo, 15 s |
| `tools/` | Scripts Python: separação em camadas (`segment.py`, `refine.py`, `build_layers.py`) e trilha (`make_audio.py`) |

## Ver a prévia

Abra `index.html` no navegador (com dois cliques, funciona offline).

## Exportar MP4 e GIF

Requer Node 18+, Playwright (`npm i playwright && npx playwright install chromium`) e ffmpeg.

```bash
node export/render.mjs                          # MP4 30 fps + GIF 480 px / 12 fps
node export/render.mjs --fps 60                 # MP4 a 60 fps
node export/render.mjs --scale 2                # 2244×2804 (ampliado)
node export/render.mjs --gif-width 600 --gif-fps 15
```

O último quadro é renderizado exatamente em t = 15 s e é **idêntico pixel a pixel à arte original**.

## Roteiro (ritmo ágil)

| Tempo | Cena |
|---|---|
| 0–1,3 s | A névoa se abre rapidamente e o logo "VICENTE" cai com um leve "pop" (back-out) |
| 1,3–2,8 s | T-Rex, pescoço longo, Triceratops e pterossauro entram rápido pelas laterais |
| 2,9 s | A placa "Você foi convidado…" cai de trás do logo e balança nas cordas |
| 3,8–4,9 s | "21 novembro" faz um pop de 90% → 100%; "14h30" sobe |
| 5,1–6,3 s | O endereço sobe; a cesta, a garrafa, as frutas, os biscoitos e os ovos entram |
| 6,4 s | "Esperamos você!" aparece em fade |
| 7–14,3 s | Composição completa com ambiente vivo: dinossauros mexendo a cabeça, pterossauro batendo as asas, folhas, névoa, cachoeira e parallax de câmera |
| 14,3–15 s | Tudo se acomoda; o último quadro é idêntico à arte original |

## Trilha sonora

Gerada 100% por síntese em `tools/make_audio.py` (sem samples nem músicas de terceiros, livre de direitos autorais):

- **Música original de aventura** (Ré dórico, 120 bpm): tambores tribais e taiko, chocalho, baixo em ostinato, marimba, pad e um tema heroico de metais a partir da data. Termina com um rufar e um acorde final aos 14 s.
- **Efeitos sincronizados**: queda e impacto do logo, "whooshes" nas entradas, rugido do T-Rex, chamado do pescoço-longo, grunhido do Triceratops, asas e grito do pterossauro, batidas de madeira e rangido de cordas nas placas, farfalhar e "pops" no piquenique, brilho no "Esperamos você!".
- **Ambiente**: floresta, pássaros, insetos e a cachoeira (à esquerda no estéreo).

Para regerar a trilha e o vídeo com som: `python3 tools/make_audio.py && node export/render.mjs`.
Na prévia (`index.html`), clique em **🔇 Som** para ativar o áudio sincronizado.

## Vídeo 2 — convite "5 anos" ajustado

`output/video2/convite-vicente-5anos-ajustado.mp4`: versão corrigida do vídeo enviado (`assets/video2/original.mp4`), 1080×1920, 30 fps, 12,4 s, com trilha.

- **Problemas no original**: um trecho de 1,4 s repetido 7 vezes, com um "pulo" a cada emenda, quadros duplicados (engasgos), 720×1280 e codec HEVC.
- **Correção**: um só ciclo, sem duplicados, em ida e volta (loop sem emenda), interpolação de movimento para 30 fps, ampliação para Full HD com leve nitidez e cor, e H.264 + AAC (compatível com WhatsApp e Instagram).
- **Trilha** (`assets/audio/soundtrack-video2.wav`): a mesma música de aventura com efeitos de rugidos, Triceratops, pterossauro, pescoço-longo, passos pesados, raptor e brilho final.

Para regerar: `python3 tools/make_audio.py video2 && python3 tools/adjust_video2.py`.
