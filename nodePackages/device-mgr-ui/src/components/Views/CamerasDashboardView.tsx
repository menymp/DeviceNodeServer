import React from "react";
import { useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom";
import WebSocket from 'ws';


const CamerasDashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const navigate = useNavigate();

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);
    // a pagination item already exists
/*
    let initObj;
let flagStop = 0;

$(document).ready(function () {
	fetchVideoConfigResponse();
	hideViewForm();
});

$("#submitNewView").click(function(){
	showViewForm();
});

$("#newConfig").click(function(){
	showViewForm();
});

$("#editConfig").click(function(){
	showViewForm();
});

$("#deleteConfig").click(function(){
});

function hideViewForm()
{
	$('#newConfigForm').hide();
	$('#videofield').show();
}

function showViewForm()
{
	$('#newConfigForm').show();
	$('#videofield').hide();
}

function getFrame()
{
	var image = document.getElementById("videofield");
	image.src = "http://localhost:9090/video_feed?vidArgs="+JSON.stringify(initObj[0]['configJsonFetch']);
}
	
function videoLoopStart() {
	getFrame();
	setTimeout(() => {
		if(flagStop == 1)
		{
			videoLoopStart();
		}
	}, 10);
}

$("#startVideo").click(
	function(){
		flagStop = 1;
		videoLoopStart();
})

$("#stopVideo").click(
	function(){
		flagStop = 0;
	}
)

function fetchVideoConfigResponse()
{
	$.ajax({
		url: "camerasDashboardActions.php",
		type: "POST",
		data:({actionOption:"fetchConfigs"}),
		cache: false,
		success: function(data)
		{
			initObj = JSON.parse(data);
			if("Message" in initObj)
			{
				$('#outputMessage').text(decodedData['Message']);
			}
		}
	});
}
*/
    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Cameras dashboard</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="deviceParentNode.name">
                            <Form.Label>Height</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="height ..."
                                autoFocus
                            />
                            <Form.Label>Width</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="width ..."
                                autoFocus
                            />
                            <Form.Label>Row Length</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="row length ..."
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Save
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={handleShow}>Editor</Button>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={5}>
                                        <Button>Next page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label> 10 </Form.Label>
                                    </Col>
                                    <Col xs={6}>
                                        <Button>Previous page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                </Row>
            </Container>
        </>
    )
}

export default CamerasDashboardView