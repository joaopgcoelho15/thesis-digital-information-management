<?php
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('ephemera-fonts', get_stylesheet_directory_uri().'/assets/fonts.css', [], '1.0');
    wp_enqueue_style('ephemera-poc', get_stylesheet_uri(), ['tainacan_tainacanStyle'], filemtime(__DIR__.'/style.css'));
}, 100);

function ephemera_poc_collections() {
    return get_posts(['post_type'=>'tainacan-collection','post_status'=>'publish','numberposts'=>-1,'orderby'=>'ID','order'=>'ASC']);
}
function ephemera_poc_items($collection, $limit = 1) {
    return get_posts(['post_type'=>'tnc_col_'.(int)$collection.'_item','post_status'=>'publish','numberposts'=>$limit,'orderby'=>'ID','order'=>'ASC']);
}
function ephemera_poc_count($collection) {
    $counts = wp_count_posts('tnc_col_'.(int)$collection.'_item');
    return (int)($counts->publish ?? 0);
}
add_action('pre_get_posts', function ($query) {
    if (!is_admin() && $query->is_main_query() && $query->is_search()) {
        $types = ['post', 'page'];
        foreach (ephemera_poc_collections() as $collection) $types[] = 'tnc_col_'.$collection->ID.'_item';
        $query->set('post_type', $types);
    }
});

