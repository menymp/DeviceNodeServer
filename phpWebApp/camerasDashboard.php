<?php
	require "header.php";
?>

	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">

	<input id="camName" placeholder="camera name...">
	<input id="camArgs" placeholder="json args...">
	<button id="createCamBtn">create camera</button>
	<button id="saveCamBtn">save camera</button>
	<button id="deleteCamBtn">delete camera</button>

 <button id="previous">Previous Page</button>
 <button id="next">Next Page</button>
  <div id="outputMessage"></div>		
  <h2>View data</h2>
	<table id="tableCams" class="table table-bordered table-sm" >
    <tbody >
    </tbody>
  </table>
</div>';
	}
?>
<script>
</script>
<?php
	require "footer.php";
?>