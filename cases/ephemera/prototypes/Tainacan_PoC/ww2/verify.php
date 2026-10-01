<?php
require '/var/www/html/wp-load.php';
$map=get_option('ephemera_ww2_map');$rows=json_decode(file_get_contents(__DIR__.'/manifest.json'),true);$checks=[];$images=0;
foreach($rows as $r){
 $id=$map['items']['ephemerajpp:'.$r['source_id']];$a=get_post_meta($id,'_ephemera_ww2_images',true);
 if(count($a)!==count($r['images']))throw new Exception('Image count mismatch');
 foreach($a as $i=>$aid){$path=wp_get_original_image_path($aid);if(hash_file('sha256',$path)!==$r['images'][$i]['sha256'])throw new Exception('Image hash mismatch '.$aid);if((int)wp_get_post_parent_id($aid)!==$id)throw new Exception('Wrong parent');$images++;}
 if($r['collection']!=='editorial'){
  $terms=wp_get_object_terms($id,'tnc_tax_'.$map['taxonomy'],['fields'=>'ids']);if(!in_array($map['term'],$terms))throw new Exception('Missing historical context');
 }
 $checks[]=['source_id'=>$r['source_id'],'id'=>$id,'url'=>get_permalink($id),'images'=>count($a),'date'=>get_post_field('post_date',$id)];
}
$before=json_decode(file_get_contents(__DIR__.'/reports/before.json'),true);$unchanged=[];
foreach($before['counts'] as $b){if(str_starts_with($b['post_type'],'tnc_col_')){$n=wp_count_posts($b['post_type'])->{$b['post_status']}??0;if((int)$n!==(int)$b['n'])throw new Exception('Existing collection changed');$unchanged[$b['post_type']]=(int)$n;}}
echo json_encode(['items'=>$checks,'verified_images'=>$images,'existing_collections'=>$unchanged,'taxonomy'=>$map['taxonomy'],'term'=>$map['term'],'collections'=>$map['collections']],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