// Public catalogue. Derive collections and classifications from published data.
function eph_input($key, $default='') {
    return isset($_GET[$key]) && is_string($_GET[$key]) ? sanitize_text_field(wp_unslash($_GET[$key])) : $default;
}
function eph_collections() {
    static $collections;
    if (!isset($collections)) $collections=array_values(array_filter(ephemera_poc_collections(),function($c){return ephemera_poc_count($c->ID)>0;}));
    return $collections;
}
function eph_types() {return array_map(function($c){return 'tnc_col_'.$c->ID.'_item';},eph_collections());}
function eph_classifications() {
    static $groups;
    if (isset($groups)) return $groups;
    $groups=[];$types=eph_types();if(!$types)return $groups;
    global $wpdb;
    foreach(get_taxonomies([], 'objects') as $taxonomy){
        if(!str_starts_with($taxonomy->name,'tnc_tax_') || !array_intersect($types,$taxonomy->object_type))continue;
        $taxid=(int)substr($taxonomy->name,8);
        if(get_post_status($taxid)!=='publish')continue;
        $placeholders=implode(',',array_fill(0,count($types),'%s'));
        $sql="SELECT tt.term_id,COUNT(DISTINCT p.ID) n FROM {$wpdb->term_taxonomy} tt JOIN {$wpdb->term_relationships} r ON r.term_taxonomy_id=tt.term_taxonomy_id JOIN {$wpdb->posts} p ON p.ID=r.object_id WHERE tt.taxonomy=%s AND p.post_status='publish' AND p.post_type IN ($placeholders) GROUP BY tt.term_id";
        $counts=$wpdb->get_results($wpdb->prepare($sql,array_merge([$taxonomy->name],$types)),OBJECT_K);
        if(!$counts)continue;
        $terms=get_terms(['taxonomy'=>$taxonomy->name,'hide_empty'=>false,'include'=>array_keys($counts)]);
        if(is_wp_error($terms))continue;
        $groups[$taxonomy->name]=['label'=>$taxonomy->label,'terms'=>$terms,'counts'=>$counts];
    }
    return $groups;
}
function eph_term_filter($value) {
    foreach(eph_classifications() as $tax=>$group)foreach($group['terms'] as $term)if($value===$tax.':'.$term->term_id)return ['taxonomy'=>$tax,'field'=>'term_id','terms'=>[(int)$term->term_id]];
    return null;
}
function eph_catalogue_query() {
    $types=eph_types();$cid=absint(eph_input('colecao'));$chosen='tnc_col_'.$cid.'_item';
    $args=['post_type'=>in_array($chosen,$types,true)?[$chosen]:($types?:['__none__']),'post_status'=>'publish','has_password'=>false,'posts_per_page'=>in_array((int)eph_input('por_pagina'),[12,24,48],true)?(int)eph_input('por_pagina'):12,'paged'=>max(1,absint(eph_input('pagina','1'))),'orderby'=>'title','order'=>'ASC','eph_catalogue_search'=>mb_substr(eph_input('pesquisa'),0,200)];
    if(eph_input('ordem')==='recentes'){$args['orderby']='date';$args['order']='DESC';}
    if(eph_input('ordem')==='za')$args['order']='DESC';
    $term=eph_term_filter(eph_input('tema'));if($term)$args['tax_query']=[$term];
    return new WP_Query($args);
}
// Search visible text fields and public Tainacan metadata, not internal keys or private fields.
add_filter('posts_where',function($where,$query){
    $search=$query->get('eph_catalogue_search');if(!is_string($search)||trim($search)==='')return $where;
    global $wpdb;
    $taxonomies=array_keys(eph_classifications());
    foreach(array_slice(preg_split('/\s+/u',trim($search)),0,12) as $word){
        $like='%'.$wpdb->esc_like($word).'%';
        $clause=$wpdb->prepare("({$wpdb->posts}.post_title LIKE %s OR {$wpdb->posts}.post_content LIKE %s OR {$wpdb->posts}.post_excerpt LIKE %s OR EXISTS (SELECT 1 FROM {$wpdb->postmeta} em JOIN {$wpdb->posts} md ON em.meta_key=CAST(md.ID AS CHAR) WHERE em.post_id={$wpdb->posts}.ID AND md.post_type='tainacan-metadatum' AND md.post_status='publish' AND em.meta_value LIKE %s)",$like,$like,$like,$like);
        if($taxonomies){$holders=implode(',',array_fill(0,count($taxonomies),'%s'));$clause.=$wpdb->prepare(" OR EXISTS (SELECT 1 FROM {$wpdb->term_relationships} er JOIN {$wpdb->term_taxonomy} et ON et.term_taxonomy_id=er.term_taxonomy_id JOIN {$wpdb->terms} t ON t.term_id=et.term_id WHERE er.object_id={$wpdb->posts}.ID AND et.taxonomy IN ($holders) AND t.name LIKE %s)",array_merge($taxonomies,[$like]));}
        $where.=' AND '.$clause.')';
    }
    return $where;
},10,2);
function eph_search_form($id='archive-search') { ?>
<form class="eph-global-search" method="get" action="<?php echo esc_url(home_url('/catalogo/')); ?>" role="search"><label class="screen-reader-text" for="<?php echo esc_attr($id); ?>">Pesquisar no catálogo</label><input id="<?php echo esc_attr($id); ?>" name="pesquisa" type="search" placeholder="Pesquisar no catálogo…" value="<?php echo esc_attr(eph_input('pesquisa')); ?>"><button type="submit">Pesquisar</button></form>
<?php }
function eph_item_card($item) {
    $cid=(int)get_post_meta($item->ID,'collection_id',true); ?>
<article class="eph-catalogue-card"><a class="eph-card-image" href="<?php echo esc_url(get_permalink($item)); ?>" tabindex="-1" aria-hidden="true"><?php if(has_post_thumbnail($item))echo get_the_post_thumbnail($item,'medium_large',['loading'=>'lazy','alt'=>'']);else echo '<span class="eph-no-image">Sem imagem disponível</span>'; ?></a><div><p class="eph-meta"><?php echo esc_html(get_the_title($cid)); ?></p><h3><a href="<?php echo esc_url(get_permalink($item)); ?>"><?php echo esc_html(get_the_title($item)); ?></a></h3><a class="eph-more" href="<?php echo esc_url(get_permalink($item)); ?>">Consultar registo →</a></div></article>
<?php }
function eph_pagination($total,$current) {
    if($total<2)return;
    echo '<nav class="eph-pagination" aria-label="Páginas de resultados">'.paginate_links(['base'=>esc_url_raw(add_query_arg('pagina','%#%')),'format'=>'','current'=>$current,'total'=>$total,'prev_text'=>'← Anterior','next_text'=>'Seguinte →']).'</nav>';
}
// Existing WordPress search forms also lead to the shared catalogue.
add_action('template_redirect',function(){
    if(!is_admin() && is_search() && !is_feed()){
        wp_safe_redirect(add_query_arg('pesquisa',get_search_query(false),home_url('/catalogo/')),302);exit;
    }
});
