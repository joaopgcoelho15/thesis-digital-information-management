# Ephemera — laboratório local Tainacan

Instância independente em http://localhost:8087. O site WordPress original e a Wikibase não foram alterados por este laboratório.

## Abrir e utilizar

- Página inicial: http://localhost:8087/
- Nove cartazes: http://localhost:8087/cartazes/
- Cinquenta entradas do reportório: http://localhost:8087/reportorio/
- Post com blocos dinâmicos nativos: http://localhost:8087/cartazes-num-post/
- Administração: http://localhost:8087/wp-admin/
- Utilizador: `ephemera`. Palavra-passe: valor de `WP_ADMIN_PASSWORD` no ficheiro local `.env`. A sessão de administração já foi utilizada no browser integrado.

Duplo clique em `Iniciar.command` para arrancar. `Parar.command` para parar preservando os dados. O Docker Desktop tem de estar instalado; os atalhos utilizam o Docker existente neste Mac. A página só fica acessível neste computador enquanto o serviço estiver ativo. Não é um alojamento público.

## Conteúdo e implementação

WordPress 6.8.3, PHP 8.3, MariaDB 11.4, Tainacan 1.3.0 e tema Tainacan Interface 2.9.0. Versões do teste, não uma recomendação de versões para produção. A interface usa pt_BR por ter traduções do plugin e tema disponíveis; alguns rótulos continuam em inglês.

- 9 cartazes do PCP de 1975 e 50 registos preenchidos da TablePress 77, retirados dos snapshots da PoC Wikibase.
- 71 associações de imagens importadas na biblioteca multimédia local; miniaturas geradas pelo WordPress.
- Campos: identificador, data original, autor, organização, tipo, fonte, notas, evento, local/país e direitos. Preservação de valores incertos e campos vazios.
- Filtros por data, organização e tipo. Paginação nativa, em cartões e outros modos disponíveis no Tainacan.
- Post editorial demonstrativo (não é cópia integral de um post original), com galeria da coleção e metadados dinâmicos do primeiro cartaz.
- Downloads da tabela pedem `w=1000`, mas o servidor pode fornecer o original. São cópias para consulta e teste; não se alteram direitos nem se faz preservação digital completa.

## Código e reprodução

`compose.yaml` cria serviços e volumes exclusivos do laboratório. `.env` contém apenas credenciais deste ambiente. A porta está ligada a 127.0.0.1:8087. Não executar `docker compose down -v` se quiser conservar a base de dados e imagens.

Scripts:

1. `scripts/prepare.py`: prepara a amostra e descarrega imagens públicas; conserva `data/sample.json` e um CSV auxiliar.
2. `scripts/import.php`: importa usando as APIs PHP do Tainacan e APIs multimédia WordPress. Executar com `docker compose run --rm cli eval-file /work/scripts/import.php` dentro desta pasta.
3. `scripts/presentation.php`: gera a página inicial e o post com blocos nativos. Não depende de uma interface personalizada de catálogo.
4. `scripts/verify.py`: compara a API local com a amostra e verifica as imagens. Executar `python3 scripts/verify.py`.
5. `scripts/backup.sh`: grava um dump SQL e arquivo de wp-content/configuração em `backups/`. Incluem dados de autenticação local; guardar de forma privada.

A configuração inicial foi efetuada com WP-CLI (`core install`, instalação do plugin/tema, idioma, permalinks e bloqueio de indexação). Para reconstrução completa, criar `.env` com DB_PASSWORD, DB_ROOT_PASSWORD e WP_ADMIN_PASSWORD; arrancar `docker compose up -d`; instalar WordPress com URL http://localhost:8087 e WP-CLI; instalar as versões acima do plugin e tema; executar preparação, importação e apresentação. Os dados já instalados persistem nos volumes Docker, não apenas nesta pasta OneDrive.

O importador conserva um mapa em `ephemera_lab_map` e a repetição concluída criou zero itens adicionais. Não é ainda um sincronizador contínuo nem oferece transações para todos os cenários de interrupção a meio de um item. Não o usar diretamente sobre o site de produção.

## Testes e avaliação

Ver `AVALIACAO.md` e `reports/verification.json`. Os JSON em reports são exportações reais da API local; `data/sample.csv` é a entrada preparada, não um teste do exportador CSV nativo.

## Atualização para WordPress 7.1 e tema do site original

Em 7 de setembro de 2026, foi confirmada por WP-CLI a atualização feita pelo utilizador para WordPress 7.1. O tema ativo continua Tainacan Interface 2.9.0. A imagem Docker em compose.yaml é a base inicial 6.8.3; o WordPress instalado foi atualizado dentro do volume persistente. Uma reconstrução de raiz exige atualizar também o core para 7.1 para reproduzir este estado.

O HTML público do Ephemera identifica `wp-content/themes/mh-magazine/` e assets com versão 3.8.4, em concordância com a captura do painel fornecida pelo utilizador. É MH Magazine, não MH Magazine Lite. A instalação do mesmo tema está pendente do ZIP original (ou cópia autorizada da pasta do tema), que não foi encontrado no projeto nem em Downloads. As configurações de personalização, menus, widgets e CSS adicional do site real também não estão incluídas apenas no ZIP do tema.

### Importação FOTOSNERO e chamadas internas Docker — 2026-09-14

A importação CSV submetida na interface ficou em espera porque as chamadas HTTP
internas para `http://localhost:8087` falhavam dentro do contentor. O servidor
Apache interno responde na porta 80 do serviço `wordpress`.

A correção local está em `scripts/ephemera-local-loopback.php`, instalada como
`wp-content/mu-plugins/ephemera-local-loopback.php`. Usa `CURLOPT_CONNECT_TO`
para encaminhar apenas HTTP para localhost:8087 para wordpress:80, mantendo
o URL/Host. Só atua com `WP_ENVIRONMENT_TYPE=local` e transporte cURL.
Não instalar esta adaptação num servidor de produção.

A fila existente foi retomada através do evento nativo `tnc-bg_import_cron`
no contentor WordPress. Processo 1 concluído a 100%, coleção 826 Fotografias Nero,
56 itens em rascunho, cada um com documento e miniatura. Não repetir o CSV
original para evitar duplicações. As rotações foram preservadas como metadados,
não aplicadas às imagens. A contagem anterior de 59 itens refere-se à amostra
inicial e não inclui esta coleção nem alterações manuais posteriores.
