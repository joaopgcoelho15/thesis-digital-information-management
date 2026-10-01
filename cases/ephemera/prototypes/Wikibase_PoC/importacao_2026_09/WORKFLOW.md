# Proposta de utilização simples do catálogo Ephemera

Estado em 6 de setembro de 2026: proposta funcional. Não foi instalado um serviço contínuo, nem ligada uma conta Google Drive. A importação e o catálogo da PoC estão publicados; a execução atual ainda depende de scripts e da sessão no browser.

## Princípio

A equipa trabalha no WordPress e no Drive. A Wikibase é o catálogo estruturado nos bastidores. Uma única interface de edição evita introduzir os mesmos dados duas vezes. Usar QIDs e PIDs diretamente deve ficar reservado à administração especializada.

## Fluxo de um novo registo

1. O colaborador prepara as imagens numa pasta institucional do Drive destinada ao registo.
2. No WordPress, cria o post e escolhe a pasta ou ficheiros através de um seletor. Para o piloto, pode começar por colar uma ligação da pasta uma única vez.
3. Um painel «Catálogo» apresenta campos simples: título, tipo, coleção, data (com possibilidade de incerteza), autor quando conhecido e indicação de quais as imagens autorizadas para consulta pública. Os valores existentes no post são reaproveitados.
4. Publicar coloca uma tarefa na fila. O post não fica dependente da disponibilidade da Wikibase.
5. O serviço lê as imagens pela API Drive com autorização limitada, gera cópias de consulta, regista o ID Drive e a versão/hash e associa-as ao QID. Os originais podem permanecer privados. Não se publica automaticamente toda a conta.
6. Cria ou atualiza apenas os campos geridos pelo sistema na Wikibase. A ligação post–QID é guardada automaticamente, incluindo o reconhecimento dos cinco posts já importados.
7. O painel mostra «A sincronizar», «Sincronizado» ou «Precisa de atenção». Uma falha transitória é repetida automaticamente. Depois de falhas persistentes, surge uma explicação simples e um botão «Tentar novamente».
8. O catálogo público apresenta dados e miniaturas. Editar novamente o post atualiza o mesmo registo. Retirar a publicação marca o estado segundo uma política definida; não apaga silenciosamente o arquivo.

## Decisões de modelação que evitam trabalho posterior

- Post editorial e objeto arquivístico são entidades diferentes. Um post com nove cartazes não equivale necessariamente a nove objetos nem a um só: o formulário deve permitir selecionar «um objeto», «conjunto» ou «post informativo». No piloto, o padrão pode ser registo editorial, sem inferir a decomposição.
- A relação entre ficheiro e objeto deve usar IDs permanentes, não apenas nomes ou posição na pasta. Vários ficheiros podem representar frente/verso do mesmo objeto.
- Cada tabela tem um mapeamento inicial; cada linha precisa de ID persistente. Começar pela TablePress 77, sem prometer interpretar automaticamente todas as tabelas futuras.
- WordPress gere os campos editoriais definidos; enriquecimentos especializados na Wikibase ficam preservados. Alterações concorrentes nos mesmos campos exigem reconciliação explícita.

## Alojamento

Wikibase Cloud também permite automatização pela API. O Drive pode alimentar automaticamente um armazenamento externo com URLs estáveis; P10 e a camada de apresentação usam essas URLs. O CSS atual é uma solução de PoC e exige regeneração quando as URLs mudam.

Numa Wikibase com uploads e Wikibase Local Media, o serviço pode carregar as cópias diretamente na wiki e criar declarações do tipo de ficheiro local. A palavra «local» significa local ao repositório da wiki, mesmo que o servidor seja uma VPS alugada num fornecedor. As propriedades URL existentes devem ser preservadas; criar uma propriedade de ficheiro local adequada, sem tentar mudar o tipo de P10 em uso.

Não comprar equipamento. Se a apresentação nativa justificar mudar de Cloud, contratar alojamento e manutenção da aplicação, não apenas uma VPS. Confirmar explicitamente atualizações de MediaWiki/Wikibase/extensões, restauro de backups, monitorização, suporte e manutenção do sincronizador. A gestão do sistema operativo não garante suporte à aplicação.

## Piloto do produto, pela ordem proposta

1. Definir quem edita cada campo e que conteúdo representa um objeto. Restringir o piloto a um tipo de conteúdo e uma pasta de teste.
2. Corrigir o plugin experimental (remover `clear=1`), configurar autenticação técnica e persistência da fila, adicionar reintentos e registo post–QID. O processo não deve depender do computador ou sessão do investigador.
3. Acrescentar o painel simples no WordPress e ligação controlada ao Drive; reaproveitar campos para evitar duplicação.
4. Ligar as cópias de consulta ao catálogo e automatizar a atualização da apresentação.
5. Validar um post novo, uma alteração, uma imagem nova, uma falha da Wikibase, um ficheiro sem acesso e uma reexecução. Nenhum caso deve exigir consola ao colaborador nem criar duplicados.
6. Testar com colaboradores reais. Só depois avançar para migração histórica por lotes, com relatório de exceções e possibilidade de retomar.

## Critérios de aceitação

- Um colaborador publica sem conhecer QIDs, PIDs, CSS ou APIs.
- Zero cópia manual de metadados entre WordPress e Wikibase.
- Publicar funciona mesmo que a Wikibase esteja indisponível; a fila recupera depois.
- Uma edição atualiza o mesmo item e preserva enriquecimentos não geridos pelo plugin.
- Erros são compreensíveis; só exceções exigem atenção humana.
- As responsabilidades de manutenção e a recuperação de dados têm um responsável identificado.

Se não existir suporte técnico sustentável, a PoC não deve ser considerada pronta para produção, mesmo que a interface seja simples. Deve comparar-se o benefício concreto da Wikibase com manter o catálogo estruturado no WordPress e exportá-lo periodicamente.
