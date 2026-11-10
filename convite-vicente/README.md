# Convite animado — Vicente (Piquenique Jurássico)

Motion graphics 2.5D (HTML + CSS + JavaScript + GSAP) feito a partir da arte original, separada em camadas.
Vertical 4:5 · 1122×1402 px (resolução nativa da arte) · 15 s · sem áudio.

## Arquivos

| Caminho | O que é |
|---|---|
| `index.html` | Prévia da animação com play/pausa, reiniciar e linha do tempo |
| `output/convite-vicente.mp4` | Vídeo final (H.264, 30 fps, 1122×1402) |
| `output/convite-vicente.gif` | GIF animado (480 px de largura, 12 fps, em loop) |
| `assets/original.png` | Arte original |
| `assets/layers/` | Camadas recortadas (PNG com transparência), fundo limpo, névoa e textura da cachoeira |
| `export/render.mjs` | Exportador: renderiza quadro a quadro e gera o MP4 e o GIF |
| `tools/` | Scripts Python que separaram a arte em camadas |

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
