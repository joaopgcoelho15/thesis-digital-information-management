<!doctype html>
<html <?php language_attributes(); ?>>
<head><meta charset="<?php bloginfo('charset'); ?>"><meta name="viewport" content="width=device-width, initial-scale=1"><?php wp_head(); ?></head>
<body <?php body_class('ephemera-poc'); ?>>
<?php wp_body_open(); ?>
<a class="eph-skip" href="#ephemera-content">Saltar para o conteúdo</a>
<div class="eph-shell">
<header>
<div class="eph-quote"><div class="eph-quotations"><p class="eph-quote-title">CITAÇÕES DO ARQUIVO EPHEMERA</p><blockquote><p>"Se o Diabo publicar panfletos vamos ao Inferno recolhe-los."</p><p>"Se nos oferecerem o pórtico da Lisnave aceitamos e depois vemos onde o pomos e como lhe damos vida e memória."</p></blockquote></div><small class="eph-demo">PoC · demonstração local</small></div>
<a href="<?php echo esc_url(home_url('/')); ?>" aria-label="Ephemera — início"><img class="eph-banner" src="<?php echo esc_url(get_stylesheet_directory_uri().'/assets/banner.jpg'); ?>" width="1500" height="347" alt="Biblioteca e arquivo Ephemera"></a>
<div class="eph-brand"><a class="eph-brand-logo" href="<?php echo esc_url(home_url('/')); ?>" aria-label="Ephemera — início"><img src="<?php echo esc_url(get_stylesheet_directory_uri().'/assets/ephemera-logo.jpg'); ?>" width="500" height="599" alt="Ephemera"></a><div class="eph-brand-copy"><a href="<?php echo esc_url(home_url('/')); ?>">Ephemera - Biblioteca e arquivo de José Pacheco Pereira</a><p>“The two offices of memory are collection and distribution.” (Samuel Johnson)</p></div></div>
<div class="eph-navigation-bar"><nav class="eph-nav" aria-label="Navegação principal">
<?php foreach([''=>'Início','catalogo'=>'Catálogo','colecoes'=>'Coleções','publicacoes'=>'Publicações'] as $slug=>$label): ?>
<a href="<?php echo esc_url(home_url('/'.$slug.($slug?'/':''))); ?>" <?php if(($slug===''&&is_front_page())||($slug!==''&&is_page($slug))||($slug==='colecoes'&&is_post_type_archive('tainacan-collection')))echo 'aria-current="page"'; ?>><?php echo esc_html($label); ?></a>
<?php endforeach; ?></nav><?php eph_search_form('header-catalogue-search'); ?></div>
</header>
<div id="ephemera-content" tabindex="-1"></div>
