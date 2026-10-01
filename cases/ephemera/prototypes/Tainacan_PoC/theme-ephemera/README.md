# Ephemera Catálogo

Tema filho de Tainacan Interface, criado para o PoC local em 17 de setembro de 2026.
Reproduz os elementos visuais observados em https://ephemerajpp.com/:
banner da biblioteca, símbolo do relógio, fonte Open Sans, navegação escura,
apontamentos vermelhos, conteúdo branco sobre fundo cinzento e coluna lateral.
É uma adaptação própria, não uma instalação do tema comercial MH Magazine.

As páginas de coleções, itens, pesquisa e posts continuam a usar os templates
do tema pai. A página inicial apresenta apenas coleções e itens publicados,
com contagens calculadas a partir dos dados. Não altera metadados ou estados
de publicação. Não há associação com o site oficial além dos links explícitos.

## Instalar no PoC existente

Executar a partir da pasta Tainacan_PoC, com Docker ligado:

```sh
docker exec ephemera-tainacan-poc-wordpress-1 mkdir -p /var/www/html/wp-content/themes/ephemera-catalogo
docker cp theme-ephemera/. ephemera-tainacan-poc-wordpress-1:/var/www/html/wp-content/themes/ephemera-catalogo/
docker exec ephemera-tainacan-poc-wordpress-1 php -r 'require "/var/www/html/wp-load.php"; switch_theme("ephemera-catalogo"); set_theme_mod("tainacan_link_color","#b44440"); set_theme_mod("tainacan_tooltip_color","#f8eeee");'
```

Para voltar ao visual anterior, ativar Tainacan Interface em Aparência > Temas.
O conteúdo original da página inicial permanece guardado no WordPress.
Os links de navegação correspondem aos slugs das coleções deste PoC.

## Proveniência dos recursos

- Banner: https://ephemerajpp.com/wp-content/uploads/2018/04/cropped-Copy-of-Cópia-de-BIBLIOS1403-1.jpg
- Símbolo: https://ephemerajpp.com/wp-content/uploads/2026/03/Copy-2-of-Relogio-Ephemera_Ephemera-segunda-proposta-7.1.2016-500x599.jpg
- Open Sans: resposta CSS pública https://fonts-api.wp.com/css?family=Open+Sans:400,600,700,800 e ficheiros em fonts.wp.com.

Os recursos gráficos da Ephemera são usados para a demonstração local solicitada.
Este tema não modifica o WordPress de produção.
