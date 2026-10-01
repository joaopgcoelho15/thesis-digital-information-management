<?php
// Re-runnable, local-only import. Run with php after copying this directory to /tmp/ephemera-ww2.
require '/var/www/html/wp-load.php';
if (get_option('home') !== 'http://localhost:8087') throw new Exception('Local PoC only');
wp_set_current_user(1);
require_once ABSPATH.'wp-admin/includes/file.php';
require_once ABSPATH.'wp-admin/includes/media.php';
require_once ABSPATH.'wp-admin/includes/image.php';
function persist($entity,$repo) {
 if (!$entity->validate()) throw new Exception(get_class($entity).': '.json_encode($entity->get_errors()));
 return $repo->insert($entity);
}
function checkpoint(){global $map;update_option('ephemera_ww2_map',$map,false);}
function find_key($key,$type='any'){
 $ids=get_posts(['post_type'=>$type,'post_status'=>['publish','draft','private','pending','inherit','future'],'numberposts'=>2,'fields'=>'ids','meta_key'=>'_ephemera_ww2_key','meta_value'=>$key]);
 if(count($ids)>1)throw new Exception('Duplicate source key: '.$key);
 return $ids[0]??0;
}
$cr=\Tainacan\Repositories\Collections::get_instance();$mr=\Tainacan\Repositories\Metadata::get_instance();$ir=\Tainacan\Repositories\Items::get_instance();$vr=\Tainacan\Repositories\Item_Metadata::get_instance();$tr=\Tainacan\Repositories\Taxonomies::get_instance();$fr=\Tainacan\Repositories\Filters::get_instance();
$map=get_option('ephemera_ww2_map',[]);$created=['items'=>0,'attachments'=>0,'posts'=>0];
$names=['propaganda'=>'Materiais de propaganda','periodicos'=>'Publicações periódicas','conjuntos'=>'Álbuns e conjuntos documentais','fotografias'=>'Fotografias históricas'];
foreach($names as $key=>$name){
 if(empty($map['collections'][$key])){
  $c=new \Tainacan\Entities\Collection();$c->set_name($name);$c->set_slug('acervo-'.$key);$c->set_description('Amostra do acervo Ephemera. O contexto histórico permite pesquisar estes registos em conjunto com outras coleções.');$c->set_status('publish');$c->set_default_view_mode('cards');$c->set_default_per_page(12);
  $c=persist($c,$cr);$map['collections'][$key]=$c->get_id();checkpoint();
 }
}
if(empty($map['taxonomy'])){
 $t=new \Tainacan\Entities\Taxonomy();$t->set_name('Contexto histórico');$t->set_slug('contexto-historico');$t->set_description('Classificação histórica transversal. Não corresponde à data de produção de cada documento.');$t->set_status('publish');$t->set_allow_insert('yes');$t->set_hierarchical('yes');$t->set_collections_ids(array_values($map['collections']));
 $t=persist($t,$tr);$map['taxonomy']=$t->get_id();checkpoint();
}
$t=new \Tainacan\Entities\Taxonomy($map['taxonomy']);$t->tainacan_register_taxonomy();$tax=$t->get_db_identifier();
if(empty($map['term'])){
 $term=term_exists('segunda-guerra-mundial-1939-1945',$tax);
 if(!$term)$term=wp_insert_term('Segunda Guerra Mundial, 1939–1945',$tax,['slug'=>'segunda-guerra-mundial-1939-1945','description'=>'Tema histórico comum às coleções. As datas específicas dos documentos constam dos respetivos registos.']);
 if(is_wp_error($term))throw new Exception($term->get_error_message());$map['term']=(int)$term['term_id'];checkpoint();
}
$fields=['source_id'=>'Identificador no WordPress de origem','source'=>'Página de origem','original_title'=>'Título na fonte','published'=>'Data de publicação no site de origem','date'=>'Data do documento indicada na fonte','level'=>'Tipo de unidade descrita','source_text'=>'Texto na fonte','notes'=>'Notas de catalogação','rights'=>'Direitos das imagens','context'=>'Contexto histórico'];
foreach($map['collections'] as $key=>$cid){
 foreach($fields as $f=>$label){
  if(!empty($map['metadata'][$key][$f]))continue;
  $m=new \Tainacan\Entities\Metadatum();$m->set_name($label);$m->set_collection_id($cid);$m->set_status('publish');$m->set_required('no');$m->set_multiple($f==='context'?'yes':'no');$m->set_metadata_type('Tainacan\\Metadata_Types\\'.($f==='context'?'Taxonomy':'Text'));
  if($f==='date')$m->set_description('Data transcrita quando documentada. Não é preenchida a partir da categoria histórica nem da data do post.');
  if($f==='context')$m->set_metadata_type_options(['taxonomy_id'=>$map['taxonomy'],'allow_new_terms'=>'no','input_type'=>'tainacan-taxonomy-checkbox']);
  $m=persist($m,$mr);$map['metadata'][$key][$f]=$m->get_id();checkpoint();
 }
 foreach(['context','level'] as $f){
  if(!empty($map['filters'][$key][$f]))continue;
  $x=new \Tainacan\Entities\Filter();$x->set_name($fields[$f]);$x->set_collection_id($cid);$x->set_metadatum_id($map['metadata'][$key][$f]);$x->set_filter_type('Tainacan\\Filter_Types\\'.($f==='context'?'TaxonomySelectbox':'Selectbox'));$x->set_status('publish');$x->set_max_options(50);
  $x=persist($x,$fr);$map['filters'][$key][$f]=$x->get_id();checkpoint();
 }
}
function image_import($im,$parent,$title,$sequence){
 global $created;
 $key='image:'.$im['url'];$aid=find_key($key,'attachment');
 if(!$aid){
  $path=__DIR__.'/media/'.$im['file'];if(hash_file('sha256',$path)!==$im['sha256'])throw new Exception('Hash mismatch');
  $tmp=wp_tempnam($im['file']);copy($path,$tmp);
  $aid=media_handle_sideload(['name'=>$im['file'],'tmp_name'=>$tmp],$parent,$title.' — '.$im['role']);
  if(is_wp_error($aid))throw new Exception($aid->get_error_message());
  update_post_meta($aid,'_ephemera_ww2_key',$key);update_post_meta($aid,'_ephemera_source_url',$im['url']);update_post_meta($aid,'_ephemera_source_sha256',$im['sha256']);update_post_meta($aid,'_wp_attachment_image_alt',$title.' — '.$im['role']);
  wp_update_post(['ID'=>$aid,'menu_order'=>$sequence,'post_excerpt'=>$im['role'],'post_content'=>'Origem: '.$im['url']]);$created['attachments']++;
 }
 return $aid;
}
$rows=json_decode(file_get_contents(__DIR__.'/manifest.json'),true,512,JSON_THROW_ON_ERROR);
foreach($rows as $r){
 $key='ephemerajpp:'.$r['source_id'];$editorial=$r['collection']==='editorial';
 $type=$editorial?'post':'tnc_col_'.$map['collections'][$r['collection']].'_item';
 $id=$map['items'][$key]??find_key($key,$type);
 if($id && get_post_meta($id,'_ephemera_ww2_complete',true)){echo "Already imported $id\n";continue;}
 if(!$id){
  if($editorial){$id=wp_insert_post(['post_type'=>'post','post_status'=>'draft','post_title'=>$r['title'],'meta_input'=>['_ephemera_ww2_key'=>$key]],true);if(is_wp_error($id))throw new Exception($id->get_error_message());$created['posts']++;}
  else{$item=new \Tainacan\Entities\Item();$item->set_collection_id($map['collections'][$r['collection']]);$item->set_title($r['title']);$item->set_description($r['notes']);$item->set_status('draft');$item=persist($item,$ir);$id=$item->get_id();update_post_meta($id,'_ephemera_ww2_key',$key);$created['items']++;}
  $map['items'][$key]=$id;checkpoint();
 }
 $aids=[];foreach($r['images'] as $i=>$im)$aids[]=image_import($im,$id,$r['title'],$i);
 update_post_meta($id,'_ephemera_ww2_images',$aids);update_post_meta($id,'_ephemera_source_url',$r['source']);
 if($editorial){
  $body='<p><strong>Publicação de 18 de setembro de 2026 · Exposição</strong></p>'.wpautop(esc_html($r['source_text']));
  $body.='<p><a href="'.esc_url($r['source']).'">Consultar a publicação original e as galerias da exposição no site Ephemera</a></p>';
  $body.='<p><a href="'.esc_url(home_url('/segunda-guerra-mundial/')).'">Explorar documentos sobre a Segunda Guerra Mundial no catálogo</a>. A ligação é temática; não indica que estes documentos integrem a exposição.</p>';
  if($aids){set_post_thumbnail($id,$aids[0]);$body=wp_get_attachment_image($aids[0],'large').$body;}
  $date=new DateTimeImmutable($r['published']);
  wp_update_post(['ID'=>$id,'post_status'=>'publish','post_content'=>$body,'post_name'=>'a-outra-guerra-exposicao-2026','edit_date'=>true,'post_date'=>$date->format('Y-m-d H:i:s'),'post_date_gmt'=>$date->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s')]);
  update_post_meta($id,'_ephemera_ww2_editorial',1);$map['editorial']=$id;
 }else{
  $item=new \Tainacan\Entities\Item($id);$r['rights']='Direitos não determinados na fonte. Cópias para demonstração local; sem nova licença atribuída.';$r['context']=[(int)$map['term']];
  foreach($fields as $f=>$label){if(!isset($r[$f]) || $r[$f]==='')continue;$v=new \Tainacan\Entities\Item_Metadata_Entity($item,new \Tainacan\Entities\Metadatum($map['metadata'][$r['collection']][$f]));$v->set_value($r[$f]);persist($v,$vr);}
  if($aids){$item->set_document_type('attachment');$item->set_document((string)$aids[0]);$item->set__thumbnail_id($aids[0]);}
  $item->set_status('publish');persist($item,$ir);update_post_meta($id,'_ephemera_ww2_level',$r['level']);
 }
 update_post_meta($id,'_ephemera_ww2_complete',1);checkpoint();echo "Imported $id: {$r['title']} (".count($aids)." images)\n";
}
if(empty($map['page'])){
 $page=get_page_by_path('segunda-guerra-mundial');
 if($page)throw new Exception('Page slug already exists outside this import');
 $id=wp_insert_post(['post_type'=>'page','post_status'=>'publish','post_title'=>'Segunda Guerra Mundial','post_name'=>'segunda-guerra-mundial'],true);if(is_wp_error($id))throw new Exception($id->get_error_message());$map['page']=$id;checkpoint();
}
flush_rewrite_rules(false);
echo json_encode(['created'=>$created,'map'=>$map],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)."\n";
