# Relatório sobre a estrutura e a qualidade do XML

## Âmbito e método

Foi analisado `ACL documentos/dic.xml.xz` em streaming. O ficheiro comprimido tem 18 211 940 bytes, corresponde a 186 699 819 bytes descomprimidos e tem SHA-256:

`a6bca7210726cc9b551d5de7963825ab729ad1d642e0da160a99a96a59828c28`

O XML está bem formado. A análise contou elementos, atributos, relações pai-filho, IDs, estados, referências e anomalias. Foi ainda validada cada entrada isoladamente contra `academia.rng` e a sua dependência `TEILex0.rng`. O consolidado completo não pode ser válido contra esse esquema porque a sua raiz `<dic>` não é uma entrada TEI.

## Estrutura global

| Propriedade | Resultado |
|---|---:|
| Elemento raiz | `dic` sem namespace |
| Profundidade máxima | 10 |
| Entradas totais | 244 124 |
| Entradas DLP | 105 955 |
| Entradas Vocabulário (`volp="only"`) | 138 169 |
| Sentidos | 232 317 |
| Definições | 231 474 |
| `xml:id` distintos | 476 320 |
| Lemas normalizados distintos | 217 537 |
| Lemas com mais de uma entrada | 29 017 |

A raiz agregadora contém entradas no namespace TEI. Existem ainda dois namespaces de metadados editoriais: o atual `http://dacl.zbr.pt/annotations` e o legado `http://www.dacl.pt/schema`.

Elementos mais frequentes:

| Elemento | Ocorrências |
|---|---:|
| `orth` | 324 328 |
| `form` | 317 197 |
| `gramGrp` | 247 589 |
| `entry` | 244 124 |
| `sense` | 232 317 |
| `def` | 231 474 |
| `ref` | 215 401 |
| `cit` | 175 492 |
| `quote` | 128 847 |
| `xr` | 124 144 |
| `meta` | 105 952 |
| `etym` | 80 729 |
| `usg` | 71 303 |

Os ficheiros CSV em `dados_analise_xml/` contêm todos os elementos, atributos e relações pai-filho, incluindo a separação DLP/Vocabulário.

## Relações e regras editoriais implícitas

As principais relações estruturais observadas são:

- `dic → entry`: agregação das unidades lexicográficas;
- `entry → form → orth`: forma/lema;
- `entry → sense`, com sentidos encaixados para subsentidos;
- `sense → def`: definição;
- `sense/entry → cit → quote`: exemplos e citações;
- `xr → ref`: remissões e relações lexicais;
- `entry → meta`: estado editorial;
- `entry → re`: formas ou expressões relacionadas.

Regras implícitas deduzidas, a confirmar editorialmente:

1. `entry@xml:id` é o identificador persistente da entrada.
2. O ID do sentido deveria derivar do ID da entrada por um sufixo numérico.
3. `entry@volp="only"` separa registos do Vocabulário dos do DLP.
4. `meta@status` representa maturidade editorial, mas não há prova de que controle sozinho a publicação.
5. `note@type="soon"` e definições `[...]` aparecem associados a conteúdo por completar; há 21 726 notas deste tipo e 21 730 definições provisórias.
6. A multiplicidade de entradas com o mesmo lema representa sobretudo homógrafos e sobreposição DLP/Vocabulário, não necessariamente duplicação errada.

## Estados editoriais

Contagem conjunta dos dois namespaces `meta`:

| Estado | Ocorrências |
|---|---:|
| `imported` | 61 104 |
| `draft` | 21 842 |
| `new` | 13 322 |
| `edited` | 7 785 |
| `reviewed` | 767 |
| `validated` | 620 |
| `revised` | 487 |
| `needs revision` | 24 |
| vazio | 1 |

Há 11 entradas DLP sem `meta`; no Vocabulário, 138 161 não têm `meta` e oito estão como `new`.

O `academia.rng` permite apenas `imported`, `edited`, `new`, `reviewed` e `validated`. Logo, `draft`, `revised`, `needs revision` e o valor vazio são incompatíveis com o esquema atual. O código público também apresenta um vocabulário ligeiramente diferente, tratando `revised`/`reviewed` como variantes. É necessária uma máquina de estados única, com transições, permissões e semântica de publicação.

Não foi encontrada uma regra que prove que apenas determinado estado é público. A entrada pública `cavalo` tem estado `edited`, mas um exemplo não permite inferir a regra geral.

## Validação formal

Foram encontradas 118 230 instruções `xml-model`:

- 107 056 apontam por HTTPS para `academia.rng`;
- 11 174 apontam para uma variante HTTP antiga.

