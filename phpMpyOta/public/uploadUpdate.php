<?php
require __DIR__ . '/../vendor/autoload.php';

/*
NOTE: this is an experiment with bing chat-gpt generated code at october 2023 01
those were the prompted command inputs for the result

having a named version file with the following json content {"version":"1.0.0", "files":["main.py","module1.py"]} in the linux directory 
sampleproject create a php endpoint script that receives a group of .py files and creates a new directory in the sampleproject directory 
with the version json number plus 1 in the sampleproject/version file, then moves the received files in the created version plus 1 directory, 
then inside this directory, create a new file named version that contains two keys, one of them is version and its value is the name of the 
parent directory, the second is an array that contains all the names and extensions of the received .py files present in the directory, 
now in the sampleproject directory make a copy of the existing file named version with the new file name being version and the version key 
value inside the current named version file, finally copies the new file named version and puts in the sampleproject directory

some extracts from the result:

Here is an example PHP script that receives a group of .py files and creates a new directory in the sampleproject directory with the version json
 number plus 1 in the sampleproject/version file, then moves the received files in the created version plus 1 directory, then inside this directory, 
 creates a new file named version that contains two keys, one of them is version and its value is the name of the parent directory, 
 the second is an array that contains all the names and extensions of the received .py files present in the directory. Finally, 
 it copies the new file named version and puts it in the sampleproject directory.

CODE INSIDE PHP TAGS!!!

This script assumes that you have a file named version in your sampleproject directory with the following JSON content:

{
    "version": 1.0,
    "files": [
        "main.py",
        "module1.py"
    ]
}
Copiar
When you upload a group of .py files to this script, it creates a new directory with a name equal to the current version number plus 1.
 It then moves all uploaded .py files to this new directory and creates a new file named version inside this directory with two keys: version, 
 which contains the name of the parent directory, and files, which contains an array of all .py files present in this directory. Finally, 
 it copies the new version file to sampleproject/version_{current_version} and replaces the contents of sampleproject/version with the contents of the new version file.

 chatgpt is still a long way to be a real coder, but the result are really impresive at first glance
*/

$projectName = $_POST['projectName'];

$dir = './' . $projectName;
$version_file = $dir . '/version';
$version_data = json_decode(file_get_contents($version_file), true);
$version = $version_data['version'];
$new_version = $version + 1;
$new_dir = $dir . '/' . $new_version;
mkdir($new_dir);
$files = $_FILES['files'];
$file_names = array();
for($i = 0; $i < count($files['name']); $i++) {
    if (pathinfo($files['name'][$i], PATHINFO_EXTENSION) == 'py') {
        $file_names[] = $files['name'][$i];
        move_uploaded_file($files['tmp_name'][$i], $new_dir . '/'. $files['name'][$i]);
        // file_put_contents($new_dir . '/'. $file['name'],  $file['data']);
    }
}
$new_version_data = (object) [
    'version' => $new_version,
    'files' => $file_names
];

file_put_contents($new_dir . '/version', json_encode($new_version_data));
copy($version_file, $dir . '/version_' . $version);
$result = copy($new_dir . '/version', $dir . '/version');
echo(var_export($result));
?>
