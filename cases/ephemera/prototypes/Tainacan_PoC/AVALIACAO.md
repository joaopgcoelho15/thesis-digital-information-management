# Avaliação prática do Tainacan para o Ephemera

Teste local realizado em 6–7 de setembro de 2026. A conclusão refere-se à amostra de 59 registos, não ao desempenho ou compatibilidade de todo o site Ephemera.

## O que foi efetivamente testado

| Operação | Resultado observado |
|---|---|
| Importar os nove cartazes e 50 linhas do reportório | Duas coleções, 59 itens; importação por código |
| Apresentar imagens | 71 ficheiros locais; miniaturas nativas, sem CSS específico por URL |
| Filtrar o reportório por PCP | Seis resultados, confirmados no browser e pela API |
| Consultar a coleção | Cartões, pesquisa, filtros e paginação nativos |
| Editar uma ficha | Alteração temporária no formulário de edição Tainacan |
| Reutilizar metadados num post | A nota alterada na ficha apareceu no post sem editar o post; a nota foi depois removida |
| Reutilizar imagens num post | Galeria nativa com os nove cartazes e acesso às fichas |
| Repetir a importação concluída | Zero itens adicionais; total mantido em 59 |
| Ler/exportar por API | Dados completos das duas coleções guardados em JSON |

No teste de edição, concluir imediatamente após preencher não conservou a alteração na primeira tentativa; com saída do campo e tempo para gravação, a alteração apareceu. A limpeza final foi confirmada pela API. Esta interação merece validação com colaboradores e feedback claro de gravação. Não foi corrigido o código do Tainacan.

## Benefícios concretos face à PoC Wikibase atual

1. Imagens, fichas e navegação já fazem parte do produto; não foi necessário gerar regras CSS para cada ficheiro nem páginas de tabela em wikitext.
2. Blog e catálogo estão no mesmo WordPress. Os blocos dinâmicos permitem reutilizar os dados do objeto no conteúdo editorial.
3. Filtros, paginação, diferentes vistas e interface de edição já existem. Evita desenvolver uma camada de apresentação equivalente para esta demonstração.
4. A equipa pode concentrar a catalogação num painel conhecido, sem editar QIDs/PIDs. Continua a precisar de aprender o conceito de coleção, item e metadado.
5. A API permite importação, integração e saída dos dados. Esta experiência não prova equivalência ao modelo de afirmações, referências e qualificadores da Wikibase.

## Limitações que a experiência mostrou

- Os valores antigos continuam heterogéneos: títulos em falta, datas como «1930?», siglas e códigos. O Tainacan não os interpreta nem corrige sozinho.
- A data foi importada como texto para preservar incertezas. O filtro permite selecionar valores, mas não oferece neste modelo uma cronologia fiável por intervalos. Isso exige campos adicionais e regras de normalização.
- A interface tem muitos controlos e alguma tradução incompleta. Configurar permissões, campos e vistas por perfil pode simplificá-la; ainda não foi feito um teste de usabilidade com funcionários.
- O Google Drive não foi ligado. As imagens provêm das cópias locais existentes e dos URLs públicos WordPress. Sincronização Drive, permissões e política de publicação continuam a ser trabalho adicional.
- Usou-se o tema oficial num WordPress novo. Não foi testada a compatibilidade com o tema, plugins, alojamento e volume do site real.
- O catálogo facilita acesso e descrição; não substitui uma política de preservação com originais, verificações de integridade e backups independentes.
- A exportação por API foi testada. Importação/exportação CSV nativa, hierarquia arquivística, controlo de autoridades e migração em larga escala ainda não foram validados.

## Recomendação após o teste

O Tainacan mostrou-se uma opção mais direta para o objetivo imediato de um catálogo visual e pesquisável ligado ao blog. Esta é uma conclusão sobre o esforço da PoC, não uma decisão final de migração institucional.

Próximo piloto: um colaborador cria um item com duas imagens, corrige metadados e insere-o num post usando os blocos; outro encontra-o por pesquisa/filtros. Medir tempo, erros e apoio necessário. Depois experimentar uma cópia do tema real, volume progressivo de dados e um fluxo controlado de Drive.

Fluxo proposto: imagens selecionadas → ficha de objeto no Tainacan → inserção/reutilização no post WordPress. Notícias e eventos sem objetos continuam posts normais. O catálogo deve ser a fonte dos metadados dos objetos; duplicá-los como campos independentes do post criaria conflitos.

A Wikibase pode continuar útil para relações semânticas avançadas e investigação, caso haja necessidade e manutenção assegurada. Não é necessário operar duas bases em paralelo já no primeiro produto.
