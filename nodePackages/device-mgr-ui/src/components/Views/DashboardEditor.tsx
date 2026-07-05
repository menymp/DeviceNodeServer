import React from "react";
import { useEffect, useState, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useNavigate } from "react-router-dom"
import { 
    useFetchControlsQuery, 
    Control, 
    useFetchControlTypesQuery, 
    useFetchControlByIdQuery, 
    useSaveControlMutation,
    useDeleteControlMutation 
} from "../../services/dashboardService";
import { useFetchDevicesQuery } from '../../services/deviceService'
import { ITEM_LIST_DISPLAY_CNT } from "../../constants";
import $ from 'jquery';


enum DASHBOARD_EDITOR_VIEW {
    HIDE = 0,
    INIT_DATA,
    LINK_DEVICE,
    SPECIFIC_PARAMETERS
}

const initialTableState = {
    headers: ['id', 'name', 'parameters', 'type'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const intDevicesTable = {
    headers: ['id', 'name', 'mode', 'type', 'path', 'node name'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
    selectBtn: false,
}

const DashboardEditor: React.FC = () => {
    // ToDo: Perform Proper validations
    const [dashEditViewState, setDashEditView] = useState(DASHBOARD_EDITOR_VIEW.HIDE);
    const [page, setPage] = useState<number>(0);
    const [devicePage, setDevicePage] = useState<number>(0);
    const [displayControls, setDisplayControls] = useState<tableInit>(initialTableState);
    const [selectedEditControl, setSelectedEditControl] = useState<Control>();
    const [devicesDisplay, setDevicesDisplay] = useState<tableInit>(intDevicesTable)
    const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')

    const { data: controls = [], isSuccess: controlsLoaded, refetch: refetchControls } = useFetchControlsQuery({ page, size: ITEM_LIST_DISPLAY_CNT });
    const { data: availableControlTypes = [] } = useFetchControlTypesQuery();
    const { data: selectedControl } = useFetchControlByIdQuery(
        { id: selectedEditControl?.idControl ?? -1 },
        { skip: selectedEditControl?.idControl === undefined || selectedEditControl?.idControl === -1 }
    );
    const { data: devices = [] } = useFetchDevicesQuery({ pageCount: devicePage*ITEM_LIST_DISPLAY_CNT, pageSize: ITEM_LIST_DISPLAY_CNT });
    const [saveControl, {isSuccess: controlSaved, isLoading: controlSaving}] = useSaveControlMutation();
    const [deleteControl, {isSuccess: controlDeleted, isLoading: controlDeleting}] = useDeleteControlMutation();

    const navigate = useNavigate();

    const [controlTypeSelected, setControlTypeSelected] = useState<number>(-1);

    const getControlTypeTemplate = (idType: number) => {
        const controlType = availableControlTypes?.find((type) => type.id === idType);
        return controlType?.controlTemplate ?? '';
    }

    const [newControlName, setNewControlName] = useState<string>('');
    const handleChangeControlName = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewControlName(event.target.value); //ToDo: perform validations
    }
    const [newLinkDeviceId, setNewLinkDeviceId] = useState<string>('');
    const handleChangeLinkDeviceId = (event: React.ChangeEvent<HTMLInputElement>) => {
        // TODO: still thinking if i should rewrite all this to make easier to validate
        setSelectedDeviceId(event.target.value);
        setNewLinkDeviceId(event.target.value);
        updateControlNewParameters(); //this should validate all inputs and update edit device
    } //ToDo: perform validations
    const newControlParameters = useRef<string>('');

    const updateControlNewParameters = () => {
        let tmpParameters: Record<string,any> = {};
        /*get every single field tagged for update*/
        var containerElements = document.querySelectorAll('[parameterMember="true"]');
        containerElements.forEach((obj, index)=>{
            /*add each element to the list*/
            let parameterType = $(obj).attr("parameterType");
            const value = $(obj).val() as string;
            if (value) {
                switch(parameterType)
                {
                    case 'REFERENCE':
                        tmpParameters[obj.id] = value;
                    break;
                    case 'FIELD':
                        tmpParameters[obj.id] = value;
                    break;
                    case 'NUMBER':
                        tmpParameters[obj.id] = parseInt(value);
                    break;
                    case 'SELECTOR':
                        tmpParameters[obj.id] = value;
                    break;
                }
            }
        });
        const strTmpParameters = JSON.stringify(tmpParameters);
        //
        newControlParameters.current = strTmpParameters;
        selectedEditControl && setSelectedEditControl({...selectedEditControl, parameters: strTmpParameters});
    }

    const saveControlChanges = async () => {
        try {
            if (!selectedEditControl?.idControl) {
                return;
            }

            const controlDataToSubmit = {
                idControl: selectedEditControl.idControl,
                parameters: JSON.parse(newControlParameters.current),
                Name: newControlName || selectedEditControl.Name,
                idType: controlTypeSelected === -1 ? selectedEditControl?.idType ?? -1 : controlTypeSelected,
            };

            await saveControl(controlDataToSubmit).unwrap();
            refetchControls();
        } catch(err) {
            console.error('Failed to save control', err);
        }
        cleanSelectedDevice();
    }

    const cleanSelectedDevice = () => {
        setSelectedEditControl({
            idControl: -1,
            parameters: '',
            Name: '',
            typename: '',
            idType: availableControlTypes?.[0]?.id ?? -1,
            username: '',
            controlTemplate: ''
        })
        setSelectedDeviceId('')
    }

    useEffect(() => {
        if (!devices?.length) {
            setDevicesDisplay(intDevicesTable);
            return;
        }

        const newTable = {
            headers: ['Device id', 'Name', 'Mode', 'Type', 'Path', 'Parent node'],
            rows: devices.map((device) => {return [device.idDevices.toString(), device.name, device.mode, device.type, device.channelPath, device.nodeName]}),
            selectBtn: true,
            selectCallback: (devDetails) => {
                setSelectedDeviceId(devDetails[0]);
            }
        } as tableInit;
        setDevicesDisplay(newTable);
    }, [devices]);

    useEffect(() => {
        if (!controlsLoaded || !controls || !controls.length) {
            setDisplayControls(initialTableState);
            return
        }
        //set ui fetched controls
        const newTable = {
            headers: ['id', 'name', 'parameters', 'type'],
            rows: controls.map((control) => {return [control.idControl.toString(), control.Name, control.parameters, control.typename]}),
            detailBtn: false,
            deleteBtn: true,
            editBtn: true,
            editCallback: (selectedControl) => {
                handleEditControl(selectedControl[0]) 
            },
            deleteCallback: (selectedControl) => {
                handleDeleteControl(selectedControl[0]) 
            }
        } as tableInit
        setDisplayControls(newTable);
    }, [controlsLoaded, controls])

    useEffect(() => {
        if (!selectedControl || !selectedEditControl) {
            return;
        }
        if (selectedEditControl.idControl !== selectedControl.idControl) {
            return;
        }
        setSelectedEditControl({ ...selectedEditControl, ...selectedControl });
    }, [selectedControl, selectedEditControl]);

    const parseJsonInputData = (data: string) => {
        var decodedData = JSON.parse(data);
        if("Message" in decodedData)
        {
            // alert(decodedData['Message']);
            // ToDo: use a proper log
            console.log(decodedData['Message']);
        }
        return decodedData;
    }

    const handleDeleteControl = async (idSelectControl: string) => {
        if (window.confirm('Quieres elimiar el nodo: ' + idSelectControl + '?')) {
            try {
                await deleteControl({id: parseInt(idSelectControl)}).unwrap();
                refetchControls();
            } catch (error) {
                console.error('Failed to delete control', error);
            }
        }
    }

    const renderControlTypeTemplate = (controlBaseTemplate: string, currentValues: string | undefined) => {
        try {
            ////BLOCK UNDER PORTING WORK IN PROGRESS////
            /*builds the current device template*/
            //name field is generic for every control
            const parsedTemplate = JSON.parse(controlBaseTemplate);
            const parsedObjectValues = currentValues && JSON.parse(currentValues);
            const listElements = Object.keys(parsedTemplate); // get list of keys
            //map all the keys in the template
            const uiElements = listElements.map((field) => {
                // render a control with keyProp name and contents of key
                // if its an array, render it as a dropdown menu!!!!
                let fieldType = parsedTemplate[field];
                let fieldBaseType = typeof(fieldType);
                let containerDiv;
                let input;
                let b;
                let br;

                switch(parsedTemplate[field]) {
                    case 'REFERENCE':
                        input = React.createElement('input', {
                            name: field,
                            id: field,
                            disabled: true,
                            parameterMember: "true", // tags the element as part of the parameter object
                            parameterType: fieldType, // tags the element as part of the parameter object
                            value: selectedDeviceId, // init with data if exists
                            onChange: updateControlNewParameters
                          });
                          
                          b = React.createElement('b', {
                            parameterText: true,
                            children: `${field}: `,
                          });
                          
                          br = React.createElement('br', {
                            parameterText: true,
                          });
                          
                          containerDiv = React.createElement('div', null, b, input, br);
                    break;
                    case 'FIELD':
                        input = React.createElement('input', {
                            name: field,
                            id: field,
                            disabled: false,
                            parameterMember: "true", // tags the element as part of the parameter object
                            parameterType: fieldType, // sets the type of field expected
                            value: parsedObjectValues[field] ?? undefined, // init with data if exists
                            onChange: updateControlNewParameters
                          });
                          
                          b = React.createElement('b', {
                            parameterText: true,
                            children: `${field}: `,
                          });
                          
                          br = React.createElement('br', {
                            parameterText: true,
                          });
                          containerDiv = React.createElement('div', null, b, input, br);
                    break;
                    case 'NUMBER':
                        input = React.createElement('input', {
                            name: field,
                            id: field,
                            disabled: true,
                            parameterMember: "true", // tags the element as part of the parameter object
                            parameterType: 'SELECTOR', // sets the type of field expected
                            value: parsedObjectValues[field] ?? undefined, // init with data if exists
                            onChange: updateControlNewParameters
                          });
                          
                          b = React.createElement('b', {
                            parameterText: true,
                            children: `${field}: `,
                          });
                          
                          br = React.createElement('br', {
                            parameterText: true,
                          });
                          
                          containerDiv = React.createElement('div', null, b, input, br);
                    break;
                    default:
                    /*check if array case*/
                    if(fieldBaseType == "object"){
                        const options = fieldType.map((value: string) => {
                            return React.createElement('option', {
                                value: value,
                                key: value
                            }, value);
                        });

                        const sel = React.createElement('select', {
                            name: field,
                            id: field,
                            disabled: false,
                            parameterMember: "true", // tags the element as part of the parameter object
                            parameterType: 'SELECTOR', // sets the type of field expected
                            children: options,
                            defaultValue: parsedObjectValues[field] ?? undefined,
                            onChange: updateControlNewParameters
                        });
                        
                        const b = React.createElement('b', {
                            parameterText: true
                        }, field + ': ');
                        
                        const br = React.createElement('br', {
                            parameterText: true
                        });
                        
                        containerDiv = React.createElement('div', null, b, sel, br);
                    }
                    break;
                }
                return containerDiv;
            });
            return uiElements;
        } catch {
            //nothing to be done
        }
    }

    const [controlElements, setControlElements] = useState<React.ReactNode[] | null>(null);

    const handleEditControl = (idSelectControl: string) => {
        const selectedEditControl = controls?.find((controlObj) => controlObj.idControl.toString() === idSelectControl)
        if (selectedEditControl) {
            setSelectedEditControl(selectedEditControl)
            const devId = selectedEditControl.parameters.idDevice;
            setSelectedDeviceId(devId);
            setNewLinkDeviceId(devId);
            setDashEditView(DASHBOARD_EDITOR_VIEW.INIT_DATA)
        }
        else
        {
            setDashEditView(DASHBOARD_EDITOR_VIEW.HIDE)
        }
    }

    const handleChangeControlType = (event: React.ChangeEvent<HTMLSelectElement>) => {
        /* Sets type selected and renders the parameters */
        setControlTypeSelected(parseInt(event.target.value));


        const controlType  = getControlTypeTemplate(parseInt(event.target.value));
        const elements = renderControlTypeTemplate(
                controlType,
                ""
            );
            setControlElements(elements as React.ReactNode[] | null);
    } //ToDo: perform validations

    useEffect(() => {
        if (!devices?.length) {
            setDevicesDisplay(intDevicesTable);
            return;
        }

        const newTable = {
            headers: ['Device id', 'Name', 'Mode', 'Type', 'Path', 'Parent node'],
            rows: devices.map((device) => {return [device.idDevices.toString(), device.name, device.mode, device.type, device.channelPath, device.nodeName]}),
            selectBtn: true,
            selectCallback: (devDetails) => {
                setSelectedDeviceId(devDetails[0])
            }
        } as tableInit;
        setDevicesDisplay(newTable);
    }, [devices]);

    useEffect(() => {
        if (!controlsLoaded || !controls || !controls.length) {
            setDisplayControls(initialTableState);
            return
        }
        //set ui fetched controls
        const newTable = {
            headers: ['id', 'name', 'parameters', 'type'],
            rows: controls.map((control) => {return [control.idControl.toString(), control.Name, JSON.stringify(control.parameters), control.typename]}),
            detailBtn: false,
            deleteBtn: true,
            editBtn: true,
            editCallback: (selectedControl) => {
                handleEditControl(selectedControl[0]) 
            },
            deleteCallback: (selectedControl) => {
                handleDeleteControl(selectedControl[0]) 
            }
        } as tableInit
        setDisplayControls(newTable);
    }, [controlsLoaded, controls])


    const hideEditor = () => {
        setDashEditView(DASHBOARD_EDITOR_VIEW.HIDE)
    }

    const submitData = () => {
        saveControlChanges();
        hideEditor()
    }
    
    return(
        <>
            <Modal className="modal-xl" show={dashEditViewState === DASHBOARD_EDITOR_VIEW.INIT_DATA} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - General characteristics</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>Control name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="control name ..."
                                defaultValue={selectedEditControl?.Name}
                                onChange={handleChangeControlName}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="controlDetails.type">
                            <Form.Label>Control id</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="control id..."
                                value={selectedEditControl?.idControl}
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={() => { setDashEditView(DASHBOARD_EDITOR_VIEW.LINK_DEVICE) } }>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Modal className="modal-xl" dialogClassName="width: 70%" show={dashEditViewState === DASHBOARD_EDITOR_VIEW.LINK_DEVICE} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - Link a device</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>Selected device id</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="selected control ..."
                                value={selectedDeviceId}
                                onChange={handleChangeLinkDeviceId}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="controlDetails.type">
                            <Form.Label>Available devices</Form.Label>
                        </Form.Group>
                    </Form>
                    <Container >
                        <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                            <Col xs={5} >
                                <Form className="mr-left ">
                                    <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                        <Row xs={12}>
                                            <Col xs={2}>
                                                <Form.Label>Filter</Form.Label>
                                            </Col>
                                            <Col xs={5}>
                                                <Form.Control type="text" placeholder="device name..." />
                                            </Col>
                                            <Col xs={5}>
                                                <Form.Control type="text" placeholder="parent node..." />
                                            </Col>
                                        </Row>
                                    </Form.Group>
                                </Form>
                            </Col>
                            <Col>
                                <Form className="mr-left ">
                                    <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                        <Row xs={12}>
                                            <Col xs={6}>
                                                <Button onClick={() =>{devicePage && setDevicePage(devicePage - 1)}}>Previous page</Button>
                                            </Col>
                                            <Col xs={1}>
                                                <Form.Label>{devicePage}</Form.Label>
                                            </Col>
                                            <Col xs={5}>
                                                <Button onClick={()=>{setDevicePage(devicePage + 1)}}>Next page</Button>
                                            </Col>
                                        </Row>
                                    </Form.Group>
                                </Form>
                            </Col>
                        </Row>
                        <Row>
                            <Col><BaseTable {...devicesDisplay}></BaseTable></Col>
                        </Row>
                    </Container>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={() => { setDashEditView(DASHBOARD_EDITOR_VIEW.INIT_DATA) }}>
                        Previous
                    </Button>
                    <Button variant="primary" onClick={() => { 
                        setDashEditView(DASHBOARD_EDITOR_VIEW.SPECIFIC_PARAMETERS);
                        if (!availableControlTypes || !availableControlTypes.length) {
                            return;
                        }
                        if (controlTypeSelected === -1) {
                            setControlTypeSelected(availableControlTypes[0].id);
                        }
                        }}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Modal className="modal-xl" show={dashEditViewState === DASHBOARD_EDITOR_VIEW.SPECIFIC_PARAMETERS} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - Specific characteristics</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form id="controlparameters.formcontainer">
                        <Form.Group className="mb-3" controlId="controltype.template">
                            <Form.Label>Control type</Form.Label>
                            <Form.Select onChange={handleChangeControlType} id="selectedProtocolItem">
                                {availableControlTypes?.map((value, index) => { return <option id={`${index}`} value={value.id}>{value.typename}</option>})}
                            </Form.Select>
                        </Form.Group>
                        {  controlElements?.map((element, index) => {
                                return (
                                    <Form.Group className="mb-3" controlId={`controlparameters.field${index}`}>
                                        {element}
                                    </Form.Group>
                                )
                        })}
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={() => { 
                        setDashEditView(DASHBOARD_EDITOR_VIEW.LINK_DEVICE);
                        updateControlNewParameters(); 
                    }}
                        >
                        Previous
                    </Button>
                    <Button variant="primary" onClick={() => {
                        updateControlNewParameters(); 
                        submitData();
                    }}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={ () => { 
                            cleanSelectedDevice()
                            setDashEditView(DASHBOARD_EDITOR_VIEW.INIT_DATA)
                            }}>New element</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={() => { navigate('/Dashboard') }}>Dashboard view</Button>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={6}>
                                        <Button onClick={()=>{page && setPage(page - 1)}}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Button onClick={()=>{setPage(page + 1)}}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <Col><BaseTable {...displayControls}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default DashboardEditor