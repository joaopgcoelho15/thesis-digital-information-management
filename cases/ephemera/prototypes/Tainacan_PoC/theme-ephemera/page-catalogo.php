<?php get_header();$results=eph_catalogue_query();$collections=eph_collections();$groups=eph_classifications();$count=(int)$results->found_posts;$per=$results->get('posts_per_page');$page=$results->get('paged'); ?>
<main class="eph-public-page" id="catalogue-results">
<p class="eph-eyebrow">Biblioteca e arquivo</p><h1>Catálogo</h1><p class="eph-lead">Pesquise documentos de todas as coleções. Combine palavras, coleções e temas para encontrar o que procura.</p>
<form class="eph-catalogue-form" method="get" action="<?php echo esc_url(get_permalink()); ?>#catalogue-results" role="search">
<div class="eph-query"><label for="catalogue-query">O que procura?</label><div><input id="catalogue-query" name="pesquisa" type="search" maxlength="200" value="<?php echo esc_attr(eph_input('pesquisa')); ?>" placeholder="Título, pessoa, lugar, assunto ou identificador…"><button type="submit">Pesquisar</button></div><p>A pesquisa inclui títulos, descrições, metadados públicos e classificações.</p></div>
<div class="eph-filter-row">
<label>Coleção<select name="colecao"><option value="">Todas as coleções</option><?php foreach($collections as $c): ?><option value="<?php echo (int)$c->ID; ?>" <?php selected(eph_input('colecao'),$c->ID); ?>><?php echo esc_html($c->post_title); ?> (<?php echo ephemera_poc_count($c->ID); ?>)</option><?php endforeach; ?></select></label>
<label>Tema / classificação<select name="tema"><option value="">Todos os temas</option><?php foreach($groups as $tax=>$group): ?><optgroup label="<?php echo esc_attr($group['label']); ?>"><?php foreach($group['terms'] as $term):$value=$tax.':'.$term->term_id; ?><option value="<?php echo esc_attr($value); ?>" <?php selected(eph_input('tema'),$value); ?>><?php echo esc_html($term->name); ?></option><?php endforeach; ?></optgroup><?php endforeach; ?></select></label>
<label>Ordenar por<select name="ordem"><option value="az" <?php selected(eph_input('ordem','az'),'az'); ?>>Título, A a Z</option><option value="za" <?php selected(eph_input('ordem'),'za'); ?>>Título, Z a A</option><option value="recentes" <?php selected(eph_input('ordem'),'recentes'); ?>>Adicionados recentemente</option></select></label>
<label>Por página<select name="por_pagina"><?php foreach([12,24,48] as $n): ?><option <?php selected($per,$n); ?>><?php echo $n; ?></option><?php endforeach; ?></select></label>
</div><div class="eph-filter-actions"><button type="submit">Aplicar filtros</button><a href="<?php echo esc_url(get_permalink()); ?>#catalogue-results">Limpar pesquisa e filtros</a></div>
</form>
<?php $ww2=get_option('ephemera_ww2_map',[]);if(!empty($ww2['page']) && eph_input('tema')==='tnc_tax_'.($ww2['taxonomy']??0).':'.($ww2['term']??0)): ?>
<p class="eph-theme-context">Conheça este tema e as atividades relacionadas: <a href="<?php echo esc_url(get_permalink($ww2['page'])); ?>"><?php echo esc_html(get_the_title($ww2['page'])); ?> →</a></p>
<?php endif; ?>
<div class="eph-result-heading"><h2><?php echo $count.' '.($count===1?'registo encontrado':'registos encontrados'); ?></h2><?php if($count): ?><span><?php echo (($page-1)*$per+1).'–'.min($page*$per,$count); ?> de <?php echo $count; ?></span><?php endif; ?></div>
<?php if(!$count): ?><div class="eph-empty"><h3>Não encontrámos registos com esta combinação.</h3><p>Experimente menos palavras ou retire um dos filtros. Também pode procurar diretamente numa coleção.</p><a href="<?php echo esc_url(home_url('/colecoes/')); ?>">Explorar coleções →</a></div><?php else: ?>
<div class="eph-catalogue-grid"><?php foreach($results->posts as $item)eph_item_card($item); ?></div>
<?php endif; eph_pagination($results->max_num_pages,$page); ?>
<section class="eph-help"><h2>Como explorar o arquivo</h2><p>Um registo pode descrever um documento, um álbum ou um conjunto. Os temas atravessam as coleções e não substituem a data de cada documento. Abra um registo para consultar as imagens, a descrição e a origem.</p><p>Procura textos e notícias do arquivo? Consulte as <a href="<?php echo esc_url(home_url('/publicacoes/')); ?>">publicações</a>.</p></section>
</main><?php get_footer(); ?>
