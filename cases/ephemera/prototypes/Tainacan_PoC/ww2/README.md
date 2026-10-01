# Segunda Guerra Mundial — migração representativa para Tainacan

Implementado em 20 de setembro de 2026 no PoC http://localhost:8087/.
Página temática: http://localhost:8087/segunda-guerra-mundial/.

## Âmbito e resultados

A resposta pública da API WordPress.com contém os 93 posts da categoria `1939-1945-ii-guerra-mundial` (ID 21307779). Foram pedidos 100 resultados na página 1; `found=93` e 93 posts recebidos, pelo que esta fotografia da categoria não exige segunda página. A tabela de decisões está em `reports/inventory.json`. O inventário não equivale a catalogação completa dos objetos ou a inspeção de todas as galerias.

A amostra seleciona sete fontes documentais e uma publicação editorial, de modo a testar vários tipos de unidade. Foram importados sete registos, 71 representações documentais, um post editorial e a sua imagem. As outras 85 publicações não foram migradas. As galerias externas foram identificadas e adiadas; não se usaram credenciais nem se mudaram permissões do Google Drive.

| Fonte WP | Unidade no catálogo | Coleção | Imagens |
|---|---|---|---:|
| 416599 | A Europa contra o inimigo — cartaz | Materiais de propaganda | 1 |
| 226742 | Cartazes britânicos — conjunto provisório | Materiais de propaganda | 10 |
| 504052 | Free French in Libya — documento de propaganda | Materiais de propaganda | 1 |
| 273556 | Der Adler — registo ao nível da série | Publicações periódicas | 37 |
| 418508 | Álbum de um soldado alemão | Álbuns e conjuntos documentais | 18 |
| 164565 | War Ration Book — conjunto provisório | Álbuns e conjuntos documentais | 2 |
| 234166 | Fotografia de Santiago — frente e verso | Fotografias históricas | 2 |
| 504362 | Anúncio de exposição — post de 18/09/2026 | Editorial | 1 |

## Decisões de organização

- A categoria histórica passou a uma taxonomia Tainacan partilhada: **Contexto histórico**, termo **Segunda Guerra Mundial, 1939–1945**. As quatro coleções usam o mesmo termo, com filtros nativos. É possível consultar o termo diretamente em `/contexto-historico/segunda-guerra-mundial-1939-1945/`.
- A página temática consulta os itens por essa taxonomia e permite pesquisa textual, filtro de coleção e de unidade. As fichas e imagens são os próprios itens Tainacan; não existem cópias desses sete itens em posts editoriais.
- Preservam-se o URL, identificador, título, texto e data de publicação da fonte. Os originais digitais são guardados localmente, associados ao item na ordem da fonte, com URL original e SHA-256.
- As imagens foram enumeradas a partir do HTML e de `data-orig-file`. O campo `attachments` da API pode estar limitado a 20 e não serviria para recuperar as 37 capas de Der Adler.
- A frente e o verso da fotografia foram confirmados visualmente e recebem legendas próprias. As páginas de álbum não foram desmembradas em objetos independentes.
- Der Adler é uma descrição de série provisória: não afirma completude nem contém 37 exemplares individualmente catalogados. O conjunto britânico mantém as dez representações juntas até revisão arquivística.
- A atribuição do álbum a Johan Hagenberger continua provável, conforme o texto de origem. A morte referida na fonte não se transforma em data das fotografias.
- O período 1939–1945 classifica o contexto; a data do documento fica vazia quando não comprovada. No periódico conservam-se os anos explícitos nos grupos de imagens. O dia 25/03/1942 da fotografia é referido como data do acontecimento, não como data de impressão do suporte.
- O anúncio de exposição conserva a data editorial de 18/09/2026. A ligação ao catálogo é temática; não afirma que os sete registos fazem parte dessa exposição. A galeria externa da publicação continua acessível através de ligação à fonte.
- Não foram atribuídas novas licenças nem autores não documentados.

## Execução reproduzível

A partir desta pasta, com Docker e o PoC ativos:

```sh
./run.sh
```

`prepare.py` lê o snapshot em `source/posts-1.json`, gera inventário e manifesto e descarrega apenas imagens públicas da Ephemera quando faltam na cache. O script falha se o snapshot deixar de corresponder aos 93 posts esperados; alterações de âmbito exigem revisão da seleção.

`import.php` recusa execução se `home` não for `http://localhost:8087`. Utiliza as entidades e repositórios do Tainacan; guarda os IDs na opção `ephemera_ww2_map`, chaves estáveis por origem e um marcador de conclusão. Itens concluídos são ignorados nas reexecuções, preservando alterações manuais. Uma interrupção após a reserva de IDs pode ser retomada. Não é um sincronizador de atualizações nem uma transação atómica; a janela entre a criação de um objeto e a gravação da sua chave ainda exige cuidado se ocorrer uma falha precisamente aí.

O tema foi atualizado em `../theme-ephemera/`: novo `page-segunda-guerra-mundial.php`, estilos e ligações na navegação e início. `run.sh` importa dados; para reinstalar a apresentação, copiar o conteúdo dessa pasta para `wp-content/themes/ephemera-catalogo/` do contentor local.

Fontes da API usadas para o snapshot:
- https://public-api.wordpress.com/rest/v1.1/sites/ephemerajpp.com/categories/slug:1939-1945-ii-guerra-mundial
- https://public-api.wordpress.com/rest/v1.1/sites/ephemerajpp.com/posts/?category=1939-1945-ii-guerra-mundial&number=100&page=1

## Validação e preservação

`reports/import-rerun.log`: segunda execução criou **0 itens, 0 anexos e 0 posts**.
`reports/verification.json`: 72 imagens verificadas pelo hash do original e pelo item/post pai; sete registos com o termo histórico. Mantiveram-se as contagens anteriores: 9 cartazes PCP, 50 registos do reportório e 56 Fotografias Nero.

No navegador verificaram-se a página temática, o filtro Fotografias históricas e a ficha nativa com documento/frente, anexo/verso e ligação ao contexto histórico. A data editorial foi corrigida para preservar a fonte através de `edit_date=true`, necessária ao publicar o rascunho.

Cópias anteriores: `reports/before.sql` (restrita, contém a base de dados local; não partilhar), `reports/before.json` e `reports/theme-before/`.

## Limites e próximos passos

A amostra testa o modelo e a apresentação, não a migração integral. O passo seguinte é rever a unidade de descrição de cada fonte, organizar a seleção de direitos e inventariar as galerias externas com acesso autorizado. Automatizar tudo sem essa classificação poderia transformar álbuns em fotografias isoladas, confundir datas de posts com datas documentais ou importar galerias incompletas. A experiência não altera o WordPress oficial, a Wikibase pública nem o texto da tese.
