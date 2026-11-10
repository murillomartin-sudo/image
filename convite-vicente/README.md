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

## Roteiro

| Tempo | Cena |
|---|---|
| 0–3 s | Floresta enevoada desperta: folhas balançam, a névoa se move, a cachoeira corre e o logo "VICENTE" desce com escala e desaceleração |
| 3–5 s | T-Rex entra pela direita, o pescoço longo pela esquerda, o Triceratops no canto superior direito e o pterossauro voa pela esquerda batendo as asas |
| 5–7 s | A placa "Você foi convidado…" desce de trás do logo e balança como um pêndulo amortecido |
| 7–10 s | A placa "21 novembro" cresce de 90% a 100%, depois "14h30" sobe |
| 10–12 s | A placa do endereço sobe; a cesta, a garrafa, as frutas, os biscoitos e os ovos aparecem com fade e deslocamento |
| 12–15 s | "Esperamos você!" entra em fade; os movimentos ambientes desaceleram até a composição ficar igual à original |
