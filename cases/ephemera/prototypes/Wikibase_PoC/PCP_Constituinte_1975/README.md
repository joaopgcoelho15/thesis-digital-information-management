# Ephemera PoC — PCP e Constituinte de 1975

Prova de conceito publicada em <https://ephemera-poc.wikibase.cloud> a partir do conjunto fechado de nove cartazes da página [PCP — Eleições para Assembleia Constituinte — 1975](https://ephemerajpp.com/2014/05/24/eleicoes-para-assembleia-constituinte-1975-pcp/).

## Resultado publicado

- Política de direitos e proveniência: <https://ephemera-poc.wikibase.cloud/wiki/Project:Copyrights>
- Propriedades: P1–P19
- Entidades-base: Q1–Q6
- Cartazes: Q7–Q15
- Primeiro exemplo: <https://ephemera-poc.wikibase.cloud/wiki/Item:Q7?uselang=pt>
- Mapeamento completo: `wikibase_ids.json`

Os metadados estruturados estão sob CC0. As imagens não estão abrangidas por essa licença: permanecem no Ephemera, são apenas ligadas por URL e têm o estado `não determinado no post de origem`.

## Imagens na Wikibase Cloud

A propriedade P10 contém a URL completa de cada imagem; P16 contém apenas o nome original do ficheiro para identificação e preservação. Por isso, `zppaldef8843_resize.jpg` é apresentado como texto e P10 como hiperligação.

Esta instância não permite carregar ficheiros (`Special:Upload` devolve `File uploads are disabled`). A Wikibase Cloud também não transforma imagens externas em miniaturas: o tipo `Commons media file` funciona apenas para ficheiros publicados no Wikimedia Commons. Estes cartazes não devem ser enviados para o Commons enquanto a licença ou autorização de publicação não estiver confirmada.

Para apresentar e preservar localmente as imagens, a fase seguinte deve usar uma destas arquiteturas:

1. Wikibase/MediaWiki alojada numa plataforma que permita uploads locais, com o tipo `Media file` da extensão Wikibase Local Media;
2. repositório de objetos digitais próprio (por exemplo, S3/MinIO, DAM ou servidor IIIF), mantendo em P10 a URL estável e acrescentando miniaturas na camada de apresentação;
3. Wikimedia Commons, apenas para objetos cuja licença livre ou domínio público esteja documentalmente confirmado.

O Google Photos pode servir para trabalho interno, mas não é recomendado como endereço permanente de preservação: as ligações de partilha não constituem identificadores públicos estáveis. Para a arquitetura final, deve preferir-se armazenamento com URLs persistentes, metadados, controlo de versões e cópias de segurança.

## Ligações externas

As entidades locais usam P14 para o QID do Wikidata e P15 para o artigo da Wikipédia. Foram ligados o tipo documental, o PCP, a eleição, Portugal e a língua portuguesa.

## WordPress → Wikibase

O plugin em `wordpress-ephemera-wikibase-sync/` cria ou atualiza um item quando um post é publicado. Guarda o QID em `_ephemera_wikibase_qid`, tornando a sincronização idempotente. Também aceita os campos `_ephemera_wikidata_id` e `_ephemera_wikipedia_url`.

Antes de o ativar é necessário criar uma conta técnica ou Bot Password no Wikibase Cloud e definir as constantes indicadas no README do plugin. Essa credencial ainda não foi criada.
