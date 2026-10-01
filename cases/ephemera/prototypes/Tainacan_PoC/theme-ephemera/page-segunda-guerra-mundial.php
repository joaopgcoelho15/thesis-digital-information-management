<?php
get_header();
$map=get_option('ephemera_ww2_map',[]);
$collections=$map['collections']??[];
$selected=isset($_GET['colecao'])?absint($_GET['colecao']):0;
$search=isset($_GET['pesquisa'])?sanitize_text_field(wp_unslash($_GET['pesquisa'])):'';
$level=isset($_GET['unidade'])?sanitize_text_field(wp_unslash($_GET['unidade'])):'';
$types=array_map(function($id){return 'tnc_col_'.(int)$id.'_item';},array_values($collections));
$tax='tnc_tax_'.(int)($map['taxonomy']??0);
$base=['post_type'=>$types?:['__none__'],'post_status'=>'publish','tax_query'=>[['taxonomy'=>$tax,'field'=>'term_id','terms'=>[(int)($map['term']??0)]]]];
$all=get_posts(array_merge($base,['numberposts'=>-1]));$levels=[];
foreach($all as $entry){$value=get_post_meta($entry->ID,'_ephemera_ww2_level',true);if($value)$levels[$value]=$value;}
sort($levels);
$args=array_merge($base,['posts_per_page'=>12,'paged'=>max(1,absint($_GET['pagina']??1)),'orderby'=>'title','order'=>'ASC']);
if(in_array($selected,array_values($collections),true))$args['post_type']=['tnc_col_'.$selected.'_item'];else $selected=0;
if($search!=='')$args['s']=$search;
if(in_array($level,$levels,true))$args['meta_query']=[['key'=>'_ephemera_ww2_level','value'=>$level]];else $level='';
$results=new WP_Query($args);
?>
<main class="eph-topic" id="ww2-catalogue">
<p class="eph-meta">Percursos no arquivo · Contexto histórico</p>
<h1>Segunda Guerra Mundial</h1>
<p class="eph-topic-lead">Cartazes, publicações, fotografias e conjuntos documentais relacionados com 1939–1945. Um tema comum atravessa diferentes coleções do arquivo.</p>
<div class="eph-topic-note"><strong>Amostra do catálogo</strong> · 7 registos de 4 coleções, selecionados a partir de 93 publicações inventariadas. Cada registo pode descrever um documento, uma série ou um conjunto. As datas dos documentos são apresentadas quando identificadas na fonte.</div>
<h2 class="eph-section-title">Explorar os documentos</h2>
<form method="get" action="<?php echo esc_url(get_permalink()); ?>#ww2-catalogue" class="eph-topic-filters">
<label>Pesquisar<input name="pesquisa" type="search" placeholder="Título ou descrição…" value="<?php echo esc_attr($search); ?>"></label>
<label>Coleção<select name="colecao"><option value="">Todas as coleções</option><?php foreach($collections as $cid): ?><option value="<?php echo (int)$cid; ?>" <?php selected($selected,$cid); ?>><?php echo esc_html(get_the_title($cid)); ?></option><?php endforeach; ?></select></label>
<label>Unidade descrita<select name="unidade"><option value="">Todas as unidades</option><?php foreach($levels as $value): ?><option <?php selected($level,$value); ?> value="<?php echo esc_attr($value); ?>"><?php echo esc_html($value); ?></option><?php endforeach; ?></select></label>
<button type="submit">Filtrar</button><a href="<?php echo esc_url(get_permalink()); ?>#ww2-catalogue">Limpar</a>
</form>
<p class="eph-meta" aria-live="polite"><?php $total=(int)$results->found_posts; echo $total.' '.($total===1?'registo encontrado':'registos encontrados'); ?></p>
<div class="eph-topic-grid">
<?php while($results->have_posts()):$results->the_post();$id=get_the_ID();$cid=(int)str_replace(['tnc_col_','_item'],'',get_post_type());$images=get_post_meta($id,'_ephemera_ww2_images',true); ?>
<article class="eph-topic-card">
<a class="eph-topic-picture" href="<?php the_permalink(); ?>" tabindex="-1" aria-hidden="true"><?php the_post_thumbnail('medium_large',['loading'=>'lazy','alt'=>'']); ?></a>
<div><p class="eph-meta"><?php echo esc_html(get_post_meta($id,'_ephemera_ww2_level',true)); ?> · <?php $n=is_array($images)?count($images):0; echo $n.' '.($n===1?'imagem':'imagens'); ?></p>
<h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
<p class="eph-topic-collection"><a href="<?php echo esc_url(get_permalink($cid)); ?>"><?php echo esc_html(get_the_title($cid)); ?></a></p>
<p><?php echo esc_html(wp_trim_words(get_the_content(),32)); ?></p>
<a class="eph-more" href="<?php the_permalink(); ?>">Consultar registo e imagens →</a></div>
</article>
<?php endwhile; wp_reset_postdata(); ?>
</div>
<?php if(!$results->found_posts): ?><p>Não foram encontrados registos com estes filtros. Experimente outra palavra ou escolha todas as coleções.</p><?php endif; ?>
<?php if($results->max_num_pages>1): ?><nav aria-label="Páginas de resultados"><?php echo paginate_links(['base'=>add_query_arg('pagina','%#%'),'format'=>'','current'=>max(1,absint($_GET['pagina']??1)),'total'=>$results->max_num_pages]); ?></nav><?php endif; ?>
<section class="eph-topic-editorial">
<h2 class="eph-section-title">Exposições e atividades</h2>
<p>Publicações sobre a investigação e a divulgação deste período histórico.</p>
<?php $editorials=get_posts(['post_type'=>'post','post_status'=>'publish','meta_key'=>'_ephemera_ww2_editorial','meta_value'=>1,'numberposts'=>5]);foreach($editorials as $entry): ?>
<article class="eph-story"><a href="<?php echo esc_url(get_permalink($entry)); ?>"><?php echo get_the_post_thumbnail($entry->ID,'medium_large',['loading'=>'lazy','alt'=>'']); ?></a><div><p class="eph-meta"><?php echo esc_html(get_the_date('d/m/Y',$entry)); ?> · Exposição</p><h3><a href="<?php echo esc_url(get_permalink($entry)); ?>"><?php echo esc_html($entry->post_title); ?></a></h3><p>Inauguração anunciada para 22 de setembro de 2026, no Barreiro.</p><a class="eph-more" href="<?php echo esc_url(get_permalink($entry)); ?>">Ler a publicação →</a></div></article>
<?php endforeach; ?>
</section>
<p class="eph-topic-note">Este percurso apresenta uma seleção de teste. Consulte também a <a href="https://ephemerajpp.com/category/crono/1939-1945-ii-guerra-mundial/">categoria completa no site Ephemera ↗</a>.</p>
</main>
<?php get_footer(); ?>