Não existe referência atual a DTD ou XSD no consolidado. O processo de 2016 usou historicamente uma DTD e um exemplo antigo do repositório aponta para XSD, mas a regra atual encontrada é Relax NG.

Validação de cada `<entry>` como documento independente:

| Coleção | Válidas | Total | Taxa |
|---|---:|---:|---:|
| DLP | 44 154 | 105 955 | 41,67% |
| Vocabulário | 0 | 138 169 | 0% |
| Total | 44 154 | 244 124 | 18,09% |

As falhas dominantes do Vocabulário são a ausência do `sense` esperado e o atributo `volp` não permitido. No DLP, surgem conteúdo/ordem inesperados em `entry`, `form`, `meta` e `re`, entre outras diferenças. Isto mostra que o esquema recolhido é um perfil DLP que não acompanha integralmente os dados efetivos e não modela o Vocabulário.

A configuração eXist do repositório público tem validação automática desligada. Assim, o esquema funciona como verificação separada, não como barreira garantida à gravação.

## Inconsistências e candidatos a revisão

### Problemas de integridade fortes

- um `xml:id` duplicado: `DLP-tangentoide_2-76d57`;
- 82 sentidos sem `xml:id`;
- 1 726 IDs de sentido não derivados do ID da entrada;
- duas entradas sem lema;
- dois valores de data não reconhecidos: `90/02/2016` e `4/17/2017`;
- atributos aparentando gralhas: `xml:land`, `tpe`, `tyupe`, `xml:ida`;
- etiquetas aparentando gralhas ou variantes legadas, como `usgGeo`, `usgDom` e `EtPed`;
- 30 valores `ref@type="entry***"` e 17 casos em que `ref@type` contém indevidamente um URL IUPAC.

### Conteúdo incompleto ou suspeito

- 21 730 sentidos com definição `[...]`;
- 21 515 notas com marcadores provisórios;
- 796 sentidos sem `def` diretamente filho;
- 523 entradas com sentidos mas sem definição em qualquer nível;
- 313 entradas DLP sem sentidos de primeiro nível;
- 15 623 `gramGrp` iguais a `???`, todos no Vocabulário;
- 186 números de sentido não inteiros, muitos dos quais são romanos e podem ser intencionais;
- 90 casos candidatos a repetição ou ordem anómala da numeração de sentidos.

### Referências

Existem 215 197 referências do tipo entrada. Em 11 602 ocorrências, correspondentes a 6 134 valores distintos, o texto normalizado não coincide exatamente com nenhum lema normalizado. Há também 7 591 referências com espaço inicial ou final.

Estas referências não podem ser classificadas automaticamente como quebradas: algumas contêm frases, variantes, afixos ou instruções editoriais. Devem ser reconciliadas por ID, e não apenas por texto. A ausência de destino estruturado torna hoje difícil distinguir remissão válida, conteúdo ainda não importado e dado perdido.

## XML consolidado versus ficheiros individuais

O que pode ser afirmado:

- os artigos descrevem armazenamento de uma entrada por documento no eXist;
- as mensagens mencionam aproximadamente 140 mil ficheiros individuais e um XML único;
- o consolidado tem uma raiz artificial `<dic>`;
- as 118 230 instruções `xml-model` internas são compatíveis com agregação de documentos independentes;
- o consolidado contém conjuntamente DLP e Vocabulário.

O que ainda não pode ser medido:

- correspondência um-para-um entre documentos e entradas;
- diferenças de conteúdo, espaços, comentários, PIs e ordem;
- entradas presentes apenas numa representação;
- nomes de ficheiro versus `xml:id`;
- qual representação vence em caso de conflito;
- frequência e direção da sincronização.

Para responder definitivamente é necessário obter o arquivo dos ficheiros individuais e os scripts atuais de importação/exportação. A comparação recomendada é: extrair cada entrada, normalizar por XML Canonicalization (C14N), associar por `xml:id`/nome do ficheiro e calcular hashes e diferenças estruturais.

## Avaliação geral

O XML é recuperável e suficientemente estruturado para uma migração, mas não deve ser importado cegamente para tabelas definitivas. A qualidade é desigual: IDs e TEI dão uma boa base, enquanto estados, referências textuais, extensões e conteúdo provisório exigem perfis explícitos e validação progressiva.

Prioridades:

1. preservar o original e garantir ida e volta sem perda;
2. separar esquemas DLP e Vocabulário ou criar um esquema modular;
3. corrigir IDs duplicados/ausentes e estabilizar sentidos;
4. unificar namespaces e estados editoriais;
5. transformar remissões textuais em relações por ID;
6. tornar validação obrigatória por nível: bem formado, esquema, regras Schematron e regras editoriais;
7. só depois normalizar o modelo relacional e publicar na Wikidata.

