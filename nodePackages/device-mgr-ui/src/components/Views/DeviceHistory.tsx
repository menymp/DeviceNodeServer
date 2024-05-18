import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchDevicesMutation, useFetchDeviceByIdMutation, device } from '../../services/deviceService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'
import useControlUtils from "../../hooks/useControlUtils";
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../types/ControlTypes'

export type DeviceHistoryParameters = {
    idDevice: string,
    ws: WebSocket
}

type GetHistoryParameters = {
    idDevice: string, 
    servercommand: string
}

type HistoryRow = {
    value: string,
    date: string
}

const initialTableState = {
    headers: ['Value', 'upload date'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const DeviceHistory = (params:  DeviceHistoryParameters) => {
    const {ws, idDevice} = params
    const [getDeviceById, {isSuccess: selectedDeviceFound, data: matchDevices}] = useFetchDeviceByIdMutation()
    const [measuresDisplay, setMeasuresDisplay] = useState<tableInit>(initialTableState)

    useEffect(() => {
        getDeviceById({deviceId: parseInt(idDevice)});

    },[])

    const getControlParameters = () => {
        return {idDevice, servercommand: "getMeasures"} as GetHistoryParameters;
    }

    const update = (response: updateResponse) => {
        ///////////////////////////////////////
        /** begins user specific code * */
        const { servercommand } = getControlParameters()
        let check = false;
        if(response.syscommand !== servercommand)
        {
            //discard all unrelated messages
            return
        }
        if(response.state === 'SUCCESS')
        {
            // decode the expected history
            displayHistoryTable(JSON.parse(response.result) as Array<HistoryRow>)
        }
        /* ends user specific code */
        //////////////////////////////////////////////////
    }


    const displayHistoryTable = (list: Array<HistoryRow>) => {
        try {
            const newTable = {
                headers: ['Value', 'upload date'],
                rows: list.map((row) => {return [row.value, row.date]}),
            } as tableInit
            setMeasuresDisplay(newTable)
        } catch (error) {
            console.log(error);
        }
    }
    const { commandHandler } = useControlUtils({ getControlParameters, ws, update});
    
    return(
        <>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={5} >
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={2}>
                                        <Form.Label>Last measures</Form.Label>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <Col><BaseTable {...measuresDisplay}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default DeviceHistory