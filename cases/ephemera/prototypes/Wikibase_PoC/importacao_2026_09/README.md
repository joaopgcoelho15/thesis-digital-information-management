# Ephemera — PoC de importação WordPress e TablePress

Recolha efetuada em 5 de setembro de 2026. Instância de destino: <https://ephemera-poc.wikibase.cloud>.

## Resultados e navegação

- [Índice da demonstração](https://ephemera-poc.wikibase.cloud/wiki/Project:PoC_%E2%80%94_Importa%C3%A7%C3%A3o_WordPress_e_TablePress)
- [Tabela de consulta ordenável](https://ephemera-poc.wikibase.cloud/wiki/Project:Report%C3%B3rio_da_oposi%C3%A7%C3%A3o_%E2%80%94_TablePress_77)
- [Coleção dos nove cartazes](https://ephemera-poc.wikibase.cloud/wiki/Item:Q1?uselang=pt)
- [Cartaz com imagem](https://ephemera-poc.wikibase.cloud/wiki/Item:Q7?uselang=pt#P10)

A confirmação quantitativa da publicação fica em `verification.json`; o mapeamento entre chaves de origem e QIDs/PIDs, em `wikibase_ids.json`. `published_entities.json` conserva uma cópia pública das entidades consultadas pela auditoria. Estes ficheiros são produzidos por `verify.py`.

## O que foi extraído

A [TablePress 77](https://ephemerajpp.com/reportorio-das-publicacoes-clandestinas-semilegais-e-legais-da-oposicao-1926-1974/) tem 700 linhas de dados: 696 preenchidas e quatro vazias. Cada entrada preenchida corresponde a um Q; o reportório tem um Q próprio. A introdução da fonte inclui vários tipos de documentos e exclui os periódicos, que têm um reportório separado. Por isso, o importador não classifica indiscriminadamente as linhas como jornais ou revistas.

Os cinco posts mais recentes na recolha foram selecionados por data descendente através da API pública WordPress.com, sem acesso ao painel de administração e sem alterar o WordPress. Os IDs são 504130, 504113, 504106, 503637 e 504094, publicados entre 2 e 5 de setembro de 2026. Cada Q representa o post editorial; não pressupõe que todas as imagens sejam objetos físicos independentes.

### Mapeamento da tabela

| Origem | Wikibase | Critério |
|---|---|---|
| Cada entrada preenchida | Q próprio, P1 → tipo de registo | Não se inventa uma propriedade por documento |
| TÍTULO | Rótulo e P2 | P2 só é preenchida quando há título na fonte |
| Título em falta | Rótulo técnico «Documento sem título…» | A ausência do título original mantém-se |
| DATA | P20, data na fonte | Conserva literalmente incertezas e códigos |
| DATA inequívoca | P5 | Precisão de ano, mês ou dia; datas inválidas não são convertidas |
| AUTOR | P21, autor na fonte | Texto; sem desambiguação automática |
| ORG | P22, organização na fonte | Texto; não se presume «emitido por» |
| BIO | P23 | Texto original |
| GEO | P24 | Texto original |
| TIPO | P25 | Código original; vocabulário por validar |
| EVENTO | P26 | Texto original |
| NOTAS | P27 | Texto original |
| Posição da linha | P28 | Proveniência no snapshot, não identidade |
| IMAGEM 1 e IMAGEM 2 | P10 repetida, qualificada por P29 | A coluna não é reinterpretada como frente/verso |
| Origem e identidade | P9 e P12 | Referências de proveniência também nas declarações |
| Ligação ao reportório | P8 e inversa P32 («tem parte») | Permite navegar nos dois sentidos |

Foram conservados 123 valores de DATA sem conversão automática. Exemplos: `1926?`, intervalos e `Z`. O relatório de extração enumera-os. Não foram encontradas entradas integralmente idênticas nesta recolha. Há títulos repetidos: as descrições distinguem as entradas para cumprir a validação de unicidade da Wikibase.

P30 identifica a tabela pelo domínio e ID TablePress. P31 guarda a data de publicação dos posts, separada da data dos objetos. P32 corresponde a «tem parte». Confirmar os PIDs reais em `wikibase_ids.json` ao reproduzir noutra instância; o script resolve/cria as propriedades por rótulo e valida o seu tipo.

## Imagens diretamente na Wikibase Cloud

A PoC usa CSS global gerado em `MediaWiki:Common.css`. Cada URL conhecida de P10 recebe uma pré-visualização; as ligações Q7–Q15 em Q1 também mostram os cartazes. O CSS aplica-se a visitantes sem sessão iniciada. Mantêm-se visíveis as ligações à origem, que podem ser abertas para ver o ficheiro.

Isto é uma camada de apresentação: **não é upload nem preservação dos ficheiros na Wikibase**. As imagens continuam no WordPress; os direitos não mudam e não passam a CC0. A regra de apresentação só usa HTTPS e os domínios de imagens do Ephemera. Não foi publicado nenhum ficheiro no Wikimedia Commons.

Limitações verificadas na instância:

- Uploads locais desativados.
- A API `parse` apresenta uma URL externa como hiperligação, sem imagem incorporada.
- O utilizador possui `editsitecss`, mas não `editsitejs`. Não foram alterados grupos nem permissões.
- Por isso, o importador gera regras CSS explícitas. Uma URL nova precisa de nova geração do CSS. O ficheiro `image-preview.js` contém uma alternativa dinâmica para instâncias que já permitam JavaScript global; não foi instalada nesta instância.
- Alterações do CSS podem demorar a aparecer devido à cache do MediaWiki/CDN. Para diagnóstico temporário, `debug=true` permite observar a versão atual; o uso normal não exige esse parâmetro depois de a cache atualizar.
- O CSS não resolve preservação, miniaturas em motores de pesquisa, leitores sem estilos ou ligações quebradas na origem. Também não substitui uma integração de media nativa para produção.
- As galerias Google Drive incorporadas nos posts não foram enumeradas. O post Flammarion usa a imagem destacada disponibilizada pela API WordPress. O corpo dos posts, incluindo incorporações, está no snapshot local para análise posterior.

Alternativas para uma fase posterior:

1. **Wikibase com uploads e Wikibase Local Media:** ficheiros e miniaturas nativos, com operação e armazenamento próprios.
2. **Repositório de imagens (S3/MinIO/IIIF) e interface dinâmica:** maior controlo de preservação e apresentação; requer desenvolvimento e alojamento.
3. **Wikimedia Commons:** apenas para ficheiros com licença livre/domínio público documentalmente confirmado; a propriedade Commons media pode usar os ficheiros existentes. Não é uma solução automática para direitos desconhecidos.

Referências técnicas: [imagens externas](https://www.mediawiki.org/wiki/Manual:$wgAllowExternalImages), [JavaScript da interface](https://www.mediawiki.org/wiki/Manual:Interface/JavaScript), [Wikibase API](https://www.mediawiki.org/wiki/Wikibase/API), [Wikibase Local Media](https://www.mediawiki.org/wiki/Extension:Wikibase_Local_Media).

## Reprodução por código

Requer Python 3, curl, Node.js para os testes JavaScript e uma sessão autenticada na Wikibase com permissões de edição. Não usa bibliotecas Python adicionais. A credencial e os cookies da sessão não são exportados.

Na pasta deste README:

```sh
# Extrair novamente os cinco posts atuais e a tabela (só leituras públicas).
python3 collect.py --refresh

# Ou reconstruir exatamente a partir dos snapshots já guardados.
python3 collect.py

# Rever plan.json e extraction_report.json ANTES de publicar.
python3 build.py

# Validar o extrator e o comportamento de criação/reexecução.
python3 -m unittest discover -p test_collect.py
node test_runner.cjs

# Disponibilizar apenas execute.js e finish.js neste computador.
python3 serve.py
```

Abrir `http://127.0.0.1:8765/execute.js` como texto no browser. Copiar o código integral e executá-lo na consola de uma página da **instância de destino**, já autenticada. O script valida a origem, consulta as entidades existentes e usa a API `wbeditentity`. Esta operação executa o programa; não se copiam manualmente títulos, linhas ou propriedades entre interfaces.

Manter esse separador aberto até `CONCLUÍDO`. O progresso e os IDs ficam em `localStorage`, sob a chave `ephemera-poc-journal`. Em caso de erro, corrigir a causa, reconstruir e executar novamente: o script volta a procurar os identificadores no servidor.

Depois da importação, abrir `http://127.0.0.1:8765/finish.js` como texto e executar o código na **mesma página autenticada**. Este segundo script liga os 696 registos ao reportório, completa imagens destacadas dos posts e gera a tabela ordenável e o índice. O guardião impede executá-lo com a importação em curso ou com um mapeamento incompleto.

```sh
# Auditoria independente, só por leitura da API pública.
python3 verify.py
```

Parar `serve.py` com Ctrl+C quando terminar. O servidor ouve apenas em `127.0.0.1` e serve apenas os dois ficheiros de código, sem listar diretórios. No Safari usado nesta sessão, `fetch` de HTTPS para o servidor HTTP local falhou; abrir o endereço local como documento de texto permitiu carregar o mesmo código sem desativar proteções do browser.

## Garantias e limites da importação

- Não usa `clear=1`, não elimina declarações e não substitui rótulos existentes.
- A reexecução do mesmo plano não cria Qs adicionais nem declarações repetidas. Testes incluem referências, qualificadores, normalização de quantidades e dados manuais.
- A identidade dos posts usa domínio + ID WordPress. Nas linhas da tabela, usa a imagem principal quando é exclusiva; nos restantes casos, usa uma impressão digital dos campos. Isto resiste à reordenação do mesmo conteúdo. **Uma alteração à imagem-chave ou aos campos usados na impressão digital pode criar nova identidade**: para sincronização contínua, deve existir um ID permanente por linha no TablePress e uma política de reconciliação.
- A fusão é aditiva. Alterações à fonte não removem valores anteriores, nem corrigem automaticamente títulos manuais. Esta PoC testa migração e reexecução, não uma sincronização editorial completa.
- Falhas explicitamente rejeitadas por limite de utilização/`maxlag` são repetidas com espera. Uma resposta de escrita perdida ou ambígua interrompe a execução; a retoma começa por consultar os identificadores para evitar duplicação.
- O guardião impede concorrência no mesmo separador; não é um bloqueio distribuído entre browsers/máquinas. Não executar importadores em simultâneo.
- A leitura prévia de todas as entidades é adequada à PoC; uma instalação grande deve usar um índice de identificadores e fila de trabalho.
- A extração valida as 11 colunas esperadas e conserva os snapshots. Uma mudança do esquema faz o programa parar.
- O plugin WordPress experimental anterior não é usado por estes scripts. Esta execução não instala plugins nem ativa sincronização contínua no site de produção.

## Ficheiros

- `collect.py`: extração e normalização conservadora.
- `plan.json`: plano revisto, com todos os campos e URLs de origem.
- `extraction_report.json`: contagens, linhas vazias e datas não convertidas.
- `runner.js`: importação pela API e CSS de pré-visualização.
- `finish-source.js`: relações inversas e apresentação nativa.
- `build.py`: gera `execute.js` e `finish.js` a partir das fontes.
- `serve.py`: distribuição local temporária do código.
- `verify.py`: auditoria independente dos dados publicados e exportação de QIDs.
- `test_collect.py` e `test_runner.cjs`: testes de extração, idempotência e preservação.
- `snapshots/`: fontes públicas recolhidas e evidências técnicas.

## Auditoria final da execução

Concluída em 5 de setembro de 2026: 704/704 itens encontrados, 13 propriedades, zero identificadores duplicados, zero declarações duplicadas e zero divergências face ao plano (incluindo qualificadores e referências). O reportório Q18 contém 696 ligações «tem parte»; Q1 contém nove. Os cinco posts são Q19–Q23, com 25 URLs de imagens no total. A tabela pública foi verificada no browser: 696 linhas e ordenação disponível. A imagem de Q22 foi confirmada visualmente numa sessão pública.

Resultados completos: `verification.json`, `wikibase_ids.json` e `published_entities.json`.

## Catálogo paginado — 6 de setembro de 2026

O catálogo anterior foi substituído por 14 páginas: 13 de 50 registos e uma de 46. A URL anterior abre a primeira página. Imagem 1 e Imagem 2 preservam as colunas da fonte; as primeiras 50 entradas têm 62 miniaturas CSS, e as restantes páginas mantêm ligações. A ordenação é local à página. Não há ainda pesquisa global com filtros.

Reprodução após a importação: executar `python3 paginate.py`, iniciar `python3 serve.py`, abrir `/catalogue.js` no servidor local e executar o conteúdo na consola da Wikibase autenticada, tal como os bundles anteriores. Este passo deve ser executado depois de `finish.js`, que gera a versão anterior do catálogo. `catalogue-source.js` conserva o CSS existente, usa controlo de revisão e não altera os itens. `catalogue-plan.json` contém o resultado esperado e `catalogue-verification.json` regista a auditoria das 14 páginas.

O fluxo proposto para utilização real está em `WORKFLOW.md`. A sincronização contínua e a integração autenticada do Drive continuam por implementar.
