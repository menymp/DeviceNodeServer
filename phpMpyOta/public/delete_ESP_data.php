<?php
  require __DIR__ . '/../vendor/autoload.php';
  use App\LoggerFactory; 
  $logger = LoggerFactory::create(); 
  $logger->info("Delete script started");

  $file = $_GET['file'];
  $dir = getcwd();
  $file = $dir.'/'.$file;
  $logger->error("Deleting file: " . $file);
  unlink($file);
?>