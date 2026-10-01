<?php
// Run only in this local lab, through wp eval-file.
if (get_option('home') !== 'http://localhost:8087') throw new Exception('Local lab only');
wp_set_current_user(1);
require_once ABSPATH.'wp-admin/includes/file.php';
require_once ABSPATH.'wp-admin/includes/media.php';
require_once ABSPATH.'wp-admin/includes/image.php';
function save_entity($e,$repo) {
 if (!$e->validate()) throw new Exception(get_class($e).': '.json_encode($e->get_errors()));
 return $repo->insert($e);
}
$cr=\Tainacan\Repositories\Collections::get_instance();$mr=\Tainacan\Repositories\Metadata::get_instance();$ir=\Tainacan\Repositories\Items::get_instance();$vr=\Tainacan\Repositories\Item_Metadata::get_instance();$fr=\Tainacan\Repositories\Filters::get_instance();
$map=get_option('ephemera_lab_map',[]);
$names=['cartazes'=>'Cartazes do PCP — Constituintes de 1975','reportorio'=>'Reportório da oposição — 50 documentos'];
$fields=['key'=>'Identificador de origem','date'=>'Data na fonte','author'=>'Autor na fonte','organization'=>'Organização na fonte','type'=>'Tipo na fonte','source'=>'Página de origem','notes'=>'Notas na fonte','event'=>'Evento na fonte','country'=>'Local / país na fonte','rights'=>'Direitos das imagens'];
foreach ($names as $key=>$name) {
 if (empty($map['collections'][$key])) {
  $c=new \Tainacan\Entities\Collection();$c->set_name($name);$c->set_slug($key);$c->set_description('Amostra local do Ephemera para testar catalogação, imagens, filtros e reutilização em posts.');$c->set_status('publish');$c->set_default_view_mode('cards');$c->set_default_per_page(12);
  $c=save_entity($c,$cr);$map['collections'][$key]=$c->get_id();update_option('ephemera_lab_map',$map);
 }
 $cid=$map['collections'][$key];
 foreach ($fields as $f=>$label) {
  if (!empty($map['metadata'][$key][$f]))continue;
  $m=new \Tainacan\Entities\Metadatum();$m->set_name($label);$m->set_collection_id($cid);$m->set_metadata_type('Tainacan\\Metadata_Types\\Text');$m->set_status('publish');$m->set_multiple('no');$m->set_required('no');
  if ($f==='date')$m->set_description('Transcrição literal. Interrogações e datas incompletas são preservadas.');
  $m=save_entity($m,$mr);$map['metadata'][$key][$f]=$m->get_id();update_option('ephemera_lab_map',$map);
 }
 foreach (['date','organization','type'] as $f) {
  if (!empty($map['filters'][$key][$f]))continue;
  $filter=new \Tainacan\Entities\Filter();$filter->set_name($fields[$f]);$filter->set_collection_id($cid);$filter->set_metadatum_id($map['metadata'][$key][$f]);$filter->set_filter_type('Tainacan\\Filter_Types\\Selectbox');$filter->set_status('publish');$filter->set_max_options(50);
  $filter=save_entity($filter,$fr);$map['filters'][$key][$f]=$filter->get_id();update_option('ephemera_lab_map',$map);
 }
}
$rows=json_decode(file_get_contents('/work/data/sample.json'),true);$created=0;
foreach ($rows as $r) {
 if (!empty($map['items'][$r['key']]))continue;
 $item=new \Tainacan\Entities\Item();$item->set_collection_id($map['collections'][$r['collection']]);$item->set_title($r['title']);$item->set_description($r['description']);$item->set_status('draft');
 $item=save_entity($item,$ir);
 $r['rights']='Direitos não determinados na fonte. Cópias locais de teste; sem nova licença atribuída.';
 foreach ($fields as $f=>$label) {
  if ($r[$f]==='')continue;
  $meta=new \Tainacan\Entities\Metadatum($map['metadata'][$r['collection']][$f]);
  $v=new \Tainacan\Entities\Item_Metadata_Entity($item,$meta);$v->set_value($r[$f]);save_entity($v,$vr);
 }
 $attachments=[];
 foreach ($r['images'] as $im) {
  $tmp=wp_tempnam($im['file']);copy('/work/data/media/'.$im['file'],$tmp);
  $aid=media_handle_sideload(['name'=>$im['file'],'tmp_name'=>$tmp],$item->get_id(),$r['title'].' — '.$im['role']);
  if(is_wp_error($aid))throw new Exception($aid->get_error_message());
  update_post_meta($aid,'_ephemera_source_url',$im['url']);update_post_meta($aid,'_wp_attachment_image_alt',$r['title'].' — '.$im['role']);
  wp_update_post(['ID'=>$aid,'post_excerpt'=>$im['role'],'post_content'=>'Origem: '.$im['url'].' | Cópia para teste local.']);$attachments[]=$aid;
 }
 if($attachments){$item->set_document_type('attachment');$item->set_document((string)$attachments[0]);$item->set__thumbnail_id($attachments[0]);}
 $item->set_status('publish');$item=save_entity($item,$ir);
 update_post_meta($item->get_id(),'_ephemera_source_key',$r['key']);
 $map['items'][$r['key']]=$item->get_id();update_option('ephemera_lab_map',$map);$created++;
 WP_CLI::log('Imported '.$item->get_id().' '.$r['title']);
}
flush_rewrite_rules(true);
WP_CLI::success('Created '.$created.'; total '.count($map['items']));
