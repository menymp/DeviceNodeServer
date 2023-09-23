<?php
  $file = $_GET['file'];
  $dir = getcwd();
  $file = $dir.'/'.$file;
  $myfile = fopen($file, "r") or die("FAIL");
  echo file_get_contents($file);
  fclose($myfile);
?>