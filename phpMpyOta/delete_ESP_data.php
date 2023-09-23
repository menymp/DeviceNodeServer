<?php
  $file = $_GET['file'];
  $dir = getcwd();
  $file = $dir.'/'.$file;
  unlink($file);
?>