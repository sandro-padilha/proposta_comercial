# Revisão do site MaJo Creative

Original: 1 arquivo de 16,7 MB (vídeos e fotos em base64, com cópias repetidas).
Revisado: pasta `majo-creative/` (`index.html` ~30 KB + `assets/`) (5,4 MB, sem duplicatas).

## Otimização
- Mídias deduplicadas (os 3 vídeos do topo estavam copiados no portfólio) e vídeos recodificados 720x1280 -> 540x960, sem trilha de áudio (os originais já eram mudos).
- Vídeos só carregam quando visíveis; no celular tocam no máximo 4 ao mesmo tempo; respeita "reduzir movimento" e "economia de dados".
- Pausa o vídeo do topo ao sair da tela; parallax só no desktop (requestAnimationFrame).
- Imagens com width/height (sem salto de layout), preload do 1º pôster, favicon, JSON-LD, tags Open Graph/Twitter.

## Mobile
- Texto do topo estava colado na borda da tela (padding do .wrap era sobrescrito).
- Alvos de toque >= 44 px (menu, filtros, rodapé); fontes mínimas de 12 px.
- Hover só em dispositivos com mouse; áreas seguras (iPhone) no botão do WhatsApp e no menu.
- Menu fecha com Esc, ícone vira ✕; item 05 do diferencial ocupa a linha inteira.

## Acessibilidade
- Contraste: preço branco sobre fundo claro (Bronze/Prata/Gold) e "tag" bronze sobre papel não passavam; corrigidos.
- Lightbox com foco preso, fundo travado, Esc e retorno do foco.
- Plano Gold agora realmente sobe 14 px no desktop (regra .rv.in anulava o efeito).
- Conteúdo visível mesmo sem JavaScript.

## Texto
- "assistir com som" removido: os vídeos não têm áudio.
- Seção "Depoimentos" com texto "Em breve" ocultada (atributo `hidden`); remova-o quando houver depoimentos reais.

## Pendências para a dona do site
- Instagram (link comentado no HTML), depoimentos reais, nomes dos planos (Bronze/Prata/Gold misturam português e inglês), definir se o preço é por evento, e og:image com URL absoluta do domínio final.
