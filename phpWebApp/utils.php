<?php
/*
utils.php

December 2023

menymp

contains usefull functions

 */

 /*
 EncodeJSONClientResponse

 encodes a json for output response
  */
function EncodeJSONClientResponse($inData)
{
	//header("Content-Type: application/json");
	$json = json_encode($inData);
	if ($json === false) 
	{
		// Avoid echo of empty string (which is invalid JSON), and
		// JSONify the error message instead:
		$json = json_encode(["jsonError" => json_last_error_msg()]);
		if ($json === false) {
			// This should not happen, but we go all the way now:
			$json = '{"jsonError":"unknown"}';
		}
        // Set HTTP response status code to: 500 - Internal Server Error
		http_response_code(500);
	}
	return $json;
}

 /*
 getJsonPostData

 encodes raw json input POST parameters into json object
  */
function getJsonPostData()
{
    // Get the raw JSON data
    $rawData = file_get_contents('php://input');
    // Decode the JSON data into an associative array
    $jsonData = json_decode($rawData, true);
    return $jsonData;
}