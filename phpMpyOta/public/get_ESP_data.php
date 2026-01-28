<?php
require __DIR__ . '/../vendor/autoload.php';
  use App\LoggerFactory; 
  $logger = LoggerFactory::create(); 
  $logger->info("Retriving php script started");

  $file = $_GET['file'];
  $dir = getcwd();
  $file = $dir.'/'.$file;

  $logger->info("Opening file: " . $file);
  $myfile = fopen($file, "r") or die("FAIL");
  echo file_get_contents($file);
  fclose($myfile);
?>