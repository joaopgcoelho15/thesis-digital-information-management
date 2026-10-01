<?php
if(get_option('home')!=='http://localhost:8087')throw new Exception('Local only');
wp_set_current_user(1);$map=get_option('ephemera_lab_map');
function block($name,$attrs=[]){return '<!-- wp:'.$name.' '.wp_json_encode($attrs,JSON_UNESCAPED_UNICODE).' /-->';}
function page($slug,$title,$body,$type='page'){
 $old=get_page_by_path($slug,OBJECT,$type);
 return wp_insert_post(['ID'=>$old?$old->ID:0,'post_type'=>$type,'post_status'=>'publish','post_name'=>$slug,'post_title'=>$title,'post_content'=>$body]);
}
$first=$map['items']['PCP1975-001'];
$article='<p>Este é um exemplo editorial criado apenas para o laboratório local. Os nove cartazes foram publicados pelo Ephemera num conjunto relativo às Eleições Constituintes de 1975.</p><p>A galeria abaixo consulta a coleção Tainacan. O texto editorial continua num post WordPress; os objetos e os respetivos metadados ficam no catálogo.</p>'.block('tainacan/items-gallery',['collectionId'=>(string)$map['collections']['cartazes'],'maxItemsNumber'=>9,'loadStrategy'=>'search','searchParams'=>['post_status'=>'publish'],'hideItemTitleMain'=>false]).'<h2>Ficha de um cartaz, reutilizada do catálogo</h2>'.block('tainacan/item-metadata',['isDynamic'=>true,'metadata'=>array_map(fn($id)=>['id'=>$id],array_values($map['metadata']['cartazes'])),'itemId'=>$first,'collectionId'=>$map['collections']['cartazes']]).'<p><a href="https://ephemerajpp.com/2014/05/24/eleicoes-para-assembleia-constituinte-1975-pcp/">Consultar o post original do Ephemera</a></p>';
$post=page('cartazes-num-post','Um post, nove objetos do catálogo',$article,'post');
$body='<p><strong>Laboratório local · 59 registos · 2 coleções</strong></p><p>Uma amostra do acervo Ephemera para experimentar imagens, pesquisa, filtros e publicação editorial no mesmo WordPress.</p><h2>Explorar as coleções</h2>';
foreach($map['collections'] as $key=>$cid){$c=new \Tainacan\Entities\Collection($cid);$list=array_values(array_filter(json_decode(file_get_contents('/work/data/sample.json'),true),fn($r)=>$r['collection']===$key));$iid=$map['items'][$list[0]['key']];$aid=get_post_thumbnail_id($iid);$c->set__thumbnail_id($aid);if($c->validate())\Tainacan\Repositories\Collections::get_instance()->insert($c);$url=get_post_type_archive_link($c->get_db_identifier());$body.='<h3><a href="'.esc_url($url).'">'.esc_html($c->get_name()).'</a></h3><p>'.count($list).' objetos · <a href="'.esc_url($url).'">Abrir imagens e filtros →</a></p><a href="'.esc_url($url).'">'.wp_get_attachment_image($aid,'medium').'</a>';}
$body.='<h2>Do catálogo para o blog</h2><p><a href="'.get_permalink($post).'">Ver um post que reutiliza imagens e metadados do Tainacan →</a></p><h2>Experimentar</h2><ol><li>Abra o reportório e filtre a organização por PCP.</li><li>Abra um documento e percorra as imagens.</li><li>No painel Tainacan, edite um registo e confirme o resultado no catálogo.</li><li>Veja os metadados desse objeto aparecerem também no post de demonstração.</li></ol><p><a href="/wp-admin/admin.php?page=tainacan_admin">Abrir painel de catalogação</a></p><p>As imagens são cópias para teste local, com a proveniência indicada. Os direitos não foram alterados. Esta amostra não inclui uma ligação automática ao Google Drive.</p>';
$home=page('laboratorio','Ephemera — Catálogo experimental',$body);update_option('show_on_front','page');update_option('page_on_front',$home);
update_option('blogdescription','Coleções, imagens e pesquisa — teste local com Tainacan');
wp_delete_post(1,true);wp_delete_post(2,true);update_option('sidebars_widgets',['wp_inactive_widgets'=>[]]);
$locations=get_registered_nav_menus();$menu=wp_get_nav_menu_object('Explorar');$mid=$menu?$menu->term_id:wp_create_nav_menu('Explorar');
if(!wp_get_nav_menu_items($mid)){foreach(['Início'=>'/','Cartazes'=>'/cartazes/','Reportório'=>'/reportorio/','Exemplo editorial'=>get_permalink($post)] as $label=>$url)wp_update_nav_menu_item($mid,0,['menu-item-title'=>$label,'menu-item-url'=>$url,'menu-item-status'=>'publish']);}
set_theme_mod('nav_menu_locations',array_fill_keys(array_keys($locations),$mid));
$map['pages']=['home'=>$home,'editorial'=>$post];update_option('ephemera_lab_map',$map);flush_rewrite_rules(true);
WP_CLI::success('Home and native Tainacan blocks published.');
